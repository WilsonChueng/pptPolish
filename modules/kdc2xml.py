import json
import logging
import tempfile
from typing import Literal, List, Callable
from io import IOBase, StringIO
from xml.dom import minidom

import requests
import base64
import os
import hashlib

_cache_path = "../clean_file/cache"


def base64decode(encode: str) -> bytes:
    missing_padding = 4 - len(encode) % 4
    if missing_padding:
        encode += '=' * missing_padding
    return base64.b64decode(encode)


BlockType = Literal['para', 'table', 'component', 'textbox', 'drawing']


def _to_class_list(d: dict, key: str, cls) -> list:
    if key not in d:
        return []
    v = d[key]
    if v is None:
        return []
    return [cls(x) for x in v]


class Node(dict):
    @property
    def outline_level(self) -> int:
        return self.get('outline_level', 10)

    @property
    def blocks(self) -> List['Block']:
        return _to_class_list(self, 'blocks', Block)

    @property
    def children(self) -> List['Node']:
        return _to_class_list(self, 'children', Node)


class RunProp(dict):
    @property
    def size(self) -> int:
        return self.get('size', 0)

    @property
    def color(self) -> str:
        return self.get('color', '')

    @property
    def font_ascii(self) -> str:
        return self.get('font_ascii', '')

    @property
    def font_east_asia(self) -> str:
        return self.get('font_east_asia', '')

    @property
    def bold(self) -> bool:
        return self.get('bold', False)

    @property
    def italic(self) -> bool:
        return self.get('italic', False)

    @property
    def underline(self) -> bool:
        return self.get('underline', False)

    @property
    def strike(self) -> bool:
        return self.get('strike', False)


class Run(dict):
    @property
    def prop(self) -> RunProp:
        return RunProp(self.get('prop', {}))

    @property
    def id(self) -> str:
        return self.get('id', '')

    @property
    def text(self) -> str:
        return self.get('text', '')


ParaAlignment = Literal['left', 'right', 'center', 'justify', 'distribute', 'fill', 'center_continuous']


class ParaProp(dict):
    @property
    def alignment(self) -> ParaAlignment:
        return self.get('alignment', )

    @property
    def def_run_prop(self) -> RunProp:
        return RunProp(self.get('def_run_prop', {}))

    @property
    def outline_level(self) -> int:
        return self.get('outline_level', 10)

    @property
    def list_string(self) -> str:
        return self.get('list_string', '')


class Para(dict):
    @property
    def runs(self) -> List[Run]:
        return _to_class_list(self, 'runs', Run)

    @property
    def prop(self) -> ParaProp:
        return ParaProp(self.get('prop', {}))


class TableCell(dict):
    @property
    def blocks(self) -> List['Block']:
        return _to_class_list(self, 'blocks', Block)

    @property
    def row_span(self) -> int:
        return self.get('row_span', 1)

    @property
    def col_span(self) -> int:
        return self.get('col_span', 1)

    @property
    def id(self) -> str:
        return self.get('id', '')


class TableRow(dict):
    @property
    def cells(self) -> List[TableCell]:
        return _to_class_list(self, 'cells', TableCell)


class Table(dict):
    @property
    def rows(self) -> List[TableRow]:
        return _to_class_list(self, 'rows', TableRow)


class Textbox(dict):
    @property
    def blocks(self) -> List['Block']:
        return _to_class_list(self, 'blocks', Block)


ComponentType = Literal['image', 'audio', 'video']


class Media(dict):
    @property
    def id(self) -> str:
        return self['id']

    @property
    def data(self) -> str:
        return self.get('data')

    @property
    def mime_type(self) -> str:
        return self.get('mime_type')

    @property
    def url(self) -> str:
        return self.get('url')


class Component(dict):
    @property
    def type(self) -> ComponentType:
        return self.get('type', '')

    @property
    def media_id(self) -> str:
        return self['media_id']


class Drawing(dict):
    @property
    def media_id(self) -> str:
        return self.get('media_id')

    @property
    def type(self) -> str:
        return self.get('type')

    @property
    def url(self) -> str:
        return self.get('url')


class Block(dict):
    @property
    def type(self) -> BlockType:
        return self['type']

    @property
    def para(self) -> Para:
        return Para(self['para'])

    @property
    def table(self) -> Table:
        return Table(self['table'])

    @property
    def component(self) -> Component:
        return Component(self['component'])

    @property
    def textbox(self) -> Textbox:
        return Textbox(self['textbox'])

    @property
    def drawing(self) -> Drawing:
        return Drawing(self['drawing'])


class Slide(dict):
    @property
    def shape_tree(self) -> List[Block]:
        return _to_class_list(self, 'shape_tree', Block)


class SlideContainer(dict):
    @property
    def category(self) -> str:
        return self.get('category', '')

    @property
    def slides(self) -> List[Slide]:
        return _to_class_list(self, 'slides', Slide)


class Comment(dict):
    pass


class DocProp(dict):
    @property
    def page_count(self) -> int:
        return self.get('page_count', 0)

    @property
    def page_props(self) -> list:
        # todo
        return []


class PresProp(dict):
    @property
    def slide_size(self) -> dict:
        return self.get('slide_size', {})

    @property
    def note_size(self) -> dict:
        # todo
        return self.get('note_size', {})


class Document(dict):
    @property
    def prop(self) -> DocProp:
        """
        文档属性
        """
        return DocProp(self.get('prop', {}))

    @property
    def blocks(self) -> List[Block]:
        """
        文档的内容按顺序组织成一个数组。tree与blocks字段必须有一个存在。
        """
        return _to_class_list(self, 'blocks', Block)

    def media(self, id: str) -> Media:
        for m in self.medias:
            if m.id == id:
                return m
        raise KeyError(f'media {id} not found')

    @property
    def medias(self) -> List[Media]:
        """
        文档中的媒体对象组织成一个数组
        """
        return _to_class_list(self, 'medias', Media)

    @property
    def comments(self) -> List[Comment]:
        """
        文档中的所有批注（评论）体组织成一个数组
        """
        return _to_class_list(self, 'comments', Comment)

    @property
    def tree(self) -> Node:
        """
        以大纲级别为层级，将文档的内容组织成一棵树。tree与blocks字段必须有一个存在。
        """
        return Node(self['tree'])

    def to_streamlit(self):
        StreamlitRenderer(self).render()

    def to_html(self, media_dir: str) -> str:
        out = StringIO()
        f = HTMLRenderer(self, media_dir)
        f.render(out)
        return out.getvalue()

    def to_markdown(self, media_dir: str) -> str:
        out = StringIO()
        MarkdownRender(self, media_dir).render(out)
        return out.getvalue()


class Presentation(dict):
    @property
    def prop(self) -> PresProp:
        """
        画布大小属性
        """
        return PresProp(self.get('prop', {}))

    @property
    def slide_containers(self) -> List[SlideContainer]:
        """
        幻灯片、母版、版式容器对象
        """
        return _to_class_list(self, 'slide_containers', SlideContainer)

    def media(self, id: str) -> Media:
        for m in self.medias:
            if m.id == id:
                return m
        raise KeyError(f'media {id} not found')

    @property
    def medias(self) -> List[Media]:
        """
        媒体资源文件，图片、音视频等
        """
        return _to_class_list(self, 'medias', Media)

    # def to_streamlit(self):
    #     StreamlitRenderer(self).render()

    def to_html(self, media_dir: str) -> str:
        out = StringIO()
        f = PPTHTMLRenderer(self, media_dir)
        f.render(out)
        return out.getvalue()

    # def to_markdown(self, media_dir: str) -> str:
    #     out = StringIO()
    #     MarkdownRender(self, media_dir).render(out)
    #     return out.getvalue()


import streamlit as st


class StreamlitRenderer:
    def __init__(self, doc: Document):
        self.doc: Document = doc

    def render(self):
        self._render_node(self.doc.tree)

    def _render_node(self, node: Node):
        for n in node.blocks:
            self._render_block(n)
        for c in node.children:
            self._render_node(c)

    def _render_block(self, block: Block):
        match block.type:
            case 'para':
                self._render_para(block.para)
            case 'table':
                self._render_table(block.table)
            case 'textbox':
                self._render_textbox(block.textbox)
            case 'component':
                self._render_component(block.component)
            case 'drawing':
                self._render_drawing(block.drawing)

    def _render_table(self, table: Table):
        _rows = []
        for row in table.rows:
            _row = []
            for cell in row.cells:
                cell_text = self._cell_text(cell)
                _row.append(cell_text)
            _rows.append(_row)
        st.table(_rows)

    def _cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != 'para':
                continue
            para_text = ''
            for run in block.para.runs:
                para_text += self._run_text(run)
            texts.append(para_text)
        return "\n".join(texts)

    def _render_textbox(self, textbox: Textbox):
        with st.container(border=None):
            for block in textbox.blocks:
                if block.type != 'para':
                    continue

                line = ''
                for run in block.para.runs:
                    line += run.text
                st.markdown(line)

    def _render_para(self, para: Para, out: IOBase):
        text = ''
        for run in para.runs:
            text += self._run_text(run)

        match para.prop.outline_level:
            case 1:
                st.header(text)
            case 2:
                st.header(text)
            case 3:
                st.header(text)
            case 4:
                st.header(text)
            case 5:
                st.header(text)
            case _:
                st.markdown(text)

    def _run_text(self, run: Run) -> str:
        text = run.text
        prop = run.prop

        if prop.bold:
            text = f'<b>{text}</b>'
        if prop.italic:
            text = f'<i>{text}</i>'
        if prop.underline:
            text = f'<u>{text}</u>'
        if prop.strike:
            text = f'<strike>{text}</strike>'

        return text


class HTMLRenderer:
    def __init__(self, doc: Document, media_dir: str):
        self.doc: Document = doc
        self.media_dir: str = media_dir
        self.images: dict[str, bytes] = {}

    def _render_node(self, node: Node, out: IOBase):
        for n in node.blocks:
            self._render_block(n, out)
        for c in node.children:
            self._render_node(c, out)

    def _render_block(self, block: Block, out: IOBase):
        match block.type:
            case 'para':
                self._render_para(block.para, out)
            case 'table':
                self._render_table(block.table, out)
            case 'textbox':
                self._render_textbox(block.textbox, out)
            case 'component':
                self._render_component(block.component, out)
            case 'drawing':
                self._render_drawing(block.drawing, out)

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != 'para':
                continue
            para_text = ''
            for run in block.para.runs:
                para_text += self._render_run(run)
            texts.append(para_text + "<br>")
        return "<br>".join(texts)

    def _render_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            out.write('<tr>')
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                out.write(f'<td rowspan="{cell.row_span}" colspan="{cell.col_span}">{cell_text}</td>')
            out.write("</tr>\n")
        out.write('</table>\n')

    def _render_textbox(self, textbox: Textbox, out: IOBase):
        lines = []
        for block in textbox.blocks:
            if block.type != 'para':
                continue

            line = ''
            for run in block.para.runs:
                line += run.text
            lines.append(line)

        text = '\n'.join(lines)
        out.write(f'<div>\n{text}\n</div>\n')

    def _format_media(self, media: Media, out: IOBase):
        if media.url:
            url = media.url.replace('ks3-cn-beijing-internal', 'ks3-cn-beijing')
        elif media.data:
            url = f"{self.media_dir}/{media.id}"

        out.write(f'<img src="{url}" style="width:100%;max-width:fit-content;">\n')

    def _render_drawing(self, block: Drawing, out: IOBase):
        t = block.type
        if t == 'image':
            media = self.doc.media(block.media_id)
            self._format_media(media, out)

    def _render_component(self, component: Component, out: IOBase):
        t = component['type']
        if t == 'image':
            media = self.doc.media(component.media_id)
            self._format_media(media, out)

    def _render_para(self, para: Para, out: IOBase):
        text = ''
        for run in para.runs:
            text += self._render_run(run)

        match para.prop.outline_level:
            case 1:
                out.write(f'<section>{text}\n')
                out.write(f'<h1>{text}</h1>\n')
            case 2:
                out.write(f'<h2>{text}</h2>\n')
            case 3:
                out.write(f'<h3>{text}</h3>\n')
            case 4:
                out.write(f'<h4>{text}</h4>\n')
            case 5:
                out.write(f'<h5>{text}</h5>\n')
            case _:
                out.write(f'<p>{text}</p>\n')

    def _render_run(self, run: Run) -> str:
        text = run.text
        prop = run.prop

        if prop.bold:
            text = f'<b>{text}</b>'
        if prop.italic:
            text = f'<i>{text}</i>'
        if prop.underline:
            text = f'<u>{text}</u>'
        if prop.strike:
            text = f'<strike>{text}</strike>'

        return text

    def render(self, out: IOBase):
        self._render_node(self.doc.tree, out)


class PPTHTMLRenderer:
    def __init__(self, doc: Presentation, media_dir: str):
        self.doc: Presentation = doc
        self.media_dir: str = media_dir
        self.images: dict[str, bytes] = {}
        self.media_id = 1

    def _render_slide_container(self, slide_container: SlideContainer, out: IOBase):
        out.write(f'<slides>\n')
        for i, slide in enumerate(slide_container.slides):
            self._render_slide(slide, i + 1, out)
        out.write(f'</slides>\n')

    def _render_slide(self, slide: Slide, slide_id, out: IOBase):
        out.write(f'<slide index="{slide_id}">\n')

        def sort_blocks(blocks):
            return sorted(blocks, key=lambda block: (block["bounding_box"]["y1"], block["bounding_box"]["x1"]))

        for block in sort_blocks(slide.shape_tree):
            self._render_block(block, out)

        out.write(f'</slide>\n')

    def _render_block(self, block: Block, out: IOBase):
        match block.type:
            case 'para':
                self._render_para(block.para, out)
            case 'table':
                self._render_table(block.table, out)
            case 'textbox':
                self._render_textbox(block.textbox, out)
            case 'component':
                self._render_component(block.component, out)
            case 'drawing':
                self._render_drawing(block.drawing, out)

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != 'para':
                continue
            para_text = ''
            for run in block.para.runs:
                para_text += self._render_run(run)
            texts.append(para_text + "<br>")
        return "<br>".join(texts)

    def _render_table(self, table: Table, out: IOBase):
        out.write("<table>\n")
        for row in table.rows:
            out.write('<tr>')
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                out.write(f'<td rowspan="{cell.row_span}" colspan="{cell.col_span}">{cell_text}</td>')
            out.write("</tr>\n")
        out.write('</table>\n')

    def _render_textbox(self, textbox: Textbox, out: IOBase):
        lines = []
        for block in textbox.blocks:
            if block.type != 'para':
                continue

            line = ''
            for run in block.para.runs:
                line += run.text
            # 设置一个特定字符串列表，如果text是这个列表中的一个，就不写入
            # special_strings = ["汇报人：WPS",
            #                    "WPS , a click to unlimited possibilities",
            #                    "WPS,a click to unlimited possibilities",
            #                    " WPS,a click to unlimited possibilities"
            #                    "金山办公软件有限公司",
            #                    "单击此处添加副标题",
            #                    "单击此处添加文档副标题内容",
            #                    "添加文档副标题"
            #                    "20XX",
            #                    "20XX/01/01"]
            special_strings = ["汇报人：WPS",
                               "汇报人: WPS",
                               "a click to unlimited possibilities",
                               "A CLICK TO UNLIMITED POSSIBILITIES",
                               "金山办公软件有限公司",
                               "单击此处",
                               "添加副标题",
                               "添加文档副标题",
                               "20XX",
                               "JSBG1988",
                               "YOUR LOGO",
                               "COLORFUL"]
            for s in special_strings:
                if s in line:
                    line = ''
                    break
            if line != '':
                new_para = '<p>' + line + '</p>'
                lines.append(new_para)

        text = '\n'.join(lines)
        if text != '':
            out.write(f'{text}\n')
            # out.write(f'<div>\n{text}\n</div>\n')

    def _format_media(self, media: Media, out: IOBase):
        if media.url:
            url = media.url.replace('ks3-cn-beijing-internal', 'ks3-cn-beijing')
        elif media.data:
            url = f"{self.media_dir}/{media.id}"

        # out.write(f'<img src="{url}" style="width:100%;max-width:fit-content;">\n')
        out.write(f'<img id="{self.media_id}">\n')
        self.media_id += 1

    def _render_drawing(self, block: Drawing, out: IOBase):
        t = block.type
        if t == 'image':
            media = self.doc.media(block.media_id)
            self._format_media(media, out)

    def _render_component(self, component: Component, out: IOBase):
        t = component['type']
        if t == 'image':
            media = self.doc.media(component.media_id)
            self._format_media(media, out)

    def _render_para(self, para: Para, out: IOBase):
        text = ''
        for run in para.runs:
            text += self._render_run(run)

        match para.prop.outline_level:
            case 1:
                out.write(f'<section>{text}\n')
                out.write(f'<h1>{text}</h1>\n')
            case 2:
                out.write(f'<h2>{text}</h2>\n')
            case 3:
                out.write(f'<h3>{text}</h3>\n')
            case 4:
                out.write(f'<h4>{text}</h4>\n')
            case 5:
                out.write(f'<h5>{text}</h5>\n')
            case _:
                out.write(f'<p>{text}</p>\n')

    def _render_run(self, run: Run) -> str:
        text = run.text
        prop = run.prop

        if prop.bold:
            text = f'<b>{text}</b>'
        if prop.italic:
            text = f'<i>{text}</i>'
        if prop.underline:
            text = f'<u>{text}</u>'
        if prop.strike:
            text = f'<strike>{text}</strike>'

        return text

    def render(self, out: IOBase):
        for slide_container in self.doc.slide_containers:
            if slide_container.category == 'slides':
                # 只渲染正文幻灯片，不要母版和版式和备注
                self._render_slide_container(slide_container, out)


class MarkdownRender:
    def __init__(self, doc: Document, media_dir: str):
        self.doc = doc
        self.media_dir = media_dir
        self.images = {}

    def render(self, out: IOBase):
        self._render_node(self.doc.tree, out)

    def _render_node(self, node: Node, out: IOBase):
        for n in node.blocks:
            self._render_block(n, out)
        for c in node.children:
            self._render_node(c, out)

    def _render_block(self, block: Block, out: IOBase):
        match block.type:
            case 'para':
                self._render_para(block.para, out)
            case 'table':
                self._render_table(block.table, out)
            case 'textbox':
                self._render_textbox(block.textbox, out)
            case 'component':
                self._render_component(block.component, out)
            case 'drawing':
                self._render_drawing(block.component, out)

    def _join_cell_text(self, cell: TableCell) -> str:
        texts = []
        for block in cell.blocks:
            if block.type != 'para':
                continue
            para_text = ''
            for run in block.para.runs:
                para_text += self._render_run(run)
            texts.append(para_text + "<br>")
        return "<br>".join(texts)

    def _render_table(self, table: Table) -> str:
        text = '\n<table>\n'
        for row in table.rows:
            text += '<tr>'
            for cell in row.cells:
                cell_text = self._join_cell_text(cell)
                text += f'<td rowspan="{cell.row_span}" colspan="{cell.col_span}">{cell_text}</td>'
            text += "</tr>\n"
        text += '</table>\n\n'
        return text

    def _render_textbox(self, textbox: Textbox) -> str:
        lines = []
        for block in textbox.blocks:
            if block.type != 'para':
                continue

            line = ''
            for run in block.para.runs:
                line += run.text
            lines.append(line)

        text = '\n'.join(lines)
        return text + "\n\n"

    def _render_drawing(self, block: Drawing, out: IOBase):
        t = block.type
        if t == 'image':
            media = self.doc.media(block.media_id)
            if media.url:
                url = media.url.replace('ks3-cn-beijing-internal', 'ks3-cn-beijing')
                out.write(f'![]({url})\n\n')
            elif media.data:
                self.images[media.id] = base64decode(media.data)
                out.write(f'![]({self.media_dir}/{media.id})\n\n')

    def _render_component(self, block: Component, out: IOBase):
        t = block.type
        if t == 'image':
            media = self.doc.media(block.media_id)
            if media.url:
                url = media.url.replace('ks3-cn-beijing-internal', 'ks3-cn-beijing')
                out.write(f'![]({url})\n\n')
            elif media.data:
                self.images[media.id] = base64decode(media.data)
                out.write(f'![]({self.media_dir}/{media.id})\n\n')

    def _render_para(self, para: Para) -> str:
        text = ''
        match para.prop.outline_level:
            case 1:
                text += '# '
            case 2:
                text += '## '
            case 3:
                text += '### '
            case 4:
                text += '#### '
            case 5:
                text += '##### '

        for run in para.runs:
            text += self._render_run(run)

        text += "\n\n"
        return text

    def _render_run(self, run: Run) -> str:
        text = run.text
        prop = run.prop

        if prop.bold:
            text = f'**{text}**'
        if prop.italic:
            text = f'){text}_'
        if prop.underline:
            text = f'<u>{text}</u>'
        if prop.strike:
            text = f'~~{text}~~'

        return text

    def format(self, out: IOBase):
        self._render_node(self.doc.tree, out)


def _bytes_hash(content: bytes) -> str:
    h = hashlib.sha1()
    h.update(content)
    return h.hexdigest()


def _render_file_kdc(name: str, content: bytes) -> dict:
    data = {
        'format': 'kdc',
        'include_elements': 'all',
        'filename': name,
    }
    files = {
        'form_file': [name, content],
    }
    resp = requests.post('https://api.wps.cn/v7/longtask/exporter/export_file_content', files=files, data=data)

    return resp.json()['data']


def parse_file_content(name: str, content: bytes, cache: bool = True):
    file_hash = _bytes_hash(content)
    cache_path = f'{_cache_path}/kdc_{file_hash}.json'
    # 获取name的后缀名
    suffix = name.split('.')[-1]

    if cache and os.path.exists(cache_path):
        with open(cache_path, 'r', encoding="utf8") as f:
            json_msg = f.read()
            print(json_msg)
            data = json.loads(json_msg)  # kdc格式信息
        if suffix == 'pptx' or suffix == 'ppt':
            return Presentation(data['doc'])
        return Document(data['doc'])  # data['doc']是kdc格式数据，构造KDC文档的根对象（Document对象）

    data = _render_file_kdc(name, content)
    if 'medias' in data['doc']:
        for m in data['doc']['medias']:
            if m['url']:
                media_url = m['url'].replace('ks3-cn-beijing-internal', 'ks3-cn-beijing')
                resp = requests.get(media_url)
                if resp.status_code != 200:
                    raise Exception(f'fetch media {media_url} failed with {resp.status_code}')
                m['data'] = base64.b64encode(resp.content).decode('utf8')
                m['url'] = ''
    match suffix:
        case 'pptx' | 'ppt':
            kdc = Presentation(data['doc'])
        case _:
            kdc = Document(data['doc'])

    if cache:
        if not os.path.exists(_cache_path):
            os.mkdir(_cache_path)
        cache_data = json.dumps(data, ensure_ascii=False, indent='  ')
        with open(cache_path, 'w+', encoding="utf8") as f:
            f.write(cache_data)
    return kdc


def ppt_to_xml(file_path: str = None, download_link: str = None, download_dir: str = '../downloads',
               cache: bool = False,
               show_xml: bool = False,
               keep_ppt: bool = False):
    """
    将PPT文件转换为XML格式。可以通过文件路径或下载链接提供PPT文件。

    参数:
        file_path (str): PPT文件的路径。
        download_link (str): PPT文件的下载链接。
        cache (bool): 是否缓存下载的文件。

    返回:
        str or None: 转换后的XML内容，如果失败则返回None。
    """
    temp_download = False
    try:
        if download_link:
            # # 下载PPT文件到临时目录
            # logging.debug(f"开始下载 PPT")
            # response = requests.get(download_link, stream=True)
            # response.raise_for_status()
            # # with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp_file:
            # os.makedirs(download_dir, exist_ok=True)
            # # 取download_link的后10位作为文件名
            # randomstr = download_link[-10:]
            # tmp_file_path = os.path.join(download_dir, f'{randomstr}.pptx')
            # with open(tmp_file_path, 'wb') as tmp_file:
            #     for chunk in response.iter_content(chunk_size=8192):
            #         if chunk:
            #             tmp_file.write(chunk)
            #     tmp_file_path = tmp_file.name
            # logging.info(f"成功下载 PPT到临时文件: {tmp_file_path}")
            # file_path = tmp_file_path
            # temp_download = True
            # content = open(file_path, 'rb').read()
            # name = os.path.basename(file_path)

            logging.debug(f"开始读取PPT内容")
            response = requests.get(download_link, stream=True)
            response.raise_for_status()  # 检查 HTTP 状态码，如果不是 200 则抛出异常
            content = response.content  # 获取二进制内容
            name = f"{download_link[-10:]}.pptx"
        else:
            if not file_path:
                logging.error("必须提供file_path或download_link参数。")
                return None
            logging.debug(f"开始读取PPT内容")
            content = open(file_path, 'rb').read()
            name = os.path.basename(file_path)

        logging.debug(f"开始转换 PPT 为 XML")
        kdc = parse_file_content(name, content, cache)
        xml_content = kdc.to_html(media_dir='/media')
        if show_xml:
            print(f"xml_content: {xml_content}")

        # # 美化XML
        # reparsed = minidom.parseString(xml_content)
        # pretty_xml = reparsed.toprettyxml(indent="")
        #
        # # 移除XML声明
        # pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip() and not line.startswith('<?xml')])
        #
        # print(pretty_xml)
        logging.info(f"成功转换 PPT 为 XML")

        # 如果是临时下载的文件，删除临时文件
        if temp_download and not keep_ppt:
            os.remove(file_path)
            logging.error(f"删除临时下载的 PPT 文件: {file_path}")

        return xml_content
    except Exception as e:
        logging.error(f"PPT 转换为 XML 失败: {e}")
        return None


if __name__ == '__main__':
    ppt_to_xml(
        download_link='https://meihua-download.ks3-cn-beijing.ksyuncs.com/temp/20241224/pptx/c6620602-118c-4e48-acb9-a69737e4c2b4.pptx?Expires=1735133749&AWSAccessKeyId=AKLTBMoErBNJRuyMTMr9bVnf&Signature=HXoHYwuvJAdWhSE7Adg1PjtdZDY%3D',
        show_xml=True,
        keep_ppt=True)
