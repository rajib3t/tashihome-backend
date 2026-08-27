from app.api.base_controller import BaseController
from fastapi import APIRouter, Depends
from app.deps.user import   get_user_profile_use_case
from app.application.use_case.user.profile_use_case import ProfileUseCase
from app.schemas.user_schema import UserBasicProfileResponse, UserData


class ProfileController(BaseController):
    def __init__(self):
        
        

        self.router = APIRouter(
            prefix="/profile",
            tags=["User - Profile"],
        )
        self._register_routes()

    
    def _register_routes(self):
        routes = [
            ("get", "/", self._get_profile, {"response_model": UserBasicProfileResponse, "response_model_by_alias": False})
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    
    async def _get_profile(
        self,
        use_case: ProfileUseCase = Depends(get_user_profile_use_case)
        ):
        result = await use_case.execute()
        
        return self.build_response(
            message="Profile retrieved successfully",
            data=result
        )



controller = ProfileController()
router = controller.router



