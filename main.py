# main.py

import os
import logging
import yaml
from modules.data_handler import DataHandler
from modules.markdown_extractor import MarkdownExtractor
from modules.markdown_to_xml import MarkdownToXMLConverter
from modules.xml_processor import XMLProcessor

def setup_logging(log_file):
    """
    设置日志记录配置。

    参数:
        log_file (str): 日志文件的路径。
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.info("日志记录已配置。")

# def resetup_logging(log_file):
#     log_dir = os.path.dirname(log_file)
#     if not os.path.exists(log_dir):
#         os.makedirs(log_dir)
#     logger = logging.getLogger()
#     for h in logger.handlers:
#         logger.removeHandler(h)
#     file_handler = logging.FileHandler(log_file, encoding='utf-8')
#     console_handler = logging.StreamHandler()
#     logger.addHandler(file_handler)
#     logger.addHandler(console_handler)
#
#     logging.info("日志记录已重新配置。")

def load_config(config_path='config/config.yaml'):
    """
    加载配置文件。

    参数:
        config_path (str): 配置文件的路径。

    返回:
        dict: 配置参数。
    """
    if not os.path.exists(config_path):
        logging.error(f"配置文件 {config_path} 不存在。")
        raise FileNotFoundError(f"配置文件 {config_path} 不存在。")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    logging.debug(f"从{config_path}加载配置文件: {config}")
    return config

def main():
    """
    主函数，协调各个模块完成数据处理流程。
    """
    try:
        # 设置日志记录
        log_file = 'logs/app.log'
        setup_logging(log_file)

        # 加载配置文件
        config = load_config()

        # if 'log_file' in config:
        #     resetup_logging(config['log_file'])

        logging.info("开始数据处理流程。")

        # 设置文件路径
        input_file = os.path.join(config['input_file'])
        output_file = os.path.join(config['output_file'])

        # 初始化模块
        data_handler = DataHandler(input_file, output_file)
        extractor = MarkdownExtractor(
            code_block_pattern=config['patterns']['code_block'],
            execution_block_pattern=config['patterns']['execution_block']
        )
        # extractor = MarkdownExtractor(
        #     code_block_pattern=r'<\|code\|>\{"function": "generate_ppt"\}<\|endofblock\|>',
        #     execution_block_pattern=r'<\|execution\|>(.*?)<\|endofblock\|>'
        # )
        converter = MarkdownToXMLConverter()
        xml_processor = XMLProcessor()

        # 读取Excel文件
        df = data_handler.read_excel()

        # 初始化新列
        df['markdown_ppt'] = None
        df['xml_ppt'] = None
        df['xml_ppt-打乱'] = None

        # 处理每一行
        for index, row in df.iterrows():
            text = row['text']
            logging.info(f"处理第{index + 1}行数据。")
            markdown = extractor.extract_markdown(text)
            if markdown is None:
                logging.warning(f"第{index + 1}行未找到目标Markdown内容。")
                continue
            df.at[index, 'markdown_ppt'] = markdown

            # 转换Markdown为XML
            converter.reset_id()
            xml = converter.convert(markdown)
            df.at[index, 'xml_ppt'] = xml

            # 打乱XML中的<p>顺序
            shuffled_xml = xml_processor.shuffle_xml(xml)
            df.at[index, 'xml_ppt-打乱'] = shuffled_xml

        # 保存结果到输出Excel文件
        data_handler.write_excel(df)

        logging.info("数据处理流程完成。")

    except Exception as e:
        logging.exception(f"处理过程中发生错误: {e}")


if __name__ == "__main__":
    main()
