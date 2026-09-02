from typing import Optional
from urllib.parse import urlparse
import io
import boto3
from aioboto3 import Session
from botocore.exceptions import ClientError
from PIL import Image, ImageOps
from app.core.config import settings
from app.core.exceptions import AppException
from app.utils.file_validation import validate_data_url_file


class StorageService:
    """Simple S3-compatible storage service supporting AWS S3 and MinIO via endpoint URL.

    Usage: configure S3 settings in environment (.env) and inject via deps.
    """

    def __init__(self):
        self.session = Session()
        self.bucket: Optional[str] = settings.S3_BUCKET
        self.client_params = {
            "aws_access_key_id": settings.S3_ACCESS_KEY,
            "aws_secret_access_key": settings.S3_SECRET_KEY,
            "region_name": settings.S3_REGION,
        }
        if settings.S3_ENDPOINT_URL:
            self.client_params["endpoint_url"] = settings.S3_ENDPOINT_URL
        if settings.S3_USE_SSL is not None:
            self.client_params["use_ssl"] = settings.S3_USE_SSL

    async def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        cache_control: str = "public, max-age=31536000, immutable",
    ) -> str:
        """Upload raw bytes to S3 and return object key."""
        async with self.session.client("s3", **self.client_params) as client:
            kwargs = {"Bucket": self.bucket, "Key": key, "Body": data}
            if content_type:
                kwargs["ContentType"] = content_type
            if cache_control:
                kwargs["CacheControl"] = cache_control
            await client.put_object(**kwargs)
        return key

    async def delete_object(self, key: str) -> bool:
        async with self.session.client("s3", **self.client_params) as client:
            await client.delete_object(Bucket=self.bucket, Key=key)
        return True

    async def generate_presigned_url(self, key: str, expires_in: int = 3600, method: str = "get_object") -> str:
        """Generate a presigned URL using synchronous boto3 (safe to call from async code)."""
        params = {k: v for k, v in self.client_params.items() if k != "use_ssl"}
        if "endpoint_url" in self.client_params:
            params["endpoint_url"] = self.client_params["endpoint_url"]

        client = boto3.client("s3", **params)
        try:
            url = client.generate_presigned_url(
                ClientMethod=method,
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError:
            raise

    async def is_presigned_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    async def get_display_url(self, value: Optional[str]) -> Optional[str]:
        if value is None:
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
    ) -> tuple[bytes, str]:

        async with self.session.client(
            "s3",
            **self.client_params,
        ) as client:

            response = await client.get_object(
                Bucket=self.bucket,
                Key=key,
            )

            data = await response["Body"].read()

            content_type = response.get(
                "ContentType",
                "application/octet-stream",
            )

            return data, content_type