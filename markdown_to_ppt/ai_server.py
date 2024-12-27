import json
import logging
import typing
import uuid

import requests
from dataclasses import dataclass, field, asdict
import sseclient
from urllib.parse import urlparse
import hashlib
from email.utils import formatdate
from loguru import logger
from markdown_to_ppt.common import dump_roundtrip
from pydantic import BaseModel
from markdown_to_ppt.config import WPSAIConfig


@dataclass
class PPTNode:
    node_type: str = "nt_span"
    text: str = ""
    level: int = 0
    children: typing.List["PPTNode"] = field(default_factory=list)


@dataclass
class RootNode:
    node_type: str = "nt_span"
    text: str = ""
    children: typing.List[PPTNode] = field(default_factory=list)


@dataclass
class GenPPTReq:
    theme_id: str
    root_node: RootNode


class GENPptxData(BaseModel):
    thumb_url: str = ""
    slide_index: int = 0
    total: int = 0
    file_url: str = ""


class GENPptResponseData(BaseModel):
    type: str
    pptx_data: GENPptxData = None


class GENPptResponse(BaseModel):
    code: int
    msg: str
    data: GENPptResponseData


class AIServer:

    def __init__(self, token, ak: str, sk: str):
        self.base_url = "http://copilot-api.wps.cn"
        self.ak = ak
        self.sk = sk
        self._wps_sid = token
        self.client = requests.session()
        self.client.hooks["response"].append(dump_roundtrip)
        trace_id = str(uuid.uuid4())
        self.headers = {
            "Cookie": f"wps_sid={self._wps_sid}",
            "X-Client-Request-ID": trace_id,
            "X-Client-Product": "CC",
            "X-Client-Type": "web",
            "X-Client-Component": "public",
            "X-Client-Version": "cc",
            "X-Client-Channel": "lingxi",
            "X-Client-Language": "zh",
            "X-Client-Device-ID": "cc",
            "x-client-entrance": "aigc",
            "X-Client-Guid": "cc",
            "Content-Type": "application/json",
        }

    def build_body(self, req: GenPPTReq):
        return {
            "business_info": {
                "billing_info": {
                    "product_name": "365wps-copilotchat-web",
                    "intention_code": "365wps_cc_create_ppt"
                }
            },
            "theme_id": req.theme_id,
            "pptx_params": {
                "slides_count": -1,
                "merge_slides": True,
                "enable_transition": False,
                "get_theme_font": False,
                "disable_gen_file": False,
                "generate_index": []
            },
            "outlines": {
                "root_node": asdict(req.root_node)
                # "root_node": root_node
            },
            "get_page_node": True,
        }

    def office_api_direct_request(self, body, path) -> requests.Response:
        url = f"{self.base_url}/{path}"
        # print(f"request url: {url}")
        req = requests.Request("POST", url, headers=self.headers, data=body)
        req = wps2_sign(req, self.ak, self.sk)
        prepared_request = self.client.prepare_request(req)
        response = self.client.send(prepared_request, stream=True)
        if response.status_code != 200:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                logger.error(response.json())
            elif "text/html" in content_type or "text/plain" in content_type:
                logger.error(response.text)
            else:
                logger.error(response.text)
            raise Exception(
                f"office_api_direct_v2_request error: {response.status_code}"
            )
        return response

    def sse_office_api_direct_request(self, body, path):
        url = f"{self.base_url}/{path}"
        req = requests.Request("POST", url, headers=self.headers, data=body)
        req = wps2_sign(req, self.ak, self.sk)
        prepared_request = self.client.prepare_request(req)
        response = self.client.send(prepared_request, stream=True)
        if response.status_code != 200:
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                logger.error(response.json())
            elif "text/html" in content_type or "text/plain" in content_type:
                logger.error(response.text)
            else:
                logger.error(response.text)
            raise Exception(
                f"office_api_direct_v2_request error: {response.status_code}"
            )
        sse = sseclient.SSEClient(response)
        return sse

    def gen_ppt_file(self, req: GenPPTReq):
        payload = json.dumps(self.build_body(req), ensure_ascii=False)
        path = "office/v5/dev/ai/generator/slides/gen_ppt_from_pxf"
        sse = self.sse_office_api_direct_request(payload, path)
        for e in sse.events():
            # logger.info(f"ppt save office api resut: {e.data}")
            rs = GENPptResponse(**json.loads(e.data))
            if rs.code != 0:
                raise Exception(f"gen ppt failed, code: {rs.code}, error_msg: {rs.msg}", rs.msg)
            if rs.data.type == "generate_pptx_start":
                total = int(rs.data.pptx_data.total)
            if rs.data.type == "generate_pptx_result":
                pass
            if rs.data.type == "generate_pptx_finish":
                return {
                    "file_url": rs.data.pptx_data.file_url,
                }

    def build_get_theme_list_body(self, scene, style, limit, offset):
        return {
            "theme_from": "recommend",
            "filter": {
                "entry": "ai_cc_panel",
                "client_type": "web",
                "product": "CC",
                "component": "public"
            },
            "theme_filter": {
                "style_tags": [],
                "scene_tags": [scene],
                "common_tags": [style],
                "slides_prefix_n": 25,
                "slides_suffix_n": 25
            },
            "limit": limit,
            'offset': offset
        }

    def get_theme_list(self, scene, style, getAll=False, nums=20, offset=0):
        url = "office/v5/dev/ai/slides/theme_tpl/list"
        if getAll:
            payload = json.dumps(self.build_get_theme_list_body(scene, style, 10000, 0), ensure_ascii=False)
        else:
            payload = json.dumps(self.build_get_theme_list_body(scene, style, nums, offset), ensure_ascii=False)
        try:
            response = self.office_api_direct_request(payload, url)
            resp_body = response.json()
            data = resp_body["data"]
            theme_list = data.get("items", [])
            return theme_list
        except Exception as e:
            logger.error(f"request theme list failed, response text: {response.text}")
            return []


def wps2_sign(req: requests.Request, ak, sk):
    """
    用法：
    req = requests.Request('get', url=url)
    req = requests.Request('put', url=url, data=data)
    req = requests.Request('put', url=url, json=object)
    req = wps2_sign(req, ak, sk)
    requests.session().send(req.prepare())
    """
    if not isinstance(req, requests.Request):
        raise TypeError(str(type(req)) + " not requests.Request")

    if req.method == "get":
        uri = urlparse(req.url)
        path_with_query = uri.path + (f"?{uri.query}" if uri.query else "")
        md5 = hashlib.md5(path_with_query.encode()).hexdigest()
    else:
        data = req.data
        if not data and req.json is not None:
            data = json.dumps(data)
        if not isinstance(data, bytes):
            data = data.encode()
        md5 = hashlib.md5(data).hexdigest()

    date = formatdate(timeval=None, localtime=False, usegmt=True)
    ct = "application/json"
    authorization = (
            f"WPS-2:{ak}:" + hashlib.sha1((sk + md5 + ct + date).encode()).hexdigest()
    )
    headers = {
        "Content-Type": ct,
        "Date": date,
        "Authorization": authorization,
        "Content-Md5": md5,
    }
    req.headers.update(headers)
    return req


if __name__ == "__main__":
    h = AIServer("V02SqeUvnMHqydaZOXdgnT8g2bmpxgo00a77609d005283f446", WPSAIConfig.ak, WPSAIConfig.sk)
    res = h.gen_ppt_file(GenPPTReq(
        theme_id="docer_3332119",
        root_node=RootNode(
            node_type="nt_span",
            text="工作生活",
            children=[
                PPTNode(
                    node_type="nt_span",
                    text="生活和工作谁重要",
                    level=0,
                    children=[
                        PPTNode(
                            node_type="nt_span",
                            text="工作咯",
                            level=1,
                            children=[]
                        )
                    ]
                ),
                PPTNode(
                    node_type="nt_span",
                    text="爱情",
                    level=0,
                    children=[
                        PPTNode(
                            node_type="nt_span",
                            text="做人",
                            level=1,
                            children=[]
                        ),
                        PPTNode(
                            node_type="nt_span",
                            text="做主",
                            level=1,
                            children=[]
                        )
                    ]
                ),
                PPTNode(
                    node_type="nt_span",
                    text="无语",
                    level=0,
                    children=[PPTNode(
                        node_type="nt_span",
                        text="大无语",
                        level=1,
                        children=[]
                    ),
                        PPTNode(
                            node_type="nt_span",
                            text="很无语",
                            level=1,
                            children=[]
                        )]
                )
            ])))
    print("========================")
    print(res)