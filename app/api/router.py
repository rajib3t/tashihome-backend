import pkgutil
import importlib
import os
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


def load_routes():
    package = "app.api"
    current_dir = os.path.dirname(__file__)
    prefixed_sections = {"admin", "vendor", "user", "public"}

    for root, dirs, files in os.walk(current_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") and d != "__pycache__"]

        relative_path = os.path.relpath(root, current_dir)
        if relative_path == ".":
            module_prefix = package
        else:
            module_prefix = f"{package}.{relative_path.replace(os.sep, '.')}"

        rel_parts = relative_path.split(os.sep)
        top_level = rel_parts[0] if relative_path != "." else ""

        for _, module_name, _ in pkgutil.iter_modules([root]):
            if not module_name.endswith("_route"):
                continue

            module = importlib.import_module(f"{module_prefix}.{module_name}")
            if hasattr(module, "router"):
                router = module.router
                if top_level in prefixed_sections:
                    prefix = f"/{top_level}"
                    if router.prefix and router.prefix.startswith(prefix):
                        api_router.include_router(router)
                    else:
                        api_router.include_router(router, prefix=prefix)
                else:
                    api_router.include_router(router)


load_routes()
