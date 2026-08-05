import unittest
from transmit_check import transmit_check

class TestTransmitCheck(unittest.TestCase):
    def test_perfect_fidelity(self):
        orig = "Function process_order must execute in < 50ms. Uses MAX_TIMEOUT = 0x00FF."
        rewr = "The process_order function shall run in < 50ms. It uses MAX_TIMEOUT = 0x00FF."
        res = transmit_check(orig, rewr)
        self.assertEqual(res['fidelity_score'], 1.0)
        self.assertEqual(res['lost_facts'], 0)

    def test_number_drift(self):
        orig = "Timeout is 50.5ms. Offset is 0xDEADBEEF."
        rewr = "Timeout is 50ms. Offset is 0xDEADBE."
        res = transmit_check(orig, rewr)
        self.assertIn("50.5", res['drift']['lost_numbers'])
        self.assertIn("0xDEADBEEF", res['drift']['lost_numbers'])
        
    def test_constraint_drift(self):
        orig = "You must never call main_thread directly."
        rewr = "You shouldn't call main_thread directly."
        res = transmit_check(orig, rewr)
        self.assertIn("must", res['drift']['lost_constraints'])
        self.assertIn("never", res['drift']['lost_constraints'])

if __name__ == '__main__':
    unittest.main()
