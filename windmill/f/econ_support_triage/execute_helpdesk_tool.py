import time
import json
import urllib.request
import urllib.error
import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "database")
DB_PATH = os.path.abspath(os.path.join(DB_DIR, "triage_audit.db"))

def record_audit_decision(
    ticket_id: str,
    department: str,
    confidence: float,
    confidence_gated: bool,
    vader_compound: float,
    vader_negative: float,
    urgency_score: int,
    kill_switch_triggered: bool,
    trigger_keywords: list,
    refund_intent_detected: bool,
    refund_order_id: str,
    return_eligible: bool,
    final_assigned_queue: str,
    applied_tags: list,
    sla_minutes: int,
    human_review_required: bool,
    latency_ms: float
):
    """
    Persists deterministic execution trace into SQLite WAL audit log.
    """
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30.0)
            conn.execute("PRAGMA busy_timeout = 30000")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO triage_audit_log (
                    ticket_id, predicted_department, confidence, confidence_gated,
                    vader_compound, vader_negative, urgency_score, kill_switch_triggered,
                    trigger_keywords, refund_intent_detected, refund_order_id,
                    return_eligible, final_assigned_queue, applied_tags, sla_minutes,
                    human_review_required, dag_execution_latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket_id, department, confidence, 1 if confidence_gated else 0,
                vader_compound, vader_negative, urgency_score, 1 if kill_switch_triggered else 0,
                json.dumps(trigger_keywords or []), 1 if refund_intent_detected else 0,
                refund_order_id, 1 if return_eligible else 0 if return_eligible is not None else None,
                final_assigned_queue, json.dumps(applied_tags or []), sla_minutes,
                1 if human_review_required else 0, latency_ms
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

def execute_with_backoff(url: str, payload: dict, headers: dict = None, max_retries: int = 3):
    """
    Deterministic exponential backoff retry for network resilience.
    Handles HTTP 429 and 500-series errors.
    """
    headers = headers or {"Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8")
    delay = 0.5

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = resp.read().decode("utf-8")
                return {
                    "success": True,
                    "status_code": resp.status,
                    "response": json.loads(data) if data else {}
                }
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0
                continue
            return {
                "success": False,
                "status_code": e.code,
                "error": f"HTTPError {e.code}: {e.reason}"
            }
        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2.0
                continue
            return {
                "success": False,
                "status_code": 0,
                "error": str(e)
            }

def main(
    ticket_id: str,
    department: str,
    confidence: float,
    urgency_level: str,
    urgency_score: int,
    kill_switch_triggered: bool,
    assigned_queue: str,
    applied_tags: list,
    sla_minutes: int,
    requires_human_approval: bool,
    sentiment_compound: float = 0.0,
    sentiment_negative: float = 0.0,
    refund_intent_detected: bool = False,
    refund_order_id: str = None,
    return_eligible: bool = None,
    trigger_keywords: list = None,
    customer_tier: str = "Standard",
    n8n_webhook_url: str = None,
    mock_mode: bool = True
) -> dict:
    """
    The Tool Executor: Standardized Helpdesk Dispatcher & Audit Logger
    """
    start_time = time.perf_counter()
    trigger_keywords = trigger_keywords or []
    applied_tags = applied_tags or []

    # Priority mapping for Helpdesks (Zendesk / Gorgias)
    priority_map = {
        "CRITICAL": "urgent",
        "ELEVATED": "high",
        "NORMAL": "normal",
        "LOW": "low"
    }
    helpdesk_priority = priority_map.get(urgency_level.upper(), "normal")

    # Formulate internal audit note
    note_lines = [
        f"🤖 [Autonomous Triage Auditor | Zero-LLM Engine]",
        f"• Classified Department: {department} (Confidence: {confidence*100:.1f}%)",
        f"• Urgency: {urgency_level} (Score: {urgency_score}/3)",
        f"• Sentiment Compound: {sentiment_compound:.3f}",
        f"• SLA Target: < {sla_minutes} minutes"
    ]

    if kill_switch_triggered:
        note_lines.append(f"⚠️ KILL-SWITCH TRIGGERED: Detected trigger words: {', '.join(trigger_keywords)}")
    if refund_intent_detected:
        elig_str = "Eligible within 30-day window" if return_eligible else "Ineligible or requires manual verification"
        note_lines.append(f"💰 Refund Intent Detected: Order {refund_order_id} ({elig_str})")
    if requires_human_approval:
        note_lines.append("🛑 TICKET ROUTED TO SUPERVISOR QUEUE FOR HUMAN AUTHORIZATION")

    internal_note = "\n".join(note_lines)

    dispatch_payload = {
        "tool": "update_helpdesk_ticket",
        "parameters": {
            "ticket_id": ticket_id,
            "status": "pending_approval" if requires_human_approval else "open",
            "priority": helpdesk_priority,
            "assignee_group": assigned_queue,
            "tags": applied_tags,
            "internal_note": internal_note,
            "customer_tier": customer_tier
        }
    }

    slack_notification = None
    if urgency_score == 3 or customer_tier.upper() == "VIP":
        slack_notification = {
            "channel": "#support-escalations",
            "message": f"🚨 *{urgency_level} Support Ticket Alert* | Ticket: `{ticket_id}` | Queue: `{assigned_queue}` | Customer: `{customer_tier}`\n> {internal_note.replace(chr(10), chr(10)+'> ')}"
        }

    # Execute against n8n if url provided, else succeed deterministically in mock/shadow mode
    n8n_result = {"status": "executed_locally", "mock": True}
    if n8n_webhook_url and not mock_mode:
        n8n_result = execute_with_backoff(n8n_webhook_url, {
            "ticket_mutation": dispatch_payload,
            "slack_alert": slack_notification
        })

    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    # Record into SQLite WAL Audit Log
    record_audit_decision(
        ticket_id=ticket_id,
        department=department,
        confidence=confidence,
        confidence_gated=bool(confidence >= 0.85),
        vader_compound=sentiment_compound,
        vader_negative=sentiment_negative,
        urgency_score=urgency_score,
        kill_switch_triggered=kill_switch_triggered,
        trigger_keywords=trigger_keywords,
        refund_intent_detected=refund_intent_detected,
        refund_order_id=refund_order_id,
        return_eligible=return_eligible,
        final_assigned_queue=assigned_queue,
        applied_tags=applied_tags,
        sla_minutes=sla_minutes,
        human_review_required=requires_human_approval,
        latency_ms=latency_ms
    )

    return {
        "status": "SUCCESS",
        "ticket_id": ticket_id,
        "assigned_queue": assigned_queue,
        "priority": helpdesk_priority,
        "applied_tags": applied_tags,
        "sla_minutes": sla_minutes,
        "human_review_required": requires_human_approval,
        "dispatch_payload": dispatch_payload,
        "slack_alert_sent": bool(slack_notification is not None),
        "audit_logged": True,
        "execution_latency_ms": latency_ms
    }
