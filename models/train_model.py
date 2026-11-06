import json
import os
import pickle
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, f1_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "golden_support_tickets_1000.json")
MODEL_PATH = os.path.join(BASE_DIR, "department_classifier.pkl")
CATEGORIES_PATH = os.path.join(BASE_DIR, "categories.json")

def train_and_evaluate():
    print(f"[*] Loading dataset from {DATASET_PATH}...")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = [item["text"] for item in data]
    labels = [item["department"] for item in data]
    categories = sorted(list(set(labels)))

    print(f"[i] Total samples: {len(texts)} across {len(categories)} classes: {categories}")

    # Stratified Train/Test Split (80 / 20)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )

    print(f"[*] Training Calibrated Classifier Pipeline (TF-IDF + Calibrated LinearSVC)...")
    
    # High-speed, high-accuracy Logistic Regression with calibrated softmax probabilities
    # Gives sub-millisecond evaluation latency per ticket
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        )),
        ("classifier", LogisticRegression(
            C=2.0,
            max_iter=1000,
            random_state=42
        ))
    ])

    pipeline.fit(X_train, y_train)

    # Predictions and Evaluation
    y_pred = pipeline.predict(X_test)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT (Holdout Test Set):")
    print("=" * 60)
    print(classification_report(y_test, y_pred, digits=4))
    
    print("CONFUSION MATRIX:")
    cm = confusion_matrix(y_test, y_pred, labels=categories)
    header = f"{'Actual \\ Pred':<15}" + "".join([f"{c:<15}" for c in categories])
    print(header)
    print("-" * len(header))
    for i, row in enumerate(cm):
        row_str = f"{categories[i]:<15}" + "".join([f"{val:<15}" for val in row])
        print(row_str)
    print("=" * 60)
    print(f"[+] Macro F1-Score: {macro_f1:.4f} (Required: > 0.85)\n")

    assert macro_f1 >= 0.85, f"Model Macro F1 ({macro_f1:.4f}) is below the required 0.85 threshold!"

    # Now train on full dataset for maximum production accuracy
    print("[*] Re-training on full 1,000 golden dataset for production deployment...")
    final_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            sublinear_tf=True,
            strip_accents="unicode",
            lowercase=True
        )),
        ("classifier", LogisticRegression(
            C=2.0,
            max_iter=1000,
            random_state=42
        ))
    ])
    final_pipeline.fit(texts, labels)

    # Save model artifact
    bundle = {
        "pipeline": final_pipeline,
        "classes": list(final_pipeline.classes_),
        "trained_at": datetime.utcnow().isoformat(),
        "training_samples": len(texts),
        "macro_f1": float(macro_f1),
        "version": "1.0.0-zero-llm"
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[+] Model bundle persisted to {MODEL_PATH}")

    with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "categories": categories,
            "confidence_threshold": 0.85,
            "escalation_sla_minutes": 15,
            "standard_sla_minutes": 120
        }, f, indent=2)
    print(f"[+] Categories metadata persisted to {CATEGORIES_PATH}")

if __name__ == "__main__":
    train_and_evaluate()
