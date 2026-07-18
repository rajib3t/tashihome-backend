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
        return {"total": r["total"], "page": r["page"], "size": r["size"]}