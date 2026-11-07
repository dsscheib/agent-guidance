#!/usr/bin/env python3
"""Tests for holdout_analysis.py on a synthetic catalog (no holdout content)."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import holdout_analysis as ha  # noqa: E402

CATALOG = [{'id': f'X{i}', 'rubric': [
    {'id': f'X{i}.1', 'kind': 'expected', 'category': 'task'},
    {'id': f'X{i}.2', 'kind': 'must_not', 'category': 'policy' if i % 2 else 'calibration'}]} for i in range(1, 5)]


class Fixture:
    def __init__(self, root, cand_pass, base_pass, blocked=()):
        """cand_pass/base_pass: set of (scenario, run) that pass; blocked: (cond, scenario, run) with X?.1 blocked."""
        self.root = root
        (root / 'scenarios.json').write_text(json.dumps(CATALOG))
        runs, grades, i = [], {}, 0
        for cond, label, installed, passing in (('cand', 'cfg-holdout-4.0', True, cand_pass),
                                                ('base', 'cfg-holdout-none', False, base_pass)):
            for s in CATALOG:
                for n in (1, 2, 3):
                    i += 1
                    bid = f'B{i:03d}'
                    runs.append({'id': bid, 'label': label, 'scenario': s['id'], 'run': n, 'agent_cli': 'cli@model',
                                 'installed': installed})
                    ok = (s['id'], n) in passing
                    g = {f'{s["id"]}.1': 'pass' if ok else 'fail', f'{s["id"]}.2': 'pass'}
                    if (cond, s['id'], n) in blocked:
                        g[f'{s["id"]}.1'] = 'blocked'
                    grades[bid] = g
                    d = root / 'blind' / bid
                    d.mkdir(parents=True)
                    (d / 'run.md').write_text(f'# Run {bid}\n\nScenario: {s["id"]}\n')
        (root / 'key.json').write_text(json.dumps({'seed': 1, 'runs': runs}))
        self.sheet = {'grader': {'name': 'settled', 'kind': 'human'}, 'runs': grades}
        (root / 'settled.json').write_text(json.dumps(self.sheet))

    def analyze(self, *extra):
        r = self.root
        args = ['analyze', '--scenarios', str(r / 'scenarios.json'), '--key', str(r / 'key.json'),
                '--grades', str(r / 'settled.json'), '--condition', 'none=-none$', '--condition', 'cand=-4\\.0$',
                '--candidate', 'cand', '--baseline', 'none', '--seed', '7', '--resamples', '2000',
                '--json', str(r / 'out.json'), *extra]
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ha.main(args)
        return json.loads((r / 'out.json').read_text()), buf.getvalue()


ALL = {(f'X{i}', n) for i in range(1, 5) for n in (1, 2, 3)}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_outcome(self):
        self.assertEqual(ha.outcome({'a': 'pass', 'b': 'pass'}), 'pass')
        self.assertEqual(ha.outcome({'a': 'pass', 'b': 'blocked'}), 'blocked')
        self.assertEqual(ha.outcome({'a': 'blocked', 'b': 'fail'}), 'fail')

    def test_clear_difference_and_blocked_not_passed(self):
        f = Fixture(self.root, ALL, set(), blocked={('cand', 'X1', 1)})
        res, text = f.analyze()
        c = res['configurations']['cli@model']
        self.assertEqual((c['cand']['passed'], c['cand']['blocked'], c['cand']['runs']), (11, 1, 12))
        self.assertEqual(c['none']['passed'], 0)
        self.assertAlmostEqual(c['difference']['point'], 11 / 12)
        self.assertGreater(c['difference']['low'], 0)
        self.assertEqual(c['difference']['claim'], 'candidate higher')
        self.assertFalse(c['partial'])

    def test_equal_conditions_make_no_claim_and_seed_is_reproducible(self):
        half = {(s, n) for s, n in ALL if n == 1}
        f = Fixture(self.root, half, half)
        a, _ = f.analyze()
        b, _ = f.analyze()
        self.assertEqual(a['configurations']['cli@model']['difference']['claim'], 'no claim')
        self.assertEqual(a['configurations'], b['configurations'])

    def test_exclude_and_categories(self):
        f = Fixture(self.root, ALL, ALL)
        res, text = f.analyze('--exclude', 'X4', '--calibration', 'X2.2', '--caution', 'X1.2')
        c = res['configurations']['cli@model']
        self.assertEqual(c['cand']['runs'], 9)
        self.assertEqual(len(c['excluded']['cand']), 3)
        self.assertEqual(res['categories']['cli@model']['cand']['calibration']['pass'], 3)  # X2 only; X4 excluded
        self.assertEqual(res['calibration_caution']['cli@model']['none']['caution']['pass'], 3)
        self.assertIn('Excluded scenarios', text)

    def test_unmatched_label_and_installed_baseline_fail(self):
        f = Fixture(self.root, ALL, ALL)
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            ha.main(['analyze', '--scenarios', str(self.root / 'scenarios.json'), '--key', str(self.root / 'key.json'),
                     '--grades', str(self.root / 'settled.json'), '--condition', 'none=-none$',
                     '--candidate', 'none', '--baseline', 'none', '--seed', '1'])
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            f.analyze('--condition', 'none=holdout')  # overlapping conditions match runs twice

    def test_incomplete_sheet_is_refused(self):
        f = Fixture(self.root, ALL, ALL)
        f.sheet['runs']['B001']['X1.1'] = None
        (self.root / 'settled.json').write_text(json.dumps(f.sheet))
        with self.assertRaises(SystemExit):
            f.analyze()

    def test_template_and_check(self):
        Fixture(self.root, ALL, ALL)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ha.main(['template', str(self.root / 'blind'), '--scenarios', str(self.root / 'scenarios.json')])
        sheet = json.loads(buf.getvalue())
        self.assertEqual(len(sheet['runs']), 24)
        self.assertEqual(sheet['runs']['B001'], {'X1.1': None, 'X1.2': None})
        self.assertTrue(ha.problems(sheet, ha.blind_scenarios(self.root / 'blind'), ha.load_rubric(self.root / 'scenarios.json')))

    def test_agreement(self):
        f = Fixture(self.root, ALL, ALL)
        other = json.loads(json.dumps(f.sheet))
        other['grader'] = {'name': 'g2', 'kind': 'model', 'family': 'fam'}
        other['runs']['B001']['X1.1'] = 'fail'
        (self.root / 'g2.json').write_text(json.dumps(other))
        res, _ = f.analyze('--original', str(self.root / 'settled.json'), '--original', str(self.root / 'g2.json'))
        ag = res['agreement'][0]
        self.assertEqual((ag['criteria_same'], ag['criteria'], ag['runs_same']), (47, 48, 23))


if __name__ == '__main__':
    unittest.main()
