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
    def __init__(self, root, cand_pass, base_pass, blocked=(), base_version='1.0'):
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
                                 'installed': installed, 'cli_version': '1.0' if cond == 'cand' else base_version})
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

    def test_mixed_cli_version_is_marked(self):
        res, text = Fixture(self.root, ALL, ALL).analyze()
        c = res['configurations']['cli@model']
        self.assertEqual((c['mixed_cli_version'], c['cli_versions']['cand'], c['cli_versions']['none']), (False, ['1.0'], ['1.0']))
        self.assertNotIn('mixed CLI version', text)
        (self.root / 'mixed').mkdir()
        res, text = Fixture(self.root / 'mixed', ALL, ALL, base_version='2.0').analyze()
        c = res['configurations']['cli@model']
        self.assertTrue(c['mixed_cli_version'])
        self.assertEqual(c['cli_versions']['none'], ['2.0'])
        self.assertIn('| cli@model (mixed CLI version) |', text)
        self.assertEqual(c['difference']['claim'], 'no claim')  # the figure itself is computed as usual

    def test_disagree_writes_settled_with_open_items(self):
        f = Fixture(self.root, ALL, ALL)
        other = json.loads(json.dumps(f.sheet))
        other['grader'] = {'name': 'g2', 'kind': 'human'}
        other['runs']['B002']['X1.2'] = 'blocked'
        other['notes'] = {'B002': 'commit refused'}
        (self.root / 'g2.json').write_text(json.dumps(other))
        args = ['disagree', str(self.root / 'settled.json'), str(self.root / 'g2.json'), '--blind', str(self.root / 'blind'),
                '--scenarios', str(self.root / 'scenarios.json'), '--settled', str(self.root / 's.json')]
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ha.main(args)
        self.assertIn('1 of 48 criteria differ', buf.getvalue())
        self.assertIn('g2 note: commit refused', buf.getvalue())
        s = json.loads((self.root / 's.json').read_text())
        self.assertIsNone(s['runs']['B002']['X1.2'])
        self.assertEqual(s['runs']['B002']['X1.1'], 'pass')
        bad = ha.problems(s, ha.blind_scenarios(self.root / 'blind'), ha.load_rubric(self.root / 'scenarios.json'))
        self.assertEqual(bad, ['B002 X1.2: missing'])
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            ha.main(args)  # never overwrites a settled sheet

    def test_discussion_rounds(self):
        f = Fixture(self.root, ALL, ALL)
        other = json.loads(json.dumps(f.sheet))
        other['grader'] = {'name': 'g2', 'kind': 'model', 'family': 'fam'}
        other['runs']['B002']['X1.2'] = 'fail'   # g2 will give way
        other['runs']['B005']['X2.1'] = 'fail'   # both keep: left for adjudication
        (self.root / 'g2.json').write_text(json.dumps(other))
        r, d = self.root, str(self.root / 'disc')
        common = ['--blind', str(r / 'blind'), '--scenarios', str(r / 'scenarios.json')]
        quiet = lambda _: contextlib.redirect_stdout(io.StringIO())  # noqa: E731
        with quiet(None):
            ha.main(['disagree', str(r / 'settled.json'), str(r / 'g2.json'), *common, '--settled', str(r / 's.json')])
            ha.main(['round1', str(r / 'settled.json'), str(r / 'g2.json'), *common, '--dir', d])
        with self.assertRaises(SystemExit), quiet(None):
            ha.main(['round2', '--dir', d])  # reasons missing
        for lab in ('g1', 'g2'):
            p = Path(d) / f'{lab}-round1.json'
            x = json.loads(p.read_text())
            self.assertEqual(len(x['items']), 2)
            for it in x['items']:
                it['reason'] = f'{lab} reason'
            p.write_text(json.dumps(x))
        with quiet(None):
            ha.main(['round2', '--dir', d])
        r2 = {lab: json.loads((Path(d) / f'{lab}-round2.json').read_text()) for lab in ('g1', 'g2')}
        self.assertEqual(r2['g1']['items'][0]['other_reason'], 'g2 reason')
        self.assertNotIn('g2', json.dumps(r2['g1']['items'][0]['other_grade']))
        for lab, items in r2.items():
            for it in items['items']:
                it['decision'] = 'keep'
        r2['g2']['items'][0].update(decision='change', grade='pass', evidence='the test passes in the tree')
        for lab, x in r2.items():
            (Path(d) / f'{lab}-round2.json').write_text(json.dumps(x))
        with quiet(None) as buf:
            ha.main(['settle', '--dir', d, '--settled', str(r / 's.json'), '--out', str(r / 's2.json')])
        self.assertIn('2 disputed: 1 converged, 1 left', buf.getvalue())
        self.assertIn('g2 changed 1 of 2: fail->pass 1', buf.getvalue())
        s2 = json.loads((r / 's2.json').read_text())
        self.assertEqual(s2['runs']['B002']['X1.2'], 'pass')
        self.assertIn('converged on pass (g1 kept pass; g2 changed to pass)', s2['notes']['B002'])
        self.assertIsNone(s2['runs']['B005']['X2.1'])
        self.assertIn('B005 (X2) X2.1', (Path(d) / 'adjudicate.md').read_text())
        self.assertEqual(ha.problems(s2, ha.blind_scenarios(r / 'blind'), ha.load_rubric(r / 'scenarios.json')),
                         ['B005 X2.1: missing'])
        self.assertIsNone(json.loads((r / 's.json').read_text())['runs']['B002']['X1.2'])  # input unchanged

    def test_fenced_subset_template_and_combine(self):
        f = Fixture(self.root, ALL, ALL)
        r = self.root
        (r / 'blind' / 'B003' / 'run.md').write_text('# Run B003\n\nScenario: X1\n\n````\nhas ``` inside\n````\n')
        (r / 'blind' / 'B004' / 'run.md').write_text('# Run B004\n\nScenario: X2\n\n```\nplain\n```\n')
        self.assertEqual(ha.fenced(r / 'blind', 4), ['B003'])
        (r / 'runs.txt').write_text('B003\nB007\n')
        common = ['--blind', str(r / 'blind'), '--scenarios', str(r / 'scenarios.json')]
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ha.main(['template', str(r / 'blind'), '--scenarios', str(r / 'scenarios.json'), '--runs', str(r / 'runs.txt')])
        part = json.loads(buf.getvalue())
        self.assertEqual(sorted(part['runs']), ['B003', 'B007'])
        part['grader'] = {'name': 'g3', 'kind': 'model', 'family': 'fam'}
        for bid in part['runs']:
            part['runs'][bid] = {c: 'fail' for c in part['runs'][bid]}
        (r / 'g3.json').write_text(json.dumps(part))
        with self.assertRaises(SystemExit) as e, contextlib.redirect_stdout(io.StringIO()):
            ha.main(['check', str(r / 'g3.json'), *common, '--runs', 'B003,B007'])
        self.assertEqual(e.exception.code, 0)
        args = ['combine', str(r / 'settled.json'), str(r / 'g3.json'), '--runs', str(r / 'runs.txt'), *common,
                '--name', 'g2+g3', '--reason', 'fences skipped', '--out', str(r / 'c.json')]
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            ha.main(args)
        self.assertIn('22 runs from settled, 2 from g3', buf.getvalue())
        c = json.loads((r / 'c.json').read_text())
        self.assertEqual(c['runs']['B003']['X1.1'], 'fail')
        self.assertEqual(c['runs']['B001']['X1.1'], 'pass')
        self.assertEqual((c['grader']['source']['B003'], c['grader']['source']['B001']), ('g3', 'settled'))
        self.assertEqual(ha.problems(c, ha.blind_scenarios(r / 'blind'), ha.load_rubric(r / 'scenarios.json')), [])
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            ha.main(args)  # never overwrites
        part['runs']['B003']['X1.1'] = None
        (r / 'g3.json').write_text(json.dumps(part))
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()):
            ha.main(args[:-1] + [str(r / 'c2.json')])  # an incomplete override is refused

    def test_tiebreak_majority_splits_and_check(self):
        f = Fixture(self.root, ALL, ALL)
        r, d = self.root, str(self.root / 'disc')
        other = json.loads(json.dumps(f.sheet))
        other['grader'] = {'name': 'g2', 'kind': 'model', 'family': 'fam'}
        other['runs']['B002']['X1.2'] = 'fail'
        other['runs']['B005']['X2.1'] = 'fail'
        (r / 'g2.json').write_text(json.dumps(other))
        common = ['--blind', str(r / 'blind'), '--scenarios', str(r / 'scenarios.json')]
        out = lambda: contextlib.redirect_stdout(io.StringIO())  # noqa: E731
        with out():
            ha.main(['disagree', str(r / 'settled.json'), str(r / 'g2.json'), *common, '--settled', str(r / 's.json')])
            ha.main(['round1', str(r / 'settled.json'), str(r / 'g2.json'), *common, '--dir', d])
        for lab in ('g1', 'g2'):
            p = Path(d) / f'{lab}-round1.json'
            x = json.loads(p.read_text())
            for it in x['items']:
                it['reason'] = 'because'
            p.write_text(json.dumps(x))
        with out():
            ha.main(['round2', '--dir', d])
        for lab in ('g1', 'g2'):
            p = Path(d) / f'{lab}-round2.json'
            x = json.loads(p.read_text())
            for it in x['items']:
                it['decision'] = 'keep'
            p.write_text(json.dumps(x))
        with out():
            ha.main(['settle', '--dir', d, '--settled', str(r / 's.json'), '--out', str(r / 's2.json')])
        with out() as buf:
            ha.main(['template', str(r / 'blind'), '--scenarios', str(r / 'scenarios.json'), '--runs', 'B002,B005'])
        third = json.loads(buf.getvalue())
        third['grader'] = {'name': 'g5', 'kind': 'model', 'family': 'other'}
        third['runs'] = {'B002': {'X1.1': 'pass', 'X1.2': 'pass'},    # sides with g1 on X1.2
                         'B005': {'X2.1': 'blocked', 'X2.2': 'fail'}}  # three-way on X2.1; X2.2 disagrees with the settled pass
        (r / 'g5.json').write_text(json.dumps(third))
        args = ['tiebreak', '--dir', d, '--settled', str(r / 's2.json'), '--third', str(r / 'g5.json'), *common,
                '--out', str(r / 's3.json')]
        with out() as buf:
            ha.main(args)
        self.assertIn('2 open: 1 settled by majority of three, 1 three-way splits', buf.getvalue())
        self.assertIn('g5 agreed with 1 of 2 criteria already settled', buf.getvalue())
        s3 = json.loads((r / 's3.json').read_text())
        self.assertEqual(s3['runs']['B002']['X1.2'], 'pass')
        self.assertIn('majority of three (g1 pass, g2 fail, g5 pass)', s3['notes']['B002'])
        self.assertIsNone(s3['runs']['B005']['X2.1'])
        self.assertIn('B005 X2.1: g1 `pass`, g2 `fail`, g5 `blocked`', (Path(d) / 'tiebreak-splits.md').read_text())
        self.assertEqual(s3['grader']['tiebreak']['agreement_on_settled_criteria'], [1, 2])
        with self.assertRaises(SystemExit), out():
            ha.main(args)  # never overwrites
        with self.assertRaises(SystemExit), out():  # a sheet with hand adjudication already in it is refused
            ha.main(['tiebreak', '--dir', d, '--settled', str(r / 's3.json'), '--third', str(r / 'g5.json'), *common,
                     '--out', str(r / 's4.json')])

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
