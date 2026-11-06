import json
import os
import sys
from sklearn.metrics import classification_report, confusion_matrix, f1_score

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "windmill", "f", "econ_support_triage")
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import delighted_script

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "golden_support_tickets_1000.json")

def evaluate_golden_dataset():
    print(f"[*] Loading Golden Dataset from {DATASET_PATH}...")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    y_true = [t["department"] for t in tickets]
    y_pred = []
    confidences = []
    kill_switch_counts = 0
    refund_counts = 0

    print(f"[*] Running {len(tickets)} support tickets through Heuristic Brain...")
    for t in tickets:
        res = delighted_script.main(
            ticket_id=t["id"],
            text=t["text"],
            customer_tier=t["customer_tier"]
        )
        y_pred.append(res["department"])
        confidences.append(res["confidence"])
        if res["urgency"]["kill_switch_triggered"]:
            kill_switch_counts += 1
        if res["refund_intent"]["detected"]:
            refund_counts += 1

    categories = sorted(list(set(y_true)))
    macro_f1 = f1_score(y_true, y_pred, average="macro")

    print("\n" + "=" * 65)
    print("GOLDEN DATASET EVALUATION REPORT (1,000 HISTORICAL TICKETS)")
    print("=" * 65)
    print(classification_report(y_true, y_pred, digits=4))
    
    print("CONFUSION MATRIX:")
    cm = confusion_matrix(y_true, y_pred, labels=categories)
    header = f"{'Actual \\ Pred':<15}" + "".join([f"{c:<15}" for c in categories])
    print(header)
    print("-" * len(header))
    for i, row in enumerate(cm):
        row_str = f"{categories[i]:<15}" + "".join([f"{val:<15}" for val in row])
        print(row_str)

    avg_conf = sum(confidences) / len(confidences)
    print("=" * 65)
    print(f"• Macro F1-Score        : {macro_f1:.4f} (Target: > 0.85)")
    print(f"• Average Model Confidence: {avg_conf*100:.2f}%")
    print(f"• Kill-Switches Flagged : {kill_switch_counts} tickets")
    print(f"• Refund Intents Handled : {refund_counts} tickets")
    print("=" * 65)

    assert macro_f1 >= 0.85, f"Macro F1 ({macro_f1:.4f}) is below the required 0.85 threshold!"
    print("[+] Golden dataset benchmark passed with flying colors!")

if __name__ == "__main__":
    evaluate_golden_dataset()

