#!/usr/bin/env python3
"""Pack a results folder, or any folder, for publication (repository-only).

  bundle.py OUT_DIR ARCHIVE.tar.zst [--redact WORD ...] [--withhold PATH --reason TEXT ...]
  bundle.py --tree SRC_DIR ARCHIVE.tar.zst [the same options]

Copies OUT_DIR's logs, fixtures, reruns and guidance snapshots into a staging folder beside the archive and rewrites
every text file outside `.git`: the results folder's path becomes `$SUITE`, the home folder `~`, and each UUID
(session, request and message IDs) a stable `uuid-<n>`, so references within the bundle still match. Values of
secret-named variables (TOKEN, SECRET, KEY, PASSWORD, AUTH, CREDENTIAL) are redacted twice: every value such a variable
has in the environment this runs in, wherever it appears, and any `NAME=value` pair with such a name, as an agent's
`env` prints it. Environments an agent installed into a fixture (`.venv`, `node_modules`, `__pycache__`) are left out:
they are third-party code, and the evidence already records the commands that installed them. Of the guidance
snapshots, only the agent views (`*-agent`, what agents were shown) are kept, without their git history. `reruns/`
holds the first attempts of rerun runs, which the protocol publishes with their cause. Fixtures' own git history is
kept as is: it holds the commit identity the agents used and the revisions the scorer checks. score.py reads the
unpacked folder directly, because it falls back to fixtures inside the folder it is given.

`--tree` packs every file under SRC_DIR instead (for grading material), with the same rewriting and checks; its path
becomes `$SUITE`.

`--verbatim GLOB` (relative to the staging folder, repeatable) keeps matching files byte for byte, for files whose
published hash is recorded, such as frozen grade sheets: they are not rewritten, but they are still scanned, so a
secret in one still stops the build.

`--redact WORD` replaces a word, in any case, with `<private>` in every text file, for names that appear in the
guidance an agent read. `--withhold PATH` (relative to the staging folder, repeatable, with one `--reason`) replaces a
file with a note giving the reason, for a transcript that holds what an agent read outside its fixture. The note keeps
the file's name, so the run still has every file it had.

Then the staging folder is scanned, and nothing is packed if it holds a secret-shaped string, a secret value from the
environment, a redacted word, a shell-history line (zsh's `: <epoch>:<n>;`), a directory listing that shows a shell
history file (the shape of an agent listing a home folder), or a result table from Copilot's own session store, which
lists the maintainer's other Copilot sessions. A run that read outside its fixture is caught here and
withheld by name, rather than published by mistake.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

INSTALLED = ('.venv', 'venv', 'node_modules', '__pycache__')
SECRET_NAME = re.compile(r'(?i)token|secret|key|password|passwd|auth|credential|cookie|session')
ENV_PAIR = re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)=([^\s"\'\\]{8,})')
UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
SECRET = re.compile(r'sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}'
                    r'|AIza[0-9A-Za-z_-]{35}|GOCSPX-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY|xox[abpr]-[A-Za-z0-9-]{10,}')
# Lines of a zsh extended history, raw or inside JSON-escaped transcripts (\n as two characters).
HISTORY = re.compile(r'(?:^|\n|\\n): 1\d{9}:\d+;')
# An `ls -l` row for a shell history file: an agent listed a home folder.
HOME_LISTING = re.compile(r'[d-][rwx-]{9}[^\n\\]{0,80}\s\.(?:zsh|bash)_history\b')
# Results of a query on Copilot's own session store: the maintainer's other Copilot sessions.
SESSION_STORE = re.compile(r'\|\s*_query_source\s*\|')


def text_files(root):
    for p in sorted(root.rglob('*')):
        if p.is_file() and not p.is_symlink() and '.git' not in p.relative_to(root).parts:
            try:
                yield p, p.read_text()
            except UnicodeDecodeError:
                continue


def stage_results(out, stage):
    for part in ('logs', 'fx', 'reruns'):
        if (out / part).is_dir():
            shutil.copytree(out / part, stage / part, symlinks=True, ignore=shutil.ignore_patterns(*INSTALLED))
    for snap in sorted((out / 'snapshots').glob('*-agent')):
        shutil.copytree(snap, stage / 'snapshots' / snap.name, symlinks=True, ignore=shutil.ignore_patterns('.git', *INSTALLED))


def problems(text, known, private):
    found = []
    if SECRET.search(text) or any(v in text for _, v in known):
        found.append('secret')
    if private and private.search(text):
        found.append('redacted word')
    if HISTORY.search(text):
        found.append('shell history')
    if HOME_LISTING.search(text):
        found.append('home folder listing')
    if SESSION_STORE.search(text):
        found.append("Copilot session store results")
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src', type=Path)
    ap.add_argument('archive', type=Path)
    ap.add_argument('--tree', action='store_true', help='pack every file under SRC, not a results folder')
    ap.add_argument('--redact', action='append', default=[], metavar='WORD')
    ap.add_argument('--withhold', action='append', default=[], metavar='PATH', help='relative to the staging folder')
    ap.add_argument('--reason', help='why the --withhold files are withheld (required with --withhold)')
    ap.add_argument('--verbatim', action='append', default=[], metavar='GLOB',
                    help='files kept byte for byte (still scanned), relative to the staging folder')
    a = ap.parse_args(argv)
    if a.withhold and not a.reason:
        ap.error('--withhold needs --reason')
    out, archive = a.src.resolve(), a.archive.resolve()
    private = re.compile('|'.join(map(re.escape, a.redact)), re.I) if a.redact else None
    stage = archive.parent / archive.name.split('.')[0]
    if stage.exists():
        sys.exit(f'{stage} exists; remove it first')
    if a.tree:
        shutil.copytree(out, stage, symlinks=True, ignore=shutil.ignore_patterns(*INSTALLED))
    else:
        stage.mkdir(parents=True)
        stage_results(out, stage)
    for rel in a.withhold:
        p = stage / rel
        if not p.is_file():
            sys.exit(f'--withhold {rel}: not a file in the staging folder')
        p.write_text(f'Withheld from publication: {a.reason}\n')
    ids, changed = {}, 0
    known = sorted(((k, v) for k, v in os.environ.items() if SECRET_NAME.search(k) and len(v) >= 8), key=lambda kv: -len(kv[1]))
    keep = {p for g in a.verbatim for p in stage.glob(g) if p.is_file()}
    missing = [g for g in a.verbatim if not any(stage.glob(g))]
    if missing:
        sys.exit(f'--verbatim matched nothing: {", ".join(missing)}')
    for p, text in text_files(stage):
        if p in keep:
            continue
        new = text
        for k, v in known:
            new = new.replace(v, f'<redacted:{k}>')
        new = ENV_PAIR.sub(lambda m: f'{m.group(1)}=<redacted>' if SECRET_NAME.search(m.group(1)) else m.group(0), new)
        new = new.replace(str(out), '$SUITE').replace(str(Path.home()), '~')
        if private:
            new = private.sub('<private>', new)
        new = UUID.sub(lambda m: ids.setdefault(m.group(0), f'uuid-{len(ids) + 1}'), new)
        if new != text:
            p.write_text(new)
            changed += 1
    leaks = [f'{p.relative_to(stage)}: {", ".join(kinds)}' for p, text in text_files(stage)
             if (kinds := problems(text, known, private))]
    if leaks:
        sys.exit(f'{len(leaks)} file(s) hold content that must not be published; nothing packed (staging left in '
                 f'{stage}):\n  ' + '\n  '.join(leaks[:40]))
    subprocess.run(['tar', '--zstd', '-cf', str(archive), '-C', str(stage.parent), stage.name], check=True)
    print(f'{archive}: {changed} files rewritten, {len(ids)} IDs replaced, {len(a.withhold)} withheld, '
          f'{len(keep)} kept verbatim, nothing that '
          f'must not be published; staging left in {stage}')


if __name__ == '__main__':
    main()
