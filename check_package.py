#!/usr/bin/env python3
"""Read-only package integrity, reference and placeholder checks."""
from pathlib import Path
import hashlib,json,re,sys
root=Path(__file__).resolve().parent
manifest=json.loads((root/'PACKAGE_MANIFEST.json').read_text())
errors=[]
for entry in manifest['files']:
    path=root/entry['path']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
        errors.append('Missing or changed packaged file: '+entry['path'])
placeholders=set()
for path in root.rglob('*.md'):
    text=path.read_text()
    placeholders.update(re.findall(r'\{\{[^}]+\}\}',text))
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if '://' in link or link.startswith('#'):
            continue
        target=(path.parent/link.split('#')[0]).resolve()
        if not target.is_relative_to(root) or not target.exists():
            errors.append(str(path.relative_to(root))+': unresolved/escaping link '+link)
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f"PASS: {len(manifest['files'])} packaged files, intact hashes and internal links.")
print(f"Setup required: {len(placeholders)} unique template placeholders; no project acceptance is implied.")
