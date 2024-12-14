import sys
import os
import time
from statistics import mean

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import pytest
from src.s3_client import S3Client
from src.fault_injection import FaultInjection
from botocore.exceptions import ClientError
from moto import mock_aws
import boto3

from prometheus_client import Summary, Counter, start_http_server, REGISTRY
from statistics import mean

def clear_prometheus_registry():
    for collector in list(REGISTRY._names_to_collectors.values()):
        REGISTRY.unregister(collector)

# Metrics dictionary
metrics = {
    "success_count": 0,
    "failure_count": 0,
    "latencies": [],
}

start_http_server(8000)

# Define Prometheus metrics
operation_latency = Summary("s3_operation_latency_seconds", "Latency of S3 operations")
operation_successes = Counter("s3_operation_successes_total", "Total successful S3 operations")
operation_failures = Counter("s3_operation_failures_total", "Total failed S3 operations")


@mock_aws
def test_s3_mocked_upload():
    s3 = boto3.client("s3")
    s3.create_bucket(Bucket="mock-bucket")

    with operation_latency.time():  # Track operation latency
        try:
            # Create a test file
            with open("test.txt", "w") as f:
                f.write("This is a test file.")

            # Upload the file
            s3.upload_file("test.txt", "mock-bucket", "test-key")

            # Clean up the file
            os.remove("test.txt")
            operation_successes.inc()  # Increment success counter
        except Exception:
            operation_failures.inc()  # Increment failure counter

@mock_aws
def test_reliability_of_upload():
    s3 = boto3.client("s3")
    bucket = "reliability-test-bucket"
    key = "test-key"

    with operation_latency.time():
        try:
            # Create a mock bucket
            s3.create_bucket(Bucket=bucket)

            # Upload a file
            s3.put_object(Bucket=bucket, Key=key, Body="First version of the file.")

            # Retrieve and check the file
            response = s3.get_object(Bucket=bucket, Key=key)
            assert response["Body"].read() == b"First version of the file."

            # Overwrite the file
            s3.put_object(Bucket=bucket, Key=key, Body="Updated version of the file.")

            # Retrieve and check the updated file
            response = s3.get_object(Bucket=bucket, Key=key)
            assert response["Body"].read() == b"Updated version of the file."

            operation_successes.inc()
        except Exception:
            operation_failures.inc()

def test_s3_get_object():
    s3_client = S3Client()
    bucket = "test-bucket"
    key = "test-key"

    # Normal case (requires a mock S3 bucket or live bucket)
    try:
        response = s3_client.get_object(bucket, key)
        assert response is not None
    except ClientError:
        pytest.skip("AWS credentials or bucket not configured.")

def test_fault_injection():
    with pytest.raises(ClientError):
        FaultInjection.simulate_error()

@mock_aws
def test_file_locations():
    s3 = boto3.client("s3", region_name="us-east-1")
    bucket_1 = "bucket-east"
    bucket_2 = "bucket-west"
    key_1 = "path/to/file1.txt"
    key_2 = "path/to/file2.txt"

    # Create buckets in different "locations"
    s3.create_bucket(Bucket=bucket_1)
    s3.create_bucket(Bucket=bucket_2)

    # Upload files to different buckets
    s3.put_object(Bucket=bucket_1, Key=key_1, Body="File in east bucket.")
    s3.put_object(Bucket=bucket_2, Key=key_2, Body="File in west bucket.")

    # Verify file in bucket_1
    response_1 = s3.get_object(Bucket=bucket_1, Key=key_1)
    assert response_1["Body"].read() == b"File in east bucket."

    # Verify file in bucket_2
    response_2 = s3.get_object(Bucket=bucket_2, Key=key_2)
    assert response_2["Body"].read() == b"File in west bucket."

@mock_aws
def test_region_specific_behavior():
    # Create an S3 client for two regions
    s3_us_east = boto3.client("s3", region_name="us-east-1")
    s3_eu_west = boto3.client("s3", region_name="eu-west-1")

    # Create buckets in respective regions
    s3_us_east.create_bucket(Bucket="us-east-bucket")  # Default region, no config needed
    s3_eu_west.create_bucket(
        Bucket="eu-west-bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    # Upload files to respective buckets
    s3_us_east.put_object(Bucket="us-east-bucket", Key="file1.txt", Body="File in US East.")
    s3_eu_west.put_object(Bucket="eu-west-bucket", Key="file2.txt", Body="File in EU West.")

    # Retrieve files and verify content
    response_us = s3_us_east.get_object(Bucket="us-east-bucket", Key="file1.txt")
    assert response_us["Body"].read() == b"File in US East."

    response_eu = s3_eu_west.get_object(Bucket="eu-west-bucket", Key="file2.txt")
    assert response_eu["Body"].read() == b"File in EU West."

@mock_aws
def test_overwrite_detection():
    s3 = boto3.client("s3")
    bucket = "test-bucket"
    key = "test-key"

    # Create a bucket and upload a file
    s3.create_bucket(Bucket=bucket)
    s3.put_object(Bucket=bucket, Key=key, Body="Original content.")

    # Check the file's content
    response = s3.get_object(Bucket=bucket, Key=key)
    assert response["Body"].read() == b"Original content."

    # Overwrite the file
    s3.put_object(Bucket=bucket, Key=key, Body="Updated content.")

    # Verify updated content
    response = s3.get_object(Bucket=bucket, Key=key)
    assert response["Body"].read() == b"Updated content."

@mock_aws
def test_list_objects():
    s3 = boto3.client("s3")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    # Upload multiple files
    s3.put_object(Bucket=bucket, Key="file1.txt", Body="Content of file1.")
    s3.put_object(Bucket=bucket, Key="file2.txt", Body="Content of file2.")

    # List objects in the bucket
    response = s3.list_objects(Bucket=bucket)
    keys = [obj["Key"] for obj in response.get("Contents", [])]

    assert "file1.txt" in keys
    assert "file2.txt" in keys

def analyze_metrics():
    total_operations = metrics["success_count"] + metrics["failure_count"]
    success_rate = (metrics["success_count"] / total_operations) * 100 if total_operations > 0 else 0
    avg_latency = mean(metrics["latencies"]) if metrics["latencies"] else 0

    print("\n=== Metrics Analysis ===")
    print(f"Total Operations: {total_operations}")
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print(f"Failures: {metrics['failure_count']}")

analyze_metrics()