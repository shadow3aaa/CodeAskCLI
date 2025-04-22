"""
命令行界面模块
"""
import os
import argparse
from typing import List, Optional, Dict, Any

from codeaskcli.api import AIClientFactory, AIApiClient
from codeaskcli.analyzer import CodeAnalyzer
from codeaskcli.templates import load_templates, load_template_from_file
from codeaskcli.config import ConfigManager


def parse_arguments():
    """解析命令行参数"""
    # 获取支持的提供商列表
    supported_providers = AIClientFactory.list_supported_providers()
    provider_help = f"AI服务提供商 (支持: {', '.join(supported_providers)})"

    parser = argparse.ArgumentParser(description='CodeAsk CLI工具 - 代码分析')
    parser.add_argument('folder_path', nargs='?', default=os.getcwd(), 
                      help='要分析的代码文件夹路径，如不提供则使用当前工作目录')
    parser.add_argument('--filter', help='文件过滤器，指定要分析的文件范围，支持glob模式，如: "lib/**.py,*.md,src/**"。如不提供，将尝试从配置文件读取。')
    parser.add_argument('--api-key', help='API密钥，如果未提供则从配置文件或环境变量读取')
    parser.add_argument('--config', help='配置文件路径，默认自动在项目目录下查找')
    
    # 服务提供商相关参数
    parser.add_argument('--provider', default=None, choices=supported_providers, help=provider_help)
    parser.add_argument('--base-url', default=None, help='API基础URL (对于OpenAI和某些提供商)')
    parser.add_argument('--model', default=None, help='使用的模型名称')
    
    # Azure特定参数
    parser.add_argument('--azure-endpoint', default=None, help='Azure OpenAI服务终结点URL')
    parser.add_argument('--azure-deployment', default=None, help='Azure OpenAI部署名称')
    parser.add_argument('--azure-api-version', default=None, help='Azure API版本')

    # 通用AI参数
    parser.add_argument('--temperature', type=float, default=None, help='生成温度')
    parser.add_argument('--max-tokens', type=int, default=None, help='最大输出token数')
    parser.add_argument('--top-p', type=float, default=None, help='Top-p采样参数')
    parser.add_argument('--top-k', type=int, default=None, help='Top-k采样参数 (仅Anthropic和Gemini)')
    parser.add_argument('--verbose', action='store_true', help='开启详细输出模式，包括API请求内容')
    
    # 项目分析参数
    parser.add_argument('--concurrency', type=int, default=None, help='并发处理文件数')
    parser.add_argument('--output', default=None, help='输出文件路径，默认为项目文件夹的.codeaskdata文件')
    parser.add_argument('--single-page-prompt', default=None, help='单页分析提示词文件路径')
    parser.add_argument('--summary-prompt', default=None, help='总结分析提示词文件路径')
    parser.add_argument('--full-analysis', action='store_true', help='强制进行完整分析，不使用增量分析')
    parser.add_argument('--no-tui', action='store_true', help='禁用终端用户界面(TUI)，使用纯文本输出')
    
    return parser.parse_args()


def prepare_prompts(args, config_manager=None) -> tuple:
    """
    准备分析用的提示词
    
    Args:
        args: 命令行参数
        config_manager: 配置管理器实例
    
    Returns:
        tuple: (single_page_prompt, summary_prompt)
    """
    # 加载默认提示词模板
    default_single_page_prompt, default_summary_prompt = load_templates()
    
    # 初始化为默认值
    single_page_prompt = default_single_page_prompt
    summary_prompt = default_summary_prompt
    
    # 如果有配置管理器，先尝试从配置文件加载
    if config_manager:
        config_single_page, config_summary = config_manager.get_templates()
        if config_single_page:
            single_page_prompt = config_single_page
        if config_summary:
            summary_prompt = config_summary
    
    # 命令行参数优先级更高，如果指定了则覆盖配置文件的设置
    if args.single_page_prompt and os.path.exists(args.single_page_prompt):
        loaded_prompt = load_template_from_file(args.single_page_prompt)
        if loaded_prompt:
            single_page_prompt = loaded_prompt
        else:
            print("加载指定的单页分析提示词文件失败，使用已有的提示词模板")
    
    if args.summary_prompt and os.path.exists(args.summary_prompt):
        loaded_prompt = load_template_from_file(args.summary_prompt)
        if loaded_prompt:
            summary_prompt = loaded_prompt
        else:
            print("加载指定的总结分析提示词文件失败，使用已有的提示词模板")
    
    return single_page_prompt, summary_prompt


def prepare_file_patterns(filter_patterns: str) -> List[str]:
    """
    准备文件过滤模式列表
    
    Args:
        filter_patterns: 逗号分隔的glob模式字符串
    
    Returns:
        glob模式列表
    """
    if not filter_patterns:
        raise ValueError("必须提供文件过滤器参数")
    
    # 分割并去除空白
    patterns = [pattern.strip() for pattern in filter_patterns.split(',')]
    # 过滤空字符串
    patterns = [pattern for pattern in patterns if pattern]
    
    if not patterns:
        raise ValueError("提供的过滤器格式无效，至少需要一个有效的glob模式")
    
    return patterns


def get_api_key(args, config_manager) -> str:
    """
    获取API密钥，优先级：环境变量 > 命令行参数 > 配置文件
    
    Returns:
        str: API密钥
    
    Raises:
        ValueError: 如果无法获取API密钥
    """
    # 确定使用的提供商
    provider = args.provider
    if not provider and config_manager:
        api_config = config_manager.get_api_config()
        provider = api_config.get('provider', 'openai')
    else:
        provider = provider or 'openai'
    
    # 根据提供商获取相应的环境变量
    env_var_map = {
        'openai': ['OPENAI_API_KEY', 'API_KEY'],
        'anthropic': ['ANTHROPIC_API_KEY', 'API_KEY'],
        'azure': ['AZURE_OPENAI_API_KEY', 'API_KEY'],
        'gemini': ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'API_KEY']
    }
    
    # 1. 首先尝试从环境变量获取（推荐用于CI环境）
    api_key = None
    for env_var in env_var_map.get(provider.lower(), ['API_KEY']):
        api_key = os.environ.get(env_var)
        if api_key:
            print(f"使用环境变量 {env_var} 中的API密钥")
            break
    
    # 2. 如果环境变量中没有，尝试从命令行参数获取
    if not api_key:
        api_key = args.api_key
        if api_key:
            print("使用命令行参数提供的API密钥")
    
    # 3. 如果命令行未提供，从配置文件获取
    if not api_key and config_manager:
        api_config = config_manager.get_api_config()
        api_key = api_config.get('api_key')
        if api_key:
            print("使用配置文件中的API密钥")
    
    if not api_key:
        raise ValueError(
            "无法获取API密钥。请通过以下方式之一提供:\n"
            f"1. 设置环境变量 {', '.join(env_var_map.get(provider.lower(), ['API_KEY']))} (推荐用于CI环境)\n"
            "2. 使用--api-key命令行参数\n"
            "3. 在配置文件中设置api.api_key"
        )
    
    return api_key


def create_api_client(args, config_manager=None) -> Any:
    """
    根据命令行参数和配置文件创建API客户端
    
    Args:
        args: 命令行参数
        config_manager: 配置管理器实例
    
    Returns:
        API客户端实例
    """
    # 获取API配置，优先使用命令行参数，然后是配置文件
    api_config = {}
    if config_manager:
        api_config = config_manager.get_api_config()
    
    # 获取API密钥
    api_key = get_api_key(args, config_manager)
    
    # 确定提供商
    provider = args.provider
    if not provider:
        provider = api_config.get('provider', 'openai')
    
    # 收集通用参数
    client_params = {
        "api_key": api_key,
        "verbose": args.verbose  # 添加verbose参数
    }
    
    # 添加来自配置文件的参数
    if 'temperature' in api_config:
        client_params["temperature"] = api_config.get('temperature')
    if 'max_tokens' in api_config:
        client_params["max_tokens"] = api_config.get('max_tokens')
    if 'top_p' in api_config:
        client_params["top_p"] = api_config.get('top_p')
    if 'top_k' in api_config and provider.lower() in ["anthropic", "gemini"]:
        client_params["top_k"] = api_config.get('top_k')
    
    # 命令行参数优先级更高，覆盖配置文件
    if args.temperature is not None:
        client_params["temperature"] = args.temperature
    else:
        # 配置文件中没有，使用默认值
        if 'temperature' not in client_params:
            client_params["temperature"] = 0.3
            
    if args.max_tokens is not None:
        client_params["max_tokens"] = args.max_tokens
    else:
        # 配置文件中没有，使用默认值
        if 'max_tokens' not in client_params:
            client_params["max_tokens"] = 4000
            
    if args.top_p is not None:
        client_params["top_p"] = args.top_p
    if args.top_k is not None and provider.lower() in ["anthropic", "gemini"]:
        client_params["top_k"] = args.top_k
    
    # 根据提供商添加特定参数
    if provider.lower() == "openai":
        # 从配置获取
        if 'base_url' in api_config:
            client_params["base_url"] = api_config.get('base_url')
        if 'model' in api_config:
            client_params["model_name"] = api_config.get('model')
        
        # 命令行覆盖
        if args.base_url:
            client_params["base_url"] = args.base_url
        if args.model:
            client_params["model_name"] = args.model
        
        # 确保有默认值
        if "base_url" not in client_params:
            client_params["base_url"] = "https://api.openai.com/v1"
        if "model_name" not in client_params:
            client_params["model_name"] = "gpt-3.5-turbo"
    
    elif provider.lower() == "anthropic":
        # 从配置获取
        if 'base_url' in api_config:
            client_params["base_url"] = api_config.get('base_url')
        if 'model' in api_config:
            client_params["model_name"] = api_config.get('model')
        
        # 命令行覆盖
        if args.base_url:
            client_params["base_url"] = args.base_url
        if args.model:
            client_params["model_name"] = args.model
        
        # 确保有默认值
        if "model_name" not in client_params:
            client_params["model_name"] = "claude-3-opus-20240229"
    
    elif provider.lower() == "azure":
        # 从配置获取
        if 'endpoint' in api_config:
            client_params["endpoint"] = api_config.get('endpoint')
        if 'deployment' in api_config:
            client_params["deployment_name"] = api_config.get('deployment')
        if 'api_version' in api_config:
            client_params["api_version"] = api_config.get('api_version')
        
        # 命令行覆盖
        if args.azure_endpoint:
            client_params["endpoint"] = args.azure_endpoint
        if args.azure_deployment:
            client_params["deployment_name"] = args.azure_deployment
        if args.azure_api_version:
            client_params["api_version"] = args.azure_api_version
        
        # 验证必要参数
        if "endpoint" not in client_params:
            raise ValueError("使用Azure OpenAI需要提供endpoint参数")
        if "deployment_name" not in client_params:
            raise ValueError("使用Azure OpenAI需要提供deployment_name参数")
        if "api_version" not in client_params:
            client_params["api_version"] = "2023-05-15"  # 设置默认版本
    
    elif provider.lower() == "gemini":
        # 从配置获取
        if 'base_url' in api_config:
            client_params["base_url"] = api_config.get('base_url')
        if 'model' in api_config:
            client_params["model_name"] = api_config.get('model')
        
        # 命令行覆盖
        if args.base_url:
            client_params["base_url"] = args.base_url
        if args.model:
            client_params["model_name"] = args.model
        
        # 确保有默认值
        if "model_name" not in client_params:
            client_params["model_name"] = "gemini-pro"
    
    # 使用工厂创建客户端
    # 为了兼容性，如果是默认的OpenAI配置，使用旧的AIApiClient
    if (provider.lower() == "openai" and
            client_params.get("base_url") == "https://api.openai.com/v1" and
            client_params.get("model_name") == "gpt-3.5-turbo" and
            "top_p" not in client_params and
            "top_k" not in client_params):
        return AIApiClient(
            api_key=api_key,
            base_url=client_params.get("base_url"),
            model_name=client_params.get("model_name"),
            temperature=client_params.get("temperature"),
            max_tokens=client_params.get("max_tokens")
        )
    else:
        # 使用新的工厂方法
        return AIClientFactory.get_client(provider, **client_params)


def run_analysis(args) -> int:
    """运行代码分析"""
    try:
        # 验证文件夹路径
        if not os.path.isdir(args.folder_path):
            print(f"错误: 指定的路径不是一个有效的文件夹: {args.folder_path}")
            return 1
        
        # 加载配置
        config_manager = ConfigManager(args.folder_path)
        config_file = None
        config_hash = None
        
        if args.config:
            config_file = args.config
            config_manager.load_config(config_file)
            # 计算配置文件哈希值
            from codeaskcli.file_utils import get_file_hash
            config_hash = get_file_hash(config_file)
        else:
            config_file = config_manager.find_config_file()
            if config_file:
                config_manager.load_config()
                # 计算配置文件哈希值
                from codeaskcli.file_utils import get_file_hash
                config_hash = get_file_hash(config_file)
                print(f"已加载配置文件: {config_file}")
        
        # 准备分析所需的输入
        single_page_prompt, summary_prompt = prepare_prompts(args, config_manager)
        
        # 获取文件过滤器
        # 1. 优先使用命令行参数 --filter
        # 2. 如果没有提供，尝试从配置文件读取
        file_patterns = None
        
        if args.filter:
            # 从命令行参数获取
            file_patterns = prepare_file_patterns(args.filter)
        else:
            # 尝试从配置文件获取
            config_filters = config_manager.get_filters()
            if config_filters:
                file_patterns = config_filters
                print(f"从配置文件获取文件过滤器")
        
        # 如果没有找到文件过滤器，提示用户必须指定过滤器
        if not file_patterns:
            print("错误: 必须提供文件过滤器来指定要分析的文件范围")
            print("可以通过以下方式提供:")
            print("1. 命令行参数: --filter 'lib/**.py,*.md,src/**'")
            print("2. 配置文件中的 'filters' 字段")
            return 1
        
        # 设置输出文件
        output_file = args.output
        if not output_file:
            # 从配置获取
            analyzer_config = config_manager.get_analyzer_config()
            output_file = analyzer_config.get('output_file')
        
        # 如果没有设置，使用默认值
        if not output_file:
            output_file = os.path.join(args.folder_path, '.codeaskdata')
        
        # 获取并发数
        concurrency = args.concurrency
        if concurrency is None:
            analyzer_config = config_manager.get_analyzer_config()
            concurrency = analyzer_config.get('concurrency', 1)
        
        print(f"使用并发线程数: {concurrency}")
        
        # 确定是否使用增量分析
        incremental = not args.full_analysis
        if incremental:
            print("启用增量分析: 仅分析新增或已修改的文件")
        else:
            print("执行完整分析: 分析所有匹配的文件")
        
        # 创建API客户端
        api_client = create_api_client(args, config_manager)
        
        # 输出使用的提供商信息
        provider = args.provider
        if not provider:
            api_config = config_manager.get_api_config()
            provider = api_config.get('provider', 'openai')
        
        print(f"使用AI提供商: {provider.upper()}")
        if hasattr(api_client, "model_name"):
            print(f"使用模型: {api_client.model_name}")
        
        # 打印文件过滤器信息
        print(f"使用文件过滤器: {', '.join(file_patterns)}")
        
        # 初始化分析器
        analyzer = CodeAnalyzer(
            api_client=api_client,
            concurrency=concurrency
        )
        
        # 运行分析
        analyzer.analyze_project(
            folder_path=args.folder_path,
            file_patterns=file_patterns,
            single_page_prompt=single_page_prompt,
            summary_prompt=summary_prompt,
            output_file=output_file,
            incremental=incremental,
            config_file=config_file,
            config_hash=config_hash,
            use_tui=not args.no_tui  # 根据命令行参数决定是否使用TUI
        )
        return 0
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1