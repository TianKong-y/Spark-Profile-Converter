<h1 align="center">Spark Profile Converter</h1>

<p align="center">
  <b>Spark 分析数据转换工具</b>
</p>
<p align="center">
    <a href="LICENSE">
        <img src="https://img.shields.io/badge/License-GPL--3.0-important?style=for-the-badge" alt="License">
    </a>
    <a href="https://qm.qq.com/q/Spt6kcvVwk">
        <img src="https://img.shields.io/badge/QQ-技术交流/反馈群-blue?style=for-the-badge" alt="QQ Group">
    </a>
    <a href="https://space.bilibili.com/288309681">
        <img src="https://img.shields.io/badge/bilibili-TianKong_y-pink?style=for-the-badge" alt="Bilibili">
    </a>
</p>

## > 简介
`Spark Profile Converter` 是一个基于 Python 的命令行工具，用于转化 [spark](https://github.com/lucko/spark) 插件生成的性能分析文件 (`.sparkprofile`)，可以将 spark 的二进制 profiler 数据转换为可读的 JSON 格式，用于进一步开发工具进行数据分析或使用AI结合详细数据进行问题快速定位。

注：本项目使用了AI进行辅助开发，因此存在部分未经精细验证的内容，如有疑问请随时提交issue或加入 [QQ交流群](https://qm.qq.com/q/Spt6kcvVwk) 讨论

## > 功能特点
*   **完整格式转换**: 将二进制的 `.sparkprofile` 文件 1:1 转换为结构完整的 JSON 文件。
*   **智能摘要生成**: 通过分析所有线程的堆栈样本，计算每个方法（method）的"自身耗时"（Self Time），并按倒序排列，快速定位到系统中最耗时的项目，生成一份 JSON 文件。
*   **零参数启动**: 直接运行脚本即可弹出图形化文件选择窗口。
*   **纯粹的离线工具**: 无需网络连接，所有操作均在本地完成。

## > 依赖项
*   Python 3.7+ (自带 `tkinter` 用于文件对话框)
*   `protoc` 编译器 (需要配置在系统环境变量中)

## > 安装与环境配置

1.  **下载或克隆项目**
    将本仓库下载或克隆到本地。

2.  **安装 `protoc`**
    您可以从 [Protobuf Releases](https://github.com/protocolbuffers/protobuf/releases) 页面下载适合您系统的 `protoc` 编译器，并将其路径添加到系统的环境变量中。

3.  **安装 Python 依赖项**:
    在 `spark_profile_converter` 目录下，有一个 `requirements.txt` 文件。通过以下命令安装：
    ```bash
    pip install -r ./requirements.txt
    ```

## > 使用方法

### 0. 获取 `.sparkprofile` 文件
请在服务器内运行 `spark` 的 `profile` 命令后，进入结果输出网页后，点击第一行中 搜索框左侧 的 `导出为文件` 按钮（Export this profile to a local file），得到 `.sparkprofile` 文件

### 1. 图形化界面 (推荐)

此方式最为简单，无需任何命令行知识。

1.  进入 `spark_profile_converter` 目录。
2.  直接运行 `app.py` 脚本：
    ```bash
    python app.py
    ```
3.  脚本会自动弹出一个文件选择窗口。
4.  选择您的 `.sparkprofile` 文件后，程序会自动在**文件所在的目录下**生成一个名为 `<原文件名>.summary.json` 的摘要报告。

### 2. 命令行 (高级)

对于需要批处理或在脚本中调用的高级用户，本工具保留了完整的命令行参数支持。

**命令格式**:
```bash
python app.py [-i <输入文件>] [-o <输出文件>] [--summarize]
```

- `-i, --input`: 可选。指定输入的 `.sparkprofile` 文件。如果省略，将弹出文件选择窗口。
- `-o, --output`: 可选。指定输出的 JSON 文件。如果省略，将根据输入文件名自动生成。
- `--summarize`: 可选。添加此标志以生成精简的摘要报告。如果省略此标志，则会生成完整的 JSON 文件。

**示例**:
```bash
# 生成 XXXXXXXXXX.summary.json 摘要文件
python app.py -i XXXXXXXXXX.sparkprofile --summarize

# 生成 XXXXXXXXXX.json 完整文件
python app.py -i XXXXXXXXXX.sparkprofile
```

## > 鸣谢
- [lucko/spark](https://github.com/lucko/spark): 收集服务器数据信息，提供了 `.sparkprofile` 文件的原始生成工具和 schema。
- [lucko/spark-viewer](https://github.com/lucko/spark-viewer): 本工具的性能分析算法参考了其前端实现。

## > 项目统计

<div align="center">

![Repobeats analytics image](https://repobeats.axiom.co/api/embed/d3cb317a2b0e2b4024822e5a3f426dc072673e7d.svg)

</div>