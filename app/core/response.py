from typing import Any, Optional
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

class APIResponse:
    @staticmethod
    def success(data: Any = None, message: str = "Success", metadata: Optional[dict] = None, status_code: int = 200) -> JSONResponse:
        response = {
            "success": True,
            "message": message,
            "data": jsonable_encoder(data)
        }
        if metadata:
            response["metadata"] = metadata
        return JSONResponse(content=response, status_code=status_code)
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_id: Optional[str] = None, errors: Optional[list] = None) -> JSONResponse:
        response = {
            "success": False,
            "message": message
        }
        if error_id:
            response["error_id"] = error_id
        if errors:
            response["errors"] = errors
        return JSONResponse(content=response, status_code=status_code)
    
    @staticmethod
    def paginated(data: list, total: int, page: int, limit: int, message: str = "Success") -> JSONResponse:
        return APIResponse.success(
            data=data,
            message=message,
            metadata={
                "total": total,
                "page": page,
                "limit": limit,
                "has_next": (page * limit) < total,
                "has_prev": page > 1
            }
        )