#!/usr/bin/env python3
"""Tier-aware install tests (repository-only). check_package.py runs this in template mode.

  test_install.py          run every case; exit 1 on any failure
  test_install.py --table  print what each tier installs, for review
"""
from pathlib import Path
import hashlib, json, os, subprocess, sys, tempfile

root = Path(__file__).resolve().parent.parent
manifest = json.loads((root / 'PACKAGE_MANIFEST.json').read_text())
module_of = {e['path']: e['module'] for e in manifest['files']}
problems = []


def install(target, *args):
    r = subprocess.run([sys.executable, '-B', str(root / 'check_package.py'), '--install', str(target), *args],
                       capture_output=True, text=True)
    if r.returncode:
        problems.append(f"install {' '.join(args) or '(no tier)'} failed: {(r.stdout + r.stderr).strip()[-300:]}")
    return r


def check(target):
    """Project-mode check of an installed copy; returns (passed, output)."""
    r = subprocess.run([sys.executable, '-B', 'check_package.py'], cwd=target, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def modules_present(target):
    return {m for p, m in module_of.items() if (target / p).is_file()}


def expect(cond, message):
    if not cond:
        problems.append(message)


def case_tiers(tmp):
    """Each tier installs exactly its modules, plus features, and passes the project check."""
    for tier, features in (('prototype', ''), ('internal', ''), ('production', 'ui'), ('enterprise', 'ui,data'),
                           ('prototype', 'ui')):
        target = tmp / f'{tier}-{features or "none"}'
        target.mkdir()
        install(target, '--tier', tier, '--features', features)
        wanted = set(manifest['tiers'][tier]) | {m for f in filter(None, features.split(',')) for m in manifest['features'][f]}
        files_expected = {m for m in wanted if any(mod == m for mod in module_of.values())}
        expect(modules_present(target) == files_expected,
               f'{tier}+{features or "no features"}: installed modules {sorted(modules_present(target))}, expected {sorted(files_expected)}')
        record = json.loads((target / 'PACKAGE_MANIFEST.json').read_text()).get('installed', {})
        expect(record.get('tier') == tier and set(record.get('modules', [])) == wanted,
               f'{tier}: installed record {record} does not match')
        passed, out = check(target)
        expect(passed, f'{tier}+{features or "no features"}: project check failed:\n    ' + out.replace('\n', '\n    ')[:600])


# The approved design (maintainer/RESTRUCTURE_DESIGN.md), stated independently of the manifest so that a
# misassigned module fails here instead of silently changing what a tier installs.
POLICY = {
    'prototype': {'has': ['AGENTS.md', 'PROJECT_PROFILE.md', 'docs/OPEN_WORK.md', 'docs/TESTING_SPEC.md', 'check_package.py',
                          'docs/procedures/final-audit.md'],
                  'lacks': ['DESIGN_DOC.md', 'docs/RUNBOOKS.md', 'docs/RELEASE_NOTES.md', 'docs/VERIFICATION_MATRIX.md',
                            'docs/PRODUCTION_READINESS.md', 'docs/UX_DESIGN_SPEC.md', 'profiles/PRODUCTION_OPERATIONS.md']},
    'internal': {'has': ['DESIGN_DOC.md', 'docs/DOMAIN_RULES.md', 'docs/RUNBOOKS.md', 'docs/RELEASE_NOTES.md',
                         'docs/SECURITY_PRODUCTION_SPEC.md'],
                 'lacks': ['docs/VERIFICATION_MATRIX.md', 'docs/PRODUCTION_READINESS.md', 'docs/procedures/release-readiness.md',
                           'profiles/PRODUCTION_OPERATIONS.md', 'docs/UX_DESIGN_SPEC.md']},
    'production': {'has': ['docs/VERIFICATION_MATRIX.md', 'docs/PRODUCTION_READINESS.md', 'docs/procedures/release-readiness.md',
                           'profiles/PRODUCTION_OPERATIONS.md', 'docs/RUNBOOKS.md'],
                   'lacks': ['docs/UX_DESIGN_SPEC.md', 'docs/DATA_PORTABILITY.md', 'docs/ENTERPRISE.md', '.github/pull_request_template.md']},
    'enterprise': {'has': ['docs/ENTERPRISE.md', '.github/pull_request_template.md', 'docs/VERIFICATION_MATRIX.md'],
                   'lacks': ['docs/UX_DESIGN_SPEC.md']},
}
FEATURE_POLICY = {'ui': ['docs/UX_DESIGN_SPEC.md', 'docs/UI_PATTERNS.md', 'docs/UX_ACCEPTANCE_CHECKLIST.md', 'docs/BRANDING.md'],
                  'data': ['docs/DATA_PORTABILITY.md']}


def case_policy(tmp):
    """Each tier and feature installs what the approved design says, checked by file name."""
    for tier, rules in POLICY.items():
        target = tmp / f'policy-{tier}'
        target.mkdir()
        install(target, '--tier', tier)
        for f in rules['has']:
            expect((target / f).is_file(), f'{tier} should install {f}')
        for f in rules['lacks']:
            expect(not (target / f).exists(), f'{tier} should not install {f}')
    for feature, files in FEATURE_POLICY.items():
        target = tmp / f'feature-{feature}'
        target.mkdir()
        install(target, '--tier', 'prototype', '--features', feature)
        for f in files:
            expect((target / f).is_file(), f'feature {feature} should install {f}')


def routing_rows(target):
    text = (target / 'AGENTS.md').read_text()
    return text[text.index('<!-- generated: routing'):text.index('<!-- end generated: procedures -->')]


def case_generated_tables(tmp):
    """AGENTS.md lists only installed documents; upgrades add rows; a stale table fails and --sync-adapters repairs it."""
    target = tmp / 'tables'
    target.mkdir()
    install(target, '--tier', 'prototype')
    rows = routing_rows(target)
    for doc in ('VERIFICATION_MATRIX', 'RUNBOOKS', 'UX_DESIGN_SPEC', 'DESIGN_DOC', 'release-readiness', 'PRODUCTION_OPERATIONS'):
        expect(doc not in rows, f'prototype AGENTS.md mentions {doc}, which it does not install')
    for doc in ('TESTING_SPEC', 'PROJECT_PROFILE', 'OPEN_WORK', 'final-audit', 'check_package.py --verify'):
        expect(doc in rows, f'prototype AGENTS.md is missing {doc}')
    install(target, '--tier', 'internal', '--features', 'ui')
    rows = routing_rows(target)
    for doc in ('DESIGN_DOC', 'RUNBOOKS', 'RELEASE_NOTES', 'UX_DESIGN_SPEC'):
        expect(doc in rows, f'internal+ui AGENTS.md is missing {doc} after the upgrade')
    expect('VERIFICATION_MATRIX' not in rows, 'internal AGENTS.md mentions VERIFICATION_MATRIX')
    install(target, '--tier', 'production')
    rows = routing_rows(target)
    expect('VERIFICATION_MATRIX' in rows and 'release-readiness' in rows, 'production AGENTS.md lacks the release rows')
    agents = target / 'AGENTS.md'
    agents.write_text(agents.read_text().replace('<!-- end generated: routing -->', '| Hand-added row | x | y |\n<!-- end generated: routing -->'))
    passed, out = check(target)
    expect(not passed and 'does not match the installed modules' in out, 'a hand-edited routing table was not flagged')
    subprocess.run([sys.executable, '-B', 'check_package.py', '--sync-adapters'], cwd=target, capture_output=True, text=True)
    passed, out = check(target)
    expect(passed and 'Hand-added row' not in agents.read_text(), '--sync-adapters did not repair the routing table:\n    ' + out[:400])


def case_enterprise(tmp):
    """Enterprise adds its gate rows once, keeps an owner's filled-in command, lists its routing rows and reports."""
    target = tmp / 'enterprise-rows'
    target.mkdir()
    install(target, '--tier', 'production')
    profile = target / 'PROJECT_PROFILE.md'
    expect('| Dependency audit |' not in profile.read_text(), 'production should not get the enterprise gate rows')
    install(target, '--tier', 'enterprise')
    text = profile.read_text()
    for gate in ('| Dependency audit |', '| Software bill of materials (SBOM) |', '| License check |'):
        expect(text.count(gate) == 1, f'enterprise install should add {gate} once')
    profile.write_text(text.replace('| Dependency audit | {{DEPENDENCY_AUDIT_COMMAND}} |', '| Dependency audit | `pip-audit` |'))
    install(target, '--tier', 'enterprise')
    text = profile.read_text()
    expect(text.count('| Dependency audit |') == 1 and '`pip-audit`' in text, 'reinstalling duplicated or overwrote the dependency audit row')
    rows = routing_rows(target)
    expect('ENTERPRISE' in rows, 'enterprise AGENTS.md lacks the ENTERPRISE routing rows')
    passed, out = check(target)
    expect(passed and 'Enterprise:' in out, 'enterprise project check failed or reported nothing:\n    ' + out[:600])


def verify_output(target, *args):
    r = subprocess.run([sys.executable, '-B', 'check_package.py', '--verify', *args], cwd=target, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def case_proposed_exclusion(tmp):
    """A proposed exclusion is a gap until the owner confirms it; a confirmed one is excluded."""
    target = tmp / 'proposed-exclusion'
    target.mkdir()
    install(target, '--tier', 'prototype')
    profile = target / 'PROJECT_PROFILE.md'
    text = profile.read_text()
    row = next(l for l in text.splitlines() if l.startswith('| Browser / accessibility smoke |'))
    proposed = row.replace(row.split('|')[2], ' Proposed: Not applicable: no user interface ', 1)
    profile.write_text(text.replace(row, proposed))
    out = verify_output(target)
    expect('gap       Browser / accessibility smoke' in out, 'a proposed exclusion should be a gap:\n    ' + out[-400:])
    profile.write_text(text.replace(row, proposed.replace('Proposed: ', '')))
    out = verify_output(target)
    expect('excluded  Browser / accessibility smoke' in out, 'a confirmed exclusion should be excluded:\n    ' + out[-400:])


def case_dependency_files(tmp):
    """A dependency-audit gap names the project's dependency files, without their contents; a configured audit does not."""
    target = tmp / 'dependency-files'
    target.mkdir()
    install(target, '--tier', 'enterprise')
    (target / 'requirements.txt').write_text('requests==2.19.0\n')
    (target / 'web').mkdir()
    (target / 'web' / 'package.json').write_text('{}\n')
    (target / 'node_modules' / 'x').mkdir(parents=True)
    (target / 'node_modules' / 'x' / 'package.json').write_text('{}\n')
    out = verify_output(target, 'release')
    line = next((l for l in out.splitlines() if l.startswith('Dependency files:')), '')
    expect('requirements.txt' in line and 'web/package.json' in line,
           'a dependency-audit gap should name requirements.txt and web/package.json:\n    ' + out[-600:])
    expect('node_modules' not in line, 'dependency files should skip node_modules: ' + line)
    expect('2.19.0' not in out, '--verify should name dependency files, not print their contents')
    expect('Dependency files:' not in verify_output(target), 'development gates have no dependency audit; no list expected')
    profile = target / 'PROJECT_PROFILE.md'
    profile.write_text(profile.read_text().replace('{{DEPENDENCY_AUDIT_COMMAND}}', '`true`'))
    expect('Dependency files:' not in verify_output(target, 'release'), 'a configured dependency audit should not list files')


def case_rename_scope(tmp):
    """A rename-only code change fails --verify's change scope when it edits guidance documents beyond the rename."""
    target = tmp / 'rename-scope'
    target.mkdir()
    install(target, '--tier', 'prototype')
    code, spec, work = target / 'app.py', target / 'docs' / 'TESTING_SPEC.md', target / 'docs' / 'OPEN_WORK.md'
    code.write_text('def count_words(text):\n    return len(text.split())\n\n\nprint(count_words("a b"))\n')
    spec.write_text(spec.read_text() + '\nThe `count_words` helper is covered by unit tests.\n')
    git = lambda *a: subprocess.run(['git', '-C', str(target), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *a],
                                    capture_output=True, text=True)
    git('init', '-q'); git('add', '-A'); git('commit', '-q', '-m', 'base')
    base = {f: f.read_text() for f in (code, spec, work)}
    def attempt(name, code_text, spec_text=None, work_extra=''):
        for f, text in base.items():
            f.write_text(text)
        (target / 'README.md').write_text(base_readme + '\n## Draft notes\nOwner notes, uncommitted.\n')
        (target / 'scratch').mkdir(exist_ok=True)
        (target / 'scratch' / 'ideas.txt').write_text('Owner notes, untracked.\n')
        code.write_text(code_text)
        if spec_text is not None:
            spec.write_text(spec_text)
        work.write_text(base[work] + work_extra)
        return verify_output(target)
    base_readme = (target / 'README.md').read_text()
    renamed = base[code].replace('count_words', 'word_count')
    out = attempt('register', renamed, work_extra='\n- Renamed count_words to word_count.\n')
    expect('failed: Change scope' in out and 'docs/OPEN_WORK.md' in out,
           'a rename that edits OPEN_WORK should fail the change scope:\n    ' + out[-500:])
    out = attempt('reference', renamed, spec_text=base[spec].replace('count_words', 'word_count'))
    expect('Change scope' not in out, 'a rename that updates a guidance reference should pass:\n    ' + out[-500:])
    out = attempt('code only', renamed)
    expect('Change scope' not in out, 'a plain rename should pass the change scope:\n    ' + out[-500:])
    out = attempt('feature', base[code] + '\n\ndef count_lines(text):\n    return text.count("\\n")\n',
                  work_extra='\n- Line counting added.\n')
    expect('Change scope' not in out, 'a feature change may update OPEN_WORK:\n    ' + out[-500:])
    expect('ask it in your reply as a direct question' in out, 'an OPEN_WORK edit should remind the agent to ask:\n    ' + out[-500:])
    expect('ask it in your reply' not in attempt('code only', renamed), 'no OPEN_WORK edit, no reminder to ask')
    out = attempt('mixed', renamed.replace('len(text.split())', 'len(text.split()) + 0'), work_extra='\n- Note.\n')
    expect('Change scope' not in out, 'a rename mixed with a logic change is not rename-only:\n    ' + out[-500:])


def case_documentation_mode(tmp):
    """--verify documentation runs only the Documentation rows, and fails when the work changes anything but documentation."""
    target = tmp / 'documentation-mode'
    target.mkdir()
    install(target, '--tier', 'prototype')
    expect('documentation mode needs git' in verify_output(target, 'documentation'), 'without git, documentation mode cannot check scope')
    git = lambda *a: subprocess.run(['git', '-C', str(target), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *a],
                                    capture_output=True, text=True)
    git('init', '-q', '-b', 'main'); git('add', '-A'); git('commit', '-q', '-m', 'base')
    (target / 'README.md').write_text((target / 'README.md').read_text() + '\nA documentation edit.\n')
    out = verify_output(target, 'documentation')
    expect(out.startswith('Verification: complete (documentation gates: 1 passed)'),
           'a README edit should pass documentation mode on the Guidance integrity row alone:\n    ' + out[-400:])
    # A guidance upgrade records itself in the manifest and the provenance file; those are guidance records, not code.
    manifest = json.loads((target / 'PACKAGE_MANIFEST.json').read_text())
    manifest['installed_from']['commit'] = 'f' * 40
    (target / 'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (target / 'docs' / 'guidance-provenance.json').write_text('{"records": []}\n')
    out = verify_output(target, 'documentation')
    expect(out.startswith('Verification: complete (documentation gates: 1 passed)'),
           'an upgrade touching only the manifest and provenance should pass documentation mode:\n    ' + out[-400:])
    (target / 'docs' / 'guidance-provenance.json').write_text('{"records": [\n')
    out = verify_output(target, 'documentation')
    expect(out.startswith('Verification: failed') and 'guidance-provenance.json' in out,
           'a provenance file that does not parse should fail the integrity gate:\n    ' + out[-400:])
    (target / 'docs' / 'guidance-provenance.json').write_text('{"records": []}\n')
    (target / 'docs' / 'settings.json').write_text('{}\n')
    out = verify_output(target, 'documentation')
    expect('failed    Change scope' in out and 'settings.json' in out, 'other JSON files are not guidance records:\n    ' + out[-400:])
    (target / 'docs' / 'settings.json').unlink()
    (target / 'app.py').write_text('print("hi")\n')
    out = verify_output(target, 'documentation')
    expect('failed    Change scope' in out and 'app.py' in out, 'untracked code should fail documentation mode:\n    ' + out[-400:])
    git('checkout', '-q', '-b', 'task'); git('add', '-A'); git('commit', '-q', '-m', 'code')
    out = verify_output(target, 'documentation')
    expect('failed    Change scope' in out and 'app.py' in out, 'code committed on a task branch should fail documentation mode:\n    ' + out[-400:])
    expect('Change scope' not in verify_output(target), 'development mode has no documentation-only scope check')
    (target / 'node_modules' / 'pkg').mkdir(parents=True)
    (target / 'node_modules' / 'pkg' / 'README.md').write_text('[missing](nowhere.md)\n')
    passed, out = check(target)
    expect(passed, 'check_package.py should skip node_modules:\n    ' + out[-400:])


def case_copilot_stop(tmp):
    """The Copilot agentStop hook blocks once when a register changed and the final reply asks nothing."""
    import threading, time
    target = tmp / 'copilot-stop'
    target.mkdir()
    install(target, '--tier', 'prototype')
    git = lambda *a: subprocess.run(['git', '-C', str(target), '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', *a],
                                    capture_output=True, text=True)
    git('init', '-q'); git('add', '-A'); git('commit', '-q', '-m', 'base')
    transcript = tmp / 'events.jsonl'
    event = lambda kind, **data: json.dumps({'type': kind, 'data': data}) + '\n'
    stamp = [int(time.time() * 1000)]
    def run(reply, active=False, late=False, tools=False, same=False):
        lines = [event('user.message', content='Implement refunds.'), event('assistant.turn_start')]
        final = event('assistant.message', content=reply, toolRequests=[{'name': 'bash'}] if tools else [])
        transcript.write_text(''.join(lines) + ('' if late else final))
        if late:
            threading.Timer(0.6, lambda: transcript.write_text(''.join(lines) + final)).start()
        stamp[0] += 0 if same else 1  # each call is a new stop event unless it repeats the last one
        payload = json.dumps({'sessionId': 'test-' + str(os.getpid()), 'timestamp': stamp[0],
                              'cwd': str(target), 'transcriptPath': str(transcript), 'stopReason': 'end_turn',
                              'stop_hook_active': active})
        r = subprocess.run([sys.executable, '-B', str(target / '.github/hooks/guidance_stop.py')], input=payload,
                           capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    expect(run('Implemented refunds.') == '', 'no register change: the stop should pass')
    (target / 'docs' / 'OPEN_WORK.md').write_text((target / 'docs' / 'OPEN_WORK.md').read_text() + '\n- Refund window undecided.\n')
    out = run('Implemented refunds; the window remains undecided.')
    expect('"block"' in out and 'docs/OPEN_WORK.md' in out, 'a register change with no question should block: ' + out)
    expect(run('Implemented refunds. How long should the refund window be?') == '', 'a reply that asks should pass')
    expect(run('Implemented refunds; the window remains undecided.', active=True) == '', 'a forced turn should never block again')
    expect('"block"' in run('The window remains undecided.', late=True), 'a reply that reaches the transcript late should still be read')
    expect(run('Running the tests now.', tools=True) == '', 'with no final reply in the transcript the hook should fail open')
    expect('"block"' in run('Still undecided.') and run('Still undecided.', same=True) == '',
           'a second copy of the hook for the same stop (repository and user level) should stay silent')
    (target / 'docs' / 'TODO.md').write_text('- Decide the tier.\n')
    expect('docs/TODO.md' in run('Adopted the guidance.'), "a project's own TODO register counts too")


def case_upgrade(tmp):
    """Moving up a tier and adding a feature adds files and keeps the project's own edits."""
    target = tmp / 'upgrade'
    target.mkdir()
    install(target, '--tier', 'prototype')
    profile = target / 'PROJECT_PROFILE.md'
    profile.write_text(profile.read_text() + '\nOwner edit that must survive.\n')
    install(target, '--tier', 'internal', '--features', 'ui')
    expect('Owner edit that must survive.' in profile.read_text(), 'upgrade overwrote an edited file')
    expect({'design', 'operations', 'ui'} <= modules_present(target), f'upgrade did not add modules: {sorted(modules_present(target))}')
    record = json.loads((target / 'PACKAGE_MANIFEST.json').read_text())['installed']
    expect(record['tier'] == 'internal' and 'ui' in record['features'], f'upgrade record wrong: {record}')
    passed, out = check(target)
    expect(passed, 'upgraded project check failed:\n    ' + out[:600])


def plan_section(out, label):
    """Paths listed under one heading of the --plan-upgrade output."""
    lines, inside = [], False
    for line in out.splitlines():
        if not line.startswith('  '):
            inside = line.startswith(label)
        elif inside:
            lines.append(line.split(' (')[0].strip())
    return lines


def case_plan_upgrade(tmp):
    """--plan-upgrade sorts each file into replace, add, merge and conflict, writes nothing in the project, and its patch
    applies; --check-upgrade then catches a lost local rule, a closed open item and a deleted script still in use."""
    git = ['git', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', '-c', 'user.name=t', '-c', 'user.email=t@example.com']
    run = lambda cmd, cwd: subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    pkg, project = tmp / 'plan-pkg', tmp / 'plan-project'
    paths = [e['path'] for e in manifest['files']] + ['PACKAGE_MANIFEST.json']
    for path in paths:
        (pkg / path).parent.mkdir(parents=True, exist_ok=True)
        (pkg / path).write_bytes((root / path).read_bytes())
    # The older release: three policy lines differ and RELEASE_NOTES does not exist yet.
    old = {'docs/TESTING_SPEC.md': ('2. **Missing tooling is a gap.**', '2. **Missing tooling is a gap (old wording).**'),
           'docs/CHANGE_WORKFLOW.md': ('## Completion\n', '## Completion (old)\n'),
           'docs/RUNBOOKS.md': ('\n## ', '\n## Old heading\n\n## ')}
    for path, (new, before) in old.items():
        text = (pkg / path).read_text()
        expect(new in text, f'plan test: {path} lacks {new!r}')
        (pkg / path).write_text(text.replace(new, before, 1))
    (pkg / 'docs/RELEASE_NOTES.md').unlink()
    record = json.loads((pkg / 'PACKAGE_MANIFEST.json').read_text())
    record['files'] = [e for e in record['files'] if e['path'] != 'docs/RELEASE_NOTES.md']
    for e in record['files']:
        if e['path'] in old:
            e['sha256'] = hashlib.sha256((pkg / e['path']).read_bytes()).hexdigest()
    (pkg / 'PACKAGE_MANIFEST.json').write_text(json.dumps(record, indent=2) + '\n')
    for cmd in (git + ['init', '-q', '-b', 'main'], git + ['add', '-A'], git + ['commit', '-q', '-m', 'old']):
        run(cmd, pkg)
    project.mkdir()
    r = run([sys.executable, '-B', str(pkg / 'check_package.py'), '--install', str(project), '--all'], pkg)
    expect(r.returncode == 0, 'plan test: old install failed: ' + r.stdout[-300:])
    spec, flow = project / 'docs/TESTING_SPEC.md', project / 'docs/CHANGE_WORKFLOW.md'
    spec.write_text(spec.read_text().replace('(old wording).**', '(old wording).** Record the blocker ID in OPEN_WORK.'))
    flow.write_text(flow.read_text().replace('## Verification\n', '## Verification\nRun the smoke script on the review host first.\n'))
    (project / 'docs/OPEN_WORK.md').write_text((project / 'docs/OPEN_WORK.md').read_text() + '\n| OW-7 | Open | Keep me | x | x |\n')
    (project / 'scripts').mkdir(exist_ok=True)
    (project / 'scripts/once.sh').write_text('true\n')
    (project / 'Makefile').write_text('once:\n\tsh scripts/once.sh\n')
    for cmd in (git + ['init', '-q', '-b', 'main'], git + ['add', '-A'], git + ['commit', '-q', '-m', 'project']):
        run(cmd, project)
    for path in paths:
        (pkg / path).write_bytes((root / path).read_bytes())
    for cmd in (git + ['add', '-A'], git + ['commit', '-q', '-m', 'new']):
        run(cmd, pkg)

    planner = [sys.executable, '-B', str(pkg / 'check_package.py')]
    inside = run(planner + ['--plan-upgrade', str(project), '--patch', str(project / 'plan.patch')], pkg)
    expect(inside.returncode and not (project / 'plan.patch').exists(), 'plan test: a patch inside the project was not refused')
    patch = tmp / 'plan.patch'
    r = run(planner + ['--plan-upgrade', str(project), '--patch', str(patch)], pkg)
    out = r.stdout + r.stderr
    expect(r.returncode == 0, 'plan test: --plan-upgrade failed: ' + out[-400:])
    expect(not run(['git', 'status', '--porcelain'], project).stdout, 'plan test: planning changed the project')
    expect('docs/OPEN_WORK.md' not in out, 'plan test: a register upstream did not change is listed')
    expect('Apply nothing' in out and 'git apply' not in out, 'plan test: the plan does not say to stop before applying')
    expect(f"{pkg / 'check_package.py'} --check-upgrade" in out, "plan test: the plan does not name this checkout's checker for the check")
    for label, path in (('Replace', 'docs/RUNBOOKS.md'), ('Add', 'docs/RELEASE_NOTES.md'), ('Merge', 'docs/CHANGE_WORKFLOW.md'),
                        ('Conflict', 'docs/TESTING_SPEC.md')):
        expect(path in plan_section(out, label), f'plan test: {path} not under {label}:\n    ' + out[:900])
    applied = run(['git', 'apply', str(patch)], project)
    expect(applied.returncode == 0, 'plan test: the patch does not apply: ' + applied.stderr[:300])
    text = flow.read_text()
    expect('Run the smoke script' in text and '## Completion\n' in text, 'plan test: the merge lost a side of CHANGE_WORKFLOW.md')
    expect(json.loads((project / 'PACKAGE_MANIFEST.json').read_text()).get('installed_from', {}).get('commit')
           == run(['git', 'rev-parse', 'HEAD'], pkg).stdout.strip(), 'plan test: the patch does not record the new commit')

    checker = planner + ['--check-upgrade', str(project)]
    # The conflict merged by hand, keeping the local rule in new words.
    spec.write_text((root / 'docs/TESTING_SPEC.md').read_text().replace('**Missing tooling is a gap.**',
                                                                       '**Missing tooling is a gap.** Record the blocker ID in OPEN_WORK.'))
    r = run(checker, pkg)
    expect(r.returncode == 0, 'plan test: --check-upgrade failed on a clean upgrade: ' + (r.stdout + r.stderr)[-400:])
    own = run([sys.executable, '-B', str(project / 'check_package.py'), '--check-upgrade', '.'], project)
    expect(own.returncode and 'Could not check local changes' in own.stdout,
           "plan test: the project's own copy passed --check-upgrade without the installed release:\n    " + (own.stdout + own.stderr)[-400:])
    flow.write_text(flow.read_text().replace('Run the smoke script on the review host first.\n', ''))
    work = project / 'docs/OPEN_WORK.md'
    work.write_text(work.read_text().replace('| OW-7 | Open |', '| OW-7 | Closed |'))
    (project / 'scripts/once.sh').unlink()
    r = run(checker, pkg)
    out = r.stdout + r.stderr
    for found, what in (('CHANGE_WORKFLOW.md' in out, 'the dropped local rule'), ('OW-7' in out, 'the closed open item'),
                        ('Makefile' in out, 'the deleted script still in use')):
        expect(r.returncode and found, f'plan test: --check-upgrade missed {what}:\n    ' + out[-500:])


def case_tools(tmp):
    """--tools installs and checks only the adapters and guardrails of the tools a project uses (V4-8)."""
    target = tmp / 'tools'
    target.mkdir()
    if install(target, '--tier', 'prototype', '--tools', 'claude').returncode:
        return  # the failed install is already a problem
    present = lambda prefix: [p for p in module_of if p.startswith(prefix) and (target / p).is_file()]
    expect(not present('.agents/') and not present('.codex/') and not present('.github/hooks/'),
           f"claude-only install copied other tools' files: {present('.agents/') + present('.codex/') + present('.github/hooks/')}")
    expect(present('.claude/') and (target / 'CLAUDE.md').is_file(), 'claude-only install lacks the Claude Code files')
    record = json.loads((target / 'PACKAGE_MANIFEST.json').read_text())['installed']
    expect(record.get('tools') == ['claude'], f'tools not recorded: {record}')
    passed, out = check(target)
    expect(passed, 'claude-only project check failed:\n    ' + out[:600])
    skill = target / '.claude/skills/final-audit/SKILL.md'
    skill.unlink()
    passed, out = check(target)
    expect(not passed and 'final-audit' in out, 'removing an adopted tool adapter did not fail the check')
    subprocess.run([sys.executable, '-B', 'check_package.py', '--sync-adapters'], cwd=target, capture_output=True, text=True)
    expect(skill.is_file() and not (target / '.agents').exists(), 'sync did not restore only the adopted tool adapters')
    plan = subprocess.run([sys.executable, '-B', str(root / 'check_package.py'), '--plan-upgrade', str(target)], capture_output=True, text=True)
    expect('.agents/' not in plan.stdout and '.codex/' not in plan.stdout, "the plan proposes other tools' files:\n    " + plan.stdout[:600])
    install(target, '--tools', 'codex')
    record = json.loads((target / 'PACKAGE_MANIFEST.json').read_text())['installed']
    expect(record.get('tools') == ['claude', 'codex'] and present('.agents/') and present('.codex/'),
           f'adding a tool did not add its files: {record}')
    passed, out = check(target)
    expect(passed, 'project check failed after adding a tool:\n    ' + out[:600])
    everything = tmp / 'tools-all'
    everything.mkdir()
    install(everything, '--tier', 'prototype')
    record = json.loads((everything / 'PACKAGE_MANIFEST.json').read_text())['installed']
    expect(record.get('tools') == sorted(manifest['tools']), f'an install without --tools should get every tool: {record}')
    r = raw_install(tmp, '--tier', 'prototype', '--tools', 'vim')
    expect(r.returncode and 'Unknown tool' in r.stdout + r.stderr, 'an unknown tool was accepted')


def case_recorded_exclusions(tmp):
    """Absent files named in backticks in the profile's Excluded guidance row are not reported, links to them are
    accepted, unrecorded absences are still listed, and a required module stays required (V4-9)."""
    target = tmp / 'exclusions'
    target.mkdir()
    if install(target, '--tier', 'production').returncode:
        return
    profile = target / 'PROJECT_PROFILE.md'
    for path in ('docs/ROADMAP.md', 'docs/REQUIREMENTS_REVIEW.md', 'docs/VERIFICATION_REVIEW.md',
                 '.github/hooks/guidance.json', '.github/hooks/guidance_guardrail.py', '.github/hooks/guidance_stop.py'):
        (target / path).unlink()
    passed, out = check(target)
    expect(not passed and 'docs/ROADMAP.md' in out, 'a linked file removed without a recorded exclusion should fail the link check')
    text = profile.read_text()
    expect('{{EXCLUDED_GUIDES_OR_NONE}}' in text, 'exclusions test: the profile lacks the Excluded guidance placeholder')
    profile.write_text(text.replace('{{EXCLUDED_GUIDES_OR_NONE}}', 'Owner decision: no roadmap (`docs/ROADMAP.md`), '
                                    'no requirements review (`docs/REQUIREMENTS_REVIEW.md`) and no Copilot (`.github/hooks/`)'))
    passed, out = check(target)
    expect(passed, 'recorded exclusions still fail the check:\n    ' + out[:600])
    expect('5 packaged files absent as recorded' in out, 'recorded exclusions not counted:\n    ' + out[:600])
    unrecorded = [l for l in out.splitlines() if 'not recorded as excluded' in l]
    expect(len(unrecorded) == 1 and unrecorded[0].endswith('docs/VERIFICATION_REVIEW.md'),
           f'only the unrecorded absence should be listed: {unrecorded}')
    design = [p for p, m in module_of.items() if m == 'design' and (target / p).is_file()]
    for path in design:
        (target / path).unlink()
    profile.write_text(profile.read_text().replace('(`docs/ROADMAP.md`)', '(' + ', '.join(f'`{p}`' for p in design + ['docs/ROADMAP.md']) + ')'))
    passed, out = check(target)
    expect(not passed and 'requires the design module' in out, 'a required module recorded as excluded should still fail:\n    ' + out[:600])


def case_gate_timeouts(tmp):
    """A gate's own limit in its Gate cell replaces --timeout for that gate only, and a timeout names its limit (V4-10)."""
    target = tmp / 'gate-timeouts'
    target.mkdir()
    if install(target, '--tier', 'prototype').returncode:
        return
    profile = target / 'PROJECT_PROFILE.md'
    text = profile.read_text()
    sleep = lambda n: f'`python3 -c "import time; time.sleep({n})"`'
    rows = {'| Format |': (sleep(2), 'Development, timeout 10s'), '| Build / generate |': (sleep(3), 'Development, timeout 1s'),
            '| Unit / integration tests |': (sleep(2), 'Development')}
    for start, (command, gate) in rows.items():
        row = next(l for l in text.splitlines() if l.startswith(start))
        cells = row.split('|')
        cells[2], cells[3] = f' {command} ', f' {gate} '
        text = text.replace(row, '|'.join(cells))
    profile.write_text(text)
    out = verify_output(target, '--timeout', '1')
    line = lambda name: next((l for l in out.splitlines() if name in l and l.startswith('  ')), '')
    expect(line('Format:').strip().startswith('passed'), 'a slow gate with its own longer limit should pass:\n    ' + out[-700:])
    expect(line('Build / generate:').strip().startswith('failed') and "timed out after 1s (this gate's own limit)" in out,
           'a gate past its own limit should fail as timed out with that limit:\n    ' + out[-700:])
    expect(line('Unit / integration tests:').strip().startswith('failed') and 'timed out after 1s (the --timeout default' in out,
           'a gate without its own limit should keep the --timeout value:\n    ' + out[-700:])


def raw_install(target, *args):
    return subprocess.run([sys.executable, '-B', str(root / 'check_package.py'), '--install', str(target), *args],
                          capture_output=True, text=True)


def case_default(tmp):
    """A fresh install without a tier copies nothing and explains the choice; --all is the 2.x set (every module
    except enterprise); --dry-run writes nothing; a rerun without a tier keeps the project's modules."""
    target = tmp / 'default'
    target.mkdir()
    r = raw_install(target)
    expect(r.returncode != 0 and 'Choose a tier; nothing was installed.' in r.stdout + r.stderr and '--all' in r.stdout + r.stderr,
           'an install without a tier did not stop and explain: ' + (r.stdout + r.stderr)[-300:])
    expect(not any(target.iterdir()), 'an install without a tier copied files: ' + ', '.join(p.name for p in target.iterdir()))
    r = raw_install(target, '--all', '--tier', 'internal')
    expect(r.returncode != 0 and not any(target.iterdir()), '--all with --tier was accepted')

    preview = tmp / 'preview'
    preview.mkdir()
    r = raw_install(preview, '--tier', 'internal', '--features', 'ui', '--dry-run')
    out = r.stdout + r.stderr
    expect(r.returncode == 0 and 'Would copy' in out and 'AGENTS.md' in out and 'docs/UX_DESIGN_SPEC.md' in out
           and 'docs/ENTERPRISE.md' not in out, '--dry-run did not list the files it would copy: ' + out[-300:])
    expect(not any(preview.iterdir()), '--dry-run wrote files')

    everything = tmp / 'everything'
    everything.mkdir()
    install(everything, '--all')
    wanted = set(module_of.values()) - {'enterprise'}
    expect(modules_present(everything) == wanted, f'--all modules {sorted(modules_present(everything))}, expected {sorted(wanted)}')
    passed, out = check(everything)
    expect(passed, '--all install check failed:\n    ' + out[:600])

    small = tmp / 'rerun'
    small.mkdir()
    install(small, '--tier', 'prototype')
    before = modules_present(small)
    install(small)
    expect(modules_present(small) == before == {'core'}, f'a rerun without a tier changed the modules: {sorted(modules_present(small))}')
    install(small, '--features', 'ui')
    expect(modules_present(small) == {'core', 'ui'}, f'a rerun adding ui gave {sorted(modules_present(small))}')


def case_missing_module(tmp):
    """Deleting every file of a required module fails the project check."""
    target = tmp / 'missing'
    target.mkdir()
    install(target, '--tier', 'internal')
    for p, m in module_of.items():
        if m == 'design':
            (target / p).unlink(missing_ok=True)
    passed, out = check(target)
    expect(not passed and 'requires the design module' in out, 'removing the design module did not fail the check:\n    ' + out[:400])


def case_broken_link(tmp):
    """A link to a file that is neither installed nor packaged still fails."""
    target = tmp / 'link'
    target.mkdir()
    install(target, '--tier', 'prototype')
    (target / 'docs' / 'NOTES.md').write_text('See [missing](MISSING.md).\n')
    passed, out = check(target)
    expect(not passed and 'MISSING.md' in out, 'a broken link passed the project check')


def table():
    sizes = {e['path']: e.get('bytes', 0) for e in manifest['files']}
    print('| Tier | Modules | Files | KB | Agent-facing prose KB |')
    print('|---|---|---|---|---|')
    tooling = ('check_package.py', 'scripts/', '.claude/', '.codex/', '.github/', '.agents/', 'README.md', 'docs/AGENT_TOOLS.md', 'CLAUDE.md')
    for tier, mods in manifest['tiers'].items():
        files = [p for p, m in module_of.items() if m in mods]
        prose = [p for p in files if p.endswith('.md') and not p.startswith(tooling) and p not in tooling]
        print(f"| {tier} | {', '.join(mods)} | {len(files)} | {sum(sizes[p] for p in files) / 1024:.0f} | {sum(sizes[p] for p in prose) / 1024:.0f} |")
    print('\nFeatures add: ' + '; '.join(f"{f}: {', '.join(p for p, m in module_of.items() if m in mods)}"
                                       for f, mods in manifest['features'].items()))


def main():
    if '--table' in sys.argv:
        table()
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for case in (case_tiers, case_policy, case_generated_tables, case_enterprise, case_proposed_exclusion, case_dependency_files, case_rename_scope, case_documentation_mode, case_copilot_stop, case_upgrade, case_plan_upgrade, case_tools, case_recorded_exclusions, case_gate_timeouts, case_default, case_missing_module, case_broken_link):
            case(tmp)
    if problems:
        print('\n'.join(problems))
        sys.exit(1)
    print('Install tests OK: tiers, design policy, generated tables, enterprise rows, proposed exclusions, dependency files, rename scope, documentation mode, Copilot stop hook, features, upgrade, upgrade plan and check, tools, recorded exclusions, gate timeouts, tier required (dry run, --all, rerun), missing module and broken link.')


if __name__ == '__main__':
    main()
