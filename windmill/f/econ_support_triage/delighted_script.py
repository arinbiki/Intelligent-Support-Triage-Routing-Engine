import re
import os
import json
import time

# Attempt to import NLP dependencies with safe fallbacks
try:
    import pickle
    HAS_PICKLE = True
except ImportError:
    HAS_PICKLE = False

try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    VADER_ANALYZER = SentimentIntensityAnalyzer()
except Exception:
    VADER_ANALYZER = None

# Global model cache to avoid reloading on each execution
_CACHED_MODEL_BUNDLE = None

KILL_SWITCH_KEYWORDS = [
    "lawyer", "attorney", "legal action", "chargeback", "bbb",
    "better business bureau", "fraud", "scam", "sue", "police",
    "unacceptable", "stolen", "dispute", "lawsuit", "small claims"
]

ELEVATED_KEYWORDS = [
    "broken", "damaged", "angry", "horrible", "disappointed",
    "furious", "ruined", "useless", "terrible", "worst", "shattered",
    "missing", "stuck", "fail", "failed", "crash"
]

REFUND_PATTERNS = [
    r"\b(?:want|need|demand|request|ask for|give me)\b.*?\b(?:refund|money back|reimbursement)\b",
    r"\b(?:cancel|cancelled)\b.*?\b(?:order|subscription)\b.*?\b(?:refund|money back)\b",
    r"\b(?:double|duplicate|unauthorized)\b.*?\b(?:charge|charged|billing|transaction)\b",
    r"\b(?:return|returned)\b.*?\b(?:package|item|product|box)\b.*?\b(?:refund|credit)\b",
    r"\brefund\s+(?:the\s+difference|my\s+money|immediately|order|full|payment)\b",
    r"\b(?:chargeback|credit card fraud|unauthorized transaction)\b"
]

def load_model_bundle():
    global _CACHED_MODEL_BUNDLE
    if _CACHED_MODEL_BUNDLE is not None:
        return _CACHED_MODEL_BUNDLE

    # Search known paths for model bundle
    search_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "department_classifier.pkl"),
        os.path.join(os.getcwd(), "models", "department_classifier.pkl"),
        "D:\\web project\\Ecommerce\\Intelligent Support Triage & Routing Engine\\models\\department_classifier.pkl",
        "/tmp/department_classifier.pkl"
    ]

    for p in search_paths:
        norm_p = os.path.abspath(p)
        if os.path.exists(norm_p):
            try:
                with open(norm_p, "rb") as f:
                    _CACHED_MODEL_BUNDLE = pickle.load(f)
                    return _CACHED_MODEL_BUNDLE
            except Exception:
                continue

    return None

def fallback_heuristic_classification(text: str):
    """
    Deterministic rule-based fallback if ML pickle is not available in environment.
    Guarantees 100% uptime and predictability.
    """
    t = text.lower()
    scores = {"Billing": 0.0, "Fulfillment": 0.0, "Technical": 0.0, "General": 0.0}

    billing_kw = ["charge", "refund", "credit card", "invoice", "vat", "receipt", "payment", "fee", "cost", "billed", "bank", "statement"]
    fulfillment_kw = ["tracking", "delivery", "package", "shipped", "carrier", "fedex", "ups", "dhl", "usps", "transit", "address", "delay", "arrived"]
    technical_kw = ["checkout", "button", "login", "password", "crash", "error", "404", "500", "app", "website", "bug", "token", "2fa", "code"]
    general_kw = ["wholesale", "size", "sizing", "store", "warranty", "vegan", "restock", "discount", "material", "australia", "corporate"]

    for kw in billing_kw:
        if kw in t: scores["Billing"] += 1.0
    for kw in fulfillment_kw:
        if kw in t: scores["Fulfillment"] += 1.0
    for kw in technical_kw:
        if kw in t: scores["Technical"] += 1.0
    for kw in general_kw:
        if kw in t: scores["General"] += 1.0

    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]
    total_score = sum(scores.values()) or 1.0
    conf = min(0.98, max(0.65, max_score / total_score)) if max_score > 0 else 0.50
    return best_cat, conf

def calculate_vader_sentiment(text: str):
    """
    Deterministic sentiment analysis via VADER with rule-based fallback.
    """
    if VADER_ANALYZER is not None:
        scores = VADER_ANALYZER.polarity_scores(text)
        return scores
    
    # Built-in lightweight dictionary fallback if nltk not installed
    t = text.lower()
    neg_count = sum(1 for w in ELEVATED_KEYWORDS + KILL_SWITCH_KEYWORDS if w in t)
    pos_count = sum(1 for w in ["great", "love", "thanks", "excellent", "awesome", "perfect", "good"] if w in t)
    
    if neg_count > pos_count:
        compound = -min(0.95, neg_count * 0.25)
        return {"compound": compound, "pos": 0.0, "neg": 0.6, "neu": 0.4}
    elif pos_count > neg_count:
        compound = min(0.95, pos_count * 0.25)
        return {"compound": compound, "pos": 0.6, "neg": 0.0, "neu": 0.4}
    return {"compound": 0.0, "pos": 0.1, "neg": 0.1, "neu": 0.8}

def main(
    ticket_id: str,
    text: str,
    customer_tier: str = "Standard",
    extracted_order_ids: list = None,
    channel: str = "email"
) -> dict:
    """
    The Heuristic Brain (Zero-LLM Autonomous Support Triage)
    Executes department classification, VADER sentiment, kill-switch urgency,
    and refund intent detection in < 15ms.
    """
    start_time = time.perf_counter()
    extracted_order_ids = extracted_order_ids or []
    clean_text = text.strip()
    lower_text = clean_text.lower()

    # 1. Department Classification (TF-IDF + Calibrated Linear Classifier)
    model_bundle = load_model_bundle()
    if model_bundle is not None and "pipeline" in model_bundle:
        pipeline = model_bundle["pipeline"]
        probs = pipeline.predict_proba([clean_text])[0]
        classes = pipeline.classes_
        best_idx = probs.argmax()
        department = str(classes[best_idx])
        confidence = float(probs[best_idx])
    else:
        department, confidence = fallback_heuristic_classification(clean_text)

    confidence_meets_threshold = bool(confidence >= 0.85)

    # 2. Urgency & Sentiment Scoring (VADER + Heuristic Overlay)
    sentiment = calculate_vader_sentiment(clean_text)
    compound = sentiment.get("compound", 0.0)

    # Check for Kill-Switch trigger words
    kill_switch_triggers = [kw for kw in KILL_SWITCH_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text)]
    elevated_triggers = [kw for kw in ELEVATED_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text)]

    kill_switch_active = len(kill_switch_triggers) > 0
    
    if kill_switch_active or compound <= -0.6:
        urgency_score = 3
        urgency_level = "CRITICAL"
    elif len(elevated_triggers) > 0 or compound <= -0.3:
        urgency_score = 2
        urgency_level = "ELEVATED"
    elif compound >= 0.3:
        urgency_score = 0
        urgency_level = "LOW"
    else:
        urgency_score = 1
        urgency_level = "NORMAL"

    # 3. Refund Intent Detection (Syntactic & Weighted Rules)
    detected_phrases = []
    for pattern in REFUND_PATTERNS:
        matches = re.findall(pattern, lower_text)
        if matches:
            detected_phrases.extend(matches)

    refund_detected = len(detected_phrases) > 0 or "refund" in lower_text
    refund_confidence = 0.95 if len(detected_phrases) > 0 else (0.80 if "refund" in lower_text else 0.0)

    # Associate order ID
    order_id_match = extracted_order_ids[0] if extracted_order_ids else None
    if not order_id_match:
        found_orders = re.findall(r"#\d{4,6}", clean_text)
        if found_orders:
            order_id_match = found_orders[0]

    # 4. Route Decision & Queue Assignment
    applied_tags = [department.upper(), f"URGENCY_{urgency_level}", customer_tier.upper()]
    sla_minutes = 120

    if kill_switch_active:
        applied_tags.append("KILL_SWITCH_TRIGGERED")
    if refund_detected:
        applied_tags.append("REFUND_REQUESTED")
    if urgency_score == 3 or compound <= -0.5:
        applied_tags.append("URGENT")
        sla_minutes = 15
    elif urgency_score == 2:
        sla_minutes = 60

    # Determine recommended queue and state
    if customer_tier.upper() == "VIP" and urgency_score == 3:
        recommended_queue = "VIP_ESCALATIONS"
        requires_human_approval = True
    elif urgency_score == 3 or kill_switch_active:
        recommended_queue = "URGENT_ESCALATIONS"
        requires_human_approval = False
    elif not confidence_meets_threshold:
        recommended_queue = "HUMAN_TRIAGE"
        requires_human_approval = True
        applied_tags.append("LOW_CONFIDENCE_GATE")
    else:
        recommended_queue = f"{department}_Team"
        requires_human_approval = False

    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    return {
        "ticket_id": ticket_id,
        "department": department,
        "confidence": round(confidence, 4),
        "confidence_meets_threshold": confidence_meets_threshold,
        "sentiment": {
            "compound": round(compound, 4),
            "negative": round(sentiment.get("neg", 0.0), 3),
            "neutral": round(sentiment.get("neu", 0.0), 3),
            "positive": round(sentiment.get("pos", 0.0), 3)
        },
        "urgency": {
            "score": urgency_score,
            "level": urgency_level,
            "kill_switch_triggered": kill_switch_active,
            "trigger_keywords": kill_switch_triggers
        },
        "refund_intent": {
            "detected": refund_detected,
            "confidence": round(refund_confidence, 2),
            "order_id": order_id_match,
            "phrases": detected_phrases[:3]
        },
        "routing": {
            "assigned_queue": recommended_queue,
            "sla_minutes": sla_minutes,
            "applied_tags": applied_tags,
            "requires_human_approval": requires_human_approval
        },
        "execution_telemetry": {
            "latency_ms": latency_ms,
            "architecture": "Zero-LLM Deterministic Engine"
        }
    }
