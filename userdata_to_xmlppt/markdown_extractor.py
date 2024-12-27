# modules/markdown_extractor.py
# 功能：从每行的text列中提取目标Markdown内容。

import re
import logging

class MarkdownExtractor:
    """
    Markdown提取器类，用于从文本中提取目标Markdown内容。

    属性:
        CODE_BLOCK_PATTERN (str): 匹配code块的正则表达式模式。
        EXECUTION_BLOCK_PATTERN (str): 匹配execution块的正则表达式模式。
    """

    def __init__(self, code_block_pattern, execution_block_pattern):
        """
        初始化MarkdownExtractor类。

        参数:
            code_block_pattern (str): 匹配code块的正则表达式模式。
            execution_block_pattern (str): 匹配execution块的正则表达式模式。
        """
        self.CODE_BLOCK_PATTERN = code_block_pattern
        self.EXECUTION_BLOCK_PATTERN = execution_block_pattern

    def extract_markdown(self, text):
        """
        从给定的text中提取目标Markdown内容。

        参数:
            text (str): 包含用户数据的文本。

        返回:
            str or None: 提取的Markdown内容，如果未找到则返回None。
        """
        logging.debug("开始提取Markdown内容。")
        # 查找第一个code块的位置
        code_block_match = re.search(self.CODE_BLOCK_PATTERN, text, re.DOTALL)
        if not code_block_match:
            logging.warning("未找到目标code块。")
            # print("未找到目标code块。")
            return None  # 未找到目标code块

        # logging.debug("找到目标code块。")
        # snippet = text[code_block_match.start():code_block_match.end()]
        # print(f"找到目标code块: {snippet}")

        # 获取code块之后的文本
        post_code_text = text[code_block_match.end():]

        # 查找execution块
        execution_block_match = re.search(self.EXECUTION_BLOCK_PATTERN, post_code_text, re.DOTALL)
        if not execution_block_match:
            logging.warning("未找到execution块。")
            # 打印部分文本以帮助调试
            snippet = post_code_text[:100] + "..." if len(post_code_text) > 100 else post_code_text
            logging.debug(f"post_code_text snippet: {snippet}")
            return None  # 未找到execution块

            # 提取Markdown内容并去除前后空白字符
        markdown = execution_block_match.group(1).strip()
        if markdown:
            logging.info("成功提取Markdown内容。")
        else:
            logging.warning("提取的Markdown内容为空。")
        return markdown