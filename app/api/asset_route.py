from fastapi import APIRouter, HTTPException, Response

from app.api.base_controller import BaseController
from app.services.storage_service import StorageService


class AssetRoute(BaseController):

    def __init__(self):
        self.router = APIRouter(
            prefix="/assets",
            tags=["Assets"],
        )

        self.storage_service = StorageService()

        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/{file_path:path}",
                self.get_asset,
                {},
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(
                path,
                handler,
                methods=[method.upper()],
                **route_kwargs,
            )

    async def get_asset(
        self,
        file_path: str,
    ):
        print("ASSET FILE:", file_path)

        try:
            data, content_type = (
                await self.storage_service.get_object_bytes(
                    file_path
                )
            )

            return Response(
                content=data,
                media_type=content_type,
                headers={
                    "Cache-Control": "private, max-age=3600",
                },
            )

        except Exception as exc:
            print(
                "ASSET ERROR:",
                repr(exc),
                "FILE:",
                file_path,
            )

            raise HTTPException(
                status_code=404,
                detail="Asset not found",
            )


controller = AssetRoute()
router = controller.router