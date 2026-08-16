import base64
import json
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class CloudFrontService:

    def __init__(
        self,
        domain: str,
        key_pair_id: str,
        private_key_path: str,
        cookie_ttl: int = 3600,
    ):
        self.domain = domain
        self.key_pair_id = key_pair_id
        self.cookie_ttl = cookie_ttl

        private_key = Path(private_key_path).read_bytes()

        self.private_key = serialization.load_pem_private_key(
            private_key,
            password=None,
        )

    @staticmethod
    def _encode(value: bytes) -> str:
        return (
            base64.b64encode(value)
            .decode()
            .replace("+", "-")
            .replace("=", "_")
            .replace("/", "~")
        )

    def create_signed_cookies(self):
        expires = int(time.time()) + self.cookie_ttl

        policy = {
            "Statement": [
                {
                    "Resource": f"https://{self.domain}/*",
                    "Condition": {
                        "DateLessThan": {
                            "AWS:EpochTime": expires
                        }
                    },
                }
            ]
        }

        policy_json = json.dumps(
            policy,
            separators=(",", ":"),
        )

        signature = self.private_key.sign(
            policy_json.encode(),
            padding.PKCS1v15(),
            hashes.SHA1(),
        )

        return {
            "CloudFront-Policy": self._encode(
                policy_json.encode()
            ),
            "CloudFront-Signature": self._encode(
                signature
            ),
            "CloudFront-Key-Pair-Id": self.key_pair_id,
        }