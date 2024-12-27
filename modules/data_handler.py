# modules/data_handler.py
# 功能：负责读取输入的Excel文件，并将处理后的数据写入输出Excel文件。

import pandas as pd
import os
import logging
from openpyxl import load_workbook
from openpyxl.styles import Alignment


class DataHandler:
    """
    数据处理类，用于读取和写入Excel文件。

    属性:
        input_file (str): 输入Excel文件的路径。
        output_file (str): 输出Excel文件的路径。
    """

    def __init__(self, input_file, output_file):
        """
        初始化DataHandler类。

        参数:
            input_file (str): 输入Excel文件的路径。
            output_file (str): 输出Excel文件的路径。
        """
        self.input_file = input_file
        self.output_file = output_file

    def read_excel(self):
        """
        读取输入的Excel文件，并验证必要的列是否存在。

        返回:
            pandas.DataFrame: 读取的DataFrame。

        异常:
            FileNotFoundError: 如果输入文件不存在。
            ValueError: 如果必要的列不存在。
        """
        logging.debug(f"尝试读取输入文件: {self.input_file}")
        if not os.path.exists(self.input_file):
            logging.error(f"输入文件 {self.input_file} 不存在。")
            raise FileNotFoundError(f"输入文件 {self.input_file} 不存在。")
        df = pd.read_excel(self.input_file)
        if 'id' not in df.columns or 'text' not in df.columns:
            logging.error("输入Excel文件必须包含'id'和'text'两列。")
            raise ValueError("输入Excel文件必须包含'id'和'text'两列。")
        logging.info("成功读取输入文件。")
        return df

    def read_output_excel(self):
        """
        读取输出的Excel文件，如果不存在则返回None。

        返回:
            pandas.DataFrame or None: 读取的DataFrame，或None如果文件不存在。
        """
        if not os.path.exists(self.output_file):
            logging.info(f"输出文件 {self.output_file} 不存在，将创建新的文件。")
            return None
        logging.info(f"尝试读取输出文件: {self.output_file}")
        try:
            df = pd.read_excel(self.output_file)
            logging.info("成功读取输出文件。")
            return df
        except Exception as e:
            logging.error(f"读取输出文件时发生错误: {e}")
            return None

    def write_excel(self, df):
        """
        将处理后的DataFrame写入输出Excel文件。

        参数:
            df (pandas.DataFrame): 处理后的DataFrame。
        """
        logging.debug(f"尝试写入输出文件: {self.output_file}")
        df.to_excel(self.output_file, index=False, sheet_name='Sheet1')
        logging.info(f"成功写入输出文件。")

        try:
            # 首先需要创建一个带格式的workbook
            writer = pd.ExcelWriter(self.output_file, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            workbook = writer.book

            # 创建一个格式对象
            text_format = workbook.add_format({
                'text_wrap': True,  # 自动换行
                'align': 'left',  # 水平居左
                'valign': 'top',  # 垂直居上
            })
            link_format = workbook.add_format({
                'text_wrap': True,  # 自动换行
                'align': 'left',  # 水平居左
                'valign': 'vcenter',  # 垂直居上
                'font_color': 'blue',  # 字体颜色为蓝色
                'underline': 1,  # 下划线
            })

            # 应用格式
            worksheet = writer.sheets['Sheet1']  # 假设工作表名为'Sheet1'

            # 设置列宽和格式
            worksheet.set_column(1, 2, 80, text_format)  # 参数：起始列，结束列，宽度，格式
            worksheet.set_column(3, 5, 40, link_format)
            worksheet.set_column(5, 5, 80, text_format)

            # 设置行高
            for row in range(1, worksheet.dim_rowmax):  # 从第2行开始
                worksheet.set_row(row, 100)  # 参数：行号，高度

            writer._save()
            logging.info("成功调整Excel格式。")
        except Exception as e:
            logging.error(f"调整Excel格式时发生错误: {e}")
