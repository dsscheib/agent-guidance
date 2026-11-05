#!/usr/bin/env python3
"""Pack a results folder for publication (repository-only).

  bundle.py OUT_DIR ARCHIVE.tar.zst [--redact WORD ...]

Copies OUT_DIR's logs, fixtures and guidance snapshots into a staging folder beside the archive and rewrites every
text file outside `.git`: the results folder's path becomes `$SUITE`, the home folder `~`, and each UUID (session,
request and message IDs) a stable `uuid-<n>`, so references within the bundle still match. Values of secret-named
variables (TOKEN, SECRET, KEY, PASSWORD, AUTH, CREDENTIAL) are redacted twice: every value such a variable has in the
environment this runs in, wherever it appears, and any `NAME=value` pair with such a name, as an agent's `env` prints it. Then it scans the staging
folder for secret-shaped strings and refuses to pack if it finds any. Environments an agent installed into a fixture
(`.venv`, `node_modules`, `__pycache__`) are left out: they are third-party code, and the evidence already records the
commands that installed them. Of the guidance snapshots, only the agent views (`*-agent`, what agents were shown) are
kept, without their git history. `--redact WORD` replaces a word, in any case, with `<private>` in every text file, for
names that appear in the guidance an agent read. Fixtures' own git history is kept as is: it holds
the commit identity the agents used and the revisions the scorer checks. score.py reads the unpacked folder directly,
because it falls back to fixtures inside the folder it is given.
"""
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
                    r'|AIza[0-9A-Za-z_-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY|xox[abpr]-[A-Za-z0-9-]{10,}')


def text_files(root):
    for p in sorted(root.rglob('*')):
        if p.is_file() and '.git' not in p.relative_to(root).parts:
            try:
                yield p, p.read_text()
            except UnicodeDecodeError:
                continue


def main():
    args = sys.argv[1:]
    redact = [args[i + 1] for i, a in enumerate(args) if a == '--redact' and i + 1 < len(args)]
    args = [a for i, a in enumerate(args) if a != '--redact' and (i == 0 or args[i - 1] != '--redact')]
    if len(args) != 2:
        sys.exit(__doc__)
    out, archive = Path(args[0]).resolve(), Path(args[1]).resolve()
    private = re.compile('|'.join(map(re.escape, redact)), re.I) if redact else None
    stage = archive.parent / archive.name.split('.')[0]
    if stage.exists():
        sys.exit(f'{stage} exists; remove it first')
    stage.mkdir(parents=True)
    for part in ('logs', 'fx'):
        if (out / part).is_dir():
            shutil.copytree(out / part, stage / part, symlinks=True, ignore=shutil.ignore_patterns(*INSTALLED))
    for snap in sorted((out / 'snapshots').glob('*-agent')):
        shutil.copytree(snap, stage / 'snapshots' / snap.name, symlinks=True, ignore=shutil.ignore_patterns('.git', *INSTALLED))
    ids, changed = {}, 0
    known = sorted(((k, v) for k, v in os.environ.items() if SECRET_NAME.search(k) and len(v) >= 8), key=lambda kv: -len(kv[1]))
    for p, text in text_files(stage):
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
    leaks = [str(p.relative_to(stage)) for p, text in text_files(stage)
             if SECRET.search(text) or any(v in text for _, v in known) or (private and private.search(text))]
    if leaks:
        sys.exit('secret-shaped strings found; nothing packed:\n  ' + '\n  '.join(leaks[:20]))
    subprocess.run(['tar', '--zstd', '-cf', str(archive), '-C', str(stage.parent), stage.name], check=True)
    print(f'{archive}: {changed} files rewritten, {len(ids)} IDs replaced, no secret-shaped strings; staging left in {stage}')


if __name__ == '__main__':
    main()
