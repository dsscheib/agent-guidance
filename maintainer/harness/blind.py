#!/usr/bin/env python3
"""Prepare blinded grading material from a results folder (repository-only).

  blind.py OUT_DIR DEST_DIR --key KEY.json --seed N [--labels REGEX] [--scenarios H1,H2]

Writes one folder per run, DEST_DIR/<ID>/run.md, holding everything a grader needs and nothing that names the
condition on purpose: the scenario ID, each step's prompt, every assistant message, the commands it ran, the step's exit
status and tree, the checks recorded after the run, and the fixture's final git state (refs with branches, tags and origin
refs, the commit log, status, the files, the diff from the run's start and the untracked files' contents).

Normalization, in this order: the run's own paths become [project], [logs], [guidance] and [results], and the home
folder `~`; the global git name and email become [user]; the run's label becomes [run] and any other run's label
[other-run]; secret values are redacted as bundle.py does; AGENTS.md, CLAUDE.md, GEMINI.md and copilot-instructions.md
become [instructions]; model names and IDs become [model]; CLI and vendor names become [cli]; UUIDs become uuid-<n>
within each run. Run lengths in seconds, CLI versions and session IDs are left out.

Run order: runs are sorted by label, scenario and run number, then shuffled with Python's random.Random(SEED); IDs
B001, B002, ... follow the shuffled order. Anyone with the seed can rebuild the key from the sorted labels, so the seed
is secret until grading ends: it goes to KEY.json with the key (ID -> label, agent, guidance, scenario, run), which
must be outside DEST_DIR. Publish both after every grade is in. Use an unguessable seed, such as
`python3 -c "import secrets; print(secrets.randbits(128))"`: with a small one, a grader who recognizes a few runs by
their format could find it by trial. DEST_DIR/BLINDING.md records the method and the seed's SHA-256, so the published
seed can be checked against it, and says that blinding is partial, because tool-specific formats still show through.

After writing, every run is scanned for CLI, model and vendor names and run labels that survived. Paths are not
scanned: an agent's own commands may name folders such as ~/scenario-runs, which graders should see and which do not
name a condition. Any hit fails the run with counts per term and run ID only, so the scan never prints transcript
content.
"""
import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bundle  # noqa: E402

INSTRUCTIONS = re.compile(r'\b(?:AGENTS|CLAUDE|GEMINI)\.md\b|\bcopilot-instructions\.md\b', re.I)
MODEL = [re.compile(p, f) for p, f in (
    (r'\bclaude-(?:opus|sonnet|haiku|fable)[\w.-]*', re.I),
    (r'\bgpt-\d[\w.-]*(?:\s+(?:Sol|Luna))?', re.I),
    (r'\bgemini-\d[\w.-]*', re.I),
    (r'\bGemini\s+\d+(?:\.\d+)*(?:\s+(?:Flash|Pro|Argon))?', re.I),
    (r'\b(?:Opus|Sonnet|Haiku|Fable)(?:\s+\d+(?:\.\d+)*)?\b', re.I),
    (r'\b(?:Argon|Luna)\b', 0),
)]
CLI = re.compile(r'\bClaude Code\b|\b(?:claude|codex|antigravity|agy|gemini|copilot|anthropic|openai|chatgpt|google|deepmind)\b',
                 re.I)
TELL = re.compile(r'\b(?:claude|codex|antigravity|agy|gemini|copilot|anthropic|openai|chatgpt|google|deepmind|opus|sonnet|haiku'
                  r'|fable)\b'
                  r'|\bgpt-\d|-holdout(?![\w])|holdout-(?:none|\d)|\[cli\]-(?:flash|sol|luna|argon)\b|\bAGENTS\.md\b', re.I)
# Pieces of run labels that survive whole-label replacement, as when a CLI shortens a long path with an ellipsis
# ("…sh-holdout-none/H3-r1", "agy-flash-hol…"): any word ending in a condition suffix, and a CLI name followed by a model.
FRAGMENTS = [re.compile(r'[\w.…-]*-holdout(?:-none|-\d+(?:\.\d+)*)?(?![\w-])'),
             re.compile(r'\[cli\]-(?:\[model\]|flash|sol|luna|argon)[\w.…-]*', re.I)]
RUN_DIR = re.compile(r'^(?P<sid>.+)-r(?P<n>\d+)$')
UNTRACKED_LIMIT = 200_000


def git(cwd, *args):
    return subprocess.run(['git', '-C', str(cwd), *args], capture_output=True, text=True).stdout.rstrip('\n')


def secrets():
    """Secret values in this environment, longest first, and the redaction bundle.py applies to `NAME=value` pairs."""
    known = sorted(((k, v) for k, v in os.environ.items() if bundle.SECRET_NAME.search(k) and len(v) >= 8),
                   key=lambda kv: -len(kv[1]))

    def redact(text):
        for k, v in known:
            text = text.replace(v, f'<redacted:{k}>')
        return bundle.ENV_PAIR.sub(lambda m: f'{m.group(1)}=<redacted>' if bundle.SECRET_NAME.search(m.group(1))
                                   else m.group(0), text)
    return redact


def scrubber(out, label, logdir, ev, redact, others):
    paths = [(str(out / 'fx' / label / logdir.name), '[project]'), (str(logdir), '[logs]'), (str(out), '[results]')]
    if ev.get('fixture'):
        paths.append((ev['fixture'], '[project]'))
    paths += [(ev[k], '[guidance]') for k in ('guidance', 'guidance_snapshot') if ev.get(k)]
    paths.sort(key=lambda p: -len(p[0]))
    home, ids = str(Path.home()), {}
    names = sorted([(label, '[run]')] + [(o, '[other-run]') for o in others], key=lambda n: -len(n[0]))
    people = [(v, '[user]') for v in (git(Path.home(), 'config', '--global', k) for k in ('user.email', 'user.name')) if v]

    def scrub(text):
        for old, new in paths:
            text = text.replace(old, new)
        for old, new in people:
            text = text.replace(old, new)
        text = text.replace(home, '~')
        for name, new in names:  # longest first: one label can be the start of another (x-holdout, x-holdout-2.0)
            text = text.replace(name, new)
        text = redact(text)
        text = INSTRUCTIONS.sub('[instructions]', text)
        for rx in MODEL:
            text = rx.sub('[model]', text)
        text = CLI.sub('[cli]', text)
        for rx in FRAGMENTS:
            text = rx.sub('[other-run]', text)
        return bundle.UUID.sub(lambda m: ids.setdefault(m.group(0), f'uuid-{len(ids) + 1}'), text)
    return scrub


def commitment(seed):
    return hashlib.sha256(str(seed).encode()).hexdigest()


def fence(text):
    text = text or ''
    ticks = '`' * max(3, max((len(m) for m in re.findall(r'`+', text)), default=0) + 1)
    return f'{ticks}\n{text}\n{ticks}'


def git_state(fx, ev):
    """The fixture's final git state, and the diff and untracked files since the run started."""
    if not (fx / '.git').exists():
        return ['Fixture not found; git state unavailable.']
    start = (ev.get('start') or {}).get('head') or git(fx, 'rev-list', '--max-parents=0', 'HEAD').splitlines()[0]
    untracked = [p for p in git(fx, 'ls-files', '--others', '--exclude-standard').splitlines()
                 if not set(Path(p).parts) & set(bundle.INSTALLED)]
    parts = [
        f'Branch checked out: {git(fx, "branch", "--show-current") or "(detached)"}; HEAD at start {start[:12]}',
        '### Refs', fence(git(fx, 'for-each-ref', '--format=%(objectname:short) %(refname)')),
        '### Commit log (all refs)', fence(git(fx, 'log', '--all', '--graph', '--decorate',
                                               '--format=%h%d %an <%ae>%n%B')),
        '### Status', fence(git(fx, 'status', '--porcelain')),
        '### Files', fence('\n'.join(git(fx, 'ls-files').splitlines() + [p + '  (untracked)' for p in untracked])),
        '### Diff from the start of the run (tracked files)', fence(git(fx, 'diff', start)),
        '### Untracked files',
    ]
    for p in untracked:
        f = fx / p
        try:
            body = f.read_text()[:UNTRACKED_LIMIT] if f.is_file() else '(not a regular file)'
        except UnicodeDecodeError:
            body = '(binary)'
        parts += [f'#### {p}', fence(body)]
    return parts or ['(none)']


def render(bid, ev, fx):
    lines = [f'# Run {bid}', f'Scenario: {ev["scenario"]}']
    for st in ev['steps']:
        lines += [f'## Step {st["step"]}', '### Prompt', fence(st.get('prompt')), '### Assistant messages']
        messages = st.get('messages') or ([st['final']] if st.get('final') else [])
        for i, m in enumerate(messages, 1):
            lines += [f'#### Message {i}', fence(m)]
        lines += ['### Commands', fence('\n'.join(st.get('commands') or [])),
                  f'### Exit: {st.get("exit")}', '### Tree after the step', fence(json.dumps(st.get('tree'), indent=1))]
    e = ev.get('evidence') or {}
    lines += ['## Checks recorded after the run', fence(json.dumps(
        {k: e.get(k) for k in ('tests_pass', 'tests_tail', 'check_package', 'review_revision')}, indent=1))]
    lines += ['## Final git state'] + git_state(fx, ev)
    return '\n\n'.join(lines) + '\n'


def collect(out, labels, scenarios):
    runs = []
    for f in sorted((out / 'logs').glob('*/*/evidence.json')):
        label, m = f.parent.parent.name, RUN_DIR.match(f.parent.name)
        if not m or (labels and not re.search(labels, label)) or (scenarios and m['sid'] not in scenarios):
            continue
        runs.append((label, m['sid'], int(m['n']), f))
    return sorted(runs, key=lambda r: r[:3])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out', type=Path)
    ap.add_argument('dest', type=Path)
    ap.add_argument('--key', type=Path, required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--labels', help='regular expression the run labels must match')
    ap.add_argument('--scenarios', help='comma-separated scenario IDs')
    a = ap.parse_args(argv)
    out, dest, key = a.out.resolve(), a.dest.resolve(), a.key.resolve()
    if dest == key or dest in key.parents:
        sys.exit('--key must be outside DEST_DIR, so the graders never receive it')
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f'{dest} is not empty')
    runs = collect(out, a.labels, set(a.scenarios.split(',')) if a.scenarios else None)
    if not runs:
        sys.exit('no runs matched')
    order = list(runs)
    random.Random(a.seed).shuffle(order)
    redact, entries = secrets(), []
    every = sorted({p.name for p in (out / 'logs').iterdir() if p.is_dir()} | {r[0] for r in runs}, key=lambda l: -len(l))
    dest.mkdir(parents=True, exist_ok=True)
    for i, (label, sid, n, f) in enumerate(order, 1):
        bid, ev = f'B{i:03d}', json.loads(f.read_text())
        fx = Path(ev['fixture']) if ev.get('fixture') and Path(ev['fixture']).is_dir() else out / 'fx' / label / f.parent.name
        scrub = scrubber(out, label, f.parent, ev, redact, [l for l in every if l != label])
        (dest / bid).mkdir()
        (dest / bid / 'run.md').write_text(scrub(render(bid, ev, fx)))
        entries.append({'id': bid, 'label': label, 'scenario': sid, 'run': n, 'agent_cli': ev.get('agent_cli'),
                        'cli_version': ev.get('cli_version'), 'guidance_commit': ev.get('guidance_commit'),
                        'installed': ev.get('installed'), 'source': str(f.parent)})
    key.parent.mkdir(parents=True, exist_ok=True)
    key.write_text(json.dumps({'seed': a.seed, 'seed_sha256': commitment(a.seed), 'runs': entries}, indent=1) + '\n')
    (dest / 'BLINDING.md').write_text(
        f'# Blinded runs\n\n{len(entries)} runs, IDs B001 to B{len(entries):03d}.\n\n'
        'Order: runs sorted by label, scenario and run number, then shuffled with Python\'s `random.Random(seed)`; '
        'IDs follow the shuffled order. The seed is published with the key after every grade is in; its SHA-256 '
        f'(of the decimal seed) is `{commitment(a.seed)}`.\n\n'
        'Normalized: CLI, vendor and model names and IDs are replaced by [cli] and [model]; AGENTS.md, CLAUDE.md, '
        'GEMINI.md and copilot-instructions.md by [instructions]; local paths by [project], [logs], [guidance], '
        '[results] and ~; run labels by [run] and [other-run]; the maintainer\'s git name and email by [user]; session '
        'and other UUIDs by uuid-<n>. Run lengths, CLI versions and session IDs are left out. '
        'Each run keeps every assistant message, the command record, the final tree and the git state.\n\n'
        '**Blinding is partial.** Tool-specific formats still show through: how each CLI records commands and '
        'messages, the tool configuration folders it uses, and the guidance files present in each fixture. The key '
        'that maps IDs to conditions is kept from the graders until every grade is in.\n')
    hits, labels = {}, every
    for p in sorted(dest.glob('B*/run.md')):  # BLINDING.md names the replaced files on purpose
        text = p.read_text()
        for m in TELL.finditer(text):
            hits.setdefault(m.group(0).lower(), set()).add(p.parent.name)
        for label in labels:
            if label in text:
                hits.setdefault('label:' + label, set()).add(p.parent.name)
    if hits:
        report = '\n  '.join(f'{term}: {len(ids)} run(s), e.g. {", ".join(sorted(ids)[:5])}' for term, ids in sorted(hits.items()))
        sys.exit(f'identifying terms survived in {dest}; do not hand it to graders:\n  {report}')
    print(f'{dest}: {len(entries)} runs blinded; seed and key in {key}; no identifying terms found')


if __name__ == '__main__':
    main()
