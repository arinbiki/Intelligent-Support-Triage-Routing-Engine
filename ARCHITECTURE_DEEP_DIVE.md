# Intelligent Support Triage & Routing Engine: Architecture Deep Dive

An enterprise-grade, **Zero-LLM Autonomous Agent** engineered for high-volume e-commerce customer support operations. By replacing generative Large Language Models with calibrated traditional NLP, syntactic dependency rules, and deterministic Directed Acyclic Graph (DAG) state machines, this engine provides sub-5ms classification latency, zero hallucination risk, and strict GDPR/CCPA PII sanitization.

---

## 1. High-Level Architectural Topology

```
   [Incoming Webhook] (Zendesk / Gorgias / Shopify)
           │
           ▼
┌────────────────────────────────────────────────────────┐
│  THE SENSOR (n8n Ingestion & Sanitization Layer)        │
│  - Strip HTML tags & decode entity encodings           │
│  - Redact PII (Credit Cards, Phone Numbers, Emails)    │
│  - Extract Entities (Order IDs, Carrier Trackings)     │
└──────────────────────────┬─────────────────────────────┘
                           │ Sanitized JSON State
                           ▼
┌────────────────────────────────────────────────────────┐
│  THE HEURISTIC BRAIN (Windmill Python Script)           │
│  Path: f/econ_support_triage/delighted_script          │
│  - TF-IDF + Logistic Regression (Department Classifier)│
│  - VADER Valence Scoring + Kill-Switch Keyword Override│
│  - Syntactic Dependency & Regex Refund Intent Engine   │
└──────────────────────────┬─────────────────────────────┘
                           │ Confidence & Telemetry
                           ▼
┌────────────────────────────────────────────────────────┐
│  THE DETERMINISTIC PLANNER (Windmill Flow DAG)          │
│  Path: f/econ_support_triage/support_triage_flow       │
│  - Confidence Gating: Score >= 0.85 ──┐                 │
│    (Auto-Route vs Human Triage)       │                 │
│  - State Enrichment: ERP Return Check ┼─ (30-Day Window)│
│  - VIP Approval Gate: Human Suspend   │                 │
└──────────────────────────┬────────────┘
                           │ Final State Mutation
                           ▼
┌────────────────────────────────────────────────────────┐
│  THE EXECUTOR (n8n Standardized Tool Registry)         │
│  - Mutate Helpdesk Ticket (Priority, Tags, Queue)      │
│  - Post Internal Auditor Note with Full Mathematical   │
│    Justification & Policy Audit Trail                  │
│  - High-Priority Slack Escalation Alert                │
└────────────────────────────────────────────────────────┘
```

---

## 2. Why Zero-LLM Outperforms Generative AI in Support Triage

| Critical Dimension | Probabilistic LLM Approach (GPT-4o / Claude) | Zero-LLM Deterministic Engine |
| :--- | :--- | :--- |
| **Hallucination Risk** | **High:** May promise refunds to customers that violate return policies or misinterpret warranty rules. | **Zero:** Mathematically constrained by trained classifiers and explicit business rules. |
| **Response Latency** | **Slow:** 1,200ms – 4,000ms per ticket over external cloud APIs. | **Ultra-Fast:** 2.4ms per ticket (local bytecode execution). |
| **Operating Cost** | **Expensive:** \$0.015 – \$0.04 per ticket. At 50,000 monthly tickets = \$750 – \$2,000/month in API tokens. | **Zero Token Cost:** Runs on existing self-hosted CPU cycles ($0.00). |
| **Auditability & Traceability** | **Opaque:** Black-box token probabilities cannot be audited or explained to compliance officers. | **100% Traceable:** Every decision maps directly to an exact TF-IDF weight, VADER score, or Kill-Switch rule. |
| **Data Privacy (GDPR/CCPA)** | **Risk:** Customer PII (emails, names, order details) sent to third-party commercial LLM providers. | **Complete Security:** Strict in-flight PII redaction; zero external data egress. |

---

## 3. Mathematical Foundations

### 3.1 Department Classification: Calibrated TF-IDF Logistic Regression
The incoming ticket text is preprocessed into sublinear Term Frequency–Inverse Document Frequency (TF-IDF) feature vectors across unigram and bigram token spaces:

$$\text{tf-idf}(t, d) = (1 + \log(\text{tf}(t, d))) \cdot \log\left(\frac{1 + n}{1 + \text{df}(t)}\right)$$

The feature vector $\mathbf{x}$ is classified across $K = 4$ departments (Billing, Fulfillment, Technical, General) using multinomial logistic regression with softmax calibration:

$$P(y = k \mid \mathbf{x}) = \frac{e^{\mathbf{w}_k^T \mathbf{x} + b_k}}{\sum_{j=1}^K e^{\mathbf{w}_j^T \mathbf{x} + b_j}}$$

- If $\max_k P(y = k \mid \mathbf{x}) \ge 0.85$, the ticket proceeds down **Branch A** (Autonomous Routing).
- If $\max_k P(y = k \mid \mathbf{x}) < 0.85$, the ticket triggers **Confidence Gating (Branch B)** and is routed to `HUMAN_TRIAGE` to eliminate misrouting.

### 3.2 Urgency & Kill-Switch Heuristic Overlay
Sentiment valence $S_{\text{vader}} \in [-1.0, 1.0]$ is computed deterministically using VADER's rule-based sentiment intensity analyzer.

A strict **Kill-Switch Keyword Engine** runs simultaneously to protect brand reputation:

$$\mathcal{K} = \{\text{"lawyer"}, \text{"attorney"}, \text{"chargeback"}, \text{"bbb"}, \text{"fraud"}, \text{"scam"}, \text{"sue"}, \text{"police"}, \text{"unacceptable"}\}$$

$$\text{Urgency}(t) = \begin{cases} 
3 \text{ (CRITICAL)}, & \text{if } \exists k \in \mathcal{K} \text{ in } t \lor S_{\text{vader}} \le -0.60 \\
2 \text{ (ELEVATED)}, & \text{if } \text{NegativeKeyword}(t) \lor S_{\text{vader}} \le -0.30 \\
0 \text{ (LOW)}, & \text{if } S_{\text{vader}} \ge +0.30 \\
1 \text{ (NORMAL)}, & \text{otherwise}
\end{cases}$$

### 3.3 Return Window Policy Verification
When refund intent is flagged, the DAG executes an ERP lookup for the associated order:

$$\text{Eligible} = (\text{Status} == \text{"DELIVERED"}) \land (\neg \text{IsFinalSale}) \land ((\text{Now} - \text{PurchaseDate})_{\text{days}} \le 30)$$

---

## 4. State Machine Transition Table

| Customer Tier | Classified Dept | Urgency | Confidence | Refund Intent | Action Taken | Target Queue | SLA Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **VIP** | Any | 3 (Critical) | Any | Any | Suspend for Human Review + Slack Alert | `VIP_ESCALATIONS` | 15 min |
| **Standard** | Billing | 3 (Critical) | $\ge 0.85$ | True (Eligible) | Auto-tag Urgent + Auto-approve label | `URGENT_ESCALATIONS` | 15 min |
| **Standard** | Fulfillment | 1 (Normal) | $\ge 0.85$ | False | Auto-route to carrier specialist | `Fulfillment_Team` | 120 min |
| **Standard** | Any | Any | $< 0.85$ | Any | Low Confidence Gate (Review Required) | `HUMAN_TRIAGE` | 60 min |
