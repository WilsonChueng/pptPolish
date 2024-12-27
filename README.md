# PPT Processor

## 项目简介

PPT Processor 是一个用于处理用户数据的Python项目。该项目从Excel文件中读取数据，提取特定的Markdown内容，转换为XML格式，并对XML内容进行随机打乱，最终将处理结果保存到新的Excel文件中。

## 项目结构

```
ppt_processor/
├── data/
│   └── input.xlsx
├── output/
│   └── output.xlsx
├── modules/
│   ├── __init__.py
│   ├── data_handler.py
│   ├── markdown_extractor.py
│   ├── markdown_to_xml.py
│   └── xml_processor.py
├── main.py
├── requirements.txt
└── README.md

```

- **data/**：存放输入的Excel文件。
- **output/**：存放处理后的输出Excel文件。
- **modules/**：存放各个功能模块的Python脚本。
- **main.py**：主控制脚本。
- **requirements.txt**：项目依赖库列表。
- **README.md**：项目说明文档。

## 安装依赖

确保您已安装Python 3.6或更高版本。然后，安装项目依赖：

```bash
pip install -r requirements.txt
```

## 使用说明

1. **配置文件**

   编辑`config/config.yaml`文件，设置正则表达式模式和其他参数。

    ```yaml
   # config/config.yaml

    # 输入和输出文件路径
    input_file: "data/input.xlsx"
    output_file: "output/output.xlsx"
    
    # 日志文件路径
    log_file: "logs/app.log"
    
    # 正则表达式模式
    patterns:
      code_block: '<\\|code\\|>\\{"function": "generate_ppt"\\}<\\|endofblock\\|>'
      execution_block: '<\\|execution\\|>(.*?)<\\|endofblock\\|>'
    ```

2. **准备输入文件**

   将您的输入Excel文件命名为`input.xlsx`，并将其放置在`data/`文件夹中。确保Excel文件包含`id`和`text`两列。

3. **运行脚本**

   在项目根目录下，通过命令行运行主脚本：

   ```bash
   python main.py
   ```

4. **查看输出**

   处理完成后，您将在`output/`文件夹中找到名为`output.xlsx`的文件，其中包含原有的数据以及新生成的`markdown_ppt`、`xml_ppt`和`xml_ppt-打乱`三列。
   同时，您可以在`logs/app.log`中查看详细的日志信息，了解处理过程中的每一步。

## 示例

假设`input.xlsx`中的一行`text`内容如下：

```
Some initial text...
<|code|>{"function": "generate_ppt"}<|endofblock|>
<|execution|>
# 欢迎
## 介绍
这是第一部分的内容。
### 细节
更多的细节内容。
<|endofblock|>
Some other text...
```

处理后，`output.xlsx`中的对应行将包含：

- **markdown_ppt**:

    ```markdown
    # 欢迎
    ## 介绍
    这是第一部分的内容。
    ### 细节
    更多的细节内容。
    ```

- **xml_ppt**:

    ```xml
    <slide id="1">
        <p>欢迎</p>
    </slide>
    <slide id="2">
        <p>介绍</p>
        <p>这是第一部分的内容。</p>
    </slide>
    <slide id="3">
        <p>细节</p>
        <p>更多的细节内容。</p>
    </slide>
    ```

- **xml_ppt-打乱**（具体顺序可能不同）:

    ```xml
    <slide id="1">
        <p>欢迎</p>
    </slide>
    <slide id="2">
        <p>这是第一部分的内容。</p>
        <p>介绍</p>
    </slide>
    <slide id="3">
        <p>更多的细节内容。</p>
        <p>细节</p>
    </slide>
    ```

## 进一步优化

- **日志记录**：使用`logging`模块记录详细的处理信息和错误。
- **配置文件**：将配置参数（如文件路径、正则表达式模式）提取到外部配置文件中。
- **单元测试**：为各个模块编写单元测试，确保代码的可靠性。
- **命令行参数**：使用`argparse`模块允许用户通过命令行传递参数，提高脚本的灵活性。

## 许可证

本项目使用MIT许可证。详情请参阅[LICENSE](LICENSE)。

## 联系方式

如有任何问题或建议，请联系您的联系方式。