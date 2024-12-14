import boto3
import time
import uuid
from prometheus_client import Summary, Counter, start_http_server

# Start Prometheus metrics server
start_http_server(8000)

# Define Prometheus metrics
operation_latency = Summary("s3_operation_latency_seconds", "Latency of S3 operations")
operation_successes = Counter("s3_operation_successes_total", "Total successful S3 operations")
operation_failures = Counter("s3_operation_failures_total", "Total failed S3 operations")

# Enable boto3 debugging
import logging
boto3.set_stream_logger('boto3', level=logging.DEBUG)

# Results dictionary for latency comparison
latency_results = {}

def compare_server_latency():
    regions = [
        "us-east-1",  # US East (N. Virginia)
        "us-west-1",  # US West (N. California)
        "us-west-2",  # US West (Oregon)
        "eu-west-1",  # Europe (Ireland)
        "eu-central-1",  # Europe (Frankfurt)
        "ap-south-1",  # Asia Pacific (Mumbai)
        "ap-northeast-1",  # Asia Pacific (Tokyo)
        "ap-northeast-2",  # Asia Pacific (Seoul)
        "ap-southeast-1",  # Asia Pacific (Singapore)
        "ap-southeast-2",  # Asia Pacific (Sydney)
        "sa-east-1",  # South America (São Paulo)
        "ca-central-1",  # Canada (Central)
    ]
    key_name = "test-key"
    body_content = "This is a test for server latency."

    for region in regions:
        # Generate a unique bucket name
        bucket_name = f"latency-test-bucket-{region}-{uuid.uuid4().hex[:8]}"

        s3 = boto3.client("s3", region_name=region)

        try:
            # Create bucket with LocationConstraint if not us-east-1
            bucket_creation_start = time.time()
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )
            bucket_creation_latency = time.time() - bucket_creation_start
            operation_start = time.time()
            # Upload an object
            s3.put_object(Bucket=bucket_name, Key=key_name, Body=body_content)
            # Retrieve the object
            response = s3.get_object(Bucket=bucket_name, Key=key_name)
            assert response["Body"].read().decode("utf-8") == body_content
            operation_successes.inc()
            operation_latency_val = time.time() - operation_start

            # Store latency data
            latency_results[region] = {
                "bucket_creation_latency": bucket_creation_latency,
                "operation_latency": operation_latency_val,
            }

            print(f"Region: {region}, Bucket Creation Latency: {bucket_creation_latency:.4f}s, "
                  f"Operation Latency: {operation_latency_val:.4f}s")

        except Exception as e:
            operation_failures.inc()
            print(f"Operation failed for region {region}: {e}")

if __name__ == "__main__":
    compare_server_latency()
