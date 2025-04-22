#!/usr/bin/env python3
"""
CodeAskCLI - 基于命令行的代码分析工具

使用AI模型分析代码库并生成报告
"""
import sys
from codeaskcli.cli import parse_arguments, run_analysis


def main():
    """主函数"""
    args = parse_arguments()
    return run_analysis(args)


if __name__ == "__main__":
    sys.exit(main())