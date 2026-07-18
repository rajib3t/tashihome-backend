import pkgutil
import importlib
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


def load_routes():
    import os
    package = "app.api"
    current_dir = os.path.dirname(__file__)

    # Load routes from app/api directory
    for _, module_name, _ in pkgutil.iter_modules([current_dir]):
        if module_name.endswith("_route"):
            module = importlib.import_module(f"{package}.{module_name}")
            if hasattr(module, "router"):
                api_router.include_router(module.router)
    
    # Load routes from subdirectories (e.g., vendors)
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        if os.path.isdir(item_path) and not item.startswith("_"):
            subpackage = f"{package}.{item}"
            for _, module_name, _ in pkgutil.iter_modules([item_path]):
                if module_name.endswith("_route"):
                    module = importlib.import_module(f"{subpackage}.{module_name}")
                    if hasattr(module, "router"):
                        api_router.include_router(module.router)


load_routes()