Here is the comprehensive, enterprise-grade system design plan for the **Intelligent Support Triage & Routing Engine** using a strict **Zero-LLM Architecture**. 

By stripping away probabilistic LLMs and replacing them with deterministic Directed Acyclic Graphs (DAGs), traditional NLP, and heuristic state machines, we achieve near-zero latency, absolute predictability, and enterprise-level security.

---

# 1. High-Level Architecture & Component Mapping

In this Zero-LLM agentic loop, the system is divided strictly into four domains based on your methodology:

*   **The Sensor (n8n):** Captures the raw support ticket, sanitizes PII, strips HTML, and extracts structured metadata (Order IDs, Email domains) via Regex.
*   **The Heuristic Brain (Windmill Scripts):** Replaces the LLM. Uses deterministic, self-hosted traditional NLP (spaCy, NLTK/VADER, Scikit-Learn) and keyword/regex scoring to classify intent, sentiment, and urgency.
*   **The Deterministic Planner (Windmill WAC/Flows):** The state machine DAG. Evaluates the confidence scores from the Brain and routes the ticket through conditional branches (Auto-route, Escalate, Suspend for Human).
*   **The Executor (n8n via MCP):** Executes the final state changes in the helpdesk (Zendesk/Gorgias) and notifies teams (Slack) using n8n's Model Context Protocol (MCP) server as a standardized tool registry.

---

# 2. Step-by-Step Build Plan

## Phase 1: The Sensor Layer (n8n Ingestion & Sanitization)
*Goal: Reliably capture high-volume webhooks and prepare clean state variables for the Brain.*

1.  **High-Availability Ingestion:**
    *   Deploy n8n in **Queue Mode** (using Redis and PostgreSQL) to ensure no webhooks are dropped during high-volume sales events or support spikes.
    *   Use a dedicated Webhook Node configured to accept JSON payloads from your helpdesk (e.g., Zendesk Webhooks, Shopify Webhooks).
2.  **Deterministic Sanitization (n8n Code Node):**
    *   *Logic:* Strip all HTML tags, decode entities, and normalize whitespace.
    *   *PII Redaction:* Apply strict Regex patterns to mask credit card numbers, phone numbers, and emails before the payload leaves n8n, ensuring compliance (GDPR/CCPA) before data hits Windmill.
3.  **Entity Extraction (n8n Code Node):**
    *   *Logic:* Use Regex to extract exact alphanumeric patterns for Order IDs (e.g., `#1000` to `#9999`) and Tracking Numbers.
    *   *Output:* Bundle the cleaned text, extracted entities, and raw metadata into a single standardized JSON state object.
4.  **Delegation:**
    *   Trigger the Windmill Flow via an HTTP Request node, passing the sanitized JSON state object as the payload.

## Phase 2: The Heuristic Brain (Windmill Python Scripts)
*Goal: Replace LLM semantic understanding with deterministic, self-hosted machine learning and NLP libraries.*

1.  **Department Classification (Scikit-Learn / TF-IDF):**
    *   *Logic:* Train a lightweight, multi-class Naive Bayes or Support Vector Machine (SVM) model offline using historical ticket data (e.g., Billing vs. Fulfillment vs. Technical).
    *   *Execution:* The Windmill Python script loads the pre-trained `.pkl` model and TF-IDF vectorizer into memory. It transforms the incoming ticket text and outputs a deterministic category and a mathematical probability score (0.0 to 1.0).
2.  **Urgency & Sentiment Scoring (VADER / Keyword Engine):**
    *   *Logic:* Use the VADER (Valence Aware Dictionary and sEntiment Reasoner) library for deterministic sentiment analysis. VADER is highly optimized for social media and short-form text, requiring zero neural network overhead.
    *   *Heuristic Overlay:* Combine VADER's compound score with a strict "Kill-Switch" keyword dictionary. If the text contains absolute trigger words (e.g., "lawyer", "chargeback", "BBB", "fraud"), the script forcibly overrides the sentiment score to Maximum Urgency (Score: 3).
3.  **Refund Intent Detection (spaCy Dependency Parsing):**
    *   *Logic:* Load a lightweight `spaCy` model. Use dependency parsing to look for specific syntactic trees (e.g., Subject: "I", Verb: "want/need", Object: "refund/money back").
    *   *Fallback:* Combine with a weighted Regex boolean check to ensure high recall. Output a binary `True/False` and a confidence weight.

## Phase 3: The Deterministic Planner (Windmill WAC / DAGs)
*Goal: Orchestrate the decision tree using Flows as Code (YAML/TypeScript definitions) without any probabilistic branching.*

1.  **Flow Definition (WAC):**
    *   Define the workflow strictly as code. The DAG begins by calling the *Heuristic Brain* script.
2.  **Confidence Gating (Branching Logic):**
    *   *Condition:* Evaluate the ML model's probability score for Department Classification.
    *   *Branch A (High Confidence >= 0.85):* Proceed to auto-tagging and routing.
    *   *Branch B (Low Confidence < 0.85):* Route immediately to a "Human Triage" suspend state.
3.  **Urgency Escalation (Conditional Step):**
    *   *Condition:* If Urgency Score == 3 (Trigger words detected) OR VADER compound score < -0.5.
    *   *Action:* Append an "URGENT" flag to the state payload.
4.  **State Enrichment (API Tool Call):**
    *   *Condition:* If Refund Intent == `True`.
    *   *Action:* The DAG pauses and calls an internal Windmill script to query your ERP/Shopify database via REST API to check if the order is within the return window. It appends `return_eligible: true/false` to the state.
5.  **Human-in-the-Loop (Suspend Step):**
    *   If the ticket is flagged as High Value (VIP customer) AND Urgency == 3, the DAG hits a **Suspend Step**. It generates a unique approval URL and sends it to the Support Manager. The DAG halts execution entirely until the manager clicks "Approve Escalation" or "Downgrade".

## Phase 4: The Standardized Tool Executor (n8n MCP Server)
*Goal: Windmill acts as the brain, but uses n8n as the standardized "hands" to interact with external SaaS APIs.*

1.  **MCP Tool Discovery:**
    *   Enable the **n8n MCP Server**. Create standardized n8n workflows for actions like `Update Zendesk Ticket`, `Send Slack Alert`, and `Add Internal Note`. Expose these as MCP tools.
2.  **Windmill as the MCP Client:**
    *   In the final step of the Windmill DAG, a Python script utilizes an MCP client library to connect to the n8n MCP endpoint.
    *   *Logic:* The script dynamically queries the MCP server for available tools, selects the `update_ticket` tool, and passes the final deterministic state (Tags, Assignee ID, Priority Level).
3.  **Execution & Error Handling:**
    *   n8n receives the MCP tool call, executes the HTTP Request to the Helpdesk API, and returns a success/failure payload back to Windmill.
    *   If the API returns a 429 (Rate Limit) or 500 error, Windmill's DAG catches the error and routes it to a deterministic exponential backoff retry loop.

---

# 3. Enterprise Testing Strategy

Because this system relies on deterministic ML and heuristic rules, testing must be rigorous and mathematical.

### Step 1: The Golden Dataset (Offline Testing)
*   Export 1,000 historical, human-tagged support tickets.
*   Run the *Heuristic Brain* Python scripts locally against this dataset.
*   Generate a Confusion Matrix to measure **Precision** (did we route to the right team?) and **Recall** (did we miss any urgent tickets?).
*   *Tuning:* Adjust the TF-IDF n-grams and Regex weights until F1-score exceeds 0.85.

### Step 2: Shadow Mode Deployment (Production Testing)
*   Deploy the Windmill Flow and n8n Webhook to production, but **disable the MCP Executor node**.
*   The system will process every live ticket, calculate the deterministic routing, and write the decision to a PostgreSQL database, *without actually changing the ticket in Zendesk/Gorgias*.
*   Run this for 14 days. Compare the Windmill DAG decisions against the actual human agent actions.

### Step 3: Threshold Calibration
*   Analyze the Shadow Mode logs. If the system is sending too many billing tickets to the technical team, tighten the confidence threshold from `0.85` to `0.90` for the Billing category.
*   Once false-positive and false-negative rates are within acceptable business limits, enable the MCP Executor.

---

# 4. Production-Grade Deployment & Observability

To ensure this Zero-LLM agent operates at an enterprise scale without degrading:

### Infrastructure Isolation
*   **Windmill Worker Groups:** Create a dedicated Worker Group specifically for the *Heuristic Brain* scripts. Loading `spaCy` and `scikit-learn` models into memory is resource-intensive. Isolate these workers on high-RAM instances so they do not starve lightweight DAG execution workers.
*   **Model Caching:** Ensure the Python scripts in Windmill use global variables or Windmill's caching mechanisms to load the `.pkl` and `spaCy` models *once* per worker startup, rather than reloading them on every single ticket execution.

### Observability & Alerting
*   **DAG Telemetry:** Use Windmill’s native OpenTelemetry exports to push DAG execution times and branch frequencies to Grafana/Datadog.
*   **n8n Queue Health:** Monitor the Redis queue depth. If the queue grows beyond 500 pending jobs, trigger an alert to scale up n8n worker nodes.
*   **Concept Drift Monitoring:** Create a weekly Windmill scheduled script that samples 100 recent auto-routed tickets. If human agents are manually re-tagging more than 5% of the auto-routed tickets, trigger an alert that the heuristic model is experiencing "concept drift" (e.g., customers are using new slang for "refund") and requires retraining.

---

# Summary of the Zero-LLM Advantage

By utilizing this architecture, you completely eliminate the risks associated with LLMs:
1.  **Zero Hallucinations:** A Scikit-Learn model and Regex cannot invent facts or promise a customer a refund that doesn't exist.
2.  **Predictable Costs:** You pay only for CPU/RAM on your self-hosted Windmill/n8n servers. There are no per-token API costs.
3.  **Sub-100ms Latency:** Traditional NLP and DAG evaluation execute in milliseconds, allowing real-time ticket tagging before the customer even finishes submitting the web form.
4.  **Absolute Auditability:** Every decision is traceable to a specific Regex match, VADER score, or DAG branch, making compliance and debugging trivial.