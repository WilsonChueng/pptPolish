import os
import random
import logging
import utils.load_env as load_env
import markdown_to_ppt.markdown2ppt_node as markdown2ppt_node
import markdown_to_ppt.ai_server as ai_server

markdown = """
# 整改进度汇报 
## 四方滑块更换新结构
### 通知号与整改类型
#### 整改通知号
* 整改通知号为SFE55TC01体开(2024)字第013号。
#### 整改类型
* 整改类型为免费。

### 准备情况概述
#### 人员准备情况
* 人员准备情况良好，标记为OK。
#### 工具准备情况
* 工具准备情况良好，标记为OK。
#### 物料准备情况
* 物料已下单，根据计划陆续发货。
#### 文件准备情况
* 文件准备情况良好，标记为OK。
#### 整改信息
* 滑块整改涉及四方235列车（其中威奥186列），AST59列（威奥59列），安三级修更换。
"""

theme_id = "docer_3332302"


def get_env_para(model_token_name):
    return os.getenv(model_token_name)


def gen_ppt(markdown):
    ppt_root_node = markdown2ppt_node.tran_markdown_to_ppt_node(markdown)
    client = ai_server.AIServer(
        load_env.get_env_para("WPS_SID"),
        load_env.get_env_para("GEN_PPT_AK"),
        load_env.get_env_para("GEN_PPT_SK"),
    )
    theme_list = client.get_theme_list("", "", getAll=True)
    # logging.info(f"theme_list: {len(theme_list)}")
    theme_id = random.choice(theme_list).get("theme_id", "")
    logging.info(f"choose theme_id: {theme_id} from all {len(theme_list)} themes")
    file_info = client.gen_ppt_file(
        ai_server.GenPPTReq(theme_id=theme_id, root_node=ppt_root_node)
    )
    if file_info is None:
        raise Exception("ai server gen ppt failed")
    file_url = file_info.get("file_url", "")
    logging.info(f"ppt_url: {file_url}")
    return theme_id, file_url


if __name__ == "__main__":
    gen_ppt(markdown)
