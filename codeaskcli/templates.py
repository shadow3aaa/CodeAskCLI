"""
提示词模板管理
"""
from typing import Tuple


def load_templates() -> Tuple[str, str]:
    """加载默认的提示词模板"""
    single_page_template = """你是一个专业的代码分析助手，请分析下面的代码文件，并提供以下内容：

1. 代码的主要功能和用途
2. 代码架构和设计模式分析
3. 存在的潜在问题、安全隐患或性能瓶颈
4. 代码质量评估和改进建议

请以Markdown格式输出分析结果，使用恰当的标题和分段使内容易于阅读。
"""

    summary_template = """你是一个专业的代码分析师，请基于提供的单文件分析结果，生成整个项目的总结分析报告。
报告应该包含以下内容：

1. 项目概述：项目的整体结构、主要功能和技术栈
2. 核心组件分析：识别并分析项目的核心组件及其交互
3. 代码质量评估：基于单文件分析，对整体代码质量进行评估
4. 架构评价：评价项目的架构设计，包括优点和不足
5. 改进建议：提供具体的改进建议，包括代码优化、架构调整等

请以Markdown格式输出报告，使用清晰的标题层次结构，必要时添加图表描述（文字形式）。
"""
    return single_page_template, summary_template


def load_template_from_file(file_path: str) -> str:
    """从文件加载提示词模板"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"加载提示词模板文件失败: {e}")
        return ""