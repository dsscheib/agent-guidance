#!/usr/bin/env python3
"""Run guidance scenarios against agent CLIs, sandboxed, and record evidence (repository-only).

  run.py --out DIR [--agents claude,codex,copilot,agy] [--scenarios S2,S12] [--runs 1,2] [--workers 3]
         [--guidance PATH | --no-install] [--label NAME]

Agents are CLI names, optionally with a model: claude@claude-haiku-5-5, codex@gpt-6-luna,
copilot@gemini-3.8-flash, agy@gemini-3.8-flash-medium.

--out is required and must be outside this repository: raw runs are bulky and contain local paths
(docs/DOCUMENTATION.md#document-budget). Results go to OUT/logs/<label>/<scenario>-r<n>/evidence.json
and fixtures to OUT/fx/<label>/. Finished runs are skipped, so an interrupted batch can be rerun.

By default the current checkout, including uncommitted changes, is copied to OUT/snapshots/<name> and
committed there, because the upgrade procedure (S11) expects a clean guidance checkout. --guidance uses
an existing snapshot instead, for example one built from `main` for a before-and-after comparison.
--no-install builds the fixtures without the package, for a no-guidance baseline; S1 and S11 are
skipped because they only make sense with guidance.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shlex
import argparse, json, os, re, shutil, subprocess, sys, threading, time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SANDBOX = HERE / 'sandbox.sh'
STEP_TIMEOUT = 25 * 60
NO_INSTALL_SKIP = {'S1', 'S11', 'S16', 'S18'}  # these set up or upgrade the guidance itself
OLD_GUIDANCE_SKIP = {'S18'}
GUIDANCE_FOR_COPILOT = None  # set in main() to the guidance snapshot
print_lock = threading.Lock()
GIT_ID = ['-c', 'user.name=Scenario Snapshot', '-c', 'user.email=snapshot@example.invalid',
          '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']


def log(msg):
    with print_lock:
        print(time.strftime('%H:%M:%S'), msg, flush=True)


def git(cwd, *args, check=False):
    r = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


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


def old_release(out, ref):
    """A checkout of an earlier release of this repository, for the agent view under --old-guidance."""
    dest = out / 'snapshots' / f'old-{ref}'
    if not (dest / '.git').is_dir():
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '-q', '--shared', str(REPO), str(dest)], check=True)
        subprocess.run(['git', '-C', str(dest), '-c', 'advice.detachedHead=false', 'checkout', '-q', ref], check=True)
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


MAINTAINER_AGENT = 'Generated by check_package.py --sync-adapters from maintainer/roles/'


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
        if f and not maintainer_only(f) and MAINTAINER_AGENT not in (snap / f).read_text(errors='replace'):
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
    if not share.is_file():
        return None
    sections = re.split(r'\n---\n', share.read_text(errors='replace'))
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
        if share.is_file():
            # The export is cumulative across a resumed session; checks.py counts only commands new to each step.
            text = share.read_text(errors='replace')
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
    status = subprocess.run(['git', '-C', str(fx), 'status', '--porcelain', '--untracked-files=no'], capture_output=True, text=True)
    return {'head': git(fx, 'rev-parse', 'HEAD'), 'changed': status.stdout.splitlines()}


def evidence(fx):
    first = git(fx, 'rev-list', '--max-parents=0', 'HEAD')
    lines = lambda p: len((fx / p).read_text().splitlines()) if (fx / p).is_file() else None
    tests = subprocess.run([sys.executable, '-m', 'unittest', '-q'], cwd=fx, capture_output=True, text=True,
                           env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    check = None
    if (fx / 'check_package.py').is_file():
        r = subprocess.run([sys.executable, 'check_package.py'], cwd=fx, capture_output=True, text=True)
        # Keep the problem lines too (an adapter problem has no colon), so a failure can be told from an environment block.
        check = (r.stdout + r.stderr).strip().splitlines()[:12]
    revision = fx / 'review' / 'REVISION'
    return {
        'branch': git(fx, 'branch', '--show-current'),
        'branches': git(fx, 'branch', '--format=%(refname:short)').splitlines(),
        'log': git(fx, 'log', '--oneline', '--all').splitlines(),
        'status': git(fx, 'status', '--porcelain').splitlines(),
        'changed_vs_initial': git(fx, 'diff', '--name-status', first, '--', '.').splitlines() if first else [],
        'untracked': git(fx, 'ls-files', '--others', '--exclude-standard').splitlines(),
        'profile_lines': lines('PROJECT_PROFILE.md'),
        'open_work_lines': lines('docs/OPEN_WORK.md'),
        'tests_pass': tests.returncode == 0,
        'tests_tail': (tests.stderr.strip().splitlines() or [''])[-1],
        'check_package': check,
        'review_revision': revision.read_text().strip() if revision.is_file() else None,
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
        for f in sorted((home / '.codex' / 'sessions').rglob(f'rollout-*{session}.jsonl')):
            for e in json_lines(f.read_text(errors='replace')):
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
    files = sorted((home / '.codex' / 'sessions').rglob(f'rollout-*{session}.jsonl'))
    if not files:
        return None
    spawns = []
    for f in files:
        for e in json_lines(f.read_text(errors='replace')):
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
    old = {'SCENARIO_OLD_GUIDANCE': opts.old_guidance} if opts.old_guidance else {}
    catalog = ['--scenarios', str(opts.catalog)] if opts.catalog else []
    b = subprocess.run([sys.executable, str(builder), *catalog, sid, str(fx)] + (['--no-install'] if opts.no_install else []),
                       capture_output=True, text=True, env={**os.environ, 'SCENARIO_HISTORY_REPO': str(REPO), 'SCENARIO_BASELINES': baselines(opts.shown), **old})
    if b.returncode:
        log(f'BUILD FAIL {label} {sid} r{n}: {(b.stdout + b.stderr).strip()[-300:]}')
        return
    # The run's own home folder (sandbox.sh): sign-in copies, CLI sessions and a scenario git identity, outside logs/
    # so nothing in it is published, and deleted when the run ends.
    home = opts.out / 'homes' / label / f'{sid}-r{n}'
    shutil.rmtree(home, ignore_errors=True)
    env = {**os.environ, 'SB_HOME': str(home), 'SB_LOGDIR': str(logdir), 'SB_GUIDANCE': str(opts.shown),
           'SB_HIDE': ' '.join(map(str, opts.hide)), 'SB_TRUST': '0' if opts.untrusted else '1'}
    try:
        if opts.dry_run:
            # No agent: from inside the sandbox, each hidden folder may show only the folders leading to this run's own
            # mounts (fixture, logs, guidance view), and the fixture must be writable.
            checks = []
            for h in opts.hide:
                allowed = {p.relative_to(h).parts[0] for p in (fx, logdir, opts.shown) if p.is_relative_to(h) and p != h}
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
                r = subprocess.run([str(SANDBOX), str(fx), *agent_cmd(agent, prompt, session, logdir, i, fx, opts.effort)],
                                   capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL, timeout=STEP_TIMEOUT)
                out, err, code = r.stdout, r.stderr, r.returncode
            except subprocess.TimeoutExpired as e:
                out = e.stdout.decode(errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or '')
                err, code = 'TIMEOUT', 'timeout'
            (logdir / f'step{i}.out').write_text(out)
            first_out = out if i == 1 else first_out
            (logdir / f'step{i}.err').write_text(err)
            if LIMIT.search((out + err)[-4000:]):
                # A usage limit voids the run; leave no evidence.json so a later rerun picks it up.
                log(f'USAGE LIMIT {label} {sid} r{n} step {i}; run left incomplete')
                return
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
        (logdir / 'evidence.json').write_text(json.dumps(ev, indent=1))
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path, help='results folder outside this repository')
    ap.add_argument('--agents', default='claude,codex,copilot,agy')
    ap.add_argument('--scenarios', default='', help='comma-separated IDs; default all')
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
    src.add_argument('--old-guidance', metavar='REF', help='install this earlier release (a tag such as 2.0 or 3.0.1) into the current fixtures')
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
    opts.shown = agent_view(old_release(opts.out, opts.old_guidance) if opts.old_guidance else opts.guidance)
    GUIDANCE_FOR_COPILOT = opts.shown
    log(f'guidance: {opts.guidance} ({"not installed" if opts.no_install else git(opts.guidance, "rev-parse", "--short", "HEAD")})')
    all_s = scenarios(opts.guidance, opts.shown, opts.catalog)
    number = lambda x: int(m.group(1)) if (m := re.match(r'[A-Z]+(\d+)', x)) else 0
    ids = opts.scenarios.split(',') if opts.scenarios else sorted(all_s, key=lambda x: (x != 'S12', number(x), x))
    if opts.no_install:
        ids = [i for i in ids if i not in NO_INSTALL_SKIP]
    if opts.old_guidance:
        # Tier variants test 3.0 features, and S18 upgrades a 2.x project, so neither means anything under 2.x guidance.
        ids = [i for i in ids if not all_s[i].get('variant_of') and i not in OLD_GUIDANCE_SKIP]
    unknown = [i for i in ids if i not in all_s]
    if unknown:
        ap.error('unknown scenarios: ' + ', '.join(unknown))
    pools = {a: ThreadPoolExecutor(max_workers=opts.workers) for a in agents}
    futures = [pools[a].submit(run_one, opts, a, all_s[i], int(n)) for n in opts.runs.split(',') for i in ids for a in agents]
    for f in as_completed(futures):
        if f.exception():
            log(f'ERROR {f.exception()!r}')
    log('ALL DONE')


if __name__ == '__main__':
    main()
