#!/usr/bin/env python3
"""Tier-aware install, verifier, selective-skill, agent-team interop, and upgrade tests (v4.0)."""
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile

root = Path(__file__).resolve().parent.parent
manifest = json.loads((root / 'PACKAGE_MANIFEST.json').read_text())
module_of = {e['path']: e.get('module') for e in manifest['files']}
AGENT_TEAM_BOOTSTRAP = Path(os.environ.get('AGENT_TEAM_BOOTSTRAP') or (root.parent / 'agent-team' / 'bootstrap.py'))
problems = []


def run_manage(cwd, *args):
    return subprocess.run([sys.executable, '-B', str(root / 'manage.py'), *args], cwd=cwd, capture_output=True, text=True)


def install(target, *args):
    r = run_manage(root, '--install', str(target), *args)
    if r.returncode:
        problems.append(f"install {' '.join(args) or '(no tier)'} failed: {(r.stdout + r.stderr).strip()[-400:]}")
    return r


def check(target, *args):
    r = subprocess.run([sys.executable, '-B', 'scripts/verify.py', *args], cwd=target, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def verify(target, *args):
    return subprocess.run([sys.executable, '-B', 'scripts/verify.py', '--verify', *args], cwd=target, capture_output=True, text=True)


def expect(cond, message):
    if not cond:
        problems.append(message)


def modules_present(target):
    return {m for p, m in module_of.items() if m and (target / p).is_file()}


def plan_section(out, label):
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(label):
            rest = lines[i + 1:]
            end = next((j for j, l in enumerate(rest) if not l.startswith('  ')), len(rest))
            return '\n'.join(rest[:end])
    return ''


def init_git(target, msg='init'):
    git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@e', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']
    for cmd in (['init', '-q', '-b', 'main'], ['add', '-A'], ['commit', '-q', '-m', msg]):
        r = subprocess.run(git + cmd, cwd=target, capture_output=True, text=True)
        if r.returncode:
            problems.append(f'git {cmd[0]} failed in {target}: {r.stderr}')
    return git


POLICY = {
    'prototype': {
        'has': ['AGENTS.md', 'CLAUDE.md', 'PROJECT_PROFILE.md', 'docs/OPEN_WORK.md', 'scripts/verify.py', '.guidance.json', 'README.md'],
        'lacks': ['DESIGN_DOC.md', 'docs/RUNBOOKS.md', 'docs/RELEASE_NOTES.md', 'docs/PRODUCTION_READINESS.md',
                  'docs/VERIFICATION_MATRIX.md', 'docs/ENTERPRISE.md', 'docs/UI.md',
                  'docs/procedures/release-review.md', 'docs/procedures/release-readiness.md', 'docs/procedures/ui-design.md',
                  '.agents/skills/release-review/SKILL.md', '.agents/skills/bootstrap-project/SKILL.md'],
    },
    'internal': {
        'has': ['DESIGN_DOC.md', 'docs/decisions/ADR_TEMPLATE.md', 'docs/RUNBOOKS.md', 'docs/RELEASE_NOTES.md'],
        'lacks': ['docs/PRODUCTION_READINESS.md', 'docs/VERIFICATION_MATRIX.md', 'docs/ENTERPRISE.md', 'docs/UI.md',
                  'docs/procedures/release-review.md', '.agents/skills/release-review/SKILL.md'],
    },
    'production': {
        'has': ['DESIGN_DOC.md', 'docs/RUNBOOKS.md', 'docs/VERIFICATION_MATRIX.md', 'docs/PRODUCTION_READINESS.md',
                'docs/procedures/release-review.md', 'docs/procedures/release-readiness.md',
                '.agents/skills/release-review/SKILL.md', '.claude/skills/release-review/SKILL.md',
                '.agents/skills/release-readiness/SKILL.md', '.claude/skills/release-readiness/SKILL.md'],
        'lacks': ['docs/ENTERPRISE.md', '.github/pull_request_template.md', 'docs/UI.md', 'docs/procedures/ui-design.md'],
    },
    'enterprise': {
        'has': ['docs/ENTERPRISE.md', '.github/pull_request_template.md', 'docs/procedures/release-review.md',
                'docs/procedures/release-readiness.md'],
        'lacks': ['docs/procedures/bootstrap-project.md', 'docs/procedures/final-audit.md', 'docs/procedures/upgrade-guidance.md',
                  'check_package.py', 'PACKAGE_MANIFEST.json', 'docs/DOMAIN_RULES.md', 'docs/TESTING_SPEC.md', 'docs/CHANGE_WORKFLOW.md'],
    },
}


def case_tiers(tmp):
    for tier, features in (('prototype', ''), ('internal', ''), ('internal', 'release-review'),
                           ('production', 'ui'), ('enterprise', 'ui,ui-design'), ('prototype', 'embedded'),
                           ('internal', 'stack-go'), ('internal', 'stack-rust')):
        target = tmp / f't-{tier}-{features or "none"}'
        target.mkdir()
        install(target, '--tier', tier, '--features', features)
        wanted = set(manifest['tiers'][tier]) | {m for f in filter(None, features.split(',')) for m in manifest['features'][f]}
        expect(modules_present(target) == wanted, f'{tier}+{features}: modules {sorted(modules_present(target))} != {sorted(wanted)}')
        rec = json.loads((target / '.guidance.json').read_text()).get('installed', {})
        expect(rec.get('tier') == tier and set(rec.get('modules', [])) == wanted, f'{tier}+{features}: .guidance.json mismatch: {rec}')
        passed, out = check(target)
        expect(passed, f'{tier}+{features}: scripts/verify.py failed:\n    ' + out.replace('\n', '\n    ')[:600])
        expect(not (target / 'PACKAGE_MANIFEST.json').exists() and not (target / 'check_package.py').exists(),
               f'{tier}: legacy check_package.py or PACKAGE_MANIFEST.json leaked into project')


def case_policy(tmp):
    for tier, spec in POLICY.items():
        target = tmp / f'policy-{tier}'
        target.mkdir()
        install(target, '--tier', tier)
        for p in spec['has']:
            expect((target / p).is_file(), f'policy {tier}: missing {p}')
        for p in spec['lacks']:
            expect(not (target / p).exists(), f'policy {tier}: unexpected {p}')
        profile = (target / 'PROJECT_PROFILE.md').read_text()
        has_rel_sec = '## Release qualification profile' in profile
        expect(has_rel_sec == (tier in ('production', 'enterprise')),
               f'policy {tier}: Release qualification profile presence={has_rel_sec}')
        expect('<!-- module:' not in profile, f'policy {tier}: raw module markers left in PROJECT_PROFILE.md')
        if tier in ('production', 'enterprise'):
            expect('## Tier gate expectations' in (target / 'docs/procedures/release-readiness.md').read_text(),
                   f'policy {tier}: release-readiness.md missing Tier gate expectations table')


def case_selective_skills_and_sync(tmp):
    proto = tmp / 'sel-proto'
    proto.mkdir()
    install(proto, '--tier', 'prototype')
    expect(not (proto / '.agents' / 'skills').exists(), 'prototype should install no skills')
    expect('## On-demand skills' not in (proto / 'AGENTS.md').read_text(), 'prototype AGENTS.md should omit On-demand skills')

    internal_rr = tmp / 'sel-int-rr'
    internal_rr.mkdir()
    install(internal_rr, '--tier', 'internal', '--features', 'release-review')
    for tool_dir in ('.agents/skills', '.claude/skills'):
        expect((internal_rr / tool_dir / 'release-review/SKILL.md').is_file(), f'missing {tool_dir}/release-review/SKILL.md')
        expect(not (internal_rr / tool_dir / 'release-readiness/SKILL.md').exists(), 'internal+release-review should not include release-readiness')
        expect(not (internal_rr / tool_dir / 'ui-design/SKILL.md').exists(), 'internal+release-review should not include ui-design')
    expect((internal_rr / '.agents/skills/release-review/SKILL.md').read_text()
           == (internal_rr / '.claude/skills/release-review/SKILL.md').read_text(), 'skill copies must match byte-for-byte')
    expect('## On-demand skills' in (internal_rr / 'AGENTS.md').read_text(), 'internal+release-review should show On-demand skills')

    ui = tmp / 'sel-ui-design'
    ui.mkdir()
    install(ui, '--tier', 'internal', '--features', 'ui-design')
    expect((ui / 'docs/UI.md').is_file() and (ui / 'docs/procedures/ui-design.md').is_file(), 'ui-design did not install UI.md + ui-design.md')
    expect((ui / '.agents/skills/ui-design/SKILL.md').is_file(), 'missing .agents/skills/ui-design/SKILL.md')
    # Hand-corrupt AGENTS.md and SKILL.md, fail scripts/verify.py, repair with manage.py --sync DIR.
    (ui / 'AGENTS.md').write_text((ui / 'AGENTS.md').read_text() + '\n## Team note\nKeep handlers pure.\n')
    (ui / '.agents/skills/ui-design/SKILL.md').unlink()
    ok, _ = check(ui)
    expect(not ok, 'scripts/verify.py should fail when skill wrapper is missing')
    r = run_manage(root, '--sync', str(ui))
    expect(r.returncode == 0, 'manage.py --sync DIR failed: ' + r.stderr)
    ok, out = check(ui)
    expect(ok, 'scripts/verify.py failed after manage.py --sync DIR: ' + out)
    expect('## Team note\nKeep handlers pure.' in (ui / 'AGENTS.md').read_text(), '--sync DIR dropped custom AGENTS.md section')
    # --sync . from inside the project resolves against cwd rather than entering template mode.
    (ui / '.claude/skills/ui-design/SKILL.md').unlink()
    r_dot = run_manage(ui, '--sync', '.')
    expect(r_dot.returncode == 0 and (ui / '.claude/skills/ui-design/SKILL.md').is_file(),
           '--sync . from project dir did not regenerate missing skill wrapper')


def case_generated_tables_and_enterprise(tmp):
    target = tmp / 'ent-rows'
    target.mkdir()
    install(target, '--tier', 'prototype')
    agents = (target / 'AGENTS.md').read_text()
    expect('DESIGN_DOC' not in agents and 'VERIFICATION_MATRIX' not in agents, 'prototype AGENTS.md leaked higher-tier rows')
    # Add custom License check row then upgrade tier to enterprise via rerun --install.
    profile = target / 'PROJECT_PROFILE.md'
    profile.write_text(profile.read_text().replace('| Guidance integrity |', '| License check | `reuse lint` | Release | Any | Checked |\n| Guidance integrity |'))
    install(target, '--tier', 'enterprise')
    text = profile.read_text()
    expect('| Dependency audit |' in text and '| Software bill of materials (SBOM) |' in text, 'enterprise rows missing after upgrade')
    expect('| License check | `reuse lint` |' in text and text.count('| License check |') == 1, 'owner License check row was overwritten or duplicated')
    agents = (target / 'AGENTS.md').read_text()
    expect('DESIGN_DOC' in agents and 'VERIFICATION_MATRIX' in agents and 'docs/ENTERPRISE' in agents, 'enterprise AGENTS.md missing rows')
    # Hand-editing, deleting, or duplicating a generated AGENTS.md table or deleting .guidance.json fails scripts/verify.py.
    (target / 'AGENTS.md').write_text(agents.replace('| Requirement verification status |', '| Tampered row |'))
    ok, out = check(target)
    expect(not ok and 'AGENTS.md routing table' in out,
           'scripts/verify.py should fail on tampered AGENTS.md table: ' + out)
    r_sync = run_manage(root, '--sync', str(target))
    expect(r_sync.returncode == 0, 'manage.py --sync failed after table edit: ' + r_sync.stderr)
    ok, out = check(target)
    expect(ok, 'scripts/verify.py failed after manage.py --sync repaired table: ' + out)

    clean_agents = (target / 'AGENTS.md').read_text()
    without_routing = re.sub(r'<!-- generated: routing;.*?<!-- end generated: routing -->\n?', '', clean_agents, flags=re.S)
    (target / 'AGENTS.md').write_text(without_routing)
    ok, out = check(target)
    expect(not ok and 'AGENTS.md routing table' in out and 'finish merging AGENTS.md' in out,
           'scripts/verify.py should fail cleanly when generated routing block markers are missing: ' + out)

    routing_block = re.search(r'(<!-- generated: routing;.*?<!-- end generated: routing -->\n?)', clean_agents, re.S).group(1)
    (target / 'AGENTS.md').write_text(clean_agents + '\n' + routing_block)
    ok, out = check(target)
    expect(not ok and 'AGENTS.md routing table' in out,
           'scripts/verify.py should fail when generated routing block is duplicated: ' + out)
    (target / 'AGENTS.md').write_text(clean_agents)

    guidance_copy = (target / '.guidance.json').read_text()
    (target / '.guidance.json').unlink()
    ok, out = check(target)
    expect(not ok and '.guidance.json not found' in out,
           'scripts/verify.py should fail when .guidance.json is removed: ' + out)
    (target / '.guidance.json').write_text(guidance_copy)
    ok, out = check(target)
    expect(ok, 'scripts/verify.py failed after restoring .guidance.json: ' + out)


def case_guardrails(tmp):
    ent = tmp / 'guard-ent'
    ent.mkdir()
    install(ent, '--tier', 'enterprise')
    expect('Bash(gh pr merge:*)' in (ent / '.claude/settings.json').read_text(), 'enterprise claude guardrail lacks gh pr merge')
    expect('gh' in (ent / '.codex/rules/guidance.rules').read_text(), 'enterprise codex guardrail lacks gh rules')
    ok, out = check(ent)
    expect(ok, 'enterprise guardrail check failed: ' + out)

    proto = tmp / 'guard-proto'
    proto.mkdir()
    install(proto, '--tier', 'prototype')
    expect('Bash(gh pr merge:*)' not in (proto / '.claude/settings.json').read_text(), 'prototype claude guardrail kept gh pr merge')
    hook_cfg = json.loads((proto / '.github/hooks/guidance.json').read_text())
    expect('preToolUse' in hook_cfg.get('hooks', {}) and 'agentStop' not in hook_cfg.get('hooks', {}),
           'default .github/hooks/guidance.json must ship preToolUse only (no agentStop)')
    # Break or delete each enterprise guardrail file and verify scripts/verify.py rejects it.
    claude_guard = ent / '.claude/settings.json'
    codex_guard = ent / '.codex/rules/guidance.rules'
    copilot_guard = ent / '.github/hooks/guidance_guardrail.py'
    orig_claude = claude_guard.read_text()
    claude_guard.write_text('{"permissions": {"ask": [], "deny": []}}\n')
    ok, out = check(ent)
    expect(not ok and 'merge a pull request' in out, 'scripts/verify.py should fail when enterprise guardrail is removed')
    claude_cfg = json.loads(orig_claude)
    claude_allow = json.loads(orig_claude)
    claude_allow['permissions']['ask'] = [r for r in claude_cfg['permissions']['ask'] if 'gh pr merge' not in r]
    claude_allow['permissions']['allow'] = ['Bash(gh pr merge:*)']
    claude_guard.write_text(json.dumps(claude_allow, indent=2) + '\n')
    ok, out = check(ent)
    expect(not ok and '.claude/settings.json' in out,
           'scripts/verify.py must reject Claude guardrail moved to permissions.allow: ' + out)
    claude_both = json.loads(orig_claude)
    claude_both['permissions']['allow'] = ['Bash(gh pr merge:*)']
    claude_guard.write_text(json.dumps(claude_both, indent=2) + '\n')
    ok, out = check(ent)
    expect(not ok and '.claude/settings.json' in out,
           'scripts/verify.py must reject Claude guardrail duplicated into permissions.allow: ' + out)
    claude_guard.write_text(orig_claude)

    orig_codex = codex_guard.read_text()
    codex_guard.write_text(orig_codex.replace('pattern = ["gh", "pr", "merge"],\n    decision = "prompt"',
                                              'pattern = ["gh", "pr", "merge"],\n    decision = "allow"'))
    ok, out = check(ent)
    expect(not ok and '.codex/rules/guidance.rules' in out,
           'scripts/verify.py must reject Codex decision = "allow" guardrail: ' + out)
    codex_guard.write_text('\n'.join(
        '# ' + l if '["gh", "pr", "merge"]' in l else l for l in orig_codex.splitlines()
    ) + '\n')
    ok, out = check(ent)
    expect(not ok and '.codex/rules/guidance.rules' in out,
           'scripts/verify.py must reject commented-out Codex guardrail: ' + out)
    codex_guard.write_text(orig_codex)

    orig_copilot_py = copilot_guard.read_text()
    copilot_guard.write_text(orig_copilot_py.replace("(['pr', 'merge'],", "# (['pr', 'merge'],"))
    ok, out = check(ent)
    expect(not ok and '.github/hooks/guidance_guardrail.py' in out,
           'scripts/verify.py must reject commented-out Copilot GH_ASK entry: ' + out)
    copilot_guard.write_text(re.sub(
        r"\(\['pr', 'merge'\],[^\n]+\n", '', orig_copilot_py, count=1,
    ) + "\nGH_DENY = [(['pr', 'merge'], 'blocked')]\n")
    ok, out = check(ent)
    expect(not ok and '.github/hooks/guidance_guardrail.py' in out,
           'scripts/verify.py must reject Copilot entry moved to inactive GH_DENY: ' + out)
    copilot_guard.write_text(re.sub(
        r"\(\['pr', 'merge'\],[^\n]+\n", '', orig_copilot_py, count=1,
    ).replace("(['clean'],", "(['pr', 'merge'], 'wrong table'),\n    (['clean'],", 1))
    ok, out = check(ent)
    expect(not ok and '.github/hooks/guidance_guardrail.py' in out,
           'scripts/verify.py must reject Copilot gh entry moved to git ASK table: ' + out)
    copilot_guard.write_text(orig_copilot_py + '\nGH_ASK = []\n')
    ok, out = check(ent)
    expect(not ok and '.github/hooks/guidance_guardrail.py' in out,
           'scripts/verify.py must reject shadowed empty GH_ASK assignment: ' + out)
    copilot_guard.write_text(orig_copilot_py)

    def run_copilot_hook(proj, payload):
        r = subprocess.run([sys.executable, '-B', '.github/hooks/guidance_guardrail.py'],
                           cwd=proj, input=json.dumps(payload), capture_output=True, text=True)
        expect(r.returncode == 0, f'guidance_guardrail.py exited {r.returncode}: {r.stderr}')
        return json.loads(r.stdout) if r.stdout.strip() else None

    for event, want in (
        ({'toolName': 'bash', 'toolArgs': {'command': 'gh pr merge 1'}}, 'ask'),
        ({'toolName': 'bash', 'toolArgs': json.dumps({'command': 'gh release create v1'})}, 'ask'),
        ({'toolName': 'bash', 'toolArgs': {'command': 'git reset --hard HEAD'}}, 'ask'),
        ({'toolName': 'view', 'toolArgs': {'path': '.env'}}, 'deny'),
        ({'toolName': 'bash', 'toolArgs': {'command': 'git status'}}, None),
    ):
        got = run_copilot_hook(ent, event)
        got_dec = got.get('permissionDecision') if isinstance(got, dict) else None
        expect(got_dec == want, f'enterprise hook decision for {event} was {got!r}, expected {want!r}')
    proto_merge = run_copilot_hook(proto, {'toolName': 'bash', 'toolArgs': {'command': 'gh pr merge 1'}})
    expect(proto_merge is None, f'prototype hook must not gate gh pr merge: {proto_merge!r}')

    for path, orig in ((claude_guard, orig_claude),
                       (codex_guard, orig_codex),
                       (copilot_guard, orig_copilot_py)):
        path.unlink()
        ok, out = check(ent)
        expect(not ok and path.name in out and 'merge a pull request' in out,
               f'scripts/verify.py should fail when {path.name} is deleted: {out}')
        path.write_text(orig)
    # Fallback checks when guardrail_checks is absent must respect adopted tools.
    gpath = ent / '.guidance.json'
    rec = json.loads(gpath.read_text())
    rec.pop('guardrail_checks', None)
    rec['installed']['tools'] = ['claude']
    gpath.write_text(json.dumps(rec, indent=2) + '\n')
    codex_guard.unlink()
    copilot_guard.unlink()
    ok, out = check(ent)
    expect(ok, 'fallback guardrail check should ignore uninstalled tools: ' + out)
    claude_guard.unlink()
    ok, out = check(ent)
    expect(not ok and '.claude/settings.json' in out, 'fallback guardrail check must fail when adopted tool file is deleted: ' + out)

    # Copilot enterprise guardrails also require preToolUse hook registration in .github/hooks/guidance.json.
    ent2 = tmp / 'guard-ent-hook'
    ent2.mkdir()
    install(ent2, '--tier', 'enterprise', '--tools', 'copilot')
    hcfg = ent2 / '.github/hooks/guidance.json'
    orig_hcfg = hcfg.read_text()
    hcfg.write_text('{"version": 1, "hooks": {}}\n')
    ok, out = check(ent2)
    expect(not ok and 'guidance.json' in out and 'preToolUse' in out,
           'scripts/verify.py should fail when .github/hooks/guidance.json empties hooks.preToolUse: ' + out)
    hcfg.unlink()
    ok, out = check(ent2)
    expect(not ok and 'guidance.json' in out and 'preToolUse' in out,
           'scripts/verify.py should fail when .github/hooks/guidance.json is missing: ' + out)
    hcfg.write_text(orig_hcfg)
    ok, out = check(ent2)
    expect(ok, 'scripts/verify.py failed after restoring .github/hooks/guidance.json: ' + out)

    base_hook = json.loads(orig_hcfg)
    for label, mut in (
        ('disabled both', lambda d: d['hooks']['preToolUse'][0].update({
            'bash': 'python3 .github/hooks/guidance_guardrail.py.disabled',
            'powershell': 'python .github/hooks/guidance_guardrail.py.disabled',
        })),
        ('disabled bash only', lambda d: d['hooks']['preToolUse'][0].update({
            'bash': 'python3 .github/hooks/guidance_guardrail.py.disabled',
        })),
        ('echo command', lambda d: d['hooks']['preToolUse'][0].update({
            'bash': 'echo .github/hooks/guidance_guardrail.py',
        })),
        ('trailing shell operator', lambda d: d['hooks']['preToolUse'][0].update({
            'bash': 'python3 .github/hooks/guidance_guardrail.py || true',
        })),
        ('wrong cwd', lambda d: d['hooks']['preToolUse'][0].update({'cwd': 'subdir'})),
        ('disabled type', lambda d: d['hooks']['preToolUse'][0].update({'type': 'disabled'})),
        ('view-only matcher', lambda d: d['hooks']['preToolUse'][0].update({'matcher': 'view'})),
        ('empty matcher', lambda d: d['hooks']['preToolUse'][0].update({'matcher': ''})),
        ('invalid regex matcher', lambda d: d['hooks']['preToolUse'][0].update({'matcher': '['})),
    ):
        cfg = json.loads(json.dumps(base_hook))
        mut(cfg)
        hcfg.write_text(json.dumps(cfg, indent=2) + '\n')
        ok, out = check(ent2)
        expect(not ok and 'guidance.json' in out and 'preToolUse' in out,
               f'scripts/verify.py should reject {label} in .github/hooks/guidance.json: ' + out)

    for label, mut in (
        ('python -B and backslash powershell', lambda d: d['hooks']['preToolUse'][0].update({
            'bash': 'python3 -B .github/hooks/guidance_guardrail.py',
            'powershell': 'python .github\\hooks\\guidance_guardrail.py',
        })),
        ('bash only without powershell', lambda d: d['hooks']['preToolUse'][0].pop('powershell', None)),
        ('bash matcher with bash only', lambda d: (
            d['hooks']['preToolUse'][0].pop('powershell', None),
            d['hooks']['preToolUse'][0].update({'matcher': 'bash'}),
        )),
    ):
        cfg = json.loads(json.dumps(base_hook))
        mut(cfg)
        hcfg.write_text(json.dumps(cfg, indent=2) + '\n')
        ok, out = check(ent2)
        expect(ok, f'scripts/verify.py should accept {label} in .github/hooks/guidance.json: ' + out)

    hcfg.write_text(orig_hcfg)
    ok, out = check(ent2)
    expect(ok, 'scripts/verify.py failed after restoring .github/hooks/guidance.json: ' + out)


def case_exclusions_deps_rename_docs_timeouts(tmp):
    target = tmp / 'verify-features'
    target.mkdir()
    install(target, '--tier', 'enterprise')
    profile = target / 'PROJECT_PROFILE.md'
    # Replace placeholders carefully so --verify works.
    text = profile.read_text()
    for placeholder, val in (
        ('{{INSTALL_COMMAND}}', 'Not applicable: stdlib'),
        ('{{RUN_COMMAND}}', '`python3 -V`'),
        ('{{FORMAT_COMMAND}}', 'Not applicable: none'),
        ('{{STATIC_AND_CONCURRENCY_COMMANDS}}', 'Not applicable: none'),
        ('{{BUILD_COMMAND}}', 'Not applicable: interpreted'),
        ('{{TEST_COMMAND}}', '`python3 -c "import sys; assert sys.version_info[0] == 3"`'),
        ('{{UI_TEST_COMMANDS_OR_JUSTIFIED_EXCLUSION}}', 'Proposed: Not applicable: CLI only'),
        ('{{RECOVERY_TEST_COMMANDS}}', 'Not applicable: stateless'),
        ('{{QUALIFICATION_COMMANDS}}', 'Not applicable: CLI'),
        ('{{VERIFIER_COMMAND}}', '`python3 scripts/verify.py --verify development`'),
        ('{{DEPENDENCY_AUDIT_COMMAND}}', '{{DEPENDENCY_AUDIT_COMMAND}}'),
    ):
        text = text.replace(placeholder, val)
    profile.write_text(text)
    (target / 'requirements.txt').write_text('requests==2.31.0\n')
    init_git(target)

    # 1. Proposed exclusion counts as a gap; --verify release names requirements.txt without exposing its versions and skips Manual rows.
    profile.write_text(profile.read_text().replace(
        '| Guidance integrity |',
        '| Deploy review | `python3 -c "open(\'manual-ran\', \'w\').write(\'x\')"` | Manual | Staging | Manual |\n| Guidance integrity |',
    ))
    r = verify(target, 'development')
    expect(r.returncode == 2 and '1 gap: Browser / accessibility smoke' in r.stdout, 'Proposed exclusion should report gap: ' + r.stdout)
    r_rel = verify(target, 'release', '--receipt', str(tmp / 'receipt.json'))
    expect(not (target / 'manual-ran').exists() and 'Deploy review' not in r_rel.stdout,
           'release verification must not execute Manual commands:\n' + r_rel.stdout)
    expect('requirements.txt' in r_rel.stdout and '2.31.0' not in r_rel.stdout, 'release dep gap check failed: ' + r_rel.stdout)
    expect((tmp / 'receipt.json').is_file(), 'verify did not write --receipt')

    # 1b. Gate label normalization: & and 'and' run in both phases; mixed/unrecognized labels fail as incomplete without silently running/dropping.
    base_profile = profile.read_text()
    profile.write_text(base_profile.replace(
        '| Guidance integrity |',
        '| Gate and check | `python3 -c "print(1)"` | Development & Release | Dev | — |\n'
        '| Gate word and | `python3 -c "print(2)"` | Development and release | Dev | — |\n'
        '| Guidance integrity |',
    ))
    r_dev = verify(target, 'development')
    expect('passed    Gate and check' in r_dev.stdout and 'passed    Gate word and' in r_dev.stdout,
           'Development & Release / and should run in development:\n' + r_dev.stdout)
    r_rel_conj = verify(target, 'release')
    expect('passed    Gate and check' in r_rel_conj.stdout and 'passed    Gate word and' in r_rel_conj.stdout,
           'Development & Release / and should run in release:\n' + r_rel_conj.stdout)

    profile.write_text(base_profile.replace(
        '| Guidance integrity |',
        '| Mixed gate | `python3 -c "open(\'mixed-ran\', \'w\').write(\'x\')"` | Release / Manual | Staging | Manual |\n'
        '| Qualified gate | `python3 -c "print(3)"` | Release (CI only) | CI | — |\n'
        '| Guidance integrity |',
    ))
    r_bad_dev = verify(target, 'development')
    expect(r_bad_dev.returncode == 2 and 'unrecognized or mixed Gate label(s)' in r_bad_dev.stdout
           and not (target / 'mixed-ran').exists() and 'Mixed gate' in r_bad_dev.stdout and 'Qualified gate' in r_bad_dev.stdout,
           'development mode must report unrecognized/mixed Gate labels:\n' + r_bad_dev.stdout)
    r_bad_rel = verify(target, 'release')
    expect(r_bad_rel.returncode != 0 and 'unrecognized or mixed Gate label(s)' in r_bad_rel.stdout
           and not (target / 'mixed-ran').exists() and 'Mixed gate' in r_bad_rel.stdout and 'Qualified gate' in r_bad_rel.stdout,
           'Release / Manual and Release (CI only) must report a problem instead of silently skipping:\n' + r_bad_rel.stdout)

    # Atomic ungated labels (N/A, No), escaped Markdown pipes (\|), and ambiguous multi-command cells.
    profile.write_text(base_profile.replace(
        '| Guidance integrity |',
        '| Optional doc check | `python3 -c "open(\'na-ran\', \'w\').write(\'x\')"` | N/A | Dev | — |\n'
        '| Legacy opt-out | `python3 -c "open(\'no-ran\', \'w\').write(\'x\')"` | No | Dev | — |\n'
        '| Pipe check | `false \\| true` | Development | Dev | — |\n'
        '| Guidance integrity |',
    ))
    r_clean = verify(target, 'development')
    expect('passed    Pipe check' in r_clean.stdout and 'unrecognized' not in r_clean.stdout
           and not (target / 'na-ran').exists() and not (target / 'no-ran').exists(),
           'N/A, No, and escaped Markdown pipes should parse cleanly:\n' + r_clean.stdout)

    for purpose, row, token in (
        ('Mixed NA gate', '| Mixed NA gate | `python3 -c "print(4)"` | Release / N/A | Dev | — |\n', 'unrecognized or mixed Gate label(s)'),
        ('Dual cmd', '| Dual cmd | `true` and `false` | Development | Dev | — |\n', 'ambiguous Command cell(s)'),
        ('Adjacent cmds', '| Adjacent cmds | `true` `false` | Development | Dev | — |\n', '2 backticked commands'),
        ('Empty cmd', '| Empty cmd | `` | Development | Dev | — |\n', 'empty command in backticks'),
        ('Trailing op', '| Trailing op | `true` && false | Development | Dev | — |\n', 'text outside backticks in Command cell'),
    ):
        profile.write_text(base_profile.replace('| Guidance integrity |', row + '| Guidance integrity |'))
        r_row = verify(target, 'development')
        expect(r_row.returncode == 2 and token in r_row.stdout and purpose in r_row.stdout,
               f'{purpose} must fail independently as incomplete:\n' + r_row.stdout)
    # Fenced example tables (```, ````, ~~~~, 3-space indented), 4-space indented code blocks, and trailing tables
    # must never become executable gates or mask a real failing gate.
    failing_profile = (base_profile
                       .replace('`python3 -c "import sys; assert sys.version_info[0] == 3"`', '`false`')
                       .replace('Proposed: Not applicable: CLI only', 'Not applicable: CLI only'))
    fake_table = ('| Purpose | Command | Gate | Environment | Evidence |\n'
                  '|---|---|---|---|---|\n'
                  '| Fake gate | `touch fenced-ran && true` | Development | Dev | — |\n')
    for label, snippet in (
        ('3-backtick', f'```markdown\n{fake_table}```\n\n'),
        ('4-backtick', f'````markdown\n{fake_table}````\n\n'),
        ('4-tilde', f'~~~~markdown\n{fake_table}~~~~\n\n'),
        ('3-space fence', '   ```markdown\n' + '\n'.join('   ' + l for l in fake_table.splitlines()) + '\n   ```\n\n'),
        ('4-space indented', '\n'.join('    ' + l for l in fake_table.splitlines()) + '\n\n'),
    ):
        test_text = failing_profile.replace('| Purpose | Command |', snippet + '| Purpose | Command |', 1)
        if label == '4-space indented':
            test_text = test_text.replace('## Command inventory',
                                          '    ## Command inventory\n\n' + snippet + '## Command inventory', 1)
        profile.write_text(test_text + '\nNote after inventory:\n\n| Extra | Header |\n|---|---|\n| Foo | Bar |\n')
        r_fence = verify(target, 'development')
        expect(r_fence.returncode == 1 and not (target / 'fenced-ran').exists()
               and 'Fake gate' not in r_fence.stdout and 'unrecognized' not in r_fence.stdout,
               f'{label} example or trailing table leaked into inventory gates:\n' + r_fence.stdout)
        (target / 'fenced-ran').unlink(missing_ok=True)
    profile.write_text(base_profile)

    # 2. Per-gate timeout (including killing/reaping child processes spawned by timed-out shell commands)
    profile.write_text(profile.read_text()
                       .replace('| Browser / accessibility smoke | Proposed: Not applicable: CLI only | Development |',
                                '| Browser / accessibility smoke | `python3 -c "import time; time.sleep(1.2)"` | Development, timeout 5s |')
                       .replace('`python3 -c "import sys; assert sys.version_info[0] == 3"`',
                                '`python3 -c "import subprocess, sys; subprocess.Popen([sys.executable, \'-c\', \'import time; time.sleep(1.5); open(\\"timeout-leaked\\", \\"w\\").write(\\"x\\")\']).wait()"`'))
    r_to = subprocess.run([sys.executable, '-B', 'scripts/verify.py', '--verify', 'development', '--timeout', '1'],
                          cwd=target, capture_output=True, text=True)
    import time
    time.sleep(1.8)
    expect('passed    Browser / accessibility smoke' in r_to.stdout and 'timed out after 1s (the --timeout default' in r_to.stdout
           and not (target / 'timeout-leaked').exists(),
           'per-gate timeout mismatch or child process survived timeout:\n' + r_to.stdout)

    # 2b. A gate that reruns the phase it belongs to is refused instead of recursing until memory runs out.
    # The depth fuse keeps a broken guard from forking without end; it stops after three nested runs.
    timed_profile = profile.read_text()
    r_nested = verify(target, 'release')
    expect('Refused:' not in r_nested.stdout,
           'a Release gate running --verify development must still run the development phase:\n' + r_nested.stdout)
    profile.write_text(timed_profile.replace(
        '| Guidance integrity |',
        '| Self rerun | `[ "${SELF_RERUN_DEPTH:-0}" -lt 3 ] && SELF_RERUN_DEPTH=$((${SELF_RERUN_DEPTH:-0}+1)) '
        'python3 scripts/verify.py --verify development` | Development | Dev | — |\n| Guidance integrity |'))
    r_self = verify(target, 'development')
    expect(r_self.returncode == 1 and 'failed    Self rerun' in r_self.stdout
           and 'Refused: a gate command reran scripts/verify.py --verify development inside itself '
               '(development -> development)' in r_self.stdout,
           'a gate rerunning its own phase must fail once instead of recursing:\n' + r_self.stdout)
    profile.write_text(timed_profile)
    # Without a 1s --timeout, the timeout case's gate runs to completion and writes its marker file.
    (target / 'timeout-leaked').unlink(missing_ok=True)

    # 3. Documentation mode passes on a clean/doc-only repo (including Unicode .md paths), and fails on uncommitted code or .txt changes.
    r_doc = verify(target, 'docs')
    expect(r_doc.returncode == 0 and 'Change scope' not in r_doc.stdout,
           '--verify docs should pass on clean repo: ' + r_doc.stdout)
    (target / 'résumé.md').write_text('# Notes\n')
    r_uni = verify(target, 'docs')
    expect(r_uni.returncode == 0 and 'Change scope' not in r_uni.stdout,
           '--verify docs should accept Unicode .md filename résumé.md: ' + r_uni.stdout)
    (target / 'résumé.md').unlink()
    for bad_file in ('app.py', 'notes.txt'):
        (target / bad_file).write_text('x = 1\n')
        r_doc_bad = verify(target, 'docs')
        expect(r_doc_bad.returncode == 1 and 'Change scope' in r_doc_bad.stdout and bad_file in r_doc_bad.stdout,
               f'--verify docs must fail with untracked {bad_file}: ' + r_doc_bad.stdout)
        (target / bad_file).unlink()

    tgit = ['git', '-c', 'user.name=t', '-c', 'user.email=t@e', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']
    (target / 'app.py').write_text('x = 1\n')
    subprocess.run(tgit + ['add', 'app.py'], cwd=target, capture_output=True, text=True, check=True)
    subprocess.run(tgit + ['commit', '-q', '-m', 'add app.py'], cwd=target, capture_output=True, text=True, check=True)
    subprocess.run(tgit + ['mv', 'app.py', 'renamed.md'], cwd=target, capture_output=True, text=True, check=True)
    r_mv = verify(target, 'docs')
    expect(r_mv.returncode == 1 and 'Change scope' in r_mv.stdout and 'app.py' in r_mv.stdout,
           '--verify docs must fail when code file is renamed to .md: ' + r_mv.stdout)
    subprocess.run(tgit + ['rm', '-f', '-q', 'renamed.md'], cwd=target, capture_output=True, text=True, check=True)
    subprocess.run(tgit + ['commit', '-q', '-m', 'remove app'], cwd=target, capture_output=True, text=True, check=True)

    unborn = tmp / 'docs-unborn'
    unborn.mkdir()
    install(unborn, '--tier', 'prototype')
    subprocess.run(tgit + ['init', '-q', '-b', 'main'], cwd=unborn, capture_output=True, text=True, check=True)
    (unborn / 'app.py').write_text('x = 1\n')
    subprocess.run(tgit + ['add', 'app.py'], cwd=unborn, capture_output=True, text=True, check=True)
    r_ub = verify(unborn, 'docs')
    expect(r_ub.returncode == 1 and 'Change scope' in r_ub.stdout and 'app.py' in r_ub.stdout,
           '--verify docs must fail on staged code file before first commit: ' + r_ub.stdout)

    (unborn / '.git' / 'index').write_bytes(b'corrupt')
    r_brk = verify(unborn, 'docs')
    expect(r_brk.returncode == 2 and 'Verification: incomplete' in r_brk.stdout,
           '--verify docs must return incomplete (exit 2) when git diff fails: ' + r_brk.stdout)

    # 4. Missing required module check fails when all files of a required module are removed.
    (target / 'docs/UI.md').unlink() if (target / 'docs/UI.md').exists() else None
    (target / 'docs/ENTERPRISE.md').unlink()
    (target / '.github/pull_request_template.md').unlink()
    ok, out = check(target)
    expect(not ok and 'enterprise module' in out, 'missing required module should fail: ' + out)


def case_recorded_exclusions_and_walk_skips(tmp):
    target = tmp / 'exclusions'
    target.mkdir()
    install(target, '--tier', 'production')
    (target / 'docs/RUNBOOKS.md').unlink()  # linked from AGENTS.md and RELEASE_NOTES.md
    ok, out = check(target)
    expect(not ok and 'unresolved or escaping link' in out, 'removing linked file without exclusion must fail')
    profile = target / 'PROJECT_PROFILE.md'
    profile.write_text(profile.read_text().replace('{{EXCLUDED_GUIDES_OR_NONE}}', '`docs/RUNBOOKS.md` (stateless worker)'))
    ok, out = check(target)
    expect(ok and '1 packaged files absent as recorded in Excluded guidance' in out, 'recorded exclusion should pass: ' + out)
    # Git-ignored folder and nested .git worktree with broken links must be skipped.
    init_git(target)
    (target / '.gitignore').write_text('managed_components/\n')
    (target / 'managed_components/dep').mkdir(parents=True)
    (target / 'managed_components/dep/README.md').write_text('[broken](missing.md)\n')
    (target / '.claude/worktrees/w1').mkdir(parents=True)
    (target / '.claude/worktrees/w1/.git').write_text('gitdir: ..\n')
    (target / '.claude/worktrees/w1/README.md').write_text('[broken](missing.md)\n')
    ok, out = check(target)
    expect(ok, 'gitignored or nested .git broken link should be skipped: ' + out)


def case_tools_and_default_and_broken(tmp):
    empty = tmp / 'empty'
    empty.mkdir()
    r = run_manage(root, '--install', str(empty))
    expect(r.returncode != 0 and 'Choose a tier' in r.stdout + r.stderr, 'install without tier must explain tiers and exit nonzero')
    expect(not list(empty.iterdir()), 'install without tier copied files')

    dry = run_manage(root, '--install', str(empty), '--tier', 'prototype', '--dry-run')
    expect(dry.returncode == 0 and 'Nothing was written' in dry.stdout and not list(empty.iterdir()), '--dry-run wrote files')

    r_all = run_manage(root, '--install', str(empty), '--all')
    mods_all = set(json.loads((empty / '.guidance.json').read_text())['installed']['modules'])
    expect('enterprise' not in mods_all and 'ui-design' not in mods_all and 'embedded' not in mods_all
           and 'release-review' in mods_all and 'ui' in mods_all,
           f'--all modules unexpected: {sorted(mods_all)}')

    claude_only = tmp / 'claude-only'
    claude_only.mkdir()
    install(claude_only, '--tier', 'production', '--tools', 'claude')
    expect((claude_only / '.claude/skills/release-review/SKILL.md').is_file()
           and not (claude_only / '.agents').exists()
           and not (claude_only / '.codex').exists()
           and not (claude_only / '.github/hooks').exists(), '--tools claude leaked other tools')
    ok, out = check(claude_only)
    expect(ok, '--tools claude failed check: ' + out)

    copilot_only = tmp / 'copilot-only'
    copilot_only.mkdir()
    install(copilot_only, '--tier', 'production', '--tools', 'copilot')
    expect((copilot_only / '.agents/skills/release-review/SKILL.md').is_file()
           and not (copilot_only / '.claude').exists()
           and not (copilot_only / '.codex').exists(), '--tools copilot leaked other tools')
    ok, out = check(copilot_only)
    expect(ok, '--tools copilot failed check: ' + out)
    rr_agents = copilot_only / '.agents/skills/release-review/SKILL.md'
    orig_rr = rr_agents.read_text()
    stale_rr = orig_rr.replace('Read ', 'Outdated ')
    rr_agents.write_text(stale_rr)
    ok, out = check(copilot_only)
    expect(not ok and '.agents/skills/release-review/SKILL.md' in out,
           '--tools copilot should fail on stale .agents/skills wrapper: ' + out)
    rr_agents.write_text(orig_rr)
    rr_claude = copilot_only / '.claude/skills/release-review/SKILL.md'
    rr_claude.parent.mkdir(parents=True)
    rr_claude.write_text(stale_rr)
    ok, out = check(copilot_only)
    expect(not ok and '.claude/skills/release-review/SKILL.md' in out,
           '--tools copilot should fail on stale .claude/skills wrapper: ' + out)
    rr_claude.unlink()
    orphan = copilot_only / '.claude/skills/orphan/SKILL.md'
    orphan.parent.mkdir(parents=True)
    orphan.write_text(orig_rr)
    ok, out = check(copilot_only)
    expect(not ok and 'Orphaned skill wrapper .claude/skills/orphan/SKILL.md' in out,
           '--tools copilot should fail on orphaned .claude/skills wrapper: ' + out)
    orphan.unlink()
    custom = copilot_only / '.claude/skills/custom/SKILL.md'
    custom.parent.mkdir(parents=True)
    custom.write_text('---\nname: custom\ndescription: "User skill"\n---\n')
    ok, out = check(copilot_only)
    expect(ok, '--tools copilot should allow user-authored .claude/skills without marker: ' + out)

    # --sync removes orphaned .claude/skills wrappers and repairs stale existing ones without creating absent wrappers.
    rr_agents.write_text(stale_rr)
    rr_claude.write_text(stale_rr)
    orphan.write_text(orig_rr)
    sync_r = run_manage(root, '--sync', str(copilot_only))
    expect(sync_r.returncode == 0, '--tools copilot --sync failed: ' + sync_r.stdout + sync_r.stderr)
    expect(rr_agents.read_text() == orig_rr and rr_claude.read_text() == orig_rr,
           '--tools copilot --sync failed to repair stale skill wrappers')
    expect(not (copilot_only / '.claude/skills/release-readiness/SKILL.md').exists(),
           '--tools copilot --sync created absent .claude/skills/release-readiness wrapper')
    expect(not orphan.exists() and custom.is_file(),
           '--tools copilot --sync must remove orphan and keep user-authored skill')
    ok, out = check(copilot_only)
    expect(ok, '--tools copilot check failed after --sync repair: ' + out)

    # Unmanaged skill at a packaged skill path must never be overwritten by --sync and must be reported as a collision.
    custom_collision = '---\nname: release-review\ndescription: "User custom review"\n---\n'
    rr_claude.write_text(custom_collision)
    ok, out = check(copilot_only)
    expect(not ok and 'collides with a packaged skill name' in out,
           '--tools copilot check must flag unmanaged collision at .claude/skills/release-review/SKILL.md: ' + out)
    sync_col = run_manage(root, '--sync', str(copilot_only))
    expect(sync_col.returncode != 0 and 'not generated by manage.py' in (sync_col.stdout + sync_col.stderr)
           and rr_claude.read_text() == custom_collision,
           '--sync must refuse to overwrite unmanaged .claude/skills/release-review/SKILL.md: '
           + sync_col.stdout + sync_col.stderr)
    rr_claude.unlink()
    ok, out = check(copilot_only)
    expect(ok, '--tools copilot check failed after removing unmanaged collision: ' + out)

    # Unmanaged skill collision on a default install (all tools) must also fail verify.py and --sync.
    def_col = tmp / 'default-skill-collision'
    def_col.mkdir()
    install(def_col, '--tier', 'production')
    rr_def = def_col / '.agents/skills/release-review/SKILL.md'
    rr_def.write_text(custom_collision)
    ok, out = check(def_col)
    expect(not ok and 'collides with a packaged skill name' in out,
           'default install check must flag unmanaged collision at .agents/skills/release-review/SKILL.md: ' + out)
    sync_def = run_manage(root, '--sync', str(def_col))
    expect(sync_def.returncode != 0 and 'not generated by manage.py' in (sync_def.stdout + sync_def.stderr)
           and rr_def.read_text() == custom_collision,
           'default --sync must refuse to overwrite unmanaged .agents/skills/release-review/SKILL.md: '
           + sync_def.stdout + sync_def.stderr)

    # Symlink containment: --install and --sync must refuse before mutating anything outside the target.
    outside = tmp / 'symlink-outside'
    outside.mkdir()
    esc_install = tmp / 'symlink-install'
    esc_install.mkdir()
    (esc_install / '.claude').symlink_to(outside, target_is_directory=True)
    r_esc = run_manage(root, '--install', str(esc_install), '--tier', 'prototype', '--tools', 'claude')
    expect(r_esc.returncode != 0 and 'Refusing to write outside' in (r_esc.stdout + r_esc.stderr)
           and not list(outside.iterdir()) and not (esc_install / 'AGENTS.md').exists(),
           '--install must reject escaping symlink before any write: ' + r_esc.stdout + r_esc.stderr)

    esc_sync = tmp / 'symlink-sync'
    esc_sync.mkdir()
    install(esc_sync, '--tier', 'production', '--tools', 'claude')
    shutil.rmtree(esc_sync / '.claude/skills')
    (esc_sync / '.claude/skills').symlink_to(outside, target_is_directory=True)
    r_sync_esc = run_manage(root, '--sync', str(esc_sync))
    expect(r_sync_esc.returncode != 0 and 'Refusing to write outside' in (r_sync_esc.stdout + r_sync_esc.stderr)
           and not list(outside.iterdir()),
           '--sync must reject escaping symlink before any write: ' + r_sync_esc.stdout + r_sync_esc.stderr)

    # Installed projects that also happen to have MAINTAINING.md and manage.py (e.g., Django) must run project verify, never project manage.py.
    django = tmp / 'django-proj'
    django.mkdir()
    install(django, '--tier', 'prototype')
    (django / 'MAINTAINING.md').write_text('# Local maintenance notes\n')
    (django / 'manage.py').write_text('from pathlib import Path\nPath("project-manage-ran").write_text("ran")\n')
    (django / 'AGENTS.md').unlink()
    (django / 'docs/OPEN_WORK.md').write_text('[broken](missing.md)\n')
    ok, out = check(django)
    expect(not ok and not (django / 'project-manage-ran').exists() and 'FAIL (project mode)' in out,
           'scripts/verify.py mistook installed project for template repo or ran project manage.py: ' + out)
    r_dj_ver = verify(django, 'development')
    expect('unconfigured template repository' not in (r_dj_ver.stdout + r_dj_ver.stderr)
           and not (django / 'project-manage-ran').exists(),
           'scripts/verify.py --verify mistook installed project for template repo: ' + r_dj_ver.stdout + r_dj_ver.stderr)

    # Even with .guidance.json removed and a non-guidance PACKAGE_MANIFEST.json carrying "repo_only",
    # pre-commit delegates to scripts/verify.py (never mistaking it for the guidance template repo).
    init_git(django)
    (django / '.guidance.json').unlink()
    (django / 'PACKAGE_MANIFEST.json').write_text(json.dumps({'package': 'other-project', 'repo_only': []}) + '\n')
    r_hook = subprocess.run(['sh', 'scripts/hooks/pre-commit'], cwd=django, capture_output=True, text=True)
    expect(r_hook.returncode != 0 and not (django / 'project-manage-ran').exists()
           and 'FAIL (project mode)' in (r_hook.stdout + r_hook.stderr),
           'scripts/hooks/pre-commit must route non-template repo through project verify.py: '
           + r_hook.stdout + r_hook.stderr)


def case_agent_team_interop(tmp):
    if not AGENT_TEAM_BOOTSTRAP.is_file():
        print(f'SKIP: agent-team interop test ({AGENT_TEAM_BOOTSTRAP} not found; set AGENT_TEAM_BOOTSTRAP to run)')
        return False
    # Order 1: agent-guidance first, then agent-team
    p1 = tmp / 'interop-1'
    p1.mkdir()
    install(p1, '--tier', 'production')
    r1 = subprocess.run([sys.executable, str(AGENT_TEAM_BOOTSTRAP), '--project', str(p1),
                         '--platforms', 'claude', 'codex', '--roles', 'auditor-advisor', 'backend', '--with-agents-md', '--apply'],
                        capture_output=True, text=True)
    expect(r1.returncode == 0, 'agent-team bootstrap failed (order 1): ' + r1.stdout + r1.stderr)
    ok, out = check(p1)
    expect(ok, 'scripts/verify.py failed after agent-team bootstrap (order 1): ' + out)
    expect('## Model escalation' in (p1 / 'AGENTS.md').read_text(), 'agent-team did not append Model escalation to AGENTS.md')
    # Re-sync and confirm project specialist agents and appended AGENTS.md sections stay intact.
    run_manage(root, '--sync', str(p1))
    expect('## Model escalation' in (p1 / 'AGENTS.md').read_text(), '--sync DIR dropped agent-team Model escalation section')
    expect((p1 / '.claude/agents/auditor-advisor.md').is_file() and (p1 / '.codex/agents/backend.toml').is_file(),
           '--sync DIR deleted agent-team specialist agents')

    # Order 2: agent-team first, then agent-guidance
    p2 = tmp / 'interop-2'
    p2.mkdir()
    r2 = subprocess.run([sys.executable, str(AGENT_TEAM_BOOTSTRAP), '--project', str(p2),
                         '--platforms', 'claude', 'codex', '--roles', 'auditor-advisor', '--with-agents-md', '--apply'],
                        capture_output=True, text=True)
    expect(r2.returncode == 0, 'agent-team bootstrap failed (order 2): ' + r2.stdout + r2.stderr)
    install(p2, '--tier', 'production')
    expect('## Model escalation' in (p2 / 'AGENTS.md').read_text(), 'install without --force clobbered agent-team Model escalation section')
    ok, out = check(p2)
    expect(ok, 'scripts/verify.py failed after agent-guidance install (order 2): ' + out)


def case_v4_upgrade(tmp):
    pkg = tmp / 'pkg-v4'
    shutil.copytree(root, pkg, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    for stub in ('maintainer/test_install.py', 'maintainer/harness/test_score.py', 'maintainer/run_scenario.py'):
        p = pkg / stub
        if p.is_file():
            p.write_text('')
    pgit = init_git(pkg, 'v4 commit 1')
    target = tmp / 'upg-v4'
    target.mkdir()
    r = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--install', str(target), '--tier', 'internal'],
                       cwd=pkg, capture_output=True, text=True)
    expect(r.returncode == 0, 'scratch v4 install failed: ' + r.stdout + r.stderr)
    (target / 'docs/OPEN_WORK.md').write_text('| OW-1 | Open | item | — |\n')
    agents = target / 'AGENTS.md'
    agents.write_text(agents.read_text() + '\n## Team local rule\nAlways benchmark SQLite WAL.\n')
    (target / 'DESIGN_DOC.md').write_text((target / 'DESIGN_DOC.md').read_text() + '\nCustom module note.\n')
    init_git(target, 'baseline project')

    # Commit 2 in scratch package: tweak rule 7 wording and DESIGN_DOC.md, then update manifest.
    pkg_agents = pkg / 'AGENTS.md'
    pkg_agents.write_text(pkg_agents.read_text().replace('dated status sections outside release notes.',
                                                          'dated status sections outside release notes or changelogs.'))
    pkg_design = pkg / 'DESIGN_DOC.md'
    pkg_design.write_text(pkg_design.read_text() + '\n<!-- upstream section -->\n')
    um = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--update-manifest'], cwd=pkg, capture_output=True, text=True)
    expect(um.returncode == 0, 'scratch --update-manifest failed: ' + um.stdout + um.stderr)
    subprocess.run(pgit + ['add', '-A'], cwd=pkg, capture_output=True, text=True, check=True)
    subprocess.run(pgit + ['commit', '-q', '-m', 'v4 commit 2'], cwd=pkg, capture_output=True, text=True, check=True)

    patch = tmp / 'v4.patch'
    plan = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--plan-upgrade', str(target), '--patch', str(patch)],
                          cwd=pkg, capture_output=True, text=True)
    expect(plan.returncode == 0 and 'Conflict' not in plan.stdout, 'v4 plan failed: ' + plan.stdout + plan.stderr)
    expect('AGENTS.md' in plan_section(plan.stdout, 'Merge'), 'AGENTS.md should be in Merge:\n' + plan.stdout)
    expect('DESIGN_DOC.md' in plan_section(plan.stdout, 'Review'), 'customized DESIGN_DOC.md should go to Review:\n' + plan.stdout)
    applied = subprocess.run(['git', 'apply', str(patch)], cwd=target, capture_output=True, text=True)
    expect(applied.returncode == 0, 'v4 patch apply failed: ' + applied.stderr)
    chk = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--check-upgrade', str(target), '--since', 'HEAD'],
                         cwd=pkg, capture_output=True, text=True)
    expect(chk.returncode == 0 and 'nothing lost' in chk.stdout, '--check-upgrade failed cleanly: ' + chk.stdout + chk.stderr)
    # Deleting OPEN_WORK item fails --check-upgrade.
    (target / 'docs/OPEN_WORK.md').write_text('| Item | Status | Summary | Blocker |\n|---|---|---|---|\n')
    chk_bad = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--check-upgrade', str(target), '--since', 'HEAD'],
                             cwd=pkg, capture_output=True, text=True)
    expect(chk_bad.returncode != 0 and 'Open items no longer in any document: OW-1' in chk_bad.stdout,
           '--check-upgrade missed deleted OW-1: ' + chk_bad.stdout)

    # Custom AGENTS.md without generated markers stays valid across same-rev and upstream --plan-upgrade + --sync.
    custom = tmp / 'upg-custom-agents'
    custom.mkdir()
    (custom / 'AGENTS.md').write_text('# Custom Agents\n\nProject-owned rules without generated tables.\n')
    rc = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--install', str(custom), '--tier', 'production'],
                        cwd=pkg, capture_output=True, text=True)
    expect(rc.returncode == 0, 'custom AGENTS.md v4 install failed: ' + rc.stdout + rc.stderr)
    expect(json.loads((custom / '.guidance.json').read_text())['agents_blocks'] == {},
           'custom AGENTS.md should record empty agents_blocks')
    ok, cout = check(custom)
    expect(ok, 'custom AGENTS.md initial check failed: ' + cout)
    init_git(custom, 'custom agents baseline')

    cp1 = tmp / 'custom-same.patch'
    p1 = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--plan-upgrade', str(custom), '--patch', str(cp1)],
                        cwd=pkg, capture_output=True, text=True)
    expect(p1.returncode == 0, 'same-rev custom AGENTS.md plan failed: ' + p1.stdout + p1.stderr)
    if cp1.read_text().strip():
        ap1 = subprocess.run(['git', 'apply', str(cp1)], cwd=custom, capture_output=True, text=True)
        expect(ap1.returncode == 0, 'same-rev custom AGENTS.md apply failed: ' + ap1.stderr)
    ok, cout = check(custom)
    expect(ok and json.loads((custom / '.guidance.json').read_text())['agents_blocks'] == {},
           'same-rev --plan-upgrade broke custom AGENTS.md: ' + cout)

    pkg_runbooks = pkg / 'docs' / 'RUNBOOKS.md'
    pkg_runbooks.write_text(pkg_runbooks.read_text() + '\n<!-- upstream runbook note -->\n')
    um3 = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--update-manifest'], cwd=pkg, capture_output=True, text=True)
    expect(um3.returncode == 0, 'scratch v4 commit 3 --update-manifest failed: ' + um3.stdout + um3.stderr)
    subprocess.run(pgit + ['add', '-A'], cwd=pkg, capture_output=True, text=True, check=True)
    subprocess.run(pgit + ['commit', '-q', '-m', 'v4 commit 3'], cwd=pkg, capture_output=True, text=True, check=True)
    cp2 = tmp / 'custom-next.patch'
    p2 = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--plan-upgrade', str(custom), '--patch', str(cp2)],
                        cwd=pkg, capture_output=True, text=True)
    expect(p2.returncode == 0 and 'docs/RUNBOOKS.md' in plan_section(p2.stdout, 'Replace'),
           'next-rev custom AGENTS.md plan failed: ' + p2.stdout + p2.stderr)
    ap2 = subprocess.run(['git', 'apply', str(cp2)], cwd=custom, capture_output=True, text=True)
    expect(ap2.returncode == 0, 'next-rev custom AGENTS.md apply failed: ' + ap2.stderr)
    rsync = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--sync', str(custom)],
                           cwd=pkg, capture_output=True, text=True)
    expect(rsync.returncode == 0, 'custom AGENTS.md --sync failed: ' + rsync.stdout + rsync.stderr)
    ok, cout = check(custom)
    expect(ok and '# Custom Agents' in (custom / 'AGENTS.md').read_text(),
           'custom AGENTS.md check or content failed after upgrade + sync: ' + cout)

    # Deletion-only local rules (inline word deletion and whole-line deletion) must be caught by --check-upgrade.
    del_target = tmp / 'upg-del'
    del_target.mkdir()
    r_del = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--install', str(del_target), '--tier', 'internal'],
                           cwd=pkg, capture_output=True, text=True)
    expect(r_del.returncode == 0, 'deletion-rule v4 install failed: ' + r_del.stdout + r_del.stderr)
    del_agents = del_target / 'AGENTS.md'
    orig_del_text = del_agents.read_text()
    inline_orig = 'bulk-reformat uncommitted changes you did not make.'
    inline_strengthened = 'bulk-reformat changes you did not make.'
    rule_line = '4. **Reuse what exists.** Inspect existing code, tests, conventions, and real commands first. Never invent routes, flags, fields, or commands.\n'
    expect(inline_orig in orig_del_text and rule_line in orig_del_text,
           'expected baseline rules missing from AGENTS.md in deletion test')
    del_agents.write_text(orig_del_text.replace(inline_orig, inline_strengthened).replace(rule_line, ''))
    init_git(del_target, 'baseline with deletion-only local rules')

    kept_del = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--check-upgrade', str(del_target), '--since', 'HEAD'],
                              cwd=pkg, capture_output=True, text=True)
    expect(kept_del.returncode == 0 and 'nothing lost' in kept_del.stdout,
           '--check-upgrade should pass when deletion-only local rules stay deleted: ' + kept_del.stdout + kept_del.stderr)

    del_agents.write_text(orig_del_text.replace(rule_line, ''))
    reinstated_inline = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--check-upgrade', str(del_target), '--since', 'HEAD'],
                                       cwd=pkg, capture_output=True, text=True)
    expect(reinstated_inline.returncode != 0 and 'local change(s) not found verbatim' in reinstated_inline.stdout,
           '--check-upgrade missed reinstated inline-deleted word ("uncommitted"): '
           + reinstated_inline.stdout + reinstated_inline.stderr)

    del_agents.write_text(orig_del_text.replace(inline_orig, inline_strengthened))
    reinstated_line = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--check-upgrade', str(del_target), '--since', 'HEAD'],
                                     cwd=pkg, capture_output=True, text=True)
    expect(reinstated_line.returncode != 0 and 'local deletion reinstated' in reinstated_line.stdout,
           '--check-upgrade missed reinstated whole deleted line: ' + reinstated_line.stdout + reinstated_line.stderr)


def case_v3_to_v4_upgrade(tmp):
    v3_repo = tmp / 'v3-src'
    v3_repo.mkdir()
    archive = subprocess.run(['git', '-C', str(root), 'archive', '3.0.2'], capture_output=True)
    if archive.returncode != 0:
        problems.append('git archive 3.0.2 failed (tag 3.0.2 required): ' + archive.stderr.decode())
        return
    subprocess.run(['tar', '-x', '-C', str(v3_repo)], input=archive.stdout, check=True)
    target = tmp / 'v3-proj'
    target.mkdir()
    r = subprocess.run([sys.executable, '-B', str(v3_repo / 'check_package.py'), '--install', str(target), '--tier', 'internal'],
                       cwd=v3_repo, capture_output=True, text=True)
    expect(r.returncode == 0, '3.0.2 install failed: ' + r.stdout + r.stderr)
    sha_302 = subprocess.run(['git', '-C', str(root), 'rev-parse', '3.0.2'], capture_output=True, text=True, check=True).stdout.strip()
    rec = json.loads((target / 'PACKAGE_MANIFEST.json').read_text())
    rec['installed_from'] = {'repository': 'https://example.invalid/repo', 'commit': sha_302, 'dirty': False, 'date': '2026-11-06'}
    (target / 'PACKAGE_MANIFEST.json').write_text(json.dumps(rec, indent=2) + '\n')
    spec = target / 'docs/TESTING_SPEC.md'
    spec.write_text(spec.read_text() + '\n- Local project rule: always run chaos fuzzing.\n'
                    '- Owners may not deploy without verification.\n')
    (target / 'docs/OPEN_WORK.md').write_text('# Open work\n\n| ID | Status | Summary | Blocker |\n|---|---|---|---|\n| OW-7 | Open | Ship telemetry | — |\n')
    (target / 'package.json').write_text(json.dumps({'scripts': {'test': 'python3 check_package.py'}}, indent=2) + '\n')
    init_git(target, 'baseline 3.0.2')

    legacy_block = run_manage(root, '--install', str(target), '--tier', 'internal')
    expect(legacy_block.returncode != 0 and 'legacy PACKAGE_MANIFEST.json install' in (legacy_block.stdout + legacy_block.stderr)
           and not (target / '.guidance.json').exists(),
           '--install without --force must refuse legacy PACKAGE_MANIFEST.json layout: '
           + legacy_block.stdout + legacy_block.stderr)

    patch = tmp / 'v3-to-v4.patch'
    plan = run_manage(root, '--plan-upgrade', str(target), '--patch', str(patch))
    expect(plan.returncode == 0, 'v3->v4 --plan-upgrade failed: ' + plan.stdout + plan.stderr)
    out = plan.stdout
    expect('README.md' in plan_section(out, 'Replace') and 'README.md' not in plan_section(out, 'Remove'),
           'untouched v3 README.md must be replaced by stub, not removed:\n' + out)
    expect('docs/DOCUMENTATION.md' in plan_section(out, 'Remove'), 'untouched retired DOCUMENTATION.md should be in Remove:\n' + out)
    expect('PACKAGE_MANIFEST.json' in plan_section(out, 'Remove'), 'PACKAGE_MANIFEST.json should be in Remove:\n' + out)
    expect('check_package.py' in plan_section(out, 'Remove'), 'untouched check_package.py should be in Remove:\n' + out)
    expect('docs/TESTING_SPEC.md' in plan_section(out, 'Review'), 'modified retired TESTING_SPEC.md must go to Review:\n' + out)
    expect('scripts/verify.py' in plan_section(out, 'Add') and '.guidance.json' in plan_section(out, 'Add'),
           'scripts/verify.py and .guidance.json must be in Add:\n' + out)

    applied = subprocess.run(['git', 'apply', str(patch)], cwd=target, capture_output=True, text=True)
    expect(applied.returncode == 0, 'v3->v4 git apply failed: ' + applied.stderr)
    expect((target / '.guidance.json').is_file() and not (target / 'PACKAGE_MANIFEST.json').exists(), '.guidance.json did not replace PACKAGE_MANIFEST.json')
    expect((target / 'scripts/verify.py').is_file() and os.access(target / 'scripts/verify.py', os.X_OK)
           and not (target / 'check_package.py').exists(), 'scripts/verify.py did not replace check_package.py with +x')
    expect((target / 'README.md').is_file() and (target / 'README.md').read_text().startswith('# v3-proj\n'),
           'README.md stub missing after v3->v4 upgrade')
    expect('always run chaos fuzzing' in (target / 'docs/TESTING_SPEC.md').read_text(), 'edited TESTING_SPEC.md was lost by patch')
    # Complete review by folding the local rules into AGENTS.md and removing retired TESTING_SPEC.md.
    agents_file = target / 'AGENTS.md'
    agents_file.write_text(agents_file.read_text() + '\n- Local project rule: always run chaos fuzzing.\n'
                           '- Owners may not deploy without verification.\n')
    (target / 'docs/TESTING_SPEC.md').unlink()
    ok, cout = check(target)
    expect(ok, 'scripts/verify.py failed after v3->v4 review fold:\n' + cout)
    chk_pkg = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_pkg.returncode != 0 and 'check_package.py was deleted but package.json still names it' in chk_pkg.stdout,
           '--check-upgrade missed broken check_package.py reference in package.json: ' + chk_pkg.stdout + chk_pkg.stderr)
    (target / 'package.json').write_text(json.dumps({'scripts': {'test': 'python3 scripts/verify.py'}}, indent=2) + '\n')
    chk = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk.returncode == 0 and 'nothing lost' in chk.stdout, 'v3->v4 --check-upgrade failed: ' + chk.stdout + chk.stderr)
    # Dropping a short prohibition ("not") or the folded local rule from AGENTS.md must fail --check-upgrade, and conflict markers must fail too.
    clean_agents = agents_file.read_text()
    agents_file.write_text(clean_agents.replace('may not deploy', 'may deploy'))
    chk_not = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_not.returncode != 0 and 'local change(s) not found verbatim' in chk_not.stdout,
           'v3->v4 --check-upgrade missed dropped short prohibition ("not"): ' + chk_not.stdout + chk_not.stderr)
    agents_file.write_text(clean_agents.replace('\n- Local project rule: always run chaos fuzzing.\n', '\n'))
    chk_drop = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_drop.returncode != 0 and 'local change(s) not found verbatim' in chk_drop.stdout,
           'v3->v4 --check-upgrade missed dropped folded local rule: ' + chk_drop.stdout + chk_drop.stderr)
    agents_file.write_text(clean_agents + '\n<<<<<<< HEAD\nleft\n=======\nright\n>>>>>>> branch\n')
    chk_conflict = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_conflict.returncode != 0 and 'unresolved merge conflict markers' in chk_conflict.stdout,
           'v3->v4 --check-upgrade must fail on unresolved conflict markers: ' + chk_conflict.stdout + chk_conflict.stderr)
    agents_file.write_text(clean_agents)

    # Untouched 3.0.2 --tier enterprise PROJECT_PROFILE.md (with installer-inserted profile_rows) must replace cleanly.
    ent_target = tmp / 'v3-ent'
    ent_target.mkdir()
    r_ent = subprocess.run([sys.executable, '-B', str(v3_repo / 'check_package.py'), '--install', str(ent_target), '--tier', 'enterprise'],
                           cwd=v3_repo, capture_output=True, text=True)
    expect(r_ent.returncode == 0, '3.0.2 enterprise install failed: ' + r_ent.stdout + r_ent.stderr)
    ent_rec = json.loads((ent_target / 'PACKAGE_MANIFEST.json').read_text())
    ent_rec['installed_from'] = {'repository': 'https://example.invalid/repo', 'commit': sha_302, 'dirty': False, 'date': '2026-11-06'}
    (ent_target / 'PACKAGE_MANIFEST.json').write_text(json.dumps(ent_rec, indent=2) + '\n')
    init_git(ent_target, 'baseline 3.0.2 enterprise')
    ent_patch = tmp / 'v3-ent-to-v4.patch'
    ent_plan = run_manage(root, '--plan-upgrade', str(ent_target), '--patch', str(ent_patch))
    expect(ent_plan.returncode == 0, 'v3 enterprise -> v4 --plan-upgrade failed: ' + ent_plan.stdout + ent_plan.stderr)
    expect('PROJECT_PROFILE.md' in plan_section(ent_plan.stdout, 'Replace')
           and 'PROJECT_PROFILE.md' not in plan_section(ent_plan.stdout, 'Review'),
           'untouched v3 enterprise PROJECT_PROFILE.md must be replaced, not reviewed:\n' + ent_plan.stdout)
    ent_applied = subprocess.run(['git', 'apply', str(ent_patch)], cwd=ent_target, capture_output=True, text=True)
    expect(ent_applied.returncode == 0, 'v3 enterprise -> v4 git apply failed: ' + ent_applied.stderr)
    ent_sync = run_manage(root, '--sync', str(ent_target))
    expect(ent_sync.returncode == 0, 'v3 enterprise -> v4 --sync failed: ' + ent_sync.stdout + ent_sync.stderr)
    ok, eout = check(ent_target)
    expect(ok, 'scripts/verify.py failed after untouched v3 enterprise -> v4 upgrade:\n' + eout)
    ent_chk = run_manage(root, '--check-upgrade', str(ent_target), '--since', 'HEAD')
    expect(ent_chk.returncode == 0 and 'nothing lost' in ent_chk.stdout,
           'v3 enterprise -> v4 --check-upgrade failed: ' + ent_chk.stdout + ent_chk.stderr)

    # Filled v3 PROJECT_PROFILE.md linking to a retired doc warns during --plan-upgrade and fails --check-upgrade until updated.
    filled = tmp / 'v3-filled'
    filled.mkdir()
    r_fill = subprocess.run([sys.executable, '-B', str(v3_repo / 'check_package.py'), '--install', str(filled), '--tier', 'production'],
                            cwd=v3_repo, capture_output=True, text=True)
    expect(r_fill.returncode == 0, '3.0.2 production install failed: ' + r_fill.stdout + r_fill.stderr)
    fill_rec = json.loads((filled / 'PACKAGE_MANIFEST.json').read_text())
    fill_rec['installed_from'] = {'repository': 'https://example.invalid/repo', 'commit': sha_302, 'dirty': False, 'date': '2026-11-06'}
    (filled / 'PACKAGE_MANIFEST.json').write_text(json.dumps(fill_rec, indent=2) + '\n')
    fill_prof = filled / 'PROJECT_PROFILE.md'
    fill_prof.write_text(fill_prof.read_text() + '\nSee [Domain rules](docs/DOMAIN_RULES.md).\n')
    init_git(filled, 'filled 3.0.2 production')
    fill_patch = tmp / 'v3-filled-to-v4.patch'
    fill_plan = run_manage(root, '--plan-upgrade', str(filled), '--patch', str(fill_patch))
    expect(fill_plan.returncode == 0 and 'Note: PROJECT_PROFILE.md links to removed file(s):' in fill_plan.stdout
           and 'docs/DOMAIN_RULES.md' in fill_plan.stdout,
           '--plan-upgrade must warn when review/kept PROJECT_PROFILE.md links to removed docs/DOMAIN_RULES.md:\n' + fill_plan.stdout)
    fill_applied = subprocess.run(['git', 'apply', str(fill_patch)], cwd=filled, capture_output=True, text=True)
    expect(fill_applied.returncode == 0, 'v3 filled -> v4 git apply failed: ' + fill_applied.stderr)
    fill_chk_bad = run_manage(root, '--check-upgrade', str(filled), '--since', 'HEAD')
    expect(fill_chk_bad.returncode != 0
           and 'docs/DOMAIN_RULES.md was deleted but PROJECT_PROFILE.md still links to it' in fill_chk_bad.stdout,
           '--check-upgrade missed broken .md link to removed docs/DOMAIN_RULES.md:\n' + fill_chk_bad.stdout)

    # Resolving retired links in a kept/upgraded .md file restores clean --check-upgrade.
    readme_orig = (target / 'README.md').read_text()
    (target / 'README.md').write_text(readme_orig + '\nSee [Spec](docs/TESTING_SPEC.md).\n')
    chk_link_bad = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_link_bad.returncode != 0
           and 'docs/TESTING_SPEC.md was deleted but README.md still links to it' in chk_link_bad.stdout,
           '--check-upgrade missed broken .md link in README.md:\n' + chk_link_bad.stdout)
    (target / 'README.md').write_text(readme_orig)
    chk_link_ok = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_link_ok.returncode == 0 and 'nothing lost' in chk_link_ok.stdout,
           '--check-upgrade failed after removing broken link from README.md:\n' + chk_link_ok.stdout)

    # Merged AGENTS.md in 3.0.2 production upgrade must scan post-merge text for removed-file links.
    pm = tmp / 'v3-prod-merge'
    pm.mkdir()
    r_pm = subprocess.run([sys.executable, '-B', str(v3_repo / 'check_package.py'), '--install', str(pm), '--tier', 'production'],
                          cwd=v3_repo, capture_output=True, text=True)
    expect(r_pm.returncode == 0, '3.0.2 production merge install failed: ' + r_pm.stdout + r_pm.stderr)
    pm_rec = json.loads((pm / 'PACKAGE_MANIFEST.json').read_text())
    pm_rec['installed_from'] = {'repository': 'https://example.invalid/repo', 'commit': sha_302, 'dirty': False, 'date': '2026-11-06'}
    (pm / 'PACKAGE_MANIFEST.json').write_text(json.dumps(pm_rec, indent=2) + '\n')
    pm_agents = pm / 'AGENTS.md'
    pm_base_agents = pm_agents.read_text() + '\n## Local team section\nKeep handlers pure.\n'
    pm_agents.write_text(pm_base_agents)
    init_git(pm, 'baseline 3.0.2 production with AGENTS.md edit')
    pm_plan = run_manage(root, '--plan-upgrade', str(pm))
    expect(pm_plan.returncode == 0 and 'AGENTS.md' in plan_section(pm_plan.stdout, 'Merge')
           and 'Note: AGENTS.md links to removed file(s):' not in pm_plan.stdout,
           '--plan-upgrade must not warn on retired upstream AGENTS.md links replaced during clean merge:\n' + pm_plan.stdout)
    pm_agents.write_text(pm_base_agents + '\nSee [Domain rules](docs/DOMAIN_RULES.md).\n')
    pm_plan2 = run_manage(root, '--plan-upgrade', str(pm))
    expect(pm_plan2.returncode == 0
           and 'Note: AGENTS.md links to removed file(s): docs/DOMAIN_RULES.md' in pm_plan2.stdout,
           '--plan-upgrade must warn when local merged AGENTS.md section links to a removed file:\n' + pm_plan2.stdout)

    # Quoted UTF-8 filenames (café.md) must not escape --check-upgrade open-item and deployed-revision checks.
    uni = tmp / 'upg-unicode'
    uni.mkdir()
    install(uni, '--tier', 'internal')
    cafe = uni / 'café.md'
    cafe.write_text('# Notes\n\n| ID | Status | Summary | Blocker |\n|---|---|---|---|\n| OW-73 | Open | Check quotes | — |\n\nDeployed revision `abc1234`.\n')
    init_git(uni, 'baseline with café.md')
    cafe.write_text('# Notes\n')
    chk_uni = run_manage(root, '--check-upgrade', str(uni), '--since', 'HEAD')
    expect(chk_uni.returncode != 0 and 'OW-73' in chk_uni.stdout and 'abc1234' in chk_uni.stdout,
           '--check-upgrade missed removed items in quoted UTF-8 filename café.md: '
           + chk_uni.stdout + chk_uni.stderr)


def case_v2_to_v4_upgrade(tmp):
    v2_repo = tmp / 'v2-src'
    v2_repo.mkdir()
    archive = subprocess.run(['git', '-C', str(root), 'archive', '2.0'], capture_output=True)
    if archive.returncode != 0:
        problems.append('git archive 2.0 failed (tag 2.0 required): ' + archive.stderr.decode())
        return
    subprocess.run(['tar', '-x', '-C', str(v2_repo)], input=archive.stdout, check=True)
    target = tmp / 'v2-proj'
    target.mkdir()
    r = subprocess.run([sys.executable, '-B', str(v2_repo / 'check_package.py'), '--install', str(target)],
                       cwd=v2_repo, capture_output=True, text=True)
    expect(r.returncode == 0, '2.0 install failed: ' + r.stdout + r.stderr)
    sha_20 = subprocess.run(['git', '-C', str(root), 'rev-parse', '2.0'], capture_output=True, text=True, check=True).stdout.strip()
    rec = json.loads((target / 'PACKAGE_MANIFEST.json').read_text())
    rec['installed_from'] = {'repository': 'https://example.invalid/repo', 'commit': sha_20, 'dirty': False, 'date': '2026-10-29'}
    (target / 'PACKAGE_MANIFEST.json').write_text(json.dumps(rec, indent=2) + '\n')
    (target / 'README.md').write_text('# v2 custom app\n')
    spec = target / 'docs/TESTING_SPEC.md'
    spec.write_text(spec.read_text() + '\n- Local v2 rule: keep WAL checkpoints small.\n')
    (target / 'docs/OPEN_WORK.md').write_text('# Open work\n\n| ID | Status | Summary | Blocker |\n|---|---|---|---|\n| OW-9 | Open | Keep audit trail | — |\n')
    init_git(target, 'baseline 2.0')

    patch = tmp / 'v2-to-v4.patch'
    plan = run_manage(root, '--plan-upgrade', str(target), '--patch', str(patch))
    expect(plan.returncode == 0, 'v2->v4 --plan-upgrade failed: ' + plan.stdout + plan.stderr)
    out = plan.stdout
    expect('AGENTS.md' in plan_section(out, 'Replace'), 'v2->v4 must keep and replace AGENTS.md:\n' + out)
    expect('README.md' in plan_section(out, 'Review') and 'README.md' not in plan_section(out, 'Remove'),
           'modified v2 README.md must go to Review, never Remove:\n' + out)
    expect('scripts/verify.py' in plan_section(out, 'Add') and '.guidance.json' in plan_section(out, 'Add'),
           'v2->v4 must add scripts/verify.py and .guidance.json:\n' + out)

    applied = subprocess.run(['git', 'apply', str(patch)], cwd=target, capture_output=True, text=True)
    expect(applied.returncode == 0, 'v2->v4 git apply failed: ' + applied.stderr)
    mods = json.loads((target / '.guidance.json').read_text())['installed']['modules']
    expect('core' in mods and 'release' in mods and 'enterprise' not in mods and 'embedded' not in mods
           and not (target / 'profiles/EMBEDDED_FIRMWARE.md').exists(),
           f'v2->v4 modules unexpected: {mods}')
    expect('# v2 custom app' in (target / 'README.md').read_text(), 'v2->v4 lost customized README.md')
    agents_file = target / 'AGENTS.md'
    agents_file.write_text(agents_file.read_text() + '\n- Local v2 rule: keep WAL checkpoints small.\n')
    (target / 'docs/TESTING_SPEC.md').unlink()
    ok, cout = check(target)
    expect(ok, 'scripts/verify.py failed after v2->v4 review fold:\n' + cout)
    chk = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk.returncode == 0 and 'nothing lost' in chk.stdout, 'v2->v4 --check-upgrade failed: ' + chk.stdout + chk.stderr)


def case_reinstall_dry_run_and_refresh(tmp):
    target = tmp / 'reinstall'
    target.mkdir()
    install(target, '--tier', 'prototype')
    agents = target / 'AGENTS.md'
    agents.write_text(agents.read_text() + '\n## Custom team rule\nKeep handlers pure.\n')

    # Customize one guardrail file; leave the remaining guardrails, AGENTS.md, PROJECT_PROFILE.md, and .guidance.json unmodified.
    claude_cfg = target / '.claude/settings.json'
    custom_claude = claude_cfg.read_text() + '\n'
    claude_cfg.write_text(custom_claude)
    before_guidance = (target / '.guidance.json').read_text()
    before_agents = agents.read_text()
    before_profile = (target / 'PROJECT_PROFILE.md').read_text()
    before_codex = (target / '.codex/rules/guidance.rules').read_text()

    dry = run_manage(root, '--install', str(target), '--tier', 'enterprise', '--dry-run')
    expect(dry.returncode == 0 and 'Nothing was written' in dry.stdout, '--dry-run upgrade failed: ' + dry.stdout + dry.stderr)
    expect((target / '.guidance.json').read_text() == before_guidance and agents.read_text() == before_agents
           and (target / 'PROJECT_PROFILE.md').read_text() == before_profile
           and (target / '.codex/rules/guidance.rules').read_text() == before_codex
           and not (target / 'docs/ENTERPRISE.md').exists(), '--dry-run modified project files')

    dry_refresh = plan_section(dry.stdout, 'Would refresh')
    dry_copy = plan_section(dry.stdout, 'Would copy')
    for path in ('AGENTS.md', 'PROJECT_PROFILE.md', '.guidance.json', '.codex/rules/guidance.rules', '.github/hooks/guidance_guardrail.py'):
        expect(path in dry_refresh, f'--dry-run should list {path} under Would refresh:\n{dry.stdout}')
    expect('.claude/settings.json' not in dry_refresh, f'--dry-run should keep customized .claude/settings.json skipped:\n{dry.stdout}')
    expect('docs/ENTERPRISE.md' in dry_copy, f'--dry-run should list docs/ENTERPRISE.md under Would copy:\n{dry.stdout}')

    live = install(target, '--tier', 'enterprise')
    live_refresh = plan_section(live.stdout, 'Refreshed')
    live_skipped = plan_section(live.stdout, 'Skipped existing files')
    for path in ('AGENTS.md', 'PROJECT_PROFILE.md', '.guidance.json', '.codex/rules/guidance.rules', '.github/hooks/guidance_guardrail.py'):
        expect(path in live_refresh and path not in live_skipped,
               f'reinstall should report {path} under Refreshed rather than Skipped:\n{live.stdout}')
    expect('.claude/settings.json' in live_skipped and claude_cfg.read_text() == custom_claude,
           f'reinstall should skip and preserve customized .claude/settings.json:\n{live.stdout}')
    expect('## Custom team rule\nKeep handlers pure.' in agents.read_text()
           and 'docs/ENTERPRISE' in agents.read_text(), 'reinstall dropped custom section or failed to refresh AGENTS.md table')
    expect('## Release qualification profile' in (target / 'PROJECT_PROFILE.md').read_text()
           and '| Dependency audit |' in (target / 'PROJECT_PROFILE.md').read_text(),
           'reinstall failed to refresh PROJECT_PROFILE.md')

    # Reinstalling with unchanged tier/modules/tools refreshes .guidance.json agents_blocks when AGENTS.md routing updates.
    pkg = tmp / 'pkg-reinstall'
    shutil.copytree(root, pkg, ignore=shutil.ignore_patterns('.git', '__pycache__'))
    same_tier = tmp / 'same-tier'
    same_tier.mkdir()
    r0 = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--install', str(same_tier), '--tier', 'prototype'],
                        cwd=pkg, capture_output=True, text=True)
    expect(r0.returncode == 0, 'scratch prototype install failed: ' + r0.stdout + r0.stderr)
    before_meta = json.loads((same_tier / '.guidance.json').read_text())
    before_meta['installed_from'] = {'repository': 'https://example.invalid/repo.git', 'commit': 'deadbeef', 'dirty': False, 'date': '2026-11-22'}
    (same_tier / '.guidance.json').write_text(json.dumps(before_meta, indent=2) + '\n')
    pkg_manifest = json.loads((pkg / 'PACKAGE_MANIFEST.json').read_text())
    pkg_manifest['agents_tables']['routing'].append({'module': 'core', 'row': '| Extra rule | a | b |'})
    (pkg / 'PACKAGE_MANIFEST.json').write_text(json.dumps(pkg_manifest, indent=2) + '\n')

    same_dry = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--install', str(same_tier), '--tier', 'prototype', '--dry-run'],
                              cwd=pkg, capture_output=True, text=True)
    expect(same_dry.returncode == 0 and 'Nothing was written' in same_dry.stdout,
           'same-tier --dry-run failed: ' + same_dry.stdout + same_dry.stderr)
    same_dry_refresh = plan_section(same_dry.stdout, 'Would refresh')
    expect('AGENTS.md' in same_dry_refresh and '.guidance.json' in same_dry_refresh,
           'same-tier --dry-run should list AGENTS.md and .guidance.json under Would refresh:\n' + same_dry.stdout)
    expect(json.loads((same_tier / '.guidance.json').read_text()) == before_meta, 'same-tier --dry-run modified .guidance.json')

    same_live = subprocess.run([sys.executable, '-B', str(pkg / 'manage.py'), '--install', str(same_tier), '--tier', 'prototype'],
                               cwd=pkg, capture_output=True, text=True)
    expect(same_live.returncode == 0, 'same-tier live reinstall failed: ' + same_live.stdout + same_live.stderr)
    same_live_refresh = plan_section(same_live.stdout, 'Refreshed')
    expect('AGENTS.md' in same_live_refresh and '.guidance.json' in same_live_refresh,
           'same-tier reinstall should list AGENTS.md and .guidance.json under Refreshed:\n' + same_live.stdout)
    after_meta = json.loads((same_tier / '.guidance.json').read_text())
    expect(after_meta['installed_from'] == before_meta['installed_from'],
           'same-tier reinstall overwrote installed_from provenance')
    ok, out = check(same_tier)
    expect(ok, 'scripts/verify.py failed after same-tier AGENTS.md refresh: ' + out)

    # Re-running --install from a different checkout commit must refuse before mixing files and hashes.
    cross = tmp / 'cross-commit'
    cross.mkdir()
    install(cross, '--tier', 'prototype')
    cross_meta = json.loads((cross / '.guidance.json').read_text())
    cross_meta['installed_from']['commit'] = '0000000000000000000000000000000000000000'
    (cross / '.guidance.json').write_text(json.dumps(cross_meta, indent=2) + '\n')
    r_cross = run_manage(root, '--install', str(cross), '--features', 'ui')
    expect(r_cross.returncode != 0 and '--plan-upgrade' in (r_cross.stdout + r_cross.stderr)
           and '--force' not in (r_cross.stdout + r_cross.stderr)
           and not (cross / 'docs/UI.md').exists(),
           'cross-commit --install must refuse and point only to --plan-upgrade: ' + r_cross.stdout + r_cross.stderr)

    # Reinstalling with a lower tier refuses cleanly without overwriting installed tier metadata; broken .guidance.json exits without traceback.
    r_down = run_manage(root, '--install', str(target), '--tier', 'prototype')
    expect(r_down.returncode != 0 and "cannot downgrade to 'prototype'" in (r_down.stdout + r_down.stderr)
           and json.loads((target / '.guidance.json').read_text())['installed']['tier'] == 'enterprise',
           'tier downgrade via --install must be refused without altering .guidance.json: ' + r_down.stdout + r_down.stderr)

    broken = tmp / 'broken-guidance-json'
    broken.mkdir()
    install(broken, '--tier', 'prototype')
    (broken / '.guidance.json').write_text('{broken\n')
    for cmd_args in (('--install', str(broken), '--tier', 'prototype'), ('--plan-upgrade', str(broken)), ('--sync', str(broken))):
        r_brk = run_manage(root, *cmd_args)
        msg_brk = r_brk.stdout + r_brk.stderr
        expect(r_brk.returncode != 0 and 'is not valid JSON' in msg_brk and 'Traceback' not in msg_brk,
               f'{cmd_args[0]} must report invalid .guidance.json without traceback: ' + msg_brk)


def case_neutrality_and_sync_constants():
    forbidden = re.compile(r'(?i)\b(?:antigravity|agent-team|xhigh|read_file|view_file|auditor-advisor|'
                           r'hardware-auditor|mechanical-auditor|ux-designer|frontend-tester|FreeCADCmd)\b'
                           r'|tools/kicad|fabrication_export\.py')
    for entry in manifest['files']:
        path = entry['path']
        if not path.endswith('.md') or path == 'CLAUDE.md' or path.startswith(('.claude/', '.codex/', '.github/', '.agents/')):
            continue
        text = (root / path).read_text()
        if path == 'AGENTS.md':
            text = re.sub(r'^Tool files \([^)]*\).*$', '', text, flags=re.M)
        m = forbidden.search(text)
        expect(m is None, f'{path}: neutrality leak ({m.group(0)})' if m else '')
    manage_src = (root / 'manage.py').read_text()
    verify_src = (root / 'scripts' / 'verify.py').read_text()
    marker_line = next(l for l in manage_src.splitlines() if l.startswith('SKILL_MARKER = '))
    expect(marker_line in verify_src, 'scripts/verify.py SKILL_MARKER drifted from manage.py')


def table():
    sizes = {e['path']: e.get('bytes', 0) for e in manifest['files']}
    print('| Tier | Modules | Files | KB | Agent-facing prose KB | AGENTS.md bytes |')
    print('|---|---|---|---|---|---|')
    tooling = ('scripts/', '.claude/', '.codex/', '.github/', '.agents/', 'CLAUDE.md')
    with tempfile.TemporaryDirectory() as tmp:
        for tier, mods in manifest['tiers'].items():
            d = Path(tmp) / tier
            d.mkdir()
            install(d, '--tier', tier)
            files = [p for p, m in module_of.items() if m in mods]
            prose = [p for p in files if p.endswith('.md') and not p.startswith(tooling) and p not in tooling]
            ag_bytes = (d / 'AGENTS.md').stat().st_size
            print(f"| {tier} | {', '.join(mods)} | {len(files)} | {sum(sizes.get(p, 0) for p in files) / 1024:.0f} | "
                  f"{sum(sizes.get(p, 0) for p in prose) / 1024:.0f} | {ag_bytes} |")
    print('\nFeatures add: ' + '; '.join(f"{f}: {', '.join(p for p, m in module_of.items() if m in mods)}"
                                       for f, mods in manifest['features'].items()))


def main():
    if '--table' in sys.argv:
        table()
        return
    skipped = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for case in (
            case_tiers,
            case_policy,
            case_selective_skills_and_sync,
            case_generated_tables_and_enterprise,
            case_guardrails,
            case_exclusions_deps_rename_docs_timeouts,
            case_recorded_exclusions_and_walk_skips,
            case_tools_and_default_and_broken,
            case_agent_team_interop,
            case_v4_upgrade,
            case_v3_to_v4_upgrade,
            case_v2_to_v4_upgrade,
            case_reinstall_dry_run_and_refresh,
        ):
            if case(tmp) is False:
                skipped.append(case.__name__)
    case_neutrality_and_sync_constants()
    if problems:
        print('\n'.join(problems))
        sys.exit(1)
    suffix = f" ({len(skipped)} skipped: {', '.join(skipped)})" if skipped else ''
    print('Install tests OK: tiers, design policy, selective skills & sync, generated tables & enterprise rows, guardrails, '
          'exclusions/deps/timeouts/docs mode, walk skips, tools & defaults, agent-team interop, v4/v3/v2 upgrades, and neutrality.'
          + suffix)


if __name__ == '__main__':
    main()
