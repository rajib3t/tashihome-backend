from __future__ import annotations
from typing import Optional
from urllib.parse import urlparse
import io
import json
import logging
try:
    import boto3
    from aioboto3 import Session
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    Session = None
    class ClientError(Exception): pass
from PIL import Image, ImageOps
from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.file_validation import validate_data_url_file

logger = logging.getLogger(__name__)


class StorageService:
    """Simple S3-compatible storage service supporting AWS S3 and MinIO via endpoint URL.

    Usage: configure S3 settings in environment (.env) and inject via deps.
    """

    def __init__(self):
        self.session = Session() if Session is not None else None
        self.bucket: Optional[str] = settings.S3_BUCKET
        self.client_params = {
            "aws_access_key_id": settings.S3_ACCESS_KEY or settings.BEDROCK_AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.S3_SECRET_KEY or settings.BEDROCK_AWS_SECRET_ACCESS_KEY,
            "region_name": settings.S3_REGION or settings.BEDROCK_AWS_REGION,
        }
        if settings.S3_ENDPOINT_URL:
            self.client_params["endpoint_url"] = settings.S3_ENDPOINT_URL
        if settings.S3_USE_SSL is not None:
            self.client_params["use_ssl"] = settings.S3_USE_SSL
        self._sync_client = None

    def _get_sync_client(self):
        if self._sync_client is None and boto3 is not None:
            params = {k: v for k, v in self.client_params.items() if k != "use_ssl"}
            if "endpoint_url" in self.client_params:
                params["endpoint_url"] = self.client_params["endpoint_url"]
            self._sync_client = boto3.client("s3", **params)
        return self._sync_client

    async def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        cache_control: str = "public, max-age=31536000, immutable",
        bucket: Optional[str] = None,
    ) -> str:
        """Upload raw bytes to S3 and return object key."""
        if self.session is None:
            logger.warning("aioboto3 Session is not available. Skipping S3 upload for key %s", key)
            return key
        target_bucket = bucket or self.bucket
        async with self.session.client("s3", **self.client_params) as client:
            kwargs = {"Bucket": target_bucket, "Key": key, "Body": data}
            if content_type:
                kwargs["ContentType"] = content_type
            if cache_control:
                kwargs["CacheControl"] = cache_control
            await client.put_object(**kwargs)
        return key

    async def upload_json(
        self,
        key: str,
        data: Any,
        bucket: Optional[str] = None,
        cache_control: str = "no-cache, no-store, must-revalidate",
    ) -> str:
        """Serialize data to JSON and upload to S3."""
        json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")
        return await self.upload_bytes(
            key=key,
            data=json_bytes,
            content_type="application/json",
            cache_control=cache_control,
            bucket=bucket,
        )

    async def delete_object(self, key: str, bucket: Optional[str] = None) -> bool:
        if self.session is None:
            return True
        target_bucket = bucket or self.bucket
        async with self.session.client("s3", **self.client_params) as client:
            await client.delete_object(Bucket=target_bucket, Key=key)
        return True

    async def generate_presigned_url(self, key: Optional[str], expires_in: int = 3600, method: str = "get_object") -> Optional[str]:
        """Generate a presigned URL using synchronous boto3 (safe to call from async code)."""
        if not key or not str(key).strip():
            return None
        key_str = str(key).strip()
        if key_str.startswith("http://") or key_str.startswith("https://"):
            return key_str
        if boto3 is None:
            return f"https://{self.bucket}.s3.amazonaws.com/{key_str}"

        client = self._get_sync_client()
        if client is None:
            return key_str
        try:
            url = client.generate_presigned_url(
                ClientMethod=method,
                Params={"Bucket": self.bucket, "Key": key_str},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError:
            raise

    async def is_presigned_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    async def get_display_url(self, value: Optional[str]) -> Optional[str]:
        if not value or not str(value).strip():
            return None
        # Check if the URL is already a presigned URL
        if await self.is_presigned_url(value):
            return value
        # Generate a presigned URL for the stored object
        return await self.generate_presigned_url(value)

    async def convert_and_upload_webp(
        self,
        key: str,
        data: bytes,
        quality: int = 76,
        lossless: bool = False,
        max_dimension: Optional[int] = 1280,
        strip_metadata: bool = True,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> str:
        """Convert image bytes to compressed WebP and upload to S3.

        Resizes if either dimension exceeds max_dimension (aspect ratio preserved).
        Optionally embeds GPS coordinates into XMP metadata.
        Returns the new .webp object key.
        """
        try:
            image = Image.open(io.BytesIO(data))
            image = ImageOps.exif_transpose(image)
        except Exception as exc:
            raise ValueError(f"Cannot decode image data: {exc}") from exc

        if image.mode == "P":
            image = image.convert("RGBA")
        elif image.mode == "CMYK":
            image = image.convert("RGB")

        if max_dimension and max(image.size) > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        if strip_metadata:
            clean = Image.new(image.mode, image.size)
            clean.putdata(list(image.getdata()))
            image = clean

        # Build XMP block with GPS coords if provided
        xmp_data: Optional[bytes] = None
        if lat is not None and lon is not None:
            xmp_data = (
                '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>'
                '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
                '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                '<rdf:Description rdf:about=""'
                ' xmlns:exif="http://ns.adobe.com/exif/1.0/">'
                f'<exif:GPSLatitude>{await self._dd_to_dms_xmp(lat, "lat")}</exif:GPSLatitude>'
                f'<exif:GPSLatitudeRef>{"N" if lat >= 0 else "S"}</exif:GPSLatitudeRef>'
                f'<exif:GPSLongitude>{await self._dd_to_dms_xmp(lon, "lon")}</exif:GPSLongitude>'
                f'<exif:GPSLongitudeRef>{"E" if lon >= 0 else "W"}</exif:GPSLongitudeRef>'
                '</rdf:Description>'
                '</rdf:RDF>'
                '</x:xmpmeta>'
                '<?xpacket end="w"?>'
            ).encode("utf-8")

        buffer = io.BytesIO()
        save_kwargs: dict = dict(
            format="WEBP",
            quality=quality,
            lossless=lossless,
            method=6,
            optimize=True,
        )
        if xmp_data:
            save_kwargs["xmp"] = xmp_data

        image.save(buffer, **save_kwargs)
        webp_bytes = buffer.getvalue()

        base_key = key.rsplit(".", 1)[0] if "." in key.split("/")[-1] else key
        webp_key = f"{base_key}.webp"

        return await self.upload_bytes(webp_key, webp_bytes, content_type="image/webp")

    

    async def _dd_to_dms_xmp(self, value: float, axis: str) -> str:
        """Convert decimal degrees to XMP DMS rational string: 'DD,MM.mmmmmmS'."""
        value = abs(value)

        degrees = int(value)
        minutes = (value - degrees) * 60
        return f"{degrees},{minutes:.6f}"

    async def convert_base64_to_bytes(
        self,
        base64_string: str,
    ) -> tuple[bytes, str]:
        """
        Convert base64 image string into raw bytes.

        Supports:
        data:image/webp;base64,...
        data:image/png;base64,...
        data:image/jpeg;base64,...
        data:application/pdf;base64,...

        Returns:
            (image_bytes, mime_type)
        """

        file_data = validate_data_url_file(base64_string)
        return file_data.raw, file_data.mime_type


    async def get_object_bytes(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> tuple[bytes, str]:
        if self.session is None:
            return b"", "application/octet-stream"
        target_bucket = bucket or self.bucket
        async with self.session.client(
            "s3",
            **self.client_params,
        ) as client:
            response = await client.get_object(
                Bucket=target_bucket,
                Key=key,
            )
            data = await response["Body"].read()
            content_type = response.get(
                "ContentType",
                "application/octet-stream",
            )
            return data, content_type

    async def get_object_json(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> Optional[Any]:
        """Download JSON object from S3 and deserialize."""
        try:
            raw_bytes, _ = await self.get_object_bytes(key=key, bucket=bucket)
            if not raw_bytes:
                return None
            return json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            logger.warning("Failed to fetch JSON object %s from bucket %s: %s", key, bucket or self.bucket, e)
            return None

    async def object_exists(
        self,
        key: str,
        bucket: Optional[str] = None,
    ) -> bool:
        """Check if an object exists in S3."""
        if self.session is None:
            return False
        target_bucket = bucket or self.bucket
        try:
            async with self.session.client("s3", **self.client_params) as client:
                await client.head_object(Bucket=target_bucket, Key=key)
            return True
        except Exception:
            return False