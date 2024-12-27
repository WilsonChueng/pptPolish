import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class APPConfig:
    encryptKey=os.getenv("ENCRYPT_KEY", "")
    proxyUrl = os.getenv("PROXY_URL", "https://lingxi.wps.cn/api/ai_bot/chat/completion")
    pptProxyUrl = os.getenv("PPT_PROXY_URL", "https://lingxi.wps.cn/api/ai_bot/ppt_assistant/chat/completion")
    noteProxyUrl = os.getenv("NOTE_PROXY_URL", "https://lingxi.wps.cn/api/ai_bot/note_assistant/chat/completion")
    drive_wpsua = os.getenv(
        "DRIVE_WPS_UA",
        r"V1BTVUEvMS4wIChtb2JpbGUta2RvY3M6Q2hyb21lXzEwNi4wLjAuMDsgbGludXg6TGludXggNjQ7IFFkdElaLWpYUW5lRXJJbzhuZnN0S2c9PTpRMmh5YjIxbElDQXhNRFl1TUM0d0xqQT0pIENocm9tZS8xMDYuMC4wLjA=",
    )

class WPSAIConfig:
    ak = os.getenv("WPS_AI_AK", "")
    sk = os.getenv("WPS_AI_SK", "")

class KBEConfig:
    wps_365_host = os.getenv("WPS_365_HOST", "https://365.kdocs.cn")


class RTCConfig:
    app_id = os.getenv("RTC_APP_ID", "")
    app_key = os.getenv("RTC_APP_KEY", "")

    ak = os.getenv("RTC_AK", "")
    sk = os.getenv("RTC_SK", "")

    volumeGain = os.getenv("RTC_VolumeGain", "1")
    Prefill = os.getenv("RTC_Prefill", "true")
    silenceTime = os.getenv("RTC_SilenceTime", "1200")
    silenceThreshold = os.getenv("RTC_SilenceThreshold", "400")
    welcomeSpeech = os.getenv("RTC_WelcomeSpeech", "你好，我是你的PPT助手，随时等候你的指令，帮你制作PPT！")
    note_welcome_speech = os.getenv("RTC_Note_WelcomeSpeech",
                              "你好，我是你的速记助手，随时记录和总结你的想法！")
    asr_config_type = os.getenv("RTC_ASR_CONFIG_TYPE", "llm")
    asr_config_bigmodel_access_token = os.getenv("RTC_ASR_CONFIG_BIGMODEL_ACCESS_TOKEN", "kwrE-XLdCLYQFbxyMaZc0YKJAKGFAeYO")
    asr_config_api_resource_id = os.getenv("RTC_ASR_CONFIG_API_RESOURCE_ID", "Speech_Recognition_Seed_streaming7441496059782025482")

    @classmethod
    def get_prefill(cls) -> bool:
        if cls.Prefill.lower() == "true":
            return True

        return False

    @classmethod
    def get_silence_time(cls) -> int:
        return int(cls.silenceTime)

    @classmethod
    def get_silence_threshold(cls) -> int:
        return int(cls.silenceThreshold)

class LogConfig(object):
    dir = os.getenv("KLOG_DIR", "")
    level = os.getenv("KLOG_LEVEL", "INFO").upper()


class MiniMaxConfig:
    token = os.getenv("LLM_TOKEN", "5ZEXz9TgrGDtr5SUnh5psi8ZtdJTw9Iz")
    name = "abab6.5s-chat"
    provider = "minimax"


class AiGatewayConfig(object):
    token = os.getenv("AI_GATEWAY_TOKEN", "5ZEXz9TgrGDtr5SUnh5psi8ZtdJTw9Iz")
    product_name = os.getenv(
        "AI_GATEWAY_PRODUCT_NAME", ""
    )  # tips: 一般禁止使用这个配置，仅权益未配置时候临时用
    intention_code = os.getenv("AI_GATEWAY_INTENTION_CODE", "")
    host = os.getenv("AI_GATEWAY_HOST", "ai-copilot-gateway.ksord.com")
    sec_text_from = os.getenv("AI_GATEWAY_SEC_TEXT_FROM", "AI_WPS_SMARTASSISTANT")
    sec_text_scene = os.getenv("AI_GATEWAY_SEC_TEXT_SCENE", "pc_web")
    builtin_uid = os.getenv(
        "AI_GATEWAY_BUILTIN_UID", ""
    )  # 如果配置内置用户ID,ai gateway就不检查权益了, 否则使用用户的id 需要检测权益

    @staticmethod
    def scene_production(ua: str):
        # https://365.kdocs.cn/l/cbvAdjpWFhKl
        scene = "pc_web"
        product_name = "365wps-copilotchat-web"
        ua = ua.lower()
        if "miniprogram" in ua or "micromessenger" in ua:
            scene = "wechat_mini_program"
            product_name = "365wps-copilotchat-wxminiprogram"
        return scene, product_name

    def sec_text(self, text: str, category: str, client_type: str) -> dict:
        # 来源于woa群消息
        #  一、业务调整送审的场景编号参数： 业务编号：不变，AI_WPS_SMARTASSISTANT 场景编号，按用户具体使用的细分功能场景，分为三类：
        #  （一）类型一，场景编号：网页端：pc_web_general、PC客户端：pc_wps_general、微信小程序：wechat_mp_general 1、通用的聊天 2、搜索类的聊天
        #  （二）类型二，场景编号：网页端：pc_web_annex、PC客户端：pc_wps_annex、微信小程序：wechat_mp_annex 1、用户输入带链接 2、用户上传文档 3、推荐问题 4. 文件命名
        #  （三）类型三，场景编号：网页端：pc_web_file、PC客户端：pc_wps_file、微信小程序：wechat_mp_file 1、 创建文档，让AI保存为文档 2、 创建PPT，与创建文档类似
        #  二、业务补传字段 extra_text： extra_text传用户输入的内容
        sec_from = self.sec_text_from or "AI_WPS_SMARTASSISTANT"
        default_sec = {
            "from": sec_from,
            "scene": self.sec_text_scene,
        }
        if text:
            default_sec["extra_text"] = [text]

        if client_type not in ["pc_web", "pc_wps", "wechat_mp"]:
            client_type = "pc_web"  # 如果没有配置值默认使用 pc_web

        if category not in ["general", "annex", "file"]:
            category = "general"

        default_sec["scene"] = f"{client_type}_{category}"

        # logger.info(f"审核参数: {default_sec}")
        return default_sec


class DoubaoGatewayConfig(object):
    token = os.getenv("LLM_TOKEN", "5ZEXz9TgrGDtr5SUnh5psi8ZtdJTw9Iz")
    name = "Doubao-pro-128k"
    provider = "doubao"
    max_out_tokens = 131072
    weight = int(os.getenv("GW_DOUBAO_WEIGHT", "0"))  # 伐值为 0 - 100