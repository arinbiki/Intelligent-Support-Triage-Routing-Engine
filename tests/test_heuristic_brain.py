import unittest
import sys
import os

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "windmill", "f", "econ_support_triage")
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import delighted_script

class TestHeuristicBrain(unittest.TestCase):

    def test_billing_classification_and_refund_intent(self):
        text = "I was double charged on my credit card statement for order #84920. Please issue a full refund immediately."
        res = delighted_script.main("TICK-TEST-1", text, customer_tier="Standard")
        self.assertEqual(res["department"], "Billing")
        self.assertGreaterEqual(res["confidence"], 0.85)
        self.assertTrue(res["refund_intent"]["detected"])
        self.assertEqual(res["refund_intent"]["order_id"], "#84920")

    def test_fulfillment_classification(self):
        text = "Where is my package? The tracking number 1Z9999999999999999 has not moved in 5 days."
        res = delighted_script.main("TICK-TEST-2", text, customer_tier="Standard")
        self.assertEqual(res["department"], "Fulfillment")
        self.assertGreaterEqual(res["confidence"], 0.85)
        self.assertFalse(res["refund_intent"]["detected"])

    def test_technical_classification(self):
        text = "When I click the Complete Checkout button, the page gives error 500."
        res = delighted_script.main("TICK-TEST-3", text, customer_tier="Standard")
        self.assertEqual(res["department"], "Technical")
        self.assertGreaterEqual(res["confidence"], 0.85)

    def test_general_inquiry_classification(self):
        text = "Do you offer wholesale pricing or bulk discounts for corporate orders over 50 units?"
        res = delighted_script.main("TICK-TEST-4", text, customer_tier="Standard")
        self.assertEqual(res["department"], "General")
        self.assertGreaterEqual(res["confidence"], 0.85)

    def test_kill_switch_triggers_critical_urgency(self):
        text = "You charged me twice. If you don't fix this right now I will call my lawyer and file a chargeback with my bank!"
        res = delighted_script.main("TICK-TEST-5", text, customer_tier="Standard")
        self.assertEqual(res["urgency"]["score"], 3)
        self.assertEqual(res["urgency"]["level"], "CRITICAL")
        self.assertTrue(res["urgency"]["kill_switch_triggered"])
        self.assertIn("lawyer", res["urgency"]["trigger_keywords"])
        self.assertIn("chargeback", res["urgency"]["trigger_keywords"])
        self.assertEqual(res["routing"]["sla_minutes"], 15)

    def test_vip_critical_escalation_requires_approval(self):
        text = "My order #84920 arrived broken and I demand an immediate refund or I report this fraud."
        res = delighted_script.main("TICK-TEST-6", text, customer_tier="VIP")
        self.assertEqual(res["routing"]["assigned_queue"], "VIP_ESCALATIONS")
        self.assertTrue(res["routing"]["requires_human_approval"])
        self.assertIn("VIP", res["routing"]["applied_tags"])

if __name__ == "__main__":
    unittest.main()
