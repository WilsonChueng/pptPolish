# process_ppt.py
import os
import time
from modules.data_handler import DataHandler
from modules.markdown_extractor import MarkdownExtractor
from modules.markdown2ppt import gen_ppt
from modules.kdc2xml import ppt_to_xml
import concurrent.futures
import logging
from tqdm import tqdm
import pandas as pd
import configparser


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

    # 获取root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # 忽略部分日志输出
    sse_logger = logging.getLogger('sseclient')
    sse_logger.setLevel(logging.WARNING)
    urllib3_logger = logging.getLogger('urllib3.connectionpool')
    urllib3_logger.setLevel(logging.WARNING)

    # 创建文件handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d [%(levelname)s]-8s (%(name)s) %(filename)s:%(lineno)d - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 创建控制台handler并设置自定义formatter
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)

    logger = logging.getLogger(__name__)
    return logger


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"  # 灰色（略微调整）
    blue = "\x1b[34;20m"  # 蓝色
    green = "\x1b[32m"  # 绿色
    yellow = "\x1b[33;20m"  # 黄色
    red = "\x1b[31;20m"  # 红色
    bold_red = "\x1b[31;1m"  # 粗体红色
    cyan = "\x1b[36;20m"  # 青色
    magenta = "\x1b[35;20m"  # 品红色
    reset = "\x1b[0m"  # 重置所有格式
    format = '%(asctime)s.%(msecs)03d [%(levelname)-8s] (%(name)s) %(filename)s:%(lineno)d - %(message)s'

    FORMATS = {
        logging.DEBUG: blue + format + reset,  # 调试信息使用蓝色
        logging.INFO: green + format + reset,  # 信息使用绿色
        logging.WARNING: yellow + format + reset,  # 警告信息使用黄色
        logging.ERROR: red + format + reset,  # 错误信息使用红色
        logging.CRITICAL: bold_red + format + reset  # 严重错误信息使用粗体红色
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)


def get_row_indices(total_rows, rows):
    """
    获取需要处理的行索引。

    参数:
        total_rows (int): 表格的总行数。
        rows (list of int): 需要处理的行号列表（1-based）。

    返回:
        list: 需要处理的行索引（0-based）。
    """
    return [row - 1 for row in rows if 1 <= row <= total_rows]


def process_ppt(rows_to_process=None):
    """
    处理Excel表格中的指定行，生成PPT下载链接和XML格式的PPT。

    参数:
        rows_to_process (list of int): 需要处理的行号列表（1-based）。如果为None，则处理所有行。
    """
    try:
        # 1. 加载配置文件
        config = configparser.ConfigParser()
        config_path = 'config.ini'
        config.read(config_path, encoding='utf-8')

        # 2. 初始日志配置，使用默认日志文件
        default_log_file = config['gen_ppt']['log_file']
        ppt_dir = config['gen_ppt']['ppt_dir']
        logger = setup_logging(default_log_file)

        logging.debug("开始数据处理流程。")

        # 3. 初始化模块
        data_handler = DataHandler(config['gen_ppt']['input_file'], config['gen_ppt']['output_file'])
        extractor = MarkdownExtractor(
            code_block_pattern=r'<\|code\|>{"function": "generate_ppt"}<\|endofblock\|>',
            execution_block_pattern=r'<\|execution\|>(.*?)<\|endofblock\|>'
        )

        # 4. 读取Excel文件
        input_df = data_handler.read_excel()

        # 5. 读取输出文件（如果存在）
        output_df = data_handler.read_output_excel()
        if output_df is None:
            # 如果输出文件不存在，创建一个新的DataFrame与input_df相同
            output_df = input_df.copy()
            # 初始化新列
            output_df['markdown_ppt'] = None
            output_df['theme_id'] = None
            output_df['ppt_download_link'] = None
            output_df['ppt_xml'] = None
            logging.info("创建新的输出DataFrame。")
        else:
            # 确保输出DataFrame包含必要的新列
            for column in ['markdown_ppt', 'ppt_download_link', 'ppt_xml', 'theme_id']:
                if column not in output_df.columns:
                    output_df[column] = None
                    logging.debug(f"添加缺失的列: {column}")

        # 6. 确定需要处理的行
        total_rows = len(input_df)
        if rows_to_process:
            selected_rows = get_row_indices(total_rows, rows_to_process)
            logging.info(f"总共有 {total_rows} 行数据。将处理 {len(selected_rows)} 行数据。")
        else:
            selected_rows = list(range(total_rows))
            logging.info(f"总共有 {total_rows} 行数据。将处理所有行。")

        # 7. 处理指定行，添加进度条
        # for idx in tqdm(selected_rows, desc="Processing rows"):
        #     row = input_df.iloc[idx]
        #     text = row['text']
        #     logging.debug(f"处理第 {idx + 1} 行数据。")
        #     markdown = extractor.extract_markdown(text)
        #     if markdown is None:
        #         logging.warning(f"第 {idx + 1} 行未找到目标Markdown内容。")
        #         continue
        #     output_df.at[idx, 'markdown_ppt'] = markdown
        #
        #     # 生成 PPT 下载链接
        #     logging.debug(f"正在生成第 {idx + 1} 行的 PPT 下载链接。")
        #     theme_id, download_link = gen_ppt(markdown)
        #     if not download_link:
        #         logging.error(f"第 {idx + 1} 行生成 PPT 下载链接失败。")
        #         continue
        #     output_df.at[idx, 'theme_id'] = theme_id
        #     output_df.at[idx, 'ppt_download_link'] = download_link
        #
        #     # 转换 PPT 为 XML (ppt_to_xml 现在接受 download_link)
        #     ppt_xml = ppt_to_xml(download_link=download_link, download_dir=ppt_dir,
        #                          show_xml=True if idx == 0 else False, keep_ppt=False)
        #     if not ppt_xml:
        #         logging.error(f"第 {idx + 1} 行转换 PPT 为 XML 失败。")
        #         continue
        #     output_df.at[idx, 'ppt_xml'] = ppt_xml

        def process_row(idx):
            try:
                row = input_df.iloc[idx]
                text = row['text']
                logging.debug(f"处理第 {idx + 1} 行数据。")
                # step 1: 提取目标Markdown内容
                markdown = extractor.extract_markdown(text)
                if markdown is None:
                    logging.warning(f"第 {idx + 1} 行未找到目标Markdown内容。")
                else:
                    if markdown:
                        logging.info("成功提取第 {idx + 1} 行Markdown内容。")
                    else:
                        logging.warning("第 {idx + 1} 行提取的Markdown内容为空。")
                output_df.at[idx, 'markdown_ppt'] = markdown

                # step 2: 生成 PPT 下载链接
                logging.debug(f"正在生成第 {idx + 1} 行的 PPT 下载链接。")
                theme_id, download_link = gen_ppt(markdown)
                if not download_link:
                    logging.error(f"第 {idx + 1} 行生成 PPT 下载链接失败。")
                output_df.at[idx, 'theme_id'] = theme_id
                output_df.at[idx, 'ppt_download_link'] = download_link

                # step 3: 转换 PPT 为 XML (ppt_to_xml 现在接受 download_link)
                ppt_xml = ppt_to_xml(download_link=download_link, download_dir=ppt_dir,
                                     show_xml=True if idx == 0 else False, keep_ppt=False)
                if not ppt_xml:
                    logging.error(f"第 {idx + 1} 行转换 PPT 为 XML 失败。")
                output_df.at[idx, 'ppt_xml'] = ppt_xml
                logging.error(f"第{idx + 1}行处理完成。")


            except Exception as e:
                logging.exception(f"处理第 {idx + 1} 行时发生异常: {e}")

        def parallel_process(selected_rows, max_workers=8):
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                futures = {
                    executor.submit(process_row, idx): idx for idx in selected_rows
                }

        # 7. 开始并行处理指定行
        parallel_process(selected_rows, max_workers=8)

        # 8. 保存结果到输出Excel文件，并调整格式
        data_handler.write_excel(output_df)

        logging.info("数据处理流程完成。")

    except Exception as e:
        logging.exception(f"处理过程中发生错误: {e}")


if __name__ == "__main__":
    # 开始计时
    start_time = time.time()
    # 指定需要处理的行号（1-based）
    rows_to_process = list(range(2400, 3400))
    process_ppt(rows_to_process)
    # for i in range(5):
    #     rows_to_process = list(range(i*1000, (i+1)*1000))
    #     process_ppt(rows_to_process)
    # 结束计时
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"总共用时: {elapsed_time:.2f} 秒。")
