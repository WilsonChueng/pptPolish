import requests
import json
from loguru import logger

def mask(s: str) -> str:
    """字符串脱敏"""
    ln = len(s)
    if ln == 0:
        return ""  # wtf?
    elif ln == 1:
        return "*"
    elif 2 <= ln <= 4:
        return s[:1] + "*" * (ln - 1)
    elif 5 <= ln <= 9:
        return s[:4] + "*" * (ln - 4)
    else:
        return s[:4] + "*" * (ln - 8) + s[ln - 4 :]


def dump_request(req: requests.Request, with_body: bool = True) -> str:
    """
    导出 requests.Request 请求报文
    只在 with_body=True 并且 Content-Type 是 application/json 才导出 body
    """
    with_body = (
        "application/json" in req.headers.get("Content-Type", "").lower() and with_body
    )
    request_line = "{request_method} {request_url}".format(
        request_method=req.method, request_url=req.url
    )
    header_text = ""
    for k, v in req.headers.items():
        if k.lower() in (
            "host",
            "cookie",
            "x-user-token",
            "x-weboffice-token",
            "authorization",
        ):
            v = mask(v)
        header_text += f"\r\n{k}: {v}"

    body = ""
    if with_body:
        reqBody = req.body
        if not reqBody and req.json:
            reqBody = json.dumps(req.json, ensure_ascii=False)

        if isinstance(reqBody, bytes):
            reqBody = reqBody.decode()
        elif not isinstance(reqBody, str):
            reqBody = str(reqBody)
        body = "\r\n" + reqBody
    return request_line + "\r\n" + header_text + "\r\n" + body


def dump_response(res: requests.Response, with_body: bool = True) -> str:
    """
    导出 requests.Response 请求报文
    只在 with_body=True 并且 Content-Type 是 application/json 才导出 body
    """
    with_body = (
        "application/json" in res.headers.get("Content-Type", "").lower() and with_body
    )
    body = "\r\n" + res.text if with_body else ""
    headers = "\r\n".join("{}: {}".format(k, v) for k, v in res.headers.items())

    return "{status_code} {reason}\r\n{headers}\r\n{body}".format(
        status_code=res.status_code,
        reason=res.reason,
        headers=headers,
        body=body,
    )

def dump_roundtrip(res: requests.Response, *args, **kwargs):
    """打印请求&响应报文"""
    text = "[request]\n%s\n[response]\n%s" % (
        dump_request(res.request),
        dump_response(res),
    )
    # print(text)
    # logger.info(text)

