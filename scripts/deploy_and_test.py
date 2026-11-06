import os
import sys
import json
import subprocess
import time

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VENV_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")

def run_step(description, cmd, cwd=PROJECT_DIR):
    print(f"\n{'='*70}\n[STEP] {description}\n{'='*70}")
    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(f"[STDERR] {res.stderr.strip()}")
    print(f"[STATUS] Code {res.returncode} in {elapsed:.2f}s")
    return res.returncode == 0

def main():
    print("""
========================================================================
   INTELLIGENT SUPPORT TRIAGE & ROUTING ENGINE (ZERO-LLM PIPELINE)
   Production Verification & Certification Runner
========================================================================
    """)

    # 1. Database Init
    ok1 = run_step("Initializing Database & Mock ERP Orders", f'"{VENV_PYTHON}" database/init_db.py')

    # 2. Model Training & Evaluation
    ok2 = run_step("Training Department Classifier & Evaluating Pipeline", f'"{VENV_PYTHON}" models/train_model.py')

    # 3. Unit & Integration Test Suite
    ok3 = run_step("Running Automated Unit & Integration Tests", f'"{VENV_PYTHON}" -m unittest discover -s tests')

    # 4. Golden Dataset Evaluation
    ok4 = run_step("Benchmarking Against 1,000 Historical Golden Support Tickets", f'"{VENV_PYTHON}" tests/golden_dataset_eval.py')

    # 5. Windmill Flow Execution
    ok5 = run_step("Executing Live Flow on Windmill Instance (http://localhost:8080)", 'wmill flow run f/econ_support_triage/support_triage_flow -d "{\\"ticket_id\\":\\"CERT-RUN-001\\",\\"text\\":\\"Where is my package? The tracking number 1Z9999999999999999 has been delayed for 4 days.\\",\\"customer_tier\\":\\"Standard\\"}"')

    all_passed = ok1 and ok2 and ok3 and ok4 and ok5

    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL CERTIFICATION CHECKS PASSED: SYSTEM READY FOR SHIPMENT!")
    else:
        print("❌ ONE OR MORE CHECKS FAILED. REVIEW LOGS ABOVE.")
    print(f"{'='*70}\n")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

