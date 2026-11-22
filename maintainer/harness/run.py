#!/usr/bin/env python3
"""Run guidance scenarios against agent CLIs, sandboxed, and record evidence (repository-only).

  run.py --out DIR [--agents claude,codex,copilot,agy] [--scenarios S2,S12 | --suite phase2] [--runs 1,2]
         [--workers 3] [--guidance PATH | --no-install] [--label NAME]

Agents are CLI names, optionally with a model: claude@claude-haiku-5-5, codex@gpt-6-luna,
copilot@gemini-3.8-flash, agy@gemini-3.8-flash-medium.

--out is required and must be outside this repository: raw runs are bulky and contain local paths
(see MAINTAINING.md). Results go to OUT/logs/<label>/<scenario>-r<n>/evidence.json
and fixtures to OUT/fx/<label>/. Finished runs are skipped, so an interrupted batch can be rerun.

By default the current checkout, including uncommitted changes, is copied to OUT/snapshots/<name> and
committed there, because the upgrade procedure (S11) expects a clean guidance checkout. --guidance uses
an existing snapshot instead, for example one built from an earlier v4 release.
--no-install builds the fixtures without the package, for a no-guidance baseline; S1, S11, S16, and S18 are
skipped because they set up or upgrade the guidance itself.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shlex
import argparse, errno, fnmatch, json, os, re, shutil, stat, subprocess, sys, tempfile, threading, time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SANDBOX = HERE / 'sandbox.sh'
STEP_TIMEOUT = 25 * 60
NO_INSTALL_SKIP = {'S1', 'S11', 'S16', 'S18'}  # these set up or upgrade the guidance itself
GUIDANCE_FOR_COPILOT = None  # set in main() to the guidance snapshot
print_lock = threading.Lock()
GIT_ID = ['-c', 'user.name=Scenario Snapshot', '-c', 'user.email=snapshot@example.invalid',
          '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']


def _open_rel_nofollow(base_dir, rel_path, flags=os.O_RDONLY):
    """Open a regular file inside base_dir without following symlinks or '..' traversal, or return None."""
    p = rel_path if isinstance(rel_path, Path) else Path(str(rel_path))
    if not str(rel_path) or p.is_absolute():
        return None
    parts = [part for part in p.parts if part and part != '.']
    if not parts or any(part == '..' for part in parts):
        return None
    dfd = None
    try:
        dfd = os.open(str(base_dir), os.O_RDONLY | os.O_DIRECTORY)
        for part in parts[:-1]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dfd)
            os.close(dfd)
            dfd = nxt
        fd = os.open(parts[-1], flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dfd)
        os.close(dfd)
        dfd = None
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            return None
        return fd
    except OSError:
        if dfd is not None:
            try:
                os.close(dfd)
            except OSError:
                pass
        return None


def safe_is_file(base_dir, rel_path):
    """Whether base_dir/rel_path is a regular file reachable without following any symlink."""
    fd = _open_rel_nofollow(base_dir, rel_path)
    if fd is None:
        return False
    os.close(fd)
    return True


def safe_read_text(base_dir, rel_path, default=None):
    """Read UTF-8 text from base_dir/rel_path without following any symlink, or return default."""
    fd = _open_rel_nofollow(base_dir, rel_path)
    if fd is None:
        return default
    with os.fdopen(fd, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def safe_write_text(base_dir, rel_path, text):
    """Write UTF-8 text to base_dir/rel_path, refusing to traverse or overwrite symlinks."""
    p = rel_path if isinstance(rel_path, Path) else Path(str(rel_path))
    parts = [part for part in p.parts if part and part != '.']
    if not str(rel_path) or p.is_absolute() or not parts or any(part == '..' for part in parts):
        raise ValueError(f'Unsafe relative path: {rel_path!r}')
    dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    dfd = os.open(str(base_dir), os.O_RDONLY | os.O_DIRECTORY)
    fd = None
    try:
        for part in parts[:-1]:
            try:
                nxt = os.open(part, dir_flags, dir_fd=dfd)
            except FileNotFoundError:
                os.mkdir(part, 0o755, dir_fd=dfd)
                nxt = os.open(part, dir_flags, dir_fd=dfd)
            os.close(dfd)
            dfd = nxt
        fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_NONBLOCK, 0o644, dir_fd=dfd)
    finally:
        os.close(dfd)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise OSError(errno.EINVAL, 'Refusing to write non-regular file', str(rel_path))
    with os.fdopen(fd, 'w', encoding='utf-8', errors='replace') as f:
        f.write(text)


def safe_codex_sessions(home, session):
    """Read Codex rollout JSONL files under home/.codex/sessions matching session without following symlinks."""
    home_p = Path(home)
    codex_dir = home_p / '.codex'
    sess_dir = codex_dir / 'sessions'
    if codex_dir.is_symlink() or not codex_dir.is_dir() or sess_dir.is_symlink() or not sess_dir.is_dir():
        return []
    pattern = f'rollout-*{session}.jsonl'
    rels = []
    for dirpath, dirnames, filenames in os.walk(sess_dir, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not (Path(dirpath) / d).is_symlink())
        rel_dir = Path(dirpath).relative_to(home_p)
        for name in filenames:
            if fnmatch.fnmatch(name, pattern):
                rels.append(rel_dir / name)
    texts = []
    for rel_file in sorted(rels):
        raw = safe_read_text(home_p, rel_file)
        if raw is not None:
            texts.append(raw)
    return texts


def log(msg):
    with print_lock:
        print(time.strftime('%H:%M:%S'), msg, flush=True)


HOST_SAFE_GIT = ('-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-c', 'protocol.ext.allow=never')
SAFE_GIT = ('env', 'GIT_CONFIG_NOSYSTEM=1', 'git', '--no-pager', *HOST_SAFE_GIT,
            '-c', 'core.excludesFile=/dev/null', '-c', 'core.pager=cat', '-c', 'safe.directory=*')
NO_EXT_DIFF_CMDS = {'diff', 'show', 'log', 'diff-files', 'diff-index', 'diff-tree'}


def safe_git_args(args):
    if args and args[0] in NO_EXT_DIFF_CMDS and '--no-ext-diff' not in args:
        return (args[0], '--no-ext-diff', '--no-textconv', *args[1:])
    return args


def git(cwd, *args, check=False):
    r = subprocess.run(['git', '-C', str(cwd), *HOST_SAFE_GIT, *safe_git_args(args)], capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def is_bytecode_path(path):
    """Whether a git path refers to a Python bytecode cache (__pycache__/, *.pyc, *.pyo)."""
    rel = path.strip()
    if len(rel) >= 2 and rel[0] == '"' and rel[-1] == '"':
        rel = rel[1:-1]
    return '__pycache__' in Path(rel).parts or rel.endswith(('.pyc', '.pyo'))


def filter_untracked_bytecode(porcelain_lines):
    """Drop empty lines and untracked Python bytecode entries; keep staged/modified entries and all other files."""
    out = []
    for line in porcelain_lines:
        if not line.strip():
            continue
        if line.startswith('?? ') and is_bytecode_path(line[3:]):
            continue
        out.append(line)
    return out


def fixture_git(cwd, *args, check=False, strip=False, timeout=30):
    """Run a read-only git command inside sandbox.sh with isolated config and hostile-hook overrides."""
    if not Path(cwd).is_dir():
        if check:
            raise SystemExit(f"git directory does not exist: {cwd}")
        return ''
    try:
        r = run_fixture_cmd(cwd, [*SAFE_GIT, *safe_git_args(args)], timeout=timeout, read_only=True)
    except subprocess.TimeoutExpired:
        if check:
            raise SystemExit(f"git {' '.join(args)} timed out")
        return ''
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip() if strip else r.stdout


def checkouts(repo):
    """Every worktree of this repository, the main checkout included: run from one worktree, the others must be hidden too."""
    listing = subprocess.run(['git', '-C', str(repo), 'worktree', 'list', '--porcelain'], capture_output=True, text=True).stdout
    return [repo] + [Path(line[len('worktree '):]) for line in listing.splitlines() if line.startswith('worktree ')]


def snapshot(out):
    """Copy this checkout (tracked and untracked, not ignored) to a clean committed snapshot.

    A dirty checkout is named by a hash of its contents, so identical trees share one snapshot. Creation is
    locked and atomic, so several run.py processes can start at once."""
    import fcntl, hashlib, tempfile
    head = git(REPO, 'rev-parse', '--short', 'HEAD') or 'nohead'
    # Python bytecode caches are never part of the guidance, even when no ignore file hides them.
    keep = lambda f: f and '__pycache__' not in f.split('/') and (REPO / f).is_file()
    files = sorted(f for f in git(REPO, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split('\0') if keep(f))
    dirty = any('__pycache__' not in line for line in git(REPO, 'status', '--porcelain').splitlines())
    name = head
    if dirty:
        digest = hashlib.sha256()
        for f in files:
            digest.update(f.encode() + b'\0' + (REPO / f).read_bytes() + b'\0')
        name += '-dirty-' + digest.hexdigest()[:10]
    root = out / 'snapshots'
    root.mkdir(parents=True, exist_ok=True)
    dest = root / name
    with open(root / '.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (dest / '.git').is_dir():
            return dest
        tmp = Path(tempfile.mkdtemp(prefix='.building-', dir=root))
        for f in files:
            (tmp / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / f, tmp / f)
        git(tmp, 'init', '-q', '-b', 'main', '--template=', check=True)
        git(tmp, *GIT_ID, 'add', '-A', check=True)
        git(tmp, *GIT_ID, 'commit', '-q', '-m', f'Scenario snapshot of {head}' + (' with uncommitted changes' if dirty else ''), check=True)
        tmp.rename(dest)
    return dest


def clear_tree(repo):
    """Remove everything in a work tree except .git."""
    for p in repo.iterdir():
        if p.name != '.git':
            shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()


def baselines(view):
    """Earlier releases' commits in an agent view, keyed by the release commit they were made from."""
    path = view / '.git' / 'scenario-baselines.json'
    return path.read_text().strip() if path.is_file() else '{}'


MAINTAINER_AGENTS = (
    'Generated by manage.py --sync from maintainer/roles/',
    'Generated by check_package.py --sync-adapters from maintainer/roles/',
)


def maintainer_only(path):
    """Repository files agents under test must not see: maintainer/, and MAINTAINING.md, whose log records scoring
    criteria such as S29's checks."""
    return path.startswith('maintainer/') or path == 'MAINTAINING.md'


def agent_view(snap):
    """The guidance an agent is shown: the snapshot without maintainer/ or MAINTAINING.md, so it cannot read the
    scenarios, the scorer, past results or the scoring criteria in the maintenance log (a Copilot + Flash run read score.py and copied a fixture's open items into a real plan)."""
    dest = snap.parent / (snap.name + '-agent')
    if (dest / '.git').is_dir():
        return dest
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix='.building-', dir=snap.parent))
    git(tmp, 'init', '-q', '-b', 'main', '--template=', check=True)
    # Earlier releases that scenarios install (install_ref) become ancestor commits, as in a real clone, so the
    # upgrade planner can read the installed baseline. Their maintainer/ and MAINTAINING.md are left out too; the fixture builder records
    # each release under its new commit (SCENARIO_BASELINES).
    catalog = snap / 'maintainer' / 'scenarios.json'
    refs = sorted({s['install_ref'] for s in json.loads(catalog.read_text())['scenarios'] if s.get('install_ref')}) if catalog.is_file() else []
    baselines = {}
    for ref in refs:
        clear_tree(tmp)
        archive = subprocess.run(['git', '-C', str(REPO), 'archive', ref], capture_output=True, check=True).stdout
        subprocess.run(['tar', '-x', '-C', str(tmp), '--exclude=maintainer', '--exclude=MAINTAINING.md'], input=archive, check=True)
        when = git(REPO, 'show', '-s', '--format=%cI', f'{ref}^{{commit}}')
        env = {**os.environ, 'GIT_AUTHOR_DATE': when, 'GIT_COMMITTER_DATE': when}
        for args in (['add', '-A'], ['commit', '-q', '-m', f'Release {ref} for agents, without maintainer files']):
            r = subprocess.run(['git', '-C', str(tmp), *GIT_ID, *args], capture_output=True, text=True, env=env)
            if r.returncode:
                raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
        baselines[ref] = git(tmp, 'rev-parse', 'HEAD')
    clear_tree(tmp)
    for f in git(snap, 'ls-files', '-z').split('\0'):
        # Maintainer agents (generated from maintainer/roles, MAINTAINING.md) stay out with maintainer/ itself.
        if f and not maintainer_only(f) and not any(m in (snap / f).read_text(errors='replace') for m in MAINTAINER_AGENTS):
            (tmp / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(snap / f, tmp / f)
    git(tmp, *GIT_ID, 'add', '-A', check=True)
    git(tmp, *GIT_ID, 'commit', '-q', '-m', f'Guidance for agents, from snapshot {snap.name}', check=True)
    (tmp / '.git' / 'scenario-baselines.json').write_text(json.dumps(baselines) + '\n')
    try:
        tmp.rename(dest)
    except OSError:  # another run.py made it first
        shutil.rmtree(tmp, ignore_errors=True)
    return dest


def scenarios(guidance, shown=None, catalog=None):
    """The scenarios to run: the snapshot's catalog, or another one (the private holdout set) given as catalog."""
    data = json.loads((catalog or guidance / 'maintainer' / 'scenarios.json').read_text())['scenarios']
    for s in data:
        sub = lambda x: x.replace('{guidance}', str(shown or guidance))
        s['prompts'] = [sub(s['prompt'])] + [sub(f) for f in s.get('followups', [])]
    return {s['id']: s for s in data}


def load_suites(guidance, catalog=None):
    """Named scenario suites from the catalog, or {} when none are defined."""
    return json.loads((catalog or guidance / 'maintainer' / 'scenarios.json').read_text()).get('suites', {})


def select_scenario_ids(all_s, suites, scenarios_arg='', suite_arg='', no_install=False):
    """Resolve and validate the scenario IDs to run."""
    if scenarios_arg and suite_arg:
        raise ValueError('--scenarios and --suite cannot be combined')
    number = lambda x: int(m.group(1)) if (m := re.match(r'[A-Z]+(\d+)', x)) else 0
    if suite_arg:
        if suite_arg not in suites:
            known = ', '.join(sorted(suites)) or '(none)'
            raise ValueError(f'unknown suite {suite_arg!r}; choose from {known}')
        ids = list(suites[suite_arg])
    elif scenarios_arg:
        ids = scenarios_arg.split(',')
    else:
        ids = sorted(all_s, key=lambda x: (x != 'S12', number(x), x))
    if no_install:
        ids = [i for i in ids if i not in NO_INSTALL_SKIP]
    unknown = [i for i in ids if i not in all_s]
    if unknown:
        raise ValueError('unknown scenarios: ' + ', '.join(unknown))
    return ids


# Reasoning effort every CLI accepts. The harness passes one explicitly (V4-18): left to the CLI, it followed the
# maintainer's own settings until DOC-085, then each CLI's default, and changed silently with either.
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')
DEFAULT_EFFORT = 'medium'


def model_effort(model):
    """An Antigravity model ID carries its effort as a suffix (gemini-3.8-flash-medium); None if it has none."""
    return next((e for e in EFFORTS if model.endswith('-' + e)), None)


def agent_cmd(agent, prompt, session, logdir, step, fx, effort=DEFAULT_EFFORT):
    """Command for one step; session is None for the first step."""
    base, _, model = agent.partition('@')
    if base == 'claude':
        # --strict-mcp-config with no --mcp-config: no MCP server, so an account connector (claude.ai Docs) that
        # connects in some runs and not others neither varies the results nor reaches the maintainer's documents.
        cmd = ['claude', '-p', prompt, '--permission-mode', 'acceptEdits',
               '--allowedTools', 'Bash Edit Write Read Glob Grep', '--output-format', 'stream-json', '--verbose',
               '--effort', effort, '--strict-mcp-config']
        cmd += ['--resume', session] if session else []
    elif base == 'codex':
        # workspace-write makes .git read-only; list it as a writable root so commits and branches work.
        git_root = ['-c', f'sandbox_workspace_write.writable_roots=["{fx}/.git"]']
        model_opt = (['-m', model] if model else []) + ['-c', f'model_reasoning_effort="{effort}"']
        if session:
            return ['codex', 'exec', 'resume', *model_opt, '-c', 'sandbox_mode="workspace-write"', *git_root, '--json', session, prompt]
        return ['codex', 'exec', *model_opt, '--sandbox', 'workspace-write', *git_root, '--json', prompt]
    elif base == 'copilot':
        # Folder trust comes from COPILOT_ALLOW_ALL=true (set in run_one), which also applies to resumed
        # sessions; --trust-folder cannot be combined with --resume.
        cmd = ['copilot', '-p', prompt, '--allow-all-tools', '--share', str(logdir / f'step{step}-share.md'),
               '--reasoning-effort', effort]
        cmd += [f'--resume={session}'] if session else []
        # S11 reads the guidance snapshot outside the project; Copilot's path guard needs it named (read-only in bwrap).
        cmd += ['--add-dir', str(GUIDANCE_FOR_COPILOT)] if GUIDANCE_FOR_COPILOT else []
    elif base == 'agy':
        cmd = ['agy', '-p', prompt, '--dangerously-skip-permissions', '--output-format', 'stream-json']
        cmd += ['--conversation', session] if session else []
        # The model ID names the effort (main() checks it matches); a model ID without one gets it as a flag.
        cmd += [] if model_effort(model) else ['--effort', effort]
    else:
        raise SystemExit(f'Unknown agent CLI: {base}')
    return cmd + (['--model', model] if model else [])


def json_lines(text):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('{'):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                pass


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def copilot_messages(share):
    """All assistant messages in a Copilot session export, oldest first, or None without an export.

    Copilot's stdout mixes replies with tool output (with some models it prints every command's full output),
    so the export, where each assistant message has its own "### Copilot" section, is the reliable source.
    The export is cumulative across a resumed session."""
    text = safe_read_text(share.parent, share.name)
    if text is None:
        return None
    sections = re.split(r'\n---\n', text)
    return [s.split('### Copilot', 1)[1].strip() for s in sections if re.search(r'^### Copilot\s*$', s, re.M)]


def cli_name(agent):
    """The CLI behind an agent label: "copilot@gpt-6.1-sol" and the older labels "copilot-sol" or "agy-flash" alike."""
    base = agent.partition('@')[0]
    return next((name for name in ('claude', 'codex', 'copilot', 'agy') if base.startswith(name)), base)


def step_messages(agent, out, logdir, step):
    """Everything the agent said to the user in one step, oldest first. The last item is its final reply."""
    base = cli_name(agent)
    if base == 'copilot':
        now = copilot_messages(logdir / f'step{step}-share.md')
        before = copilot_messages(logdir / f'step{step - 1}-share.md') if step > 1 else []
        return now[len(before or []):] if now is not None else None
    events = list(json_lines(out))
    if base == 'claude':
        return [c['text'] for ev in events if ev.get('type') == 'assistant'
                for c in ev.get('message', {}).get('content', []) if c.get('type') == 'text' and c.get('text', '').strip()]
    if base == 'codex':
        return [ev['item'].get('text', '') for ev in events
                if ev.get('type') == 'item.completed' and ev.get('item', {}).get('type') == 'agent_message']
    if base == 'agy':
        return [d['response'] for ev in events for d in walk(ev) if isinstance(d.get('response'), str)]
    return None


COMMAND_KEYS = {'command', 'cmd', 'CommandLine', 'commandLine', 'command_line'}


def parse_step(agent, out, logdir, step):
    """Return (session_id, final_reply, shell_commands) from one step's output."""
    base = cli_name(agent)
    session, final, commands = None, '', []
    if base == 'copilot':
        m = re.search(r'--resume=([0-9a-f-]{36})', out)
        session = m.group(1) if m else None
        share = logdir / f'step{step}-share.md'
        messages = step_messages(agent, out, logdir, step)
        final = messages[-1] if messages else None
        if final is None:
            # No export: fall back to stdout without the tool-call trace (lines starting with ●, │, └, ✗ or ✓).
            final = re.split(r'\n(?:Session exported to:|Changes |AI Credits)', out)[0]
            final = '\n'.join(l for l in final.splitlines() if not re.match(r'\s*[●│└✗✓]', l)).strip()
        text = safe_read_text(share.parent, share.name)
        if text is not None:
            # The export is cumulative across a resumed session; checks.py counts only commands new to each step.
            commands = re.findall(r'^\$ (.+)$', text, re.M) + re.findall(r'"command":\s*"((?:[^"\\]|\\.)*)"', text)
        return session, final, commands
    events = list(json_lines(out))
    for ev in events:
        for d in walk(ev):
            for k in ('session_id', 'thread_id', 'conversation_id'):
                if isinstance(d.get(k), str) and not session:
                    session = d[k]
            for k in COMMAND_KEYS:
                v = d.get(k)
                if isinstance(v, str):
                    commands.append(v)
                elif isinstance(v, list) and all(isinstance(x, str) for x in v):
                    commands.append(' '.join(v))
    if base == 'claude':
        final = next((ev.get('result', '') for ev in reversed(events) if ev.get('type') == 'result'), '')
    elif base == 'codex':
        msgs = [ev['item'].get('text', '') for ev in events
                if ev.get('type') == 'item.completed' and ev.get('item', {}).get('type') == 'agent_message']
        final = msgs[-1] if msgs else ''
    elif base == 'agy':
        # The final reply is a "response" string inside the last result event, nested one or two levels down.
        replies = [d['response'] for ev in events for d in walk(ev) if isinstance(d.get('response'), str)]
        final = replies[-1] if replies else ''
    return session, final, commands


def tree(fx):
    """The fixture's HEAD and its changed tracked files, recorded after each step (untracked notes do not count)."""
    status = fixture_git(fx, 'status', '--porcelain', '--untracked-files=no')
    return {'head': fixture_git(fx, 'rev-parse', 'HEAD', strip=True), 'changed': status.splitlines()}


def run_fixture_cmd(fx, cmd, timeout=120, read_only=False):
    """Execute one fixture command inside sandbox.sh with empty HOME/tmp, wiped env, and no network."""
    if not SANDBOX.is_file():
        return subprocess.CompletedProcess(cmd, 127, '', 'sandbox.sh not found')
    fx_resolved = Path(fx).resolve()
    with tempfile.TemporaryDirectory(prefix='guidance-probe-') as d:
        sb = Path(d)
        home, logdir, guidance = sb / 'home', sb / 'log', sb / 'guidance'
        for p in (home, logdir, guidance):
            p.mkdir()
        env = {
            **os.environ,
            'SB_HOME': str(home),
            'SB_LOGDIR': str(logdir),
            'SB_GUIDANCE': str(guidance),
            'SB_SIGN_IN': '',
            'SB_TRUST': '0',
            'SB_KEYRING': '0',
            'SB_OFFLINE': '1',
            'SB_RO_FIX': '1' if read_only else '0',
        }
        home_path = Path.home()
        py_prefix = Path(sys.executable).resolve().parent.parent
        if py_prefix.is_relative_to(home_path) and py_prefix != home_path:
            default_tools = ' '.join(
                f'{home_path}/{p}' for p in (
                    '.local/bin', '.local/share/mise', '.config/mise', '.local/share/uv',
                    '.local/share/pop-workstation', '.cargo/bin', '.rustup', 'go/bin'))
            base_tools = env.get('SB_TOOLS', '') or default_tools
            if str(py_prefix) not in base_tools.split():
                env['SB_TOOLS'] = f'{base_tools} {py_prefix}'.strip()
        if not fx_resolved.is_relative_to(REPO):
            hide = env.get('SB_HIDE', '').split()
            if str(REPO) not in hide:
                hide.append(str(REPO))
            env['SB_HIDE'] = ' '.join(hide)
        return subprocess.run(
            [str(SANDBOX), str(fx_resolved), *cmd],
            capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, timeout=timeout,
        )


def evidence(fx):
    # Collect git state and fixture files before running tests/verify so test side effects cannot alter scored state.
    first = fixture_git(fx, 'rev-list', '--max-parents=0', 'HEAD', strip=True)
    lines = lambda p: len(raw.splitlines()) if (raw := safe_read_text(fx, p)) is not None else None
    branch = fixture_git(fx, 'branch', '--show-current', strip=True)
    branches = fixture_git(fx, 'branch', '--format=%(refname:short)', strip=True).splitlines()
    git_log = fixture_git(fx, 'log', '--oneline', '--all', strip=True).splitlines()
    status = filter_untracked_bytecode(fixture_git(fx, 'status', '--porcelain', '--untracked-files=all').splitlines())
    changed_vs_initial = fixture_git(fx, 'diff', '--name-status', first, '--', '.', strip=True).splitlines() if first else []
    untracked = [p for p in fixture_git(fx, 'ls-files', '--others', '--exclude-standard', strip=True).splitlines()
                 if p and not is_bytecode_path(p)]
    profile_lines = lines('PROJECT_PROFILE.md')
    open_work_lines = lines('docs/OPEN_WORK.md')
    rev_raw = safe_read_text(fx, 'review/REVISION')
    review_revision = rev_raw.strip() if rev_raw is not None else None
    with tempfile.TemporaryDirectory(prefix='guidance-test-') as test_tmp:
        test_fx = Path(test_tmp) / 'fx'
        shutil.copytree(fx, test_fx, symlinks=True, ignore=shutil.ignore_patterns('__pycache__'))
        try:
            tests = run_fixture_cmd(test_fx, [sys.executable, '-B', '-m', 'unittest', '-q'], timeout=120)
            tests_pass = tests.returncode == 0
            tests_tail = ((tests.stderr or tests.stdout).strip().splitlines() or [''])[-1]
        except subprocess.TimeoutExpired:
            tests_pass, tests_tail = False, 'timed out'
    check = None
    if safe_is_file(fx, 'scripts/verify.py'):
        try:
            r = run_fixture_cmd(fx, [sys.executable, '-B', 'scripts/verify.py'], timeout=60, read_only=True)
            check = (r.stdout + r.stderr).strip().splitlines()[:12]
        except subprocess.TimeoutExpired:
            check = ['timed out']
    elif safe_is_file(fx, 'check_package.py'):
        try:
            r = run_fixture_cmd(fx, [sys.executable, '-B', 'check_package.py'], timeout=60, read_only=True)
            # Keep the problem lines too (an adapter problem has no colon), so a failure can be told from an environment block.
            check = (r.stdout + r.stderr).strip().splitlines()[:12]
        except subprocess.TimeoutExpired:
            check = ['timed out']
    return {
        'branch': branch,
        'branches': branches,
        'log': git_log,
        'status': status,
        'changed_vs_initial': changed_vs_initial,
        'untracked': untracked,
        'profile_lines': profile_lines,
        'open_work_lines': open_work_lines,
        'tests_pass': tests_pass,
        'tests_tail': tests_tail,
        'check_package': check,
        'review_revision': review_revision,
    }


VERSIONS = {}


def cli_version(agent):
    """First line of `<cli> --version`, cached per CLI."""
    base = agent.partition('@')[0]
    if base not in VERSIONS:
        r = subprocess.run([base, '--version'], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        VERSIONS[base] = ((r.stdout or r.stderr).strip().splitlines() or ['unknown'])[0]
    return VERSIONS[base]


LIMIT = re.compile(r"(?i)hit your (?:\S+ )?limit|usage limit|quota exceeded|resource.?exhausted")


def observed_settings(agent, first_out, home, session):
    """What the CLI reports it ran with, read before the run's home is deleted: Claude Code's init event (model,
    MCP servers, plugins, skills) and Codex's session record (model, reasoning effort). Other CLIs record none."""
    base = cli_name(agent)
    if base == 'claude':
        init = next((e for e in json_lines(first_out) if e.get('subtype') == 'init'), None)
        if init:
            return {'model': init.get('model'), 'mcp_servers': sorted(m.get('name') for m in init.get('mcp_servers') or []),
                    'plugins': sorted(p.get('name') for p in init.get('plugins') or []), 'skills': len(init.get('skills') or [])}
    if base == 'codex' and session:
        for text in safe_codex_sessions(home, session):
            for e in json_lines(text):
                if e.get('type') == 'turn_context':
                    p = e.get('payload') or {}
                    return {'model': p.get('model'), 'effort': p.get('effort')}
    return {}


def codex_spawns(agent, home, session):
    """Codex's subagent spawns in one run, read from its session record before the run's home is deleted: its print
    mode's JSON shows only the wait for a subagent, not which agent it started. Each is the spawn's agent type, task
    name and argument names (the message itself is stored encrypted); None for other CLIs or without a session record."""
    if cli_name(agent) != 'codex' or not session:
        return None
    texts = safe_codex_sessions(home, session)
    if not texts:
        return None
    spawns = []
    for text in texts:
        for e in json_lines(text):
            p = e.get('payload') if isinstance(e.get('payload'), dict) else {}
            if p.get('type') == 'function_call' and p.get('name') == 'spawn_agent':
                try:
                    args = json.loads(p.get('arguments') or '{}')
                except ValueError:
                    args = {}
                args = args if isinstance(args, dict) else {}
                spawns.append({'agent_type': args.get('agent_type') or args.get('agent') or args.get('role') or 'default',
                               'task_name': str(args.get('task_name') or '')[:200], 'keys': sorted(args)})
    return spawns


def run_one(opts, agent, s, n):
    sid, label = s['id'], opts.label or agent
    fx = opts.out / 'fx' / label / f'{sid}-r{n}'
    logdir = opts.out / 'logs' / label / f'{sid}-r{n}'
    if (logdir / 'evidence.json').is_file():
        return
    shutil.rmtree(fx, ignore_errors=True)
    shutil.rmtree(logdir, ignore_errors=True)
    logdir.mkdir(parents=True)
    fx.parent.mkdir(parents=True, exist_ok=True)
    builder = (REPO if opts.no_install else opts.guidance) / 'maintainer' / 'run_scenario.py'
    # Snapshots have no history, so scenarios that install an earlier release (install_ref) take it from this repository.
    catalog = ['--scenarios', str(opts.catalog)] if opts.catalog else []
    b = subprocess.run([sys.executable, str(builder), *catalog, sid, str(fx)] + (['--no-install'] if opts.no_install else []),
                       capture_output=True, text=True, env={**os.environ, 'SCENARIO_HISTORY_REPO': str(REPO), 'SCENARIO_BASELINES': baselines(opts.shown)})
    if b.returncode:
        log(f'BUILD FAIL {label} {sid} r{n}: {(b.stdout + b.stderr).strip()[-300:]}')
        return
    # The run's own home and scratch share folders (sandbox.sh): kept separate from logdir so agents cannot write or symlink into host logs.
    home = opts.out / 'homes' / label / f'{sid}-r{n}'
    share_dir = opts.out / 'shares' / label / f'{sid}-r{n}'
    shutil.rmtree(home, ignore_errors=True)
    shutil.rmtree(share_dir, ignore_errors=True)
    share_dir.mkdir(parents=True)
    env = {**os.environ, 'SB_HOME': str(home), 'SB_LOGDIR': str(share_dir), 'SB_GUIDANCE': str(opts.shown),
           'SB_HIDE': ' '.join(map(str, opts.hide)), 'SB_TRUST': '0' if opts.untrusted else '1'}
    try:
        if opts.dry_run:
            # No agent: from inside the sandbox, each hidden folder may show only the folders leading to this run's own
            # mounts (fixture, scratch share dir, guidance view), and the fixture must be writable.
            checks = []
            for h in opts.hide:
                allowed = {p.relative_to(h).parts[0] for p in (fx, share_dir, opts.shown) if p.is_relative_to(h) and p != h}
                keep = ' '.join(f'-e {a}' for a in sorted(allowed)) or '-e /'
                checks.append(f'extra=$(ls -A {h} 2>/dev/null | grep -v -x {keep}); [ -z "$extra" ] || echo "VISIBLE in {h}: $extra"')
            # The home folder is the run's own (finding 54): no history, keys or earlier CLI sessions, and the
            # scenario git identity with no credential helper.
            private = ('.zsh_history', '.bash_history', '.ssh', '.gnupg', '.local/share/keyrings', '.claude/projects',
                       '.claude/history.jsonl', '.claude.json', '.codex/sessions', '.copilot/session-state',
                       '.gemini/antigravity-cli/conversations', '.config/gh', '.config/rclone')
            checks.append('for f in ' + ' '.join(private) + '; do [ -e "$HOME/$f" ] && echo "VISIBLE in home: $f"; done')
            # The only Codex configuration is the trust of this fixture (or none, with --untrusted).
            trust = '' if opts.untrusted else f'[projects."{fx.resolve()}"]\ntrust_level = "trusted"\n'
            checks.append(f'[ "$(cat "$HOME/.codex/config.toml" 2>/dev/null)" = "$(printf {shlex.quote(trust)})" ] '
                          '|| echo "Codex configuration is not only the fixture trust"')
            checks.append('[ "$(git config user.email)" = agent@example.invalid ] || echo "git identity is not the scenario identity"')
            checks.append('[ -z "$(git config --get-regexp "^credential" 2>/dev/null)" ] || echo "a git credential helper is set"')
            script = '; '.join(checks + ['touch .sandbox-probe && rm .sandbox-probe || echo "fixture not writable"'])
            r = subprocess.run([str(SANDBOX), str(fx), 'sh', '-c', script], capture_output=True, text=True, env=env)
            problems = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
            log(f"DRY RUN {label} {sid} r{n}: " + ('built; hidden folders empty apart from this run, home folder the run\'s own, '
                                                    'fixture writable' if not problems
                                                    else 'PROBLEM ' + '; '.join(problems)))
            shutil.rmtree(logdir, ignore_errors=True)
            return
        if cli_name(agent) in ('copilot', 'agy'):
            env['SB_KEYRING'] = '1'  # both sign in from the keyring; Copilot's commands can read it too (finding 53)
        if cli_name(agent) == 'copilot':
            # Exactly "true" trusts the fixture, loading its hooks, on every step including resumed ones.
            env['COPILOT_ALLOW_ALL'] = 'true'
            if opts.copilot_user_hooks:
                env['SB_COPILOT_HOOKS'] = str(opts.copilot_user_hooks)
        session, steps, start, first_out = None, [], tree(fx), ''
        for i, prompt in enumerate(s['prompts'], 1):
            log(f'start {label} {sid} r{n} step {i}/{len(s["prompts"])}')
            t0 = time.time()
            try:
                r = subprocess.run([str(SANDBOX), str(fx), *agent_cmd(agent, prompt, session, share_dir, i, fx, opts.effort)],
                                   capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, timeout=STEP_TIMEOUT)
                out, err, code = r.stdout, r.stderr, r.returncode
            except subprocess.TimeoutExpired as e:
                out = e.stdout.decode(errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or '')
                err, code = 'TIMEOUT', 'timeout'
            safe_write_text(logdir, f'step{i}.out', out)
            first_out = out if i == 1 else first_out
            safe_write_text(logdir, f'step{i}.err', err)
            if LIMIT.search((out + err)[-4000:]):
                # A usage limit voids the run; leave no evidence.json so a later rerun picks it up.
                log(f'USAGE LIMIT {label} {sid} r{n} step {i}; run left incomplete')
                return
            if cli_name(agent) == 'copilot':
                share_text = safe_read_text(share_dir, f'step{i}-share.md')
                if share_text is not None:
                    safe_write_text(logdir, f'step{i}-share.md', share_text)
            sess, final, commands = parse_step(agent, out + '\n' + err, logdir, i)
            session = session or sess
            messages = step_messages(agent, out + '\n' + err, logdir, i)
            steps.append({'step': i, 'prompt': prompt, 'exit': code, 'seconds': round(time.time() - t0),
                          'final': final, 'messages': messages if messages else [final], 'commands': commands, 'tree': tree(fx)})
            log(f'done  {label} {sid} r{n} step {i} exit={code} {round(time.time() - t0)}s')
            if len(s['prompts']) > i and not session:
                steps.append({'step': i, 'error': 'no session id; follow-ups not sent'})
                break
        ev = {'agent': label, 'agent_cli': agent, 'cli_version': cli_version(agent), 'date': time.strftime('%Y-%m-%d'), 'guidance': str(opts.shown), 'guidance_commit': git(opts.shown, 'rev-parse', 'HEAD'), 'guidance_snapshot': str(opts.guidance),
              'installed': not opts.no_install, 'scenario': sid, 'run': n, 'session': session, 'start': start, 'steps': steps,
              'fixture': str(fx), 'catalog': str(opts.catalog) if opts.catalog else None, 'evidence': evidence(fx),
              'settings': {'effort': opts.effort, 'trusted': not opts.untrusted, 'mcp': 'off' if cli_name(agent) == 'claude' else 'none configured',
                           'observed': observed_settings(agent, first_out, home, session)},
              'spawns': codex_spawns(agent, home, session)}
        safe_write_text(logdir, 'evidence.json', json.dumps(ev, indent=1))
    finally:
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(share_dir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path, help='results folder outside this repository')
    ap.add_argument('--agents', default='claude,codex,copilot,agy')
    sel = ap.add_mutually_exclusive_group()
    sel.add_argument('--scenarios', default='', help='comma-separated IDs; default all')
    sel.add_argument('--suite', default='', help='named scenario suite from catalog (e.g. phase1, phase2, phase3)')
    ap.add_argument('--runs', default='1,2')
    ap.add_argument('--workers', type=int, default=3, help='concurrent runs per agent')
    ap.add_argument('--label', help='results folder name; default the agent name (one agent only)')
    ap.add_argument('--effort', choices=EFFORTS, default=DEFAULT_EFFORT,
                    help=f'reasoning effort passed to every CLI and recorded in the evidence (default {DEFAULT_EFFORT}); '
                         'an Antigravity model ID that names an effort must name this one')
    ap.add_argument('--untrusted', action='store_true',
                    help='do not trust the fixture in Codex, as runs before the trust change did; default trusted, as a real project is')
    src = ap.add_mutually_exclusive_group()
    src.add_argument('--guidance', type=Path, help='existing committed guidance snapshot to test')
    src.add_argument('--no-install', action='store_true', help='no-guidance baseline')
    ap.add_argument('--catalog', type=Path, help='scenario catalog to run instead of the snapshot\'s, such as the private holdout '
                    'set; its fixtures folder sits beside it, and the folder is hidden from agents')
    ap.add_argument('--hide', type=Path, action='append', default=[],
                    help='another folder to hide from agents (repeatable); this repository and its other worktrees, ~/holdout, '
                         '~/scenario-runs and --out always are')
    ap.add_argument('--dry-run', action='store_true', help='build each fixture and check the sandbox hides what it should; run no agent')
    ap.add_argument('--copilot-user-hooks', action='store_true',
                    help="give Copilot the guidance stop hook as a user-level hook (~/.copilot/hooks), inside the sandbox only")
    opts = ap.parse_args()
    opts.out = opts.out.resolve()
    if opts.out.is_relative_to(REPO):
        ap.error('--out must be outside this repository')
    agents = opts.agents.split(',')
    if opts.label and len(agents) > 1:
        ap.error('--label works with one agent at a time')
    for agent in agents:
        named = model_effort(agent.partition('@')[2]) if cli_name(agent) == 'agy' else None
        if named and named != opts.effort:
            ap.error(f'{agent} names effort {named}, but --effort is {opts.effort}')
    if not shutil.which('bwrap'):
        ap.error('bubblewrap (bwrap) is required')
    opts.out.mkdir(parents=True, exist_ok=True)
    # Agents must not read the scenarios' expected answers, the holdout set, or other runs' fixtures and results.
    home = Path.home()
    catalog_dir = [opts.catalog.resolve().parent] if opts.catalog else []
    opts.catalog = opts.catalog.resolve() if opts.catalog else None
    opts.hide = sorted({p.resolve() for p in [*checkouts(REPO), home / 'holdout', home / 'scenario-runs', opts.out, *catalog_dir, *opts.hide]
                        if p.resolve() != home})
    opts.guidance = opts.guidance.resolve() if opts.guidance else snapshot(opts.out)
    if git(opts.guidance, 'status', '--porcelain'):
        ap.error(f'guidance snapshot is not clean: {opts.guidance}')
    if opts.copilot_user_hooks:
        # A user-level hooks file pointing at the snapshot's stop hook; sandbox.sh mounts it over ~/.copilot/hooks.
        hooks = opts.out / 'copilot-user-hooks'
        hooks.mkdir(exist_ok=True)
        stop = agent_view(opts.guidance) / '.github' / 'hooks' / 'guidance_stop.py'
        (hooks / 'guidance.json').write_text(json.dumps({'version': 1, 'hooks': {'agentStop': [
            {'type': 'command', 'bash': f'python3 {stop}', 'timeoutSec': 10}]}}, indent=2) + '\n')
        opts.copilot_user_hooks = hooks
    global GUIDANCE_FOR_COPILOT
    opts.shown = agent_view(opts.guidance)
    GUIDANCE_FOR_COPILOT = opts.shown
    log(f'guidance: {opts.guidance} ({"not installed" if opts.no_install else git(opts.guidance, "rev-parse", "--short", "HEAD")})')
    all_s = scenarios(opts.guidance, opts.shown, opts.catalog)
    suites = load_suites(opts.guidance, opts.catalog)
    try:
        ids = select_scenario_ids(all_s, suites, opts.scenarios, opts.suite, opts.no_install)
    except ValueError as err:
        ap.error(str(err))
    pools = {a: ThreadPoolExecutor(max_workers=opts.workers) for a in agents}
    futures = [pools[a].submit(run_one, opts, a, all_s[i], int(n)) for n in opts.runs.split(',') for i in ids for a in agents]
    for f in as_completed(futures):
        if f.exception():
            log(f'ERROR {f.exception()!r}')
    log('ALL DONE')


if __name__ == '__main__':
    main()
