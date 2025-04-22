"""
文件处理相关工具函数
"""
import os
import glob
import hashlib
from typing import List, Optional


def get_file_hash(file_path: str) -> str:
    """计算文件的哈希值，与原项目保持一致"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    except Exception as e:
        print(f"计算文件哈希失败: {file_path}, 错误: {e}")
        return ""


def read_file(file_path: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败: {file_path}, 错误: {e}")
        return ""


def find_matching_files(folder_path: str, file_patterns: List[str]) -> List[str]:
    """根据模式查找匹配的文件"""
    all_files = []
    for pattern in file_patterns:
        pattern_path = os.path.join(folder_path, '**', pattern)
        matches = glob.glob(pattern_path, recursive=True)
        all_files.extend(matches)
    
    # 去重
    return list(set(all_files))


def save_analysis_results(output_file: str, analysis_data: dict, summary: str) -> None:
    """保存分析结果到文件"""
    import json
    
    # 确定输出路径
    output_path = output_file
    if os.path.isdir(output_file):
        output_path = os.path.join(output_file, '.codeaskdata')
    
    # 保存JSON结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "globalAnalysis": {
                "results": {
                    "cli_analysis": {
                        "globalAnalysisName": analysis_data["globalAnalysisName"],
                        "singlePagePrompt": analysis_data["singlePagePrompt"],
                        "summaryPrompt": analysis_data["summaryPrompt"],
                        "summary": analysis_data["summary"],
                        "timestamp": analysis_data["timestamp"],
                        # 保存配置文件信息
                        "configHash": analysis_data.get("configHash"),
                        "configFile": analysis_data.get("configFile")
                    }
                }
            },
            "singleFileResults": analysis_data["single_file_results"]
        }, f, ensure_ascii=False, indent=2)
    print(f"分析结果已保存到: {output_path}")
    
    # 保存总结到项目目录下的SUMMARY.md
    base_dir = os.path.dirname(output_path)
    if not os.path.isabs(base_dir):
        base_dir = os.path.abspath(base_dir)
    
    summary_path = os.path.join(base_dir, "SUMMARY.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"Markdown总结已保存到: {summary_path}")
    
    # 保存单页分析结果到与原文件同名的.md文件
    if analysis_data.get("single_file_results"):
        for file_result in analysis_data["single_file_results"]:
            filename = file_result.get("filename", "unknown")
            # 创建与源文件相同的目录结构
            analysis_file_path = os.path.join(base_dir, f"{filename}.md")
            analysis_dir = os.path.dirname(analysis_file_path)
            
            # 确保目录存在
            if not os.path.exists(analysis_dir):
                os.makedirs(analysis_dir, exist_ok=True)
                
            # 保存分析结果
            with open(analysis_file_path, 'w', encoding='utf-8') as f:
                f.write(file_result.get("content", "分析结果为空"))
        
        print(f"单页分析结果已保存到各源文件同名的.md文件中")