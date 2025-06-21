import argparse
import json
import os
import sys
import zlib
from collections import defaultdict
from tkinter import Tk, filedialog

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError

# Import the newly generated protobuf modules from the 'spark' subdirectory
from spark import spark_sampler_pb2, spark_heap_pb2
from spark import spark_pb2 as spark_health_pb2  # 'HealthData' is in the base spark.proto


class NodeAccumulator:
    """一个辅助类，用于聚合具有相同方法签名节点的数据。"""
    def __init__(self, key):
        self.key = key
        self.nodes = []
        self.self_time = 0
        self.total_time = 0
        self.sample_count = 0

    def append(self, node, self_time):
        self.nodes.append(node)
        self.self_time += self_time
        self.total_time += node.get('time', 0)
        self.sample_count += 1 # 每个节点代表该方法的一个样本

    def to_dict(self):
        # 将第一个节点的详细信息作为代表
        first_node = self.nodes[0]
        return {
            'methodName': first_node.get('methodName'),
            'className': first_node.get('className'),
            'description': first_node.get('description'),
            'selfTime': self.self_time,
            'totalTime': self.total_time,
            'sampleCount': self.sample_count,
        }

def _visit_node_for_summary(node, accumulator):
    """递归访问一个节点以计算其自身耗时并填充累加器。"""
    child_time = 0
    if 'children' in node:
        for child in node['children']:
            _visit_node_for_summary(child, accumulator)
            child_time += child.get('time', 0)

    self_time = node.get('time', 0) - child_time
    
    # 用于标识唯一方法的键
    key_parts = [
        node.get('className', '未知类'),
        node.get('methodName', '未知方法'),
        node.get('description', '未知描述')
    ]
    key = ".".join(key_parts)
    
    if key not in accumulator:
        accumulator[key] = NodeAccumulator(key)
    
    accumulator[key].append(node, self_time)

def summarize_data(data, top_n=50):
    """
    分析完整的JSON数据，生成一个可读的摘要报告，
    报告包含基于自身耗时（Self Time）排名的前N个热点方法。
    """
    summary = {
        'metadata': data.get('metadata', {}),
        'hotspots': []
    }
    
    all_methods = {} # 用于聚合所有线程中方法的累加器
    
    for thread in data.get('threads', []):
        thread_methods = {} # 当前线程的方法累加器
        if 'children' in thread:
            for node in thread['children']:
                _visit_node_for_summary(node, thread_methods)
        
        # 将当前线程的方法合并到全局累加器中
        for key, node_acc in thread_methods.items():
            if key not in all_methods:
                all_methods[key] = NodeAccumulator(key)
            
            all_methods[key].self_time += node_acc.self_time
            all_methods[key].total_time += node_acc.total_time
            all_methods[key].sample_count += node_acc.sample_count
            all_methods[key].nodes.extend(node_acc.nodes)

    # 按自身耗时（self_time）对所有收集到的方法进行排序，以找到最热的点
    sorted_methods = sorted(all_methods.values(), key=lambda x: x.self_time, reverse=True)
    
    summary['hotspots'] = [method.to_dict() for method in sorted_methods[:top_n]]
    
    return summary


def convert_local_file(file_path, output_path, data_type, summarize=False):
    """
    将一个本地的 .sparkprofile 文件（压缩或未压缩）转换为 JSON。
    """
    print(f"正在尝试转换文件 '{file_path}'，类型为 '{data_type}'...")

    try:
        # 1. 从文件读取原始二进制数据
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        print(f"从文件读取了 {len(raw_data)} 字节。")

        # 2. 尝试解压数据，如果失败则回退到使用原始数据
        processed_data = None
        try:
            # 官方查看器使用 zlib.inflate，其默认 wbits 为 15。
            # Python 的 zlib.decompress 使用此默认值。
            processed_data = zlib.decompress(raw_data)
            print(f"解压后数据大小为 {len(processed_data)} 字节。")
        except zlib.error:
            print("zlib 解压失败。假设文件未被压缩，将继续使用原始数据。")
            processed_data = raw_data

        # 3. 根据 '--type' 参数选择正确的 protobuf 消息类型
        if data_type == 'sampler':
            # 分析器数据的主消息是 SamplerData
            message = spark_sampler_pb2.SamplerData()
        elif data_type == 'heap':
            message = spark_heap_pb2.HeapData()
        elif data_type == 'health':
            # HealthData 消息在基础的 spark.proto 中，编译为 spark_pb2
            message = spark_health_pb2.HealthData()
        else:
            print(f"错误：未知的数据类型 '{data_type}'。请使用 'sampler'、'heap' 或 'health'。")
            return

        # 4. 解析处理过的数据（可能已解压）
        try:
            message.ParseFromString(processed_data)
            print("成功解析 Protobuf 数据。")
        except Exception as e:
            print(f"严重错误：在 ParseFromString 期间发生意外错误：{e}")
            return

        # 5. 转换为 JSON 并保存
        json_obj = MessageToDict(message, preserving_proto_field_name=True)
        print(f"成功转换为 JSON。顶层键为: {list(json_obj.keys())}")

        if summarize:
            print("正在进行数据摘要以查找热点...")
            final_obj = summarize_data(json_obj)
            print("摘要完成。")
        else:
            final_obj = json_obj

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_obj, f, indent=2)

        if summarize:
            print(f"摘要成功！热点分析报告已保存至: {output_path}")
        else:
            print(f"转换成功！输出已保存至: {output_path}")

    except FileNotFoundError:
        print(f"错误：在 '{file_path}' 未找到输入文件。")
    except DecodeError as e:
        print(f"错误：解码 Protobuf 消息时出错: {e}")
        print("这通常意味着 '--type' 参数对于给定的文件不正确，或者 .proto schema 版本错误。")
    except Exception as e:
        print(f"发生意外错误: {e}")


def prompt_for_file():
    """为用户打开一个文件对话框，以选择 .sparkprofile 文件。"""
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    filepath = filedialog.askopenfilename(
        title="请选择一个 .sparkprofile 文件",
        filetypes=(("spark profile files", "*.sparkprofile"), ("All files", "*.*"))
    )
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="一个将本地 spark profile 文件转换为 JSON 的工具。",
        formatter_class=argparse.RawTextHelpFormatter  # Preserve newlines in help text
    )
    parser.add_argument(
        '-i', '--input',
        dest='local_file',
        type=str,
        help="本地 .sparkprofile 文件的路径。\n如果未提供此参数，将会弹出一个文件选择窗口。"
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help="用于保存输出 JSON 文件的路径。\n如果未提供，将根据输入文件名自动生成。"
    )
    parser.add_argument(
        '-t', '--type',
        type=str,
        choices=['sampler', 'heap', 'health'],
        default='sampler',
        help="profile 数据的类型。如果未提供，默认为 'sampler'。"
    )
    parser.add_argument(
        '--summarize',
        action='store_true',
        help="生成一个包含热点方法的摘要 JSON，而不是完整的原始数据。"
    )

    args = parser.parse_args()

    # --- Input File Logic ---
    input_file = args.local_file
    if not input_file:
        print("未通过命令行指定输入文件，正在打开文件选择窗口...")
        input_file = prompt_for_file()
        if not input_file:
            print("未选择文件，程序退出。")
            return

    # --- Output File Logic ---
    output_file = args.output
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        if args.summarize:
            output_file = base_name + ".summary.json"
        else:
            output_file = base_name + ".json"
        print(f"未指定输出路径，将自动使用: {output_file}")

    convert_local_file(input_file, output_file, args.type, args.summarize)


if __name__ == '__main__':
    main() 