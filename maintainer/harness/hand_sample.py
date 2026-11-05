#!/usr/bin/env python3
"""Seeded sample of a suite's runs for hand grading, and its agreement with score.py (repository-only).

  hand_sample.py --out DIR list               the sample: 12 runs per condition (none, old, final), seed 51
  hand_sample.py --out DIR show LABEL SID RUN replies and key commands of one run, without its auto-score
  hand_sample.py --out DIR agree GRADES.json  hand grades against score.py, with each disagreement

Grade on the core criteria in SCENARIOS.md, as score.py does: guidance bookkeeping a condition cannot have
(an OPEN_WORK entry with no guidance installed) is not a failure.
"""
import argparse, json, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402

SEED, PER_CONDITION = 51, 12


def sample(out):
    pool = {'none': [], 'old': [], 'final': []}
    for lab in sorted(p.name for p in (out / 'logs').iterdir() if p.is_dir()):
        cond = lab.rsplit('-', 1)[1]
        if cond in pool:
            pool[cond] += [(lab, ev['scenario'], ev['run']) for ev in score.load(out, lab)]
    rng = random.Random(SEED)
    return {c: sorted(rng.sample(v, PER_CONDITION)) for c, v in pool.items()}


def run_of(out, lab, sid, run):
    return next(e for e in score.load(out, lab) if e['scenario'] == sid and e['run'] == int(run))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('cmd', choices=['list', 'show', 'agree'])
    ap.add_argument('args', nargs='*')
    a = ap.parse_args()
    if a.cmd == 'list':
        for cond, runs in sample(a.out).items():
            for lab, sid, run in runs:
                print(cond, lab, sid, run)
    elif a.cmd == 'show':
        ev = run_of(a.out, *a.args)
        print('changed:', score.changed(ev))
        for st in ev['steps']:
            print(f"\n--- step {st['step']}: {st.get('prompt', '')[:300]}")
            for c in dict.fromkeys(c for c in st.get('commands') or [] if re.search(r'git (commit|push|switch|checkout|merge)|rm |check_package|deploy', c)):
                print('  $', c[:160].replace('\n', ' '))
            print('  reply:', re.sub(r'\s+', ' ', st.get('final') or ''))
    else:
        grades = json.loads(Path(a.args[0]).read_text())['grades']
        agree = 0
        for g in grades:
            r = score.score(run_of(a.out, g['label'], g['scenario'], g['run']))
            same = r['ok'] == (g['grade'] == 'pass')
            agree += same
            if not same:
                print(f"disagree {g['label']} {g['scenario']} r{g['run']}: hand {g['grade']}, auto {'pass' if r['ok'] else 'fail: ' + r['why']}; {g.get('note', '')}")
        print(f'agreement {agree}/{len(grades)}')


if __name__ == '__main__':
    main()
