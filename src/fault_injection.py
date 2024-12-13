from botocore.exceptions import ClientError

class FaultInjection:
    @staticmethod
    def simulate_error():
        raise ClientError(
            {"Error": {"Code": "503", "Message": "Service Unavailable"}},
            "GetObject"
        )
