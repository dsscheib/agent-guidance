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
    expect(not ok and 'AGENTS.md routing table' in out,
           'scripts/verify.py should fail when generated routing block is deleted: ' + out)

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
    # Break enterprise guardrail and verify scripts/verify.py rejects it.
    (ent / '.claude/settings.json').write_text('{"permissions": {"ask": [], "deny": []}}\n')
    ok, out = check(ent)
    expect(not ok and 'merge a pull request' in out, 'scripts/verify.py should fail when enterprise guardrail is removed')


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

    # 2. Per-gate timeout
    profile.write_text(profile.read_text()
                       .replace('| Browser / accessibility smoke | Proposed: Not applicable: CLI only | Development |',
                                '| Browser / accessibility smoke | `python3 -c "import time; time.sleep(1.2)"` | Development, timeout 5s |')
                       .replace('`python3 -c "import sys; assert sys.version_info[0] == 3"`',
                                '`python3 -c "import time; time.sleep(1.5)"`'))
    r_to = subprocess.run([sys.executable, '-B', 'scripts/verify.py', '--verify', 'development', '--timeout', '1'],
                          cwd=target, capture_output=True, text=True)
    expect('passed    Browser / accessibility smoke' in r_to.stdout and 'timed out after 1s (the --timeout default' in r_to.stdout,
           'per-gate timeout mismatch:\n' + r_to.stdout)

    # 3. Documentation mode passes on a clean/doc-only repo, and fails on uncommitted code changes.
    r_doc = verify(target, 'docs')
    expect(r_doc.returncode == 0 and 'Change scope' not in r_doc.stdout,
           '--verify docs should pass on clean repo: ' + r_doc.stdout)
    (target / 'app.py').write_text('x = 1\n')
    r_doc_code = verify(target, 'docs')
    expect(r_doc_code.returncode == 1 and 'Change scope' in r_doc_code.stdout,
           '--verify docs must fail with untracked app.py: ' + r_doc_code.stdout)
    (target / 'app.py').unlink()

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
    expect('enterprise' not in mods_all and 'ui-design' not in mods_all and 'release-review' in mods_all and 'ui' in mods_all,
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
    rr_agents.write_text('stale\n')
    ok, out = check(copilot_only)
    expect(not ok and '.agents/skills/release-review/SKILL.md' in out,
           '--tools copilot should fail on stale .agents/skills wrapper: ' + out)
    rr_agents.write_text(orig_rr)
    rr_claude = copilot_only / '.claude/skills/release-review/SKILL.md'
    rr_claude.parent.mkdir(parents=True)
    rr_claude.write_text('stale\n')
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


def case_agent_team_interop(tmp):
    if not AGENT_TEAM_BOOTSTRAP.is_file():
        print(f'SKIP: agent-team interop test ({AGENT_TEAM_BOOTSTRAP} not found; set AGENT_TEAM_BOOTSTRAP to run)')
        return
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
    spec.write_text(spec.read_text() + '\n- Local project rule: always run chaos fuzzing.\n')
    (target / 'docs/OPEN_WORK.md').write_text('# Open work\n\n| ID | Status | Summary | Blocker |\n|---|---|---|---|\n| OW-7 | Open | Ship telemetry | — |\n')
    init_git(target, 'baseline 3.0.2')

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
    expect((target / 'scripts/verify.py').is_file() and not (target / 'check_package.py').exists(), 'scripts/verify.py did not replace check_package.py')
    expect((target / 'README.md').is_file() and (target / 'README.md').read_text().startswith('# v3-proj\n'),
           'README.md stub missing after v3->v4 upgrade')
    expect('always run chaos fuzzing' in (target / 'docs/TESTING_SPEC.md').read_text(), 'edited TESTING_SPEC.md was lost by patch')
    # Complete review by folding the local rule into AGENTS.md and removing retired TESTING_SPEC.md.
    agents_file = target / 'AGENTS.md'
    agents_file.write_text(agents_file.read_text() + '\n- Local project rule: always run chaos fuzzing.\n')
    (target / 'docs/TESTING_SPEC.md').unlink()
    ok, cout = check(target)
    expect(ok, 'scripts/verify.py failed after v3->v4 review fold:\n' + cout)
    chk = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk.returncode == 0 and 'nothing lost' in chk.stdout, 'v3->v4 --check-upgrade failed: ' + chk.stdout + chk.stderr)
    # Dropping the folded local rule from AGENTS.md must fail --check-upgrade.
    agents_file.write_text(agents_file.read_text().replace('\n- Local project rule: always run chaos fuzzing.\n', ''))
    chk_drop = run_manage(root, '--check-upgrade', str(target), '--since', 'HEAD')
    expect(chk_drop.returncode != 0 and 'local change(s) not found verbatim' in chk_drop.stdout,
           'v3->v4 --check-upgrade missed dropped folded local rule: ' + chk_drop.stdout + chk_drop.stderr)


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
    expect('core' in mods and 'release' in mods and 'enterprise' not in mods, f'v2->v4 modules unexpected: {mods}')
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
            case(tmp)
    case_neutrality_and_sync_constants()
    if problems:
        print('\n'.join(problems))
        sys.exit(1)
    print('Install tests OK: tiers, design policy, selective skills & sync, generated tables & enterprise rows, guardrails, '
          'exclusions/deps/timeouts/docs mode, walk skips, tools & defaults, agent-team interop, v4/v3/v2 upgrades, and neutrality.')


if __name__ == '__main__':
    main()
