from fastapi import APIRouter, File, UploadFile

from app.api.base_controller import BaseController
import logging

logger = logging.getLogger(__name__)

class SettingsController(BaseController):
    

    def __init__(self):
        
        

        self.router = APIRouter(
            prefix="/settings",
            tags=["Settings"],
        )
        self._register_routes()

    def _register_routes(self):

        routes = [
            ("post", "/", self._save_setting, {"response_model": None, "response_model_by_alias": False}),
        ]


        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    
    async  def _save_setting(
            self,
            app_name:str,
            app_logo : UploadFile = File(...),

        ):
        pass

controller = SettingsController()
router = controller.router
