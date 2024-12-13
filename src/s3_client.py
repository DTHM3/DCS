import boto3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        self.s3 = boto3.client('s3')

    def upload_file(self, bucket, key, file_path):
        self.s3.upload_file(file_path, bucket, key)

    def download_file(self, bucket, key, file_path):
        self.s3.download_file(bucket, key, file_path)

    def get_object(self, bucket, key):
        try:
            return self.s3.get_object(Bucket=bucket, Key=key)
        except Exception as e:
            logger.error(f"Failed to get object: {e}")
            raise