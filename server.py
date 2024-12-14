import threading
from prometheus_client import start_http_server, Summary, Counter
import time

# Define metrics
operation_latency = Summary("s3_operation_latency_seconds", "Latency of S3 operations")
operation_successes = Counter("s3_operation_successes_total", "Total successful S3 operations")

# Start the metrics server in a separate thread
def start_metrics_server():
    start_http_server(8000)
    print("Prometheus metrics server running on http://localhost:8000/metrics")
    while True:
        time.sleep(1)  # Keep the thread alive

metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
metrics_thread.start()

# Simulate other operations
def simulate_operations():
    while True:
        with operation_latency.time():
            try:
                # Simulated successful operation
                operation_successes.inc()
                time.sleep(1)  # Simulate operation time
            except Exception as e:
                print(f"Operation failed: {e}")

if __name__ == "__main__":
    simulate_operations()
