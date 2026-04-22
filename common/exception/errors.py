from typing import Any

from fastapi import HTTPException
from starlette.background import BackgroundTask

from common.response.response_code import CustomErrorCode, StandardResponseCode


class BaseExceptionMixin(Exception):
    code: int

    def __init__(
        self,
        *,
        msg: str = None,
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        self.msg = msg
        self.data = data
        # The original background task: https://www.starlette.io/background/
        self.background = background


class HTTPError(HTTPException):
    def __init__(
        self, *, code: int, msg: Any = None, headers: dict[str, Any] | None = None
    ):
        super().__init__(status_code=code, detail=msg, headers=headers)


class CustomError(BaseExceptionMixin):
    def __init__(
        self,
        *,
        error: CustomErrorCode,
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        self.code = error.code
        super().__init__(msg=error.msg, data=data, background=background)


class RequestError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_400

    def __init__(
        self,
        *,
        msg: str = "Bad Request",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(msg=msg, data=data, background=background)


class ForbiddenError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_403

    def __init__(
        self,
        *,
        msg: str = "Forbidden",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(msg=msg, data=data, background=background)


class NotFoundError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_404

    def __init__(
        self,
        *,
        msg: str = "Not Found",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(msg=msg, data=data, background=background)


class ServerError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_500

    def __init__(
        self,
        *,
        msg: str = "Internal Server Error",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(msg=msg, data=data, background=background)


class GatewayError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_502

    def __init__(
        self,
        *,
        msg: str = "Bad Gateway",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(msg=msg, data=data, background=background)


class AuthorizationError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_401

    def __init__(
        self,
        *,
        msg: str = "Permission Denied",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        super().__init__(msg=msg, data=data, background=background)


class TokenError(HTTPError):
    code = StandardResponseCode.HTTP_401

    def __init__(
        self, *, msg: str = "Not Authenticated", headers: dict[str, Any] | None = None
    ):
        super().__init__(
            code=self.code, msg=msg, headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class DebugError(BaseExceptionMixin):
    code = StandardResponseCode.HTTP_500

    def __init__(
        self,
        *,
        msg: str = "Debug Error",
        data: Any = None,
        background: BackgroundTask | None = None,
        debug_info: dict = None,
    ):
        self.debug_info = debug_info or {}
        super().__init__(msg=msg, data=data, background=background)


class ProcessingError(DebugError):
    def __init__(
        self,
        *,
        step: str,
        error: Exception,
        msg: str = "Processing Error",
        data: Any = None,
    ):
        debug_info = {
            "step": step,
            "error_type": type(error).__name__,
            "error_details": str(error),
        }
        super().__init__(msg=msg, data=data, debug_info=debug_info)


class ResearchProblem(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        type_: str,
        title: str,
        detail: str | None = None,
        instance: str | None = None,
        headers: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.type = type_
        self.title = title
        self.detail = detail
        self.instance = instance
        self.headers = headers or {}
        self.extra = extra or {}
        super().__init__(detail or title)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status_code,
        }
        if self.detail:
            payload["detail"] = self.detail
        if self.instance:
            payload["instance"] = self.instance
        payload.update(self.extra)
        return payload


class LLMUnavailableError(Exception):
    """Raised when the configured LLM provider cannot return a usable result."""


class ContentPolicyError(Exception):
    """Raised when the provider blocks analysis for policy reasons."""


class StorageError(ServerError):
    """Base exception for storage operations."""

    def __init__(
        self,
        *,
        operation: str,
        entity: str | None = None,
        msg: str = "Storage operation failed",
        data: Any = None,
        background: BackgroundTask | None = None,
    ):
        error_msg = f"{msg} - Operation: {operation}"
        if entity:
            error_msg += f", Entity: {entity}"
        super().__init__(msg=error_msg, data=data, background=background)


class EntityCreationError(StorageError):
    """Raised when entity creation fails."""

    def __init__(
        self, *, entity: str, msg: str = "Failed to create entity", data: Any = None
    ):
        super().__init__(operation="create", entity=entity, msg=msg, data=data)
