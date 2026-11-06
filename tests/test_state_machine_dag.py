import unittest
import sys
import os

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "windmill", "f", "econ_support_triage")
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import order_eligibility_checker
import execute_helpdesk_tool
import delighted_script

class TestStateMachineDAG(unittest.TestCase):

    def test_order_return_eligibility_within_window(self):
        # Order #84920 was seeded 3 days ago, delivered, not final sale
        res = order_eligibility_checker.main("#84920", return_window_days=30)
        self.assertTrue(res["return_eligible"])
        self.assertEqual(res["reason"], "ELIGIBLE_FOR_RETURN_OR_REFUND")
        self.assertLessEqual(res["days_since_purchase"], 30)

    def test_order_return_eligibility_outside_window(self):
        # Order #1002 was seeded 45 days ago
        res = order_eligibility_checker.main("#1002", return_window_days=30)
        self.assertFalse(res["return_eligible"])
        self.assertEqual(res["reason"], "OUTSIDE_RETURN_WINDOW")

    def test_order_return_eligibility_final_sale(self):
        # Order #1003 is marked final sale
        res = order_eligibility_checker.main("#1003", return_window_days=30)
        self.assertFalse(res["return_eligible"])
        self.assertEqual(res["reason"], "FINAL_SALE_EXCLUDED")

    def test_tool_executor_dispatch_and_audit(self):
        # Test helpdesk mutation formatting
        res = execute_helpdesk_tool.main(
            ticket_id="TICK-AUDIT-001",
            department="Billing",
            confidence=0.96,
            urgency_level="CRITICAL",
            urgency_score=3,
            kill_switch_triggered=True,
            assigned_queue="VIP_ESCALATIONS",
            applied_tags=["BILLING", "VIP", "URGENT"],
            sla_minutes=15,
            requires_human_approval=True,
            sentiment_compound=-0.8,
            refund_intent_detected=True,
            refund_order_id="#84920",
            return_eligible=True,
            trigger_keywords=["lawyer"],
            customer_tier="VIP",
            mock_mode=True
        )

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["priority"], "urgent")
        self.assertEqual(res["assigned_queue"], "VIP_ESCALATIONS")
        self.assertTrue(res["human_review_required"])
        self.assertTrue(res["slack_alert_sent"])
        self.assertTrue(res["audit_logged"])
        self.assertIn("update_helpdesk_ticket", res["dispatch_payload"]["tool"])

if __name__ == "__main__":
    unittest.main()

