#!/usr/bin/env python3
"""Grade sheets and the pre-registered analysis for the private holdout set (repository-only).

  holdout_analysis.py template BLIND_DIR --scenarios SCENARIOS.json > sheet.json
  holdout_analysis.py check SHEET.json --blind BLIND_DIR --scenarios SCENARIOS.json
  holdout_analysis.py analyze --scenarios SCENARIOS.json --key KEY.json --grades SETTLED.json
        --condition none=REGEX --condition candidate=REGEX [--condition old=REGEX]
        --candidate candidate --baseline none --seed N [--resamples 10000]
        [--exclude H5,...] [--calibration ID,...] [--caution ID,...]
        [--original G1.json --original G2.json ...] [--scorer SCORER.json] [--json OUT.json]

Nothing about the holdout is written here: criterion IDs, kinds and categories come from the catalog at run time.

`template` writes an empty grade sheet for the blinded runs blind.py wrote: one entry per run ID, with every criterion of
its scenario (read from the `Scenario:` line of run.md) set to null. Graders fill each with "pass", "fail" or "blocked",
and the `grader` block with their name, "human" or "model", and a model's family. It needs no key, so graders never see
one. `check` reports missing, unknown and invalid grades in a sheet.

Sheet format, for each grader, the settled grades and an automatic scorer alike:
  {"grader": {"name": "...", "kind": "human|model", "family": "..."},
   "runs": {"B001": {"H1.1": "pass", "H1.2": "blocked", ...}, ...},
   "notes": {"B001": "optional free text"}}

`analyze` follows the protocol's Grading and Analysis sections:
- Run outcome: pass if every criterion passes, blocked if none fails and one or more are blocked, otherwise fail.
- Configuration: the key's agent_cli (CLI and model). Condition: the one --condition regex that matches the run's
  label; a run matching none or several is an error. A run in a condition named "none" that had guidance installed is
  an error too.
- Primary, per configuration: runs passed with the candidate and the baseline, out of the runs that exist (a partial
  configuration is reported with its real counts, never filled in), blocked runs beside them, and the difference in
  pass rate with a paired 95% percentile interval from a bootstrap over whole scenarios: each resample draws scenarios
  with replacement from those with runs in both conditions and takes both conditions' runs of each drawn scenario.
  Each configuration's resampling uses random.Random(f"{seed}/{configuration}"), so dropping one configuration leaves
  the others' intervals unchanged. Blocked runs count as not passed. Scenarios given with --exclude (found broken after
  the first run) are left out of the primary figure and shown separately.
- Secondary: criterion pass rates per category, the --calibration and --caution criteria on their own, and blocked
  runs per configuration.
- Agreement: for each pair of --original sheets, and for --scorer against the settled grades, the share of criteria
  and of run outcomes graded the same, and Cohen's kappa on criteria.
- CLI versions: the key's cli_version for each condition of each configuration. A configuration whose candidate and
  baseline runs used different versions, or more than one, is marked "mixed CLI version" beside the primary figure,
  which is computed as usual: the comparison is confounded with the version change.
A difference whose interval includes zero is marked "no claim".
"""
import argparse
import itertools
import json
import random
import re
import sys
from pathlib import Path

GRADES = ('pass', 'fail', 'blocked')
SCENARIO_LINE = re.compile(r'^Scenario: (\S+)\s*$', re.M)


def load_rubric(path):
    """{scenario ID: [(criterion ID, kind, category), ...]} from the catalog."""
    data = json.loads(Path(path).read_text())
    scenarios = data if isinstance(data, list) else data.get('scenarios', [])
    rubric = {}
    for s in scenarios:
        crits = [(c['id'], c['kind'], c['category']) for c in s.get('rubric') or []]
        if not crits:
            sys.exit(f'{s["id"]} has no rubric')
        rubric[s['id']] = crits
    return rubric


def blind_scenarios(blind):
    """{run ID: scenario ID} from blind.py's run.md files."""
    runs = {}
    for p in sorted(Path(blind).glob('B*/run.md')):
        m = SCENARIO_LINE.search(p.read_text())
        if not m:
            sys.exit(f'{p} has no Scenario line')
        runs[p.parent.name] = m.group(1)
    if not runs:
        sys.exit(f'no B*/run.md in {blind}')
    return runs


def problems(sheet, run_scenarios, rubric):
    """Every missing, unknown or invalid grade in a sheet, as text."""
    out, runs = [], sheet.get('runs') or {}
    g = sheet.get('grader') or {}
    if not g.get('name') or g.get('kind') not in ('human', 'model') or (g.get('kind') == 'model' and not g.get('family')):
        out.append('grader block needs a name, kind "human" or "model", and a family for a model')
    for bid in sorted(set(runs) - set(run_scenarios)):
        out.append(f'{bid}: not a run in this set')
    for bid, sid in sorted(run_scenarios.items()):
        if sid not in rubric:
            out.append(f'{bid}: scenario {sid} is not in the catalog')
            continue
        given = runs.get(bid) or {}
        ids = [c for c, _, _ in rubric[sid]]
        for cid in ids:
            if given.get(cid) not in GRADES:
                out.append(f'{bid} {cid}: {"missing" if given.get(cid) is None else repr(given[cid])}')
        for cid in sorted(set(given) - set(ids)):
            out.append(f'{bid} {cid}: not a criterion of {sid}')
    return out


def outcome(grades):
    vals = list(grades.values())
    if 'fail' in vals:
        return 'fail'
    return 'blocked' if 'blocked' in vals else 'pass'


def load_sheet(path, run_scenarios, rubric):
    sheet = json.loads(Path(path).read_text())
    bad = problems(sheet, run_scenarios, rubric)
    if bad:
        sys.exit(f'{path}: {len(bad)} problem(s)\n  ' + '\n  '.join(bad[:40]))
    return sheet


def rate(passed, n):
    return passed / n if n else float('nan')


def pct(x):
    return 'n/a' if x != x else f'{100 * x:.1f}%'


def bootstrap(cand, base, resamples, rng):
    """Paired percentile interval for cand rate - base rate; cand/base map scenario -> (passed, runs)."""
    paired = sorted(set(cand) & set(base))
    if not paired:
        return None
    diffs = []
    for _ in range(resamples):
        draw = [rng.choice(paired) for _ in paired]
        cp, cn = sum(cand[s][0] for s in draw), sum(cand[s][1] for s in draw)
        bp, bn = sum(base[s][0] for s in draw), sum(base[s][1] for s in draw)
        diffs.append(cp / cn - bp / bn)
    diffs.sort()
    lo, hi = diffs[int(0.025 * resamples)], diffs[min(resamples - 1, int(0.975 * resamples))]
    return lo, hi, paired


def kappa(a, b):
    """Cohen's kappa for two equal-length label lists."""
    n = len(a)
    if not n:
        return float('nan')
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(k) / n) * (b.count(k) / n) for k in GRADES)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def agreement(s1, s2, run_scenarios, rubric):
    a, b, same_runs = [], [], 0
    for bid, sid in run_scenarios.items():
        g1, g2 = s1['runs'][bid], s2['runs'][bid]
        for cid, _, _ in rubric[sid]:
            a.append(g1[cid])
            b.append(g2[cid])
        same_runs += outcome(g1) == outcome(g2)
    same = sum(x == y for x, y in zip(a, b))
    return {'criteria_same': same, 'criteria': len(a), 'runs_same': same_runs, 'runs': len(run_scenarios),
            'kappa': kappa(a, b)}


def analyze(a):
    rubric = load_rubric(a.scenarios)
    key = json.loads(Path(a.key).read_text())
    runs = {r['id']: r for r in key['runs']}
    run_scenarios = {bid: r['scenario'] for bid, r in runs.items()}
    settled = load_sheet(a.grades, run_scenarios, rubric)
    conds = []
    for spec in a.condition:
        name, _, rx = spec.partition('=')
        if not rx:
            sys.exit(f'--condition {spec}: expected NAME=REGEX')
        conds.append((name, re.compile(rx)))
    names = [n for n, _ in conds]
    for n in (a.candidate, a.baseline):
        if n not in names:
            sys.exit(f'condition {n} is not defined with --condition')
    exclude = set(filter(None, (a.exclude or '').split(',')))
    for sid in exclude:
        if sid not in rubric:
            sys.exit(f'--exclude {sid}: not in the catalog')
    all_ids = {c for crits in rubric.values() for c, _, _ in crits}
    calibration = [c for c in (a.calibration or '').split(',') if c]
    caution = [c for c in (a.caution or '').split(',') if c]
    for c in calibration + caution:
        if c not in all_ids:
            sys.exit(f'{c}: not a criterion in the catalog')
    kind_of = {c: (k, cat) for crits in rubric.values() for c, k, cat in crits}

    rows = []  # (config, condition, scenario, run, outcome, grades, cli version)
    for bid, r in sorted(runs.items()):
        hit = [n for n, rx in conds if rx.search(r['label'])]
        if len(hit) != 1:
            sys.exit(f'{bid} (label {r["label"]}): matches {len(hit)} conditions; each run must match exactly one')
        if hit[0] == 'none' and r.get('installed'):
            sys.exit(f'{bid} (label {r["label"]}) is in condition "none" but had guidance installed')
        g = settled['runs'][bid]
        rows.append((r.get('agent_cli') or r['label'], hit[0], r['scenario'], r['run'], outcome(g), g, r.get('cli_version')))
    configs = sorted({r[0] for r in rows})

    res = {'seed': a.seed, 'resamples': a.resamples, 'candidate': a.candidate, 'baseline': a.baseline,
           'excluded_scenarios': sorted(exclude), 'grader': settled.get('grader'), 'configurations': {}}
    out = [f'# Holdout analysis', '',
           f'Candidate `{a.candidate}` against baseline `{a.baseline}`. Bootstrap: {a.resamples} resamples over whole '
           f'scenarios, seed {a.seed}, random.Random(f"{{seed}}/{{configuration}}"). Blocked runs count as not passed.'
           + (f' Excluded from the primary figure: {", ".join(sorted(exclude))}.' if exclude else ''), '',
           '## Primary', '',
           '| Configuration | Candidate passed | Blocked | Baseline passed | Blocked | Difference | 95% interval | Claim |',
           '|---|---|---|---|---|---|---|---|']
    for cfg in configs:
        c_rows = [r for r in rows if r[0] == cfg]
        entry = {}
        per = {}
        for cond in (a.candidate, a.baseline):
            sel = [r for r in c_rows if r[1] == cond and r[2] not in exclude]
            by_s = {}
            for r in sel:
                p, n = by_s.get(r[2], (0, 0))
                by_s[r[2]] = (p + (r[4] == 'pass'), n + 1)
            per[cond] = by_s
            entry[cond] = {'passed': sum(r[4] == 'pass' for r in sel), 'blocked': sum(r[4] == 'blocked' for r in sel),
                           'failed': sum(r[4] == 'fail' for r in sel), 'runs': len(sel),
                           'scenarios': len(by_s), 'expected_runs_if_complete': 3 * len(set(rubric) - exclude)}
        ce, be = entry[a.candidate], entry[a.baseline]
        diff = rate(ce['passed'], ce['runs']) - rate(be['passed'], be['runs'])
        bs = bootstrap(per[a.candidate], per[a.baseline], a.resamples, random.Random(f'{a.seed}/{cfg}'))
        if bs:
            lo, hi, paired = bs
            claim = 'no claim' if lo <= 0 <= hi else ('candidate higher' if lo > 0 else 'candidate lower')
            entry['difference'] = {'point': diff, 'low': lo, 'high': hi, 'paired_scenarios': paired, 'claim': claim}
            iv = f'{100 * lo:+.1f} to {100 * hi:+.1f} pts'
        else:
            claim, iv = 'no paired scenarios', 'n/a'
            entry['difference'] = {'point': diff, 'claim': claim}
        partial = any(e['runs'] < e['expected_runs_if_complete'] for e in (ce, be))
        entry['partial'] = partial
        versions = {cond: sorted({str(r[6]) for r in c_rows if r[1] == cond}) for cond in names}
        entry['cli_versions'] = versions
        mixed = len(set(versions[a.candidate]) | set(versions[a.baseline])) > 1
        entry['mixed_cli_version'] = mixed
        marks = [m for m, on in (('partial', partial), ('mixed CLI version', mixed)) if on]
        out.append(f'| {cfg}{" (" + ", ".join(marks) + ")" if marks else ""} | {ce["passed"]}/{ce["runs"]} | {ce["blocked"]} | '
                   f'{be["passed"]}/{be["runs"]} | {be["blocked"]} | '
                   f'{"n/a" if diff != diff else f"{100 * diff:+.1f} pts"} | {iv} | {claim} |')
        if exclude:
            entry['excluded'] = {cond: [{'scenario': r[2], 'run': r[3], 'outcome': r[4]} for r in c_rows
                                        if r[1] == cond and r[2] in exclude] for cond in names}
        res['configurations'][cfg] = entry

    out += ['', '## CLI versions', '', '| Configuration | ' + ' | '.join(names) + ' |', '|---|' + '---|' * len(names)]
    for cfg in configs:
        v = res['configurations'][cfg]['cli_versions']
        out.append(f'| {cfg} | ' + ' | '.join(', '.join(v[n]) or '-' for n in names) + ' |')
    out += ['', '## Run outcomes by condition', '', '| Configuration | Condition | Passed | Blocked | Failed | Runs |',
            '|---|---|---|---|---|---|']
    for cfg in configs:
        for cond in names:
            sel = [r for r in rows if r[0] == cfg and r[1] == cond and r[2] not in exclude]
            if sel:
                k = [r[4] for r in sel]
                out.append(f'| {cfg} | {cond} | {k.count("pass")} | {k.count("blocked")} | {k.count("fail")} | {len(k)} |')

    def crit_table(title, pick, key_name):
        lines = ['', f'## {title}', '', '| Configuration | Condition | ' + key_name + ' | Pass | Blocked | Fail | Pass rate |',
                 '|---|---|---|---|---|---|---|']
        table = {}
        for cfg in configs:
            for cond in names:
                sel = [r for r in rows if r[0] == cfg and r[1] == cond and r[2] not in exclude]
                groups = {}
                for r in sel:
                    for cid, g in r[5].items():
                        k = pick(cid)
                        if k is not None:
                            groups.setdefault(k, []).append(g)
                for k, gs in sorted(groups.items()):
                    t = {g: gs.count(g) for g in GRADES}
                    table.setdefault(cfg, {}).setdefault(cond, {})[k] = t
                    lines.append(f'| {cfg} | {cond} | {k} | {t["pass"]} | {t["blocked"]} | {t["fail"]} | '
                                 f'{pct(rate(t["pass"], len(gs)))} |')
        return lines, table

    lines, res['categories'] = crit_table('Secondary: criteria by category', lambda c: kind_of[c][1], 'Category')
    out += lines
    if calibration or caution:
        group = {c: 'calibration' for c in calibration} | {c: 'caution' for c in caution}
        lines, res['calibration_caution'] = crit_table(
            'Secondary: calibration against caution criteria', lambda c: group.get(c), 'Group')
        out += lines
        out.append(f'\nCalibration: {", ".join(calibration) or "none given"}. Caution: {", ".join(caution) or "none given"}.')

    if exclude:
        out += ['', '## Excluded scenarios (not in the primary figure)', '', '| Configuration | Condition | Scenario | Run | Outcome |',
                '|---|---|---|---|---|']
        for r in sorted(r for r in rows if r[2] in exclude):
            out.append(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |')

    sheets = [(p, load_sheet(p, run_scenarios, rubric)) for p in a.original or []]
    if sheets or a.scorer:
        out += ['', '## Agreement', '', '| Between | Criteria same | Run outcomes same | Kappa (criteria) |', '|---|---|---|---|']
        res['agreement'] = []
        pairs = [((p1, s1), (p2, s2)) for (p1, s1), (p2, s2) in itertools.combinations(sheets, 2)]
        if a.scorer:
            pairs.append(((a.scorer, load_sheet(a.scorer, run_scenarios, rubric)), (a.grades, settled)))
        for (p1, s1), (p2, s2) in pairs:
            ag = agreement(s1, s2, run_scenarios, rubric)
            n1, n2 = (s1['grader']['name'], s2['grader']['name'])
            res['agreement'].append({'a': n1, 'b': n2, **ag})
            out.append(f'| {n1} / {n2} | {ag["criteria_same"]}/{ag["criteria"]} | {ag["runs_same"]}/{ag["runs"]} | '
                       f'{ag["kappa"]:.3f} |')
        res['graders'] = [s['grader'] for _, s in sheets]
        out += ['', 'Graders: ' + '; '.join(
            f'{g["name"]} ({g["kind"]}{", " + g["family"] if g.get("family") else ""})' for g in res['graders'])]

    out += ['', 'No claim is made from a difference whose interval includes zero, and none about model or vendor rankings.']
    print('\n'.join(out))
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, default=list) + '\n')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('template')
    t.add_argument('blind')
    t.add_argument('--scenarios', required=True)
    c = sub.add_parser('check')
    c.add_argument('sheet')
    c.add_argument('--blind', required=True)
    c.add_argument('--scenarios', required=True)
    n = sub.add_parser('analyze')
    n.add_argument('--scenarios', required=True)
    n.add_argument('--key', required=True)
    n.add_argument('--grades', required=True, help='the settled grade sheet')
    n.add_argument('--condition', action='append', required=True, help='NAME=REGEX on the run label')
    n.add_argument('--candidate', required=True)
    n.add_argument('--baseline', required=True)
    n.add_argument('--seed', type=int, required=True)
    n.add_argument('--resamples', type=int, default=10_000)
    n.add_argument('--exclude', help='comma-separated scenario IDs found broken after the first run')
    n.add_argument('--calibration', help='comma-separated criterion IDs')
    n.add_argument('--caution', help='comma-separated criterion IDs')
    n.add_argument('--original', action='append', help="a grader's original sheet; give each one")
    n.add_argument('--scorer', help="an automatic scorer's sheet, compared with the settled grades")
    n.add_argument('--json')
    a = ap.parse_args(argv)
    if a.cmd == 'template':
        rubric, runs = load_rubric(a.scenarios), blind_scenarios(a.blind)
        missing = sorted({s for s in runs.values() if s not in rubric})
        if missing:
            sys.exit(f'scenarios not in the catalog: {", ".join(missing)}')
        sheet = {'grader': {'name': '', 'kind': '', 'family': ''},
                 'runs': {bid: {c: None for c, _, _ in rubric[sid]} for bid, sid in sorted(runs.items())},
                 'notes': {}}
        print(json.dumps(sheet, indent=1))
    elif a.cmd == 'check':
        bad = problems(json.loads(Path(a.sheet).read_text()), blind_scenarios(a.blind), load_rubric(a.scenarios))
        print('\n'.join(bad) if bad else 'complete')
        sys.exit(1 if bad else 0)
    else:
        analyze(a)


if __name__ == '__main__':
    main()
