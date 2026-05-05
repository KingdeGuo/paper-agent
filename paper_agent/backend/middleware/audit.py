"""Audit logging middleware for enterprise compliance."""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

audit_logger = logging.getLogger("paper_agent.audit")


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs API requests for audit trail."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        if request.url.path.startswith("/api/"):
            user = getattr(request.state, "user", None)
            username = getattr(user, "username", "anonymous") if user else "anonymous"

            audit_logger.info(
                "audit",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "user": username,
                    "client_ip": request.client.host if request.client else "unknown",
                },
            )

        return response
