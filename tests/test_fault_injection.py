import sys
import os
import time
from statistics import mean

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

print("Directory exists:", os.path.exists("C:\\Users\\tripp\\Documents\\Repos\\DCS\\src"))
print("Contents of src:", os.listdir("C:\\Users\\tripp\\Documents\\Repos\\DCS\\src"))

from moto import mock_aws
import pytest
from src.fault_injection import FaultInjection
from botocore.exceptions import ClientError
import boto3

from prometheus_client import Summary, Counter, start_http_server, REGISTRY
from statistics import mean

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def clear_prometheus_registry():
    for collector in list(REGISTRY._names_to_collectors.values()):
        REGISTRY.unregister(collector)

# Start Prometheus metrics server
start_http_server(8000)

# Define Prometheus metrics
operation_latency = Summary("s3_operation_latency_seconds", "Latency of S3 operations")
operation_successes = Counter("s3_operation_successes_total", "Total successful S3 operations")
operation_failures = Counter("s3_operation_failures_total", "Total failed S3 operations")

@mock_aws
def test_fault_injection():
    with operation_latency.time():
        try:
            with pytest.raises(ClientError):
                FaultInjection.simulate_error()
            operation_successes.inc()
        except Exception:
            operation_failures.inc()

@mock_aws
def test_upload_to_non_existent_bucket():
    s3 = boto3.client("s3")
    with operation_latency.time():
        try:
            with pytest.raises(s3.exceptions.NoSuchBucket):
                s3.put_object(Bucket="non-existent-bucket", Key="test-key", Body="This will fail.")
            operation_successes.inc()
        except Exception:
            operation_failures.inc()
