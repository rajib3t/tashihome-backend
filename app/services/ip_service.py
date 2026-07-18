from app.core.config import settings
import httpx
from app.schemas.ip_detail_schema import IpDetailResponse
import logging

logger = logging.getLogger(__name__)

class IpService:
    def __init__(self) -> None:
        self.ip_details_api_url = settings.IP_DETAILS_API_URL

    async def get_ip_details(self, ip: str) -> IpDetailResponse:
        if not self.ip_details_api_url:
            logger.warning("IP_DETAILS_API_URL not configured, returning empty response")
            return IpDetailResponse()
        
        url = f"{self.ip_details_api_url}{ip}"
        logger.info(f"Fetching IP details from: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json() if response else {}
                logger.info(f"API Response for {ip}: {data}")
                return IpDetailResponse(**data)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching IP details for {ip}: {e}")
            return IpDetailResponse()
        except Exception as e:
            logger.error(f"Unexpected error fetching IP details for {ip}: {e}")
            return IpDetailResponse()

    async def get_ip_details_from_header(self, request) -> IpDetailResponse:
        ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
        return await self.get_ip_details(ip)

    async def get_client_ip(self, request) -> str:
        ip = request.headers.get("X-Forwarded-For") or request.headers.get("X-Real-IP") or request.client.host
        # X-Forwarded-For can contain multiple IPs, use the first one (client IP)
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        return ip
