import json

from loguru import logger as logging
from markdown_to_ppt.exceptions import NotFound as HTTPNotFound
from werkzeug.wrappers import Response

"""
================================================================================================================
这里的错误码必须跟 
https://ksogit.kingsoft.net/wow/solution/-/blob/master/server/src/internal/errs/register.go
保持一致，如果这里还没定义，从那边拷贝过来
================================================================================================================
"""


class ApiException(Exception):
    result: str = "InternalError"
    httpcode: int = 500

    def __init__(self, msg: str = "", detail=None) -> None:
        self.msg = msg
        self.detail = detail
        super().__init__(self.str())

    def str(self) -> str:
        return f"result={self.result} msg={self.msg} detail={self.detail}"

    def get_headers(self):
        return {"Content-Type": "application/json"}

    def get_body(self):
        ret = {
            "result": self.result,
            "msg": self.msg,
        }
        if detail := self.detail:
            ret["detail"] = detail
        return ret

    def get_response(self) -> Response:
        return Response(
            json.dumps(self.get_body(), ensure_ascii=False),
            status=self.httpcode,
            headers=self.get_headers(),
        )

    def __call__(self, environ, start_response) -> Response:
        """
        符合 WSGI 标准的一个 Response 返回
        """
        return self.get_response()(environ, start_response)

    @staticmethod
    def parse(e: Exception) -> "ApiException":
        from pydantic import ValidationError

        logging.exception(e)
        if isinstance(e, ApiException):
            return e
        if isinstance(e, (HTTPNotFound)):
            from flask import request

            logging.debug(f"{request.method}_{request.full_path}")
            return NotFound()
        if isinstance(e, ValidationError):
            return InvalidArgument()
        return ApiException(msg="服务异常，请稍后重试")


class UserUnauthorized(ApiException):
    result = "UserUnauthorized"
    httpcode = 401


class PermissionDenied(ApiException):
    result = "PermissionDenied"
    httpcode = 403


class UserLimited(ApiException):
    result = "UserLimited"
    httpcode = 429


class SessionNotExisted(ApiException):
    result = "SessionNotExisted"
    httpcode = 400


class InvalidArgument(ApiException):
    result = "InvalidArgument"
    httpcode = 400


class InvalidLanguage(ApiException):
    result = "InvalidLanguage"
    httpcode = 400


class InvalidCode(ApiException):
    result = "InvalidCode"
    httpcode = 400


class NotFound(ApiException):
    result = "NotFound"
    httpcode = 404


class InternalError(ApiException):
    result = "InternalError"
    httpcode = 500


class InvalidFileType(ApiException):
    result = "InvalidFileType"
    httpcode = 400


class SpaceFull(ApiException):
    result = "SpaceFull"
    httpcode = 403


class AuditFailed(ApiException):
    httpcode = 400
    result = "AuditFailed"

    def __init__(self, msg: str = "", detail=None) -> None:
        msg: str = (
            "我还在不断学习中，暂时无法回答此问题，请尝试重新提问"  # 特殊处理，不给自定义 msg
        )
        super().__init__(msg, detail)


class UrlFetchFailed(ApiException):
    httpcode = 400
    result = "UrlFetchFailed"

    def __init__(
        self,
        msg: str = "由于网站限制，灵犀未能阅读网页的内容，请换个链接试试。",
        detail=None,
    ) -> None:
        super().__init__(msg, detail)


class WebSearchFailed(ApiException):
    httpcode = 400
    result = "WebSearchFailed"

    def __init__(self, msg: str = "网络搜索失败", detail=None) -> None:
        super().__init__(msg, detail)


class AIError(ApiException):
    httpcode = 400
    result = "AIError"


class RateLimiter(ApiException):
    httpcode = 429
    result = "RateLimiter"


class PromptTokenExceedLimit(ApiException):
    httpcode = 429
    result = "PromptTokenExceedLimit"


class Unavailable(ApiException):
    httpcode = 500
    result = "Unavailable{}"


class Timeout(ApiException):
    httpcode = 500
    result = "Timeout"


class PrivilegeInsufficient(ApiException):
    httpcode = 403
    result = "PrivilegeInsufficient"


class ParseFileFailed(ApiException):
    httpcode = 400
    result = "ParseFileFailed"


class SessionIsRunning(ApiException):
    httpcode = 403
    result = "SessionIsRunning"


class InvalidSlideCount(ApiException):
    httpcode = 404
    result = "InvalidSlideCount"


class InvalidFileSize(ApiException):
    httpcode = 404
    result = "InvalidFileSize"


class InvalidSlideSize(ApiException):
    httpcode = 404
    result = "InvalidSlideSize"


class EmptySlides(ApiException):
    httpcode = 404
    result = "EmptySlides"
