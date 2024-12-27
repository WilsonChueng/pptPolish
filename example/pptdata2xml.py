import pandas as pd
import re
import xml.etree.ElementTree as ET
import random
import os


# 数据读取模块
class DataHandler:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def read_excel(self):
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"输入文件 {self.input_file} 不存在。")
        df = pd.read_excel(self.input_file)
        if 'id' not in df.columns or 'text' not in df.columns:
            raise ValueError("输入Excel文件必须包含'id'和'text'两列。")
        return df

    def write_excel(self, df):
        df.to_excel(self.output_file, index=False)
        print(f"处理完成，结果已保存到 {self.output_file}。")


# 数据提取模块
class MarkdownExtractor:
    CODE_BLOCK_PATTERN = r'<\|code\|>\{"function": "generate_ppt"\}<\|endofblock\|>'
    EXECUTION_BLOCK_PATTERN = r'<\|execution\|>(.*?)<\|endofblock\|>'

    @staticmethod
    def extract_markdown(text):
        code_block_match = re.search(MarkdownExtractor.CODE_BLOCK_PATTERN, text, re.DOTALL)
        if not code_block_match:
            return None  # 未找到目标code块
        post_code_text = text[code_block_match.end():]
        execution_block_match = re.search(MarkdownExtractor.EXECUTION_BLOCK_PATTERN, post_code_text, re.DOTALL)
        if not execution_block_match:
            return None  # 未找到execution块
        markdown = execution_block_match.group(1).strip()
        return markdown


# Markdown转换模块
class MarkdownToXMLConverter:
    def __init__(self):
        self.slide_id = 1

    def reset_id(self):
        self.slide_id = 1

    def convert(self, markdown):
        lines = markdown.split('\n')
        xml_slides = []
        current_slide = None

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue  # 跳过空行

            if line.startswith('# '):
                current_slide = self._create_slide(line[2:].strip())
                xml_slides.append(current_slide)
            elif line.startswith('## '):
                current_slide = self._create_slide(line[3:].strip())
                xml_slides.append(current_slide)
            elif line.startswith('### '):
                current_slide = self._create_slide(line[4:].strip())
                xml_slides.append(current_slide)
            elif line.startswith('#### '):
                current_slide = self._create_slide(line[5:].strip())
                xml_slides.append(current_slide)
            else:
                if current_slide is None:
                    current_slide = self._create_slide(line)
                else:
                    p = ET.Element('p')
                    p.text = line
                    current_slide.append(p)
                # 检查下一个行是否需要关闭 slide
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith(('# ', '## ', '### ', '#### ')):
                        xml_slides.append(current_slide)
                        current_slide = None

        if current_slide is not None:
            xml_slides.append(current_slide)

        # 生成XML字符串
        xml_content = "\n".join([ET.tostring(slide, encoding='unicode') for slide in xml_slides])
        return xml_content

    def _create_slide(self, content):
        slide = ET.Element('slide', id=str(self.slide_id))
        self.slide_id += 1
        p = ET.Element('p')
        p.text = content
        slide.append(p)
        return ET.tostring(slide, encoding='unicode')


# XML处理模块
class XMLProcessor:
    @staticmethod
    def shuffle_xml(xml_str):
        slides = ET.Element('slides')  # 创建一个根元素
        for slide_elem in ET.fromstring(f"<slides>{xml_str}</slides>"):
            slide = ET.Element('slide', id=slide_elem.attrib['id'])
            p_elements = list(slide_elem.findall('p'))
            random.shuffle(p_elements)
            for p in p_elements:
                slide.append(p)
            slides.append(slide)

        # 重新赋予id
        for idx, slide in enumerate(slides.findall('slide'), start=1):
            slide.set('id', str(idx))

        # 生成新的XML字符串
        new_xml = "\n".join([ET.tostring(slide, encoding='unicode') for slide in slides.findall('slide')])
        return new_xml


# 主控制模块
class PPTProcessor:
    def __init__(self, input_file, output_file):
        self.data_handler = DataHandler(input_file, output_file)
        self.extractor = MarkdownExtractor()
        self.converter = MarkdownToXMLConverter()
        self.xml_processor = XMLProcessor()

    def process(self):
        df = self.data_handler.read_excel()
        # 初始化新列
        df['markdown_ppt'] = None
        df['xml_ppt'] = None
        df['xml_ppt-打乱'] = None

        for index, row in df.iterrows():
            text = row['text']
            markdown = self.extractor.extract_markdown(text)
            if markdown is None:
                print(f"第{index + 1}行未找到目标Markdown内容。")
                continue
            df.at[index, 'markdown_ppt'] = markdown

            # 转换Markdown为XML
            self.converter.reset_id()
            xml = self.converter.convert(markdown)
            df.at[index, 'xml_ppt'] = xml

            # 打乱XML中的<p>顺序
            shuffled_xml = self.xml_processor.shuffle_xml(xml)
            df.at[index, 'xml_ppt-打乱'] = shuffled_xml

        self.data_handler.write_excel(df)


# 运行脚本
def main():
    input_file = 'input.xlsx'  # 请确保此文件存在于当前目录
    output_file = 'output.xlsx'
    processor = PPTProcessor(input_file, output_file)
    try:
        processor.process()
    except Exception as e:
        print(f"处理过程中发生错误: {e}")


if __name__ == "__main__":
    main()
