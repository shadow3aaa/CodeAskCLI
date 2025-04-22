"""
配置文件管理模块
"""
import os
import json
import yaml
import tomli
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigManager:
    """配置管理器，处理不同格式的配置文件"""
    
    CONFIG_FILENAMES = [
        "codeask.yaml", "codeask.yml",     # YAML 格式
        "codeask.toml",                     # TOML 格式
        "codeask.json",                     # JSON 格式
        ".codeask/config.yaml", ".codeask/config.yml",  # 目录下的配置
        ".codeask/config.toml",
        ".codeask/config.json"
    ]
    
    def __init__(self, project_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            project_dir: 项目目录路径，如果为None则使用当前目录
        """
        self.project_dir = project_dir or os.getcwd()
        self.config = {}
        self.config_file = None
    
    def find_config_file(self) -> Optional[str]:
        """
        在项目目录中查找配置文件
        
        Returns:
            找到的配置文件路径，如果没找到则返回None
        """
        for filename in self.CONFIG_FILENAMES:
            config_path = os.path.join(self.project_dir, filename)
            if os.path.isfile(config_path):
                return config_path
        return None
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，如果为None则自动查找
            
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 如果找不到配置文件
            ValueError: 如果配置文件格式不支持或解析失败
        """
        # 如果没有指定配置文件路径，则尝试自动查找
        if not config_path:
            config_path = self.find_config_file()
            if not config_path:
                self.config = {}
                return self.config
        
        self.config_file = config_path
        file_ext = os.path.splitext(config_path)[1].lower()
        
        try:
            with open(config_path, 'rb') as f:
                if file_ext in ['.yaml', '.yml']:
                    # 使用YAML加载器
                    self.config = yaml.safe_load(f)
                elif file_ext == '.toml':
                    # 使用TOML加载器
                    self.config = tomli.load(f)
                elif file_ext == '.json':
                    # 使用JSON加载器
                    f.seek(0)  # 因为之前已以二进制模式打开，需要重置指针
                    self.config = json.loads(f.read().decode('utf-8'))
                else:
                    raise ValueError(f"不支持的配置文件格式: {file_ext}")
            
            # 确保返回的是字典
            if not isinstance(self.config, dict):
                self.config = {}
                
            return self.config
        except Exception as e:
            print(f"加载配置文件 {config_path} 失败: {e}")
            self.config = {}
            return self.config

    def get_templates(self) -> tuple:
        """
        从配置中获取单页分析和总结分析的提示词
        
        Returns:
            tuple: (single_page_template, summary_template)
        """
        # 初始化为None，表示未在配置中找到
        single_page_template = None
        summary_template = None
        
        # 检查配置中是否有提示词相关内容
        templates = self.config.get('templates', {})
        
        # 检查是否有直接的提示词内容
        if isinstance(templates, dict):
            single_page_template = templates.get('single_page')
            summary_template = templates.get('summary')
            
            # 如果配置中指定了提示词文件路径，则从文件加载
            single_page_file = templates.get('single_page_file')
            if single_page_file and not single_page_template:
                file_path = os.path.join(self.project_dir, single_page_file)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            single_page_template = f.read()
                    except Exception as e:
                        print(f"读取单页分析提示词文件失败: {e}")
            
            summary_file = templates.get('summary_file')
            if summary_file and not summary_template:
                file_path = os.path.join(self.project_dir, summary_file)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            summary_template = f.read()
                    except Exception as e:
                        print(f"读取总结分析提示词文件失败: {e}")
            
            # 如果找到了配置的模板，输出提示信息
            if single_page_template:
                print("从配置文件加载单页分析提示词")
            if summary_template:
                print("从配置文件加载总结分析提示词")
        
        return single_page_template, summary_template
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        从配置中获取API相关配置
        
        Returns:
            Dict: API配置字典
        """
        return self.config.get('api', {})
    
    def get_analyzer_config(self) -> Dict[str, Any]:
        """
        从配置中获取分析器相关配置
        
        Returns:
            Dict: 分析器配置字典
        """
        return self.config.get('analyzer', {})
    
    def get_filters(self) -> Optional[List[str]]:
        """
        从配置中获取文件过滤器
        
        Returns:
            List[str]: 文件过滤器模式列表，如果未指定则返回None
        """
        # 首先尝试从filters字段获取
        filters = self.config.get('filters', None)
        
        # 如果filters不存在，尝试从filter字段获取（单数形式兼容）
        if filters is None:
            filters = self.config.get('filter', None)
        
        # 检查旧版配置中的extensions字段（兼容性处理，但会打印警告）
        if filters is None:
            extensions = self.config.get('extensions', None)
            if extensions is not None:
                if isinstance(extensions, str):
                    # 字符串格式
                    extensions_list = [ext.strip() for ext in extensions.split(',') if ext.strip()]
                    filters = [f"**/*{ext}" for ext in extensions_list]
                    print("警告: 配置文件中使用的'extensions'字段已弃用，请改用'filters'字段")
                elif isinstance(extensions, list):
                    # 列表格式
                    filters = [f"**/*{ext}" for ext in extensions if ext and isinstance(ext, str)]
                    print("警告: 配置文件中使用的'extensions'字段已弃用，请改用'filters'字段")
        
        # 处理不同格式的过滤器配置
        if filters is None:
            return None
        elif isinstance(filters, str):
            # 如果是逗号分隔的字符串，分割成列表
            return [f.strip() for f in filters.split(',') if f.strip()]
        elif isinstance(filters, list):
            # 如果已经是列表，直接返回
            return [f for f in filters if f and isinstance(f, str)]
        else:
            # 其他类型，返回None
            return None