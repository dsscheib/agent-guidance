#!/usr/bin/env python3
"""Build guidance-scenario fixtures for agent testing (repository-only).

  run_scenario.py S2 /path/to/new-dir   build one scenario and print its prompt
  run_scenario.py S2 DIR --no-install   build it without the package, for a no-guidance baseline
  run_scenario.py --list                list scenarios
  run_scenario.py --write-table         regenerate the catalog in SCENARIOS.md
  run_scenario.py --check               build every scenario in a temporary directory and check the catalog
  run_scenario.py --scenarios FILE ...  use another scenario set (fixtures in a fixtures/ folder beside FILE),
                                        such as a private holdout set; --check then skips the catalog
"""
from pathlib import Path
import argparse, json, os, re, shutil, subprocess, sys, tempfile

here = Path(__file__).resolve().parent
root = here.parent
scenarios_path = here / 'scenarios.json'
fixtures_dir = here / 'fixtures'
catalog_path = here / 'SCENARIOS.md'
BEGIN, END = '<!-- scenarios:begin -->', '<!-- scenarios:end -->'
PLACEHOLDER = re.compile(r'\{\{([^}:]+)(:[^}]*)?\}\}')
# Git hooks export GIT_DIR and friends; scrub them so fixture repos never touch this repository.
ENV = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
ENV.update(PYTHONDONTWRITEBYTECODE='1', GIT_AUTHOR_NAME='Scenario Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
           GIT_COMMITTER_NAME='Scenario Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')


def load():
    return json.loads(scenarios_path.read_text())['scenarios']


def fixture(name):
    return json.loads((fixtures_dir / name / 'fixture.json').read_text())


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True)


def apply(target, spec):
    for path, content in spec.get('files', {}).items():
        (target / path).parent.mkdir(parents=True, exist_ok=True)
        (target / path).write_text(content)
    for patch in spec.get('patches', []):
        path = target / patch['path']
        text = path.read_text()
        if text.count(patch['old']) != 1:
            raise SystemExit(f"Patch for {patch['path']} must match exactly once: {patch['old']!r}")
        path.write_text(text.replace(patch['old'], patch['new']))


def fill_profile(target, values, strict=True):
    """Fill fixture values into PROJECT_PROFILE.md and, when installed, docs/ENTERPRISE.md.

    An earlier release's template lacks some placeholders, so strict=False skips values it has no place for."""
    used = set()

    def replace(match):
        key = match.group(1).strip()
        if key in values:
            used.add(key)
            return values[key]
        return match.group(0)

    for path in (target / 'PROJECT_PROFILE.md', target / 'docs' / 'ENTERPRISE.md'):
        if path.is_file():
            path.write_text(PLACEHOLDER.sub(replace, path.read_text()))
    unknown = values.keys() - used
    if unknown and strict:
        raise SystemExit('Fixture profile keys match no PROJECT_PROFILE.md or ENTERPRISE.md placeholder: ' + ', '.join(sorted(unknown)))


def build(scenario, target):
    """Install the package, layer fixtures, commit, then add uncommitted state. Returns a list of problems."""
    target = Path(target).resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f'Target must be empty or absent: {target}')
    target.mkdir(parents=True, exist_ok=True)
    install = scenario.get('install', True)
    # SCENARIO_OLD_GUIDANCE installs an earlier release into every scenario, for an old-guidance comparison.
    ref = scenario.get('install_ref') or os.environ.get('SCENARIO_OLD_GUIDANCE')
    if install and ref:
        # An earlier release, as a project that adopted it would have it: a shared clone at that commit runs its own installer.
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / 'guidance'
            # A harness snapshot has no history; the harness names the repository that has it.
            history = os.environ.get('SCENARIO_HISTORY_REPO') or str(root)
            for cmd, cwd in ((['git', 'clone', '-q', '--shared', history, str(old)], root),
                             (['git', '-c', 'advice.detachedHead=false', 'checkout', '-q', ref], old)):
                result = run(cmd, cwd)
                if result.returncode:
                    raise SystemExit(f"{' '.join(cmd)} failed: {result.stderr}")
            result = run([sys.executable, str(old / 'check_package.py'), '--install', str(target)], old)
            if result.returncode:
                raise SystemExit(result.stdout + result.stderr)
    elif install:
        # A scenario without a tier keeps the 2.x set its fixtures were written against.
        tier = ['--tier', scenario['tier']] if scenario.get('tier') else ['--all']
        tier += ['--features', ','.join(scenario['features'])] if scenario.get('features') else []
        result = run([sys.executable, str(root / 'check_package.py'), '--install', str(target), *tier], root)
        if result.returncode:
            raise SystemExit(result.stdout + result.stderr)
    values = {}
    for name in scenario['fixtures']:
        values.update(fixture(name).get('profile', {}))
        files = fixtures_dir / name / 'files'
        for src in sorted(files.rglob('*')) if files.is_dir() else []:
            if src.is_file():
                dest = target / src.relative_to(files)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
    if install and not scenario.get('install_ref'):  # an earlier adoption's profile is the project's own filled-in file
        fill_profile(target, values, strict=not ref)
    apply(target, scenario.get('setup', {}))
    git = ['git', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null']
    for cmd in (git + ['init', '-q', '-b', 'main'], git + ['add', '-A'], git + ['commit', '-q', '-m', f"Scenario {scenario['id']} fixture"]):
        result = run(cmd, target)
        if result.returncode:
            raise SystemExit(f"{' '.join(cmd)} failed: {result.stderr}")
    if scenario.get('remote'):
        # A local bare repository as origin, inside .git so it is never part of the work tree.
        origin = target / '.git' / 'scenario-origin.git'
        for cmd in (git + ['init', '-q', '--bare', '-b', 'main', str(origin)], git + ['remote', 'add', 'origin', str(origin)],
                    git + ['push', '-q', '-u', 'origin', 'main']):
            result = run(cmd, target)
            if result.returncode:
                raise SystemExit(f"{' '.join(cmd)} failed: {result.stderr}")
    apply(target, scenario.get('dirty', {}))

    problems = []
    configured = scenario.get('configured', True)
    if not install:
        stray = [p for p in ('check_package.py', 'PACKAGE_MANIFEST.json', 'PROJECT_PROFILE.md') if (target / p).exists()]
        if stray:
            problems.append('uninstalled fixture contains package files: ' + ', '.join(stray))
    elif configured is not None:
        required = run([sys.executable, 'check_package.py', '--require', 'code'], target)
        if configured != (required.returncode == 0):
            problems.append(f"profile should be {'configured' if configured else 'unconfigured'}: {required.stdout.strip().splitlines()[-1]}")
    if scenario.get('tests'):
        tests = run([sys.executable, '-m', 'unittest', '-q'], target)
        outcome = 'pass' if tests.returncode == 0 else 'fail'
        if outcome != scenario['tests']:
            problems.append(f"tests should {scenario['tests']} but {outcome}ed: {tests.stderr.strip().splitlines()[-1:]}")
    return problems


def prompt(scenario):
    """The prompt with {guidance} replaced by this checkout's path."""
    return scenario['prompt'].replace('{guidance}', str(root))


def followups(scenario):
    """Later prompts for a longitudinal scenario, pasted one at a time into the same session."""
    return [f.replace('{guidance}', str(root)) for f in scenario.get('followups', [])]


def cell(text):
    return text.replace('|', '\\|').replace('\n', ' ')


def table():
    scenarios = load()
    names = sorted(p.name for p in fixtures_dir.iterdir() if (p / 'fixture.json').is_file())
    lines = ['| Fixture | Contents |', '|---|---|']
    lines += [f"| `{n}` | {cell(fixture(n)['description'])} |" for n in names]
    lines += ['', '| # | Fixtures | Prompt | Expected | Must not |', '|---|---|---|---|---|']
    for s in scenarios:
        state = ', '.join(f'`{f}`' for f in s['fixtures']) or 'Fresh install, unconfigured'
        if not s.get('install', True):
            state += ' (package not installed)'
        extras = [label for key, label in (('setup', 'setup patch'), ('dirty', 'uncommitted changes')) if key in s]
        if extras:
            state += ' + ' + ', '.join(extras)
        asked = ' → '.join(f'"{p}"' for p in [s['prompt']] + s.get('followups', []))
        lines.append(f"| {s['id']} | {state} | {cell(asked)} | {cell('; '.join(s['expected']))} | {cell('; '.join(s['must_not']))} |")
    return '\n'.join(lines)


def catalog_text():
    text = catalog_path.read_text()
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    return text, start, end


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('scenario', nargs='?')
    parser.add_argument('target', nargs='?')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--write-table', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--no-install', action='store_true', help='build without the package (no-guidance baseline)')
    parser.add_argument('--scenarios', type=Path, help='scenario file of another set; its fixtures are in fixtures/ beside it')
    args = parser.parse_args()
    global scenarios_path, fixtures_dir
    if args.scenarios:
        scenarios_path = args.scenarios.resolve()
        fixtures_dir = scenarios_path.parent / 'fixtures'
        if args.write_table:
            parser.error('--write-table regenerates the catalog of this repository\'s scenarios only')
    scenarios = {s['id']: s for s in load()}

    if args.list:
        for s in scenarios.values():
            print(f"{s['id']:>4}  {prompt(s)}")
        return
    if args.write_table:
        text, start, end = catalog_text()
        catalog_path.write_text(text[:start] + '\n' + table() + '\n' + text[end:])
        print('Wrote scenario catalog to ' + catalog_path.relative_to(root).as_posix())
        return
    if args.check:
        problems = []
        text, start, end = catalog_text()
        if not args.scenarios and text[start:end].strip() != table():
            problems.append('SCENARIOS.md catalog is stale; run maintainer/run_scenario.py --write-table')
        for s in scenarios.values():
            with tempfile.TemporaryDirectory() as tmp:
                try:
                    problems += [f"{s['id']}: {p}" for p in build(s, Path(tmp) / s['id'])]
                except SystemExit as error:
                    problems.append(f"{s['id']}: {error}")
        if problems:
            print('\n'.join(problems))
            sys.exit(1)
        print(f'Scenarios OK: {len(scenarios)} fixtures build with the expected profile and test state.')
        return
    if not (args.scenario and args.target) or args.scenario not in scenarios:
        parser.error('give a scenario ID (see --list) and a new or empty target directory')

    s = scenarios[args.scenario]
    if args.no_install:
        s = {**s, 'install': False, 'configured': None}
    problems = build(s, args.target)
    if problems:
        sys.exit('Fixture does not match its definition:\n' + '\n'.join(problems))
    target = Path(args.target).resolve()
    print(f"Built {s['id']} in {target}\n")
    print('Open that directory in the agent under test, start a fresh session and paste this prompt verbatim:\n')
    print('    ' + prompt(s) + '\n')
    later = followups(s)
    if later:
        print('Then, in the same session, paste each follow-up after the agent finishes the previous step:\n')
        print(''.join(f'    {n}. {f}\n' for n, f in enumerate(later, 2)))
        print('At the end, also measure the fixture: line counts of PROJECT_PROFILE.md and docs/OPEN_WORK.md, new files under docs/ '
              'and scripts/, and `git log` (every review deployment must match a commit).\n')
    print('Expected:\n' + ''.join(f'  - {e}\n' for e in s['expected']))
    print('Must not:\n' + ''.join(f'  - {m}\n' for m in s['must_not']))
    print('Record the result in maintainer/RESULTS.md:')
    commit = run(['git', 'rev-parse', '--short', 'HEAD'], root).stdout.strip() or '<commit>'
    print(f"| <date> | {s['id']} | <agent> | <version> | {commit} | <run #> | pass / fail | <notes> |")


if __name__ == '__main__':
    main()
