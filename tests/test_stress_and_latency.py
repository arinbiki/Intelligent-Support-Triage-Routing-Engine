import unittest
import time
import sys
import os
import json

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "windmill", "f", "econ_support_triage")
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))

import delighted_script

DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "golden_support_tickets_1000.json")

class TestStressAndLatency(unittest.TestCase):

    def setUp(self):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            self.tickets = json.load(f)
        # Warmup engine model bundle into memory
        delighted_script.main("WARMUP", "Warmup ticket", "Standard")

    def test_sub_15ms_latency_and_throughput(self):
        latencies = []
        start_batch = time.perf_counter()

        for t in self.tickets:
            t_start = time.perf_counter()
            res = delighted_script.main(
                ticket_id=t["id"],
                text=t["text"],
                customer_tier=t["customer_tier"]
            )
            t_elapsed = (time.perf_counter() - t_start) * 1000.0 # ms
            latencies.append(t_elapsed)

        total_batch_time = time.perf_counter() - start_batch
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p50 = latencies_sorted[int(n * 0.50)]
        p90 = latencies_sorted[int(n * 0.90)]
        p99 = latencies_sorted[int(n * 0.99)]
        avg_latency = sum(latencies) / n
        throughput = n / total_batch_time

        print(f"\n" + "=" * 60)
        print(f"STRESS & LATENCY BENCHMARK ({n} SUPPORT TICKETS)")
        print(f"=" * 60)
        print(f"• Total Execution Time : {total_batch_time:.3f} seconds")
        print(f"• Average Latency      : {avg_latency:.3f} ms / ticket")
        print(f"• Median (P50) Latency : {p50:.3f} ms")
        print(f"• 90th Percentile (P90): {p90:.3f} ms")
        print(f"• 99th Percentile (P99): {p99:.3f} ms")
        print(f"• Engine Throughput    : {throughput:.1f} tickets / second")
        print(f"=" * 60)

        # Assert sub-15ms average latency for Zero-LLM predictability
        self.assertLess(avg_latency, 15.0, f"Average latency ({avg_latency:.2f}ms) exceeds 15ms target!")

if __name__ == "__main__":
    unittest.main()
