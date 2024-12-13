
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

print("Directory exists:", os.path.exists("C:\\Users\\tripp\\Documents\\Repos\\DCS\\src"))
print("Contents of src:", os.listdir("C:\\Users\\tripp\\Documents\\Repos\\DCS\\src"))

from moto import mock_aws
import pytest
from src.fault_injection import FaultInjection
from botocore.exceptions import ClientError
import boto3



@mock_aws
def test_fault_injection():
    with pytest.raises(ClientError):
        FaultInjection.simulate_error()

@mock_aws
def test_upload_to_non_existent_bucket():
    s3 = boto3.client("s3")
    with pytest.raises(s3.exceptions.NoSuchBucket):
        s3.put_object(Bucket="non-existent-bucket", Key="test-key", Body="This will fail.")
