import csv
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from io import StringIO
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr
from home_energy_estimator import main

class TestHomeEnergyEstimator(unittest.TestCase):

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.appliances_path = self.root / 'appliances.csv'
        self.schedule_path = self.root / 'schedule.csv'

    def tearDown(self):
        self.tmp.cleanup()

    def write_csv(self, path: Path, rows):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def run_cli(self, args):
        orion_explicit_test_argv = ['home_energy_estimator'] + args
        with patch('sys.argv', orion_explicit_test_argv):
            out = StringIO()
            err = StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                try:
                    main()
                except SystemExit as e:
                    exit_code = e.code
                else:
                    exit_code = 0
        return (exit_code, out.getvalue(), err.getvalue())

    def test_basic_estimation(self):
        self.write_csv(self.appliances_path, [['name', 'power_watts'], ['fridge', '100'], ['lamp', '60']])
        self.write_csv(self.schedule_path, [['name', 'day', 'hours'], ['fridge', '1', '24'], ['lamp', '1', '5'], ['fridge', '2', '24'], ['lamp', '2', '5']])
        exit_code, out, err = self.run_cli(['--appliances', str(self.appliances_path), '--schedule', str(self.schedule_path), '--period', '2'])
        self.assertEqual(exit_code, 0)
        self.assertIn('Day 1: 2.70 kWh', out)
        self.assertIn('Day 2: 2.70 kWh', out)
        self.assertIn('fridge: 4.80 kWh', out)
        self.assertIn('lamp: 0.60 kWh', out)
        self.assertIn('Period total: 5.40 kWh', out)
        self.assertEqual(err, '')

    def test_confidence_bounds(self):
        self.write_csv(self.appliances_path, [['name', 'power_watts'], ['fridge', '100'], ['lamp', '60']])
        self.write_csv(self.schedule_path, [['name', 'day', 'hours'], ['fridge', '1', '24'], ['lamp', '1', '5'], ['fridge', '2', '24'], ['lamp', '2', '5']])
        exit_code, out, err = self.run_cli(['--appliances', str(self.appliances_path), '--schedule', str(self.schedule_path), '--period', '2', '--confidence'])
        self.assertEqual(exit_code, 0)
        self.assertIn('Day 1: 2.70 kWh (2.57-2.84)', out)
        self.assertIn('fridge: 4.80 kWh (4.56-5.04)', out)
        self.assertIn('Period total: 5.40 kWh (5.13-5.67)', out)
        self.assertEqual(err, '')

    def test_unknown_appliance_error(self):
        self.write_csv(self.appliances_path, [['name', 'power_watts'], ['fridge', '100']])
        self.write_csv(self.schedule_path, [['name', 'day', 'hours'], ['fridge', '1', '24'], ['tv', '1', '1']])
        exit_code, out, err = self.run_cli(['--appliances', str(self.appliances_path), '--schedule', str(self.schedule_path), '--period', '1'])
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Schedule references unknown appliance 'tv'", err)

    def test_negative_hours_error(self):
        self.write_csv(self.appliances_path, [['name', 'power_watts'], ['fridge', '100']])
        self.write_csv(self.schedule_path, [['name', 'day', 'hours'], ['fridge', '1', '-5']])
        exit_code, out, err = self.run_cli(['--appliances', str(self.appliances_path), '--schedule', str(self.schedule_path), '--period', '1'])
        self.assertNotEqual(exit_code, 0)
        self.assertIn("Negative hours for appliance 'fridge'", err)
if __name__ == '__main__':
    unittest.main()
