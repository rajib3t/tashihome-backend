from app.repositories.base_repository import Page

class BaseController:
    def __init__(self):
        pass

    def build_response(self, message, data=None, meta=None):
        return {
            "status": "success",
            "message": message,
            "meta": meta,
            "data": data,
        }

    def pagination_meta(self, r):
        if isinstance(r, Page):
            return {
                "total": r.total,
                "page": r.page,
                "size": r.page_size,
                "total_pages": r.pages,
            }

        total = r.get("total", 0) if isinstance(r, dict) else getattr(r, "total", 0)
        page = r.get("page", 1) if isinstance(r, dict) else getattr(r, "page", 1)
        size = r.get("size", r.get("page_size", 10)) if isinstance(r, dict) else getattr(r, "size", getattr(r, "page_size", 10))
        total_pages = (total + size - 1) // size if size > 0 else 0
        return {
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }
