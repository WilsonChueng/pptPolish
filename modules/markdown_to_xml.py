# modules/markdown_to_xml.py
# 功能：将提取的Markdown文本转换为XML格式。

import xml.etree.ElementTree as ET
import logging
from xml.dom import minidom

class MarkdownToXMLConverter:
    """
    Markdown到XML转换器类，用于将Markdown文本转换为指定格式的XML。

    属性:
        slide_id (int): 当前slide的ID，初始为1。
    """

    def __init__(self):
        """
        初始化MarkdownToXMLConverter类，设置slide_id为1。
        """
        self.slide_id = 1

    def reset_id(self):
        """
        重置slide_id为1，用于每次转换开始时。
        """
        self.slide_id = 1
        logging.debug("重置slide_id为1。")

    def convert(self, markdown):
        """
        将Markdown文本转换为XML格式的字符串。

        参数:
            markdown (str): 需要转换的Markdown文本。

        返回:
            str: 转换后的XML字符串。
        """
        logging.debug("开始将Markdown转换为XML。")
        lines = markdown.split('\n')
        root = ET.Element('slides')  # 创建根元素
        xml_slides = []
        current_slide = None

        for line in lines:
            line = line.strip()
            if not line:
                continue  # 跳过空行

            # 判断当前行的标题级别
            if line.startswith('# '):
                # 一级标题 - 创建新slide
                content = line[2:].strip()
                current_slide = self._create_slide(content)
                root.append(current_slide)
                logging.debug(f"创建一级标题slide")

            elif line.startswith('## '):
                # 二级标题 - 创建新slide
                content = line[3:].strip()
                current_slide = self._create_slide(content)
                root.append(current_slide)
                logging.debug(f"创建二级标题slide")

            elif line.startswith('### '):
                # 三级标题 - 创建新slide
                content = line[4:].strip()
                current_slide = self._create_slide(content)
                root.append(current_slide)
                logging.debug(f"创建三级标题slide")

            elif line.startswith('#### '):
                # 四级标题 - 添加到当前slide
                content = line[5:].strip()
                if current_slide is not None:
                    p = ET.SubElement(current_slide, 'p')
                    p.text = content
                    logging.debug(f"添加四级标题到当前slide")
                    # p = ET.Element('p')
                    # p.text = content
                    # try:
                    #     slide_elem = ET.fromstring(current_slide)
                    #     slide_elem.append(p)
                    #     current_slide = ET.tostring(slide_elem, encoding='unicode')
                    #     xml_slides[-1] = current_slide
                    #     logging.debug(f"添加四级标题到当前slide: {content}")
                    # except ET.ParseError as e:
                    #     logging.error(f"解析XML时出错: {e}")
                else:
                    logging.warning("当前没有活动的slide，无法添加四级标题。")

            else:
                # 正文内容 - 添加到当前 slide
                if line.startswith('* '):
                    line = line[2:].strip()
                if current_slide is None:
                    current_slide = self._create_slide(line)
                    logging.debug(f"创建正文内容slide")
                else:
                    if current_slide is not None:
                        p = ET.SubElement(current_slide, 'p')
                        p.text = line
                        logging.debug(f"添加正文内容到当前slide")
                        # p = ET.Element('p')
                        # p.text = line
                        # try:
                        #     slide_elem = ET.fromstring(current_slide)
                        #     slide_elem.append(p)
                        #     current_slide = ET.tostring(slide_elem, encoding='unicode')
                        #     xml_slides[-1] = current_slide
                        #     logging.debug(f"添加正文内容到当前slide: {line}")
                        # except ET.ParseError as e:
                        #     logging.error(f"解析XML时出错: {e}")
                    else:
                        logging.warning("当前没有活动的slide，无法添加正文内容。")

        # # 生成XML字符串
        # xml_content = "\n".join(xml_slides)
        # logging.debug("成功将Markdown转换为XML。")
        # return xml_content

        # 生成初步的XML字符串
        rough_string = ET.tostring(root, 'utf-8')
        # 使用minidom进行美化
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="")
        # 移除多余的空行
        pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip() and not line.startswith('<?xml')])

        logging.debug("成功将Markdown转换为指定的XML。")
        return pretty_xml

    def _create_slide_str(self, content):
        """
        创建一个slide元素，并添加内容。

        参数:
            content (str): slide内的文本内容。

        返回:
            str: 转换后的slide XML字符串。
        """
        slide = ET.Element('slide', id=str(self.slide_id))
        self.slide_id += 1
        p = ET.Element('p')
        p.text = content
        slide.append(p)
        slide_str = ET.tostring(slide, encoding='unicode')
        logging.debug(f"创建slide XML: {slide_str}")
        return slide_str

    def _create_slide(self, content):
        """
        创建一个slide元素，并添加内容。

        参数:
            content (str): slide内的文本内容。

        返回:
            xml.etree.ElementTree.Element: 转换后的slide XML元素。
        """
        slide = ET.Element('slide', id=str(self.slide_id))
        self.slide_id += 1
        p = ET.SubElement(slide, 'p')
        p.text = content
        return slide

if __name__ == '__main__':
    converter = MarkdownToXMLConverter()
    markdown = f"""
# 医佰分医疗科技公司介绍 
## 医疗科技与影像诊断
### 医学影像技术的重要性
#### 医学影像技术在疾病诊断中的作用
* 医学影像技术是现代医学诊断不可或缺的工具，它通过X射线、CT扫描、MRI、超声等手段，为医生提供直观的体内结构图像，极大地提高了疾病诊断的准确性和效率。

#### 医学影像技术对治疗方案的影响
* 凭借医学影像技术，医生能够更精确地定位病变部位，制定个性化的治疗方案，从而提高治疗效果，减少不必要的手术和药物使用。

### 医疗影像诊断技术的发展趋势
#### 技术创新与智能化
* 随着人工智能和机器学习技术的发展，医疗影像诊断正朝着自动化和智能化方向发展。例如，深度学习算法能够帮助识别复杂的图像模式，提高诊断速度和准确性。

#### 跨学科融合与精准医疗
* 医学影像技术正与遗传学、生物信息学等其他学科融合，推动精准医疗的发展。通过影像数据与遗传信息的结合，医生可以为患者提供更加个性化的治疗方案。

#### 移动医疗与远程诊断
* 移动医疗设备和远程诊断技术的进步，使得医学影像资料可以实时传输到专家手中，即使在偏远地区，患者也能获得及时的诊断和治疗建议。


## 医疗器械管理与维护
### 医疗设备在医院资产中的地位
#### 医疗设备的资产价值
* 医疗设备通常占医院总资产的大部分，是医院提供高质量医疗服务的基础。例如，先进的MRI和CT扫描仪等设备对于诊断和治疗至关重要。

#### 医疗设备对医院运营的影响
* 医疗设备的运行效率直接影响医院的服务质量和患者满意度。高效的设备管理能够确保设备的正常运行，减少因设备故障导致的手术延误和患者不便。

### 提升医疗设备管理水平的策略
#### 实施定期维护和检查
* 定期对医疗设备进行维护和检查，可以预防设备故障，延长设备使用寿命，确保设备始终处于最佳工作状态。

#### 引入先进的资产管理软件
* 利用先进的资产管理软件，可以实时监控设备状态，优化设备使用计划，减少设备闲置时间，提高设备使用效率。

#### 培训专业维护团队
* 建立一支专业的设备维护团队，对设备进行日常维护和紧急修复，可以有效减少设备故障率，保障医疗服务的连续性。

### 降低医疗设备维护成本的方法
#### 采用预防性维护策略
* 通过预防性维护，可以避免设备出现重大故障，从而减少昂贵的紧急维修费用和设备更换成本。

#### 采购高质量的医疗设备
* 购买高质量的医疗设备虽然初期投资较大，但长期来看，由于其耐用性和可靠性，可以减少维修次数和维护成本。

#### 与专业服务提供商合作
* 与专业的医疗设备服务提供商合作，可以利用其专业知识和经验，更有效地管理设备，降低维护成本，同时确保设备的性能和安全。


## 医佰分的运营理念与服务
### “客户第一，质量为先”的理念
#### 客户至上的服务承诺
* 医佰分医疗科技始终将客户需求放在首位，致力于提供定制化的服务方案，确保客户满意度和忠诚度的持续提升。

#### 质量为先的产品与服务标准
* 公司严格遵循国际质量管理体系，确保所有产品和服务均达到最高标准，以保障患者安全和医疗效果。

### 医疗设备运营管理解决方案概述
#### 全面的设备管理解决方案
* 医佰分提供从设备采购、安装、维护到升级的全方位服务，确保医疗设备的高效运行和长期稳定。

#### 定制化的维护与支持服务
* 根据不同医院和设备的特点，医佰分提供个性化的维护计划和专业技术支持，以满足客户的特定需求。

#### 智能化的资产管理平台
* 利用先进的信息技术，医佰分开发了智能化的资产管理平台，帮助医院实时监控设备状态，优化资源配置，降低运营成本。
"""
    xml = converter.convert(markdown)
    print(xml)