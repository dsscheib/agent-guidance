#!/usr/bin/env python3
"""Grade sheets and the pre-registered analysis for the private holdout set (repository-only).

  holdout_analysis.py template BLIND_DIR --scenarios SCENARIOS.json [--runs RUNS] > sheet.json
  holdout_analysis.py check SHEET.json --blind BLIND_DIR --scenarios SCENARIOS.json [--runs RUNS]
  holdout_analysis.py fenced BLIND_DIR [--min 4] > runs.txt
  holdout_analysis.py combine BASE.json OVERRIDE.json --runs RUNS --blind BLIND_DIR --scenarios SCENARIOS.json
        --name NAME --reason TEXT --out OUT.json
  holdout_analysis.py disagree G1.json G2.json --blind BLIND_DIR --scenarios SCENARIOS.json --settled OUT.json > LIST.md
  holdout_analysis.py round1 G1.json G2.json --blind BLIND_DIR --scenarios SCENARIOS.json --dir DISCUSS_DIR
  holdout_analysis.py round2 --dir DISCUSS_DIR
  holdout_analysis.py settle --dir DISCUSS_DIR --settled SETTLED.json --out SETTLED2.json
  holdout_analysis.py tiebreak --dir DISCUSS_DIR --settled SETTLED2.json --third G5.json --blind BLIND_DIR
        --scenarios SCENARIOS.json --out SETTLED3.json
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

RUNS is a comma-separated list of run IDs or a file with one per line. With --runs, `template` writes a sheet for those
runs only and `check` checks a sheet against them. `fenced` lists the runs whose run.md has a code fence of --min or
more backticks (blind.py lengthens a fence when the text inside holds backticks), which a grader can misread.

`combine` builds one grader's sheet from two: OVERRIDE's grades for RUNS, BASE's for every other run. Its grader block
has kind "composite", the two sources, the reason, and `source` naming the sheet each run came from; both inputs must
be complete for their runs. It is for replacing a grader's invalid grades on some runs by a fresh grader's, so the
pair still has two independent grades on every run. Publish both inputs as well.

`disagree` compares two complete sheets after both are submitted. It prints each criterion they graded differently, with
the criterion's text and both graders' notes on that run, and writes a settled sheet (refusing to overwrite one): the
grades both gave, and null where they differ. Fill those after discussion; `check` on it lists what is still open. It
reads no key.

Discussion between graders, in files (the originals are never changed):
- `round1` writes DISCUSS_DIR/g1-round1.json and g2-round1.json, for the first and second sheet: each grader's own
  disputed items (run, criterion, its text, the grader's grade) with `reason` null. Each grader fills its reasons,
  citing evidence in the run, without seeing the other's.
- `round2`, once both reasons are filled, writes g1-round2.json and g2-round2.json: each item with the grader's own
  grade and reason and the other grader's, named only "the other grader". Each grader sets `decision` to "keep" or
  "change", and for a change, `grade` and the `evidence` that supports it.
- `settle` writes a new settled sheet (--out, never overwriting): where both final grades now agree, that grade, with a
  note on how each grader got there ("converged"); the rest stay null for a human to adjudicate, listed in
  DISCUSS_DIR/adjudicate.md with both positions. It prints how many grades each grader changed, and in which
  direction, so one grader giving way to the other shows. After adjudication, `check` on the new sheet must say complete.
- `tiebreak` settles what discussion left open with a third grader instead of a human. The third grader grades whole
  runs (a sheet from `template --runs` with every run that has an open criterion), blind to the two graders' grades,
  reasons and which criteria are disputed. Each open criterion takes the majority of the two final grades and the
  third; where all three differ, it stays null for a human, listed in DISCUSS_DIR/tiebreak-splits.md. It reports the
  third grader's agreement with the criteria already settled in its runs, as a check on its tie-breaks, and records
  the rule and the third grader in the settled sheet's grader block. Decide to use it before seeing its grades.

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
    if g.get('kind') == 'composite':
        src = g.get('source') or {}
        if not g.get('name') or len(g.get('sources') or []) < 2 or set(src) != set(run_scenarios):
            out.append('a composite grader block needs a name, its sources, and a source for every run')
    elif not g.get('name') or g.get('kind') not in ('human', 'model') or (g.get('kind') == 'model' and not g.get('family')):
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


def parse_runs(spec, run_scenarios):
    """Run IDs from a file (one per line) or a comma-separated list, each checked against the blinded set."""
    p = Path(spec)
    ids = [s.strip() for s in (p.read_text().splitlines() if p.is_file() else spec.split(','))]
    ids = sorted(set(filter(None, ids)))
    unknown = [i for i in ids if i not in run_scenarios]
    if unknown or not ids:
        sys.exit(f'--runs: {"no run IDs" if not ids else "not in the blinded set: " + ", ".join(unknown[:20])}')
    return ids


def subset(run_scenarios, runs):
    return {bid: run_scenarios[bid] for bid in runs}


def fenced(blind, minimum):
    rx = re.compile(r'^`{%d,}' % minimum, re.M)
    return [p.parent.name for p in sorted(Path(blind).glob('B*/run.md')) if rx.search(p.read_text())]


def combine(a):
    rubric, everything = load_rubric(a.scenarios), blind_scenarios(a.blind)
    over_ids = parse_runs(a.runs, everything)
    rest = sorted(set(everything) - set(over_ids))
    base = json.loads(Path(a.base).read_text())
    over = json.loads(Path(a.override).read_text())
    bad = [f'{a.base}: {x}' for x in problems({**base, 'runs': {b: base['runs'].get(b) for b in rest}},
                                              subset(everything, rest), rubric)]
    bad += [f'{a.override}: {x}' for x in problems({**over, 'runs': {b: (over.get('runs') or {}).get(b) for b in over_ids}},
                                                   subset(everything, over_ids), rubric)]
    extra = sorted(set(over.get('runs') or {}) - set(over_ids))
    if extra:
        bad.append(f'{a.override}: has runs outside --runs, e.g. {", ".join(extra[:5])}')
    if bad:
        sys.exit(f'{len(bad)} problem(s):\n  ' + '\n  '.join(bad[:40]))
    bn, on = base['grader']['name'], over['grader']['name']
    if bn == on:
        sys.exit('the two sheets have the same grader name')
    notes = {}
    for b in rest:
        if (base.get('notes') or {}).get(b):
            notes[b] = base['notes'][b]
    for b in over_ids:
        if (over.get('notes') or {}).get(b):
            notes[b] = over['notes'][b]
    write_new(a.out, {
        'grader': {'name': a.name, 'kind': 'composite', 'sources': [base['grader'], over['grader']],
                   'reason': a.reason, 'source': {b: (on if b in over_ids else bn) for b in sorted(everything)}},
        'runs': {b: (over if b in over_ids else base)['runs'][b] for b in sorted(everything)}, 'notes': notes})
    print(f'{a.out}: {len(rest)} runs from {bn}, {len(over_ids)} from {on}')


def criterion_texts(path):
    data = json.loads(Path(path).read_text())
    return {c['id']: c.get('text', '') for s in (data if isinstance(data, list) else data.get('scenarios', []))
            for c in s.get('rubric') or []}


def write_new(path, obj):
    path = Path(path)
    if path.exists():
        sys.exit(f'{path} exists; not overwriting it')
    path.write_text(json.dumps(obj, indent=1) + '\n')


def read_round(d, label, rnd):
    p = Path(d) / f'{label}-round{rnd}.json'
    if not p.exists():
        sys.exit(f'{p} not found')
    return p, json.loads(p.read_text())


def round1(a):
    texts, rubric, run_scenarios = criterion_texts(a.scenarios), load_rubric(a.scenarios), blind_scenarios(a.blind)
    s1, s2 = (load_sheet(p, run_scenarios, rubric) for p in (a.g1, a.g2))
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    items = [(bid, sid, cid, s1['runs'][bid][cid], s2['runs'][bid][cid]) for bid, sid in sorted(run_scenarios.items())
             for cid, _, _ in rubric[sid] if s1['runs'][bid][cid] != s2['runs'][bid][cid]]
    for label, mine in (('g1', 3), ('g2', 4)):
        write_new(d / f'{label}-round1.json', {
            'instructions': 'For each item, write in `reason` why you gave your grade, citing the evidence in that '
                            "run's run.md (message, command, file or git state). Do not change `your_grade`.",
            'items': [{'run': it[0], 'scenario': it[1], 'criterion': it[2], 'text': texts.get(it[2], ''),
                       'your_grade': it[mine], 'reason': None} for it in items]})
    print(f'{len(items)} disputed criteria; wrote {d}/g1-round1.json and {d}/g2-round1.json')


def round2(a):
    (p1, r1), (p2, r2) = read_round(a.dir, 'g1', 1), read_round(a.dir, 'g2', 1)
    k = lambda it: (it['run'], it['criterion'])  # noqa: E731
    if [k(x) for x in r1['items']] != [k(x) for x in r2['items']]:
        sys.exit('the two round-1 files list different items')
    empty = [f'{p.name} {x["run"]} {x["criterion"]}' for p, r in ((p1, r1), (p2, r2)) for x in r['items']
             if not (x.get('reason') or '').strip()]
    if empty:
        sys.exit(f'{len(empty)} reason(s) missing:\n  ' + '\n  '.join(empty[:40]))
    for label, mine, other in (('g1', r1, r2), ('g2', r2, r1)):
        write_new(Path(a.dir) / f'{label}-round2.json', {
            'instructions': 'Each item shows your grade and reason and the other grader\'s. Set `decision` to "keep" '
                            'or "change". Change only if the other reason points to evidence you missed or misread; '
                            'then set `grade` to pass, fail or blocked and `evidence` to what in run.md supports it.',
            'items': [{'run': m['run'], 'scenario': m['scenario'], 'criterion': m['criterion'], 'text': m['text'],
                       'your_grade': m['your_grade'], 'your_reason': m['reason'],
                       'other_grade': o['your_grade'], 'other_reason': o['reason'],
                       'decision': None, 'grade': None, 'evidence': None}
                      for m, o in zip(mine['items'], other['items'])]})
    print(f'wrote {a.dir}/g1-round2.json and {a.dir}/g2-round2.json')


def round_finals(d):
    """Both graders' round-2 items and final grades; exits on any incomplete or inconsistent decision."""
    (p1, r1), (p2, r2) = read_round(d, 'g1', 2), read_round(d, 'g2', 2)
    bad, finals = [], []
    for p, r in ((p1, r1), (p2, r2)):
        f = []
        for x in r['items']:
            where = f'{p.name} {x["run"]} {x["criterion"]}'
            if x.get('decision') == 'keep':
                f.append(x['your_grade'])
            elif x.get('decision') == 'change':
                if x.get('grade') not in GRADES or x['grade'] == x['your_grade'] or not (x.get('evidence') or '').strip():
                    bad.append(f'{where}: a change needs a different grade and its evidence')
                f.append(x.get('grade'))
            else:
                bad.append(f'{where}: decision must be "keep" or "change"')
                f.append(None)
        finals.append(f)
    if [(x['run'], x['criterion']) for x in r1['items']] != [(x['run'], x['criterion']) for x in r2['items']]:
        bad.append('the two round-2 files list different items')
    if bad:
        sys.exit(f'{len(bad)} problem(s):\n  ' + '\n  '.join(bad[:40]))
    return r1, r2, finals


def settle(a):
    r1, r2, finals = round_finals(a.dir)
    settled = json.loads(Path(a.settled).read_text())
    converged, open_items, changes = 0, [], {'g1': {}, 'g2': {}}
    for x, y, f1, f2 in zip(r1['items'], r2['items'], *finals):
        bid, cid = x['run'], x['criterion']
        for label, it, fin in (('g1', x, f1), ('g2', y, f2)):
            if fin != it['your_grade']:
                t = f'{it["your_grade"]}->{fin}'
                changes[label][t] = changes[label].get(t, 0) + 1
        if settled['runs'][bid].get(cid) is not None:
            sys.exit(f'{bid} {cid} is already settled in {a.settled}; was it made by `disagree` for these sheets?')
        how = lambda lab, it, fin: f'{lab} {"kept" if fin == it["your_grade"] else "changed to"} {fin}'  # noqa: E731
        if f1 == f2:
            converged += 1
            settled['runs'][bid][cid] = f1
            note = f'{cid}: converged on {f1} ({how("g1", x, f1)}; {how("g2", y, f2)})'
        else:
            open_items.append((x, y, f1, f2))
            note = f'{cid}: still disputed after discussion (g1 {f1}, g2 {f2}); adjudicate'
        notes = settled.setdefault('notes', {})
        notes[bid] = (notes[bid] + '\n' if notes.get(bid) else '') + note
    adj = Path(a.dir) / 'adjudicate.md'
    for p in (Path(a.out), adj):
        if p.exists():
            sys.exit(f'{p} exists; not overwriting it')
    write_new(a.out, settled)
    lines = [f'# Still disputed after discussion: {len(open_items)}', '',
             'Decide each from the run\'s run.md and the protocol\'s Grading section, without the key. Write the grade '
             f'into {a.out} and add "adjudicated by <name>: <reason>" to the run\'s note.', '']
    for x, y, f1, f2 in open_items:
        lines += [f'## {x["run"]} ({x["scenario"]}) {x["criterion"]}', '', x['text'], '',
                  f'- g1 final `{f1}`. Reason: {x["your_reason"]}' + (f' Change evidence: {x["evidence"]}' if x.get('evidence') else ''),
                  f'- g2 final `{f2}`. Reason: {y["your_reason"]}' + (f' Change evidence: {y["evidence"]}' if y.get('evidence') else ''), '']
    adj.write_text('\n'.join(lines) + '\n')
    total = len(r1['items'])
    print(f'{total} disputed: {converged} converged, {len(open_items)} left for adjudication ({adj}); wrote {a.out}')
    for label in ('g1', 'g2'):
        ch = changes[label]
        print(f'{label} changed {sum(ch.values())} of {total}' + (': ' + ', '.join(f'{t} {n}' for t, n in sorted(ch.items())) if ch else ''))


def tiebreak(a):
    """Fill what discussion left open by the majority of three, with a third grader's independent grades."""
    r1, r2, (f1s, f2s) = round_finals(a.dir)
    rubric, everything = load_rubric(a.scenarios), blind_scenarios(a.blind)
    settled, third = json.loads(Path(a.settled).read_text()), json.loads(Path(a.third).read_text())
    open_ = {(x['run'], x['criterion']): (f1, f2) for x, f1, f2 in zip(r1['items'], f1s, f2s) if f1 != f2}
    nulls = {(b, c) for b, g in settled['runs'].items() for c, v in g.items() if v is None}
    if nulls != set(open_):
        sys.exit(f'{a.settled} has {len(nulls)} open criteria, but {len(open_)} were still disputed after round 2; '
                 'use the sheet `settle` wrote, before any hand adjudication')
    need, have = {b for b, _ in open_}, set(third.get('runs') or {})
    if need - have:
        sys.exit(f'{a.third} lacks runs with open criteria: {", ".join(sorted(need - have)[:20])}')
    bad = problems(third, subset(everything, sorted(have)), rubric)
    if bad:
        sys.exit(f'{a.third}: {len(bad)} problem(s)\n  ' + '\n  '.join(bad[:40]))
    out, splits_path = Path(a.out), Path(a.dir) / 'tiebreak-splits.md'
    for p in (out, splits_path):
        if p.exists():
            sys.exit(f'{p} exists; not overwriting it')
    tn = third['grader']['name']
    same = checked = 0
    for b in sorted(have):  # the check: the third grader against criteria already settled in the same runs
        for c, v in settled['runs'][b].items():
            if v is not None:
                checked += 1
                same += third['runs'][b][c] == v
    majority, splits = 0, []
    notes = settled.setdefault('notes', {})
    for (b, c), (f1, f2) in sorted(open_.items()):
        t = third['runs'][b][c]
        if t in (f1, f2):
            majority += 1
            settled['runs'][b][c] = t
            note = f'{c}: settled {t} by majority of three (g1 {f1}, g2 {f2}, {tn} {t})'
        else:
            splits.append((b, c, f1, f2, t))
            note = f'{c}: three-way split (g1 {f1}, g2 {f2}, {tn} {t}); a human decides'
        notes[b] = (notes[b] + '\n' if notes.get(b) else '') + note
    settled['grader']['tiebreak'] = {'grader': third['grader'], 'rule': 'majority of three; three-way splits by a human',
                                     'agreement_on_settled_criteria': [same, checked]}
    write_new(out, settled)
    lines = [f'# Three-way splits: {len(splits)}', '',
             f'Decide each from run.md and the protocol\'s Grading section, without the key, and write the grade and '
             f'"decided by <name>: <reason>" into {out}.', '']
    lines += [f'- {b} {c}: g1 `{f1}`, g2 `{f2}`, {tn} `{t}`' for b, c, f1, f2, t in splits]
    splits_path.write_text('\n'.join(lines) + '\n')
    print(f'{len(open_)} open: {majority} settled by majority of three, {len(splits)} three-way splits ({splits_path}); '
          f'wrote {out}')
    print(f'{tn} agreed with {same} of {checked} criteria already settled in its runs '
          f'({pct(rate(same, checked))}); if that is low, its tie-breaks are not reliable either')


def disagree(a):
    texts = criterion_texts(a.scenarios)
    rubric, run_scenarios = load_rubric(a.scenarios), blind_scenarios(a.blind)
    s1, s2 = (load_sheet(p, run_scenarios, rubric) for p in (a.g1, a.g2))
    n1, n2 = s1['grader']['name'], s2['grader']['name']
    out = Path(a.settled)
    if out.exists():
        sys.exit(f'{out} exists; it may hold settled grades already')
    settled, rows = {}, []
    for bid, sid in sorted(run_scenarios.items()):
        settled[bid] = {}
        for cid, _, _ in rubric[sid]:
            x, y = s1['runs'][bid][cid], s2['runs'][bid][cid]
            settled[bid][cid] = x if x == y else None
            if x != y:
                rows.append((bid, sid, cid, x, y))
    out.write_text(json.dumps({'grader': {'name': 'settled', 'kind': 'human', 'family': '',
                                          'from': [n1, n2], 'method': 'discussion'},
                               'runs': settled, 'notes': {}}, indent=1) + '\n')
    total = sum(len(v) for v in settled.values())
    lines = [f'# Disagreements: {n1} / {n2}', '', f'{len(rows)} of {total} criteria differ, in '
             f'{len({r[0] for r in rows})} of {len(settled)} runs. Settled sheet with agreed grades: {out}', '']
    last = None
    for bid, sid, cid, x, y in rows:
        if bid != last:
            lines += [f'## {bid} ({sid})', '']
            for name, s in ((n1, s1), (n2, s2)):
                note = (s.get('notes') or {}).get(bid)
                if note:
                    lines.append(f'- {name} note: {note}')
            last = bid
        lines.append(f'- **{cid}** {texts.get(cid, "")}: {n1} `{x}`, {n2} `{y}`')
    print('\n'.join(lines))


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
    t.add_argument('--runs', help='run IDs, comma-separated or a file with one per line')
    c = sub.add_parser('check')
    c.add_argument('sheet')
    c.add_argument('--blind', required=True)
    c.add_argument('--scenarios', required=True)
    c.add_argument('--runs', help='run IDs, comma-separated or a file with one per line')
    f = sub.add_parser('fenced')
    f.add_argument('blind')
    f.add_argument('--min', type=int, default=4)
    m = sub.add_parser('combine')
    m.add_argument('base')
    m.add_argument('override')
    m.add_argument('--runs', required=True)
    m.add_argument('--blind', required=True)
    m.add_argument('--scenarios', required=True)
    m.add_argument('--name', required=True, help='name of the combined grader, e.g. "g2+g3"')
    m.add_argument('--reason', required=True)
    m.add_argument('--out', required=True)
    d = sub.add_parser('disagree')
    d.add_argument('g1')
    d.add_argument('g2')
    d.add_argument('--blind', required=True)
    d.add_argument('--scenarios', required=True)
    d.add_argument('--settled', required=True, help='where to write the settled sheet with agreed grades filled in')
    r = sub.add_parser('round1')
    r.add_argument('g1')
    r.add_argument('g2')
    r.add_argument('--blind', required=True)
    r.add_argument('--scenarios', required=True)
    r.add_argument('--dir', required=True)
    r = sub.add_parser('round2')
    r.add_argument('--dir', required=True)
    r = sub.add_parser('settle')
    r.add_argument('--dir', required=True)
    r.add_argument('--settled', required=True, help='the sheet `disagree` wrote')
    r.add_argument('--out', required=True, help='the new settled sheet')
    r = sub.add_parser('tiebreak')
    r.add_argument('--dir', required=True)
    r.add_argument('--settled', required=True, help='the sheet `settle` wrote')
    r.add_argument('--third', required=True, help="the third grader's sheet, made with template --runs")
    r.add_argument('--blind', required=True)
    r.add_argument('--scenarios', required=True)
    r.add_argument('--out', required=True)
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
        if a.runs:
            runs = subset(runs, parse_runs(a.runs, runs))
        missing = sorted({s for s in runs.values() if s not in rubric})
        if missing:
            sys.exit(f'scenarios not in the catalog: {", ".join(missing)}')
        sheet = {'grader': {'name': '', 'kind': '', 'family': ''},
                 'runs': {bid: {c: None for c, _, _ in rubric[sid]} for bid, sid in sorted(runs.items())},
                 'notes': {}}
        print(json.dumps(sheet, indent=1))
    elif a.cmd == 'check':
        runs = blind_scenarios(a.blind)
        if a.runs:
            runs = subset(runs, parse_runs(a.runs, runs))
        bad = problems(json.loads(Path(a.sheet).read_text()), runs, load_rubric(a.scenarios))
        print('\n'.join(bad) if bad else 'complete')
        sys.exit(1 if bad else 0)
    elif a.cmd == 'fenced':
        print('\n'.join(fenced(a.blind, a.min)))
    elif a.cmd == 'combine':
        combine(a)
    elif a.cmd == 'disagree':
        disagree(a)
    elif a.cmd in ('round1', 'round2', 'settle', 'tiebreak'):
        {'round1': round1, 'round2': round2, 'settle': settle, 'tiebreak': tiebreak}[a.cmd](a)
    else:
        analyze(a)


if __name__ == '__main__':
    main()
