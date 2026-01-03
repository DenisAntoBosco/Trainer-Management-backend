import traceback
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.error_log import ErrorLog
from ..core.database import AsyncSessionLocal

class ErrorLogger:
    @staticmethod
    async def log_error(
        error: Exception,
        component: str,
        function_name: str,
        severity: str = "ERROR",
        created_by: Optional[uuid.UUID] = None
    ) -> str:
        try:
            error_id = f"ERR_{uuid.uuid4().hex[:8].upper()}"
            
            async with AsyncSessionLocal() as db:
                error_log = ErrorLog(
                    error_id=error_id,
                    error_message=str(error),
                    stack_trace=traceback.format_exc(),
                    component=component,
                    severity=severity,
                    function_name=function_name,
                    created_by=created_by
                )
                
                db.add(error_log)
                await db.commit()
                
            return error_id
        except Exception as e:
            print(f"Failed to log error: {e}")
            traceback.print_exc()
            return f"ERR_{uuid.uuid4().hex[:8].upper()}"