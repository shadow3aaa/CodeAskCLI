# CodeAskCLI

使用AI模型分析代码库并生成详细报告的命令行工具。参考了[CodeAsk](https://github.com/woniu9524/CodeAsk/issues)

## 功能

- 生成项目总结和单文件分析
- 将分析结果保存为易于阅读的Markdown文件
- 命令行实现，方便集成到ci

## 使用

```bash
# 安装uv
# windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macos/linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 运行
uv run main.py
```

## 使用方法

基本使用示例：

```bash
python main.py /path/to/code --filter "lib/**.py,*.md,src/**" --api-key YOUR_API_KEY
```

## 使用环境变量提供API密钥

为了保护敏感信息，特别是在CI/CD环境下，建议通过环境变量提供API密钥：

```bash
# 设置环境变量
# OpenAI
export OPENAI_API_KEY=sk-your-api-key

# Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-your-key

# Azure OpenAI
export AZURE_OPENAI_API_KEY=your-azure-key

# Google Gemini
export GEMINI_API_KEY=your-gemini-key

# 然后不需要在命令行中提供API密钥
uv run main.py /path/to/code --filter "lib/**.py,*.md"
```

在Windows下，使用以下命令设置环境变量：

```cmd
set OPENAI_API_KEY=sk-your-api-key
```

或者在PowerShell中：

```powershell
$env:OPENAI_API_KEY = "sk-your-api-key"
```

## 配置文件

可以通过配置文件设置常用选项，以减少命令行参数。支持YAML、TOML和JSON格式。
示例配置文件（codeask.yaml）：

```yaml
# CodeAskCLI 配置文件示例
# 将此文件保存为项目目录下的 codeask.yaml 文件

# API相关配置
api:
  # AI服务提供商，可选: openai, anthropic, azure, gemini
  provider: openai
  
  # 模型名称
  # 对于OpenAI: gpt-3.5-turbo, gpt-4-turbo, gpt-4o 等
  # 对于Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307 等
  # 对于Gemini: gemini-pro, gemini-ultra 等
  # 对于Azure: 由您的部署决定
  model: deepseek-reasoner
  
  # API参数设置
  temperature: 0.6      # 控制输出的随机性，0为最保守，1为最创造性
  max_tokens: 8000      # 生成文本的最大长度
  
  # 仅在开发环境使用，生产环境建议使用环境变量
  # 环境变量
  # openai: OPENAI_API_KEY
  # anthropic: ANTHROPIC_API_KEY
  # azure: AZURE_OPENAI_API_KEY
  # gemini: GEMINI_API_KEY

  api_key: sk-your-api-key-here
  
  # 自定义API基础URL (对于自托管或代理服务)
  base_url: https://api.deepseek.com/v1

  # Azure OpenAI特有配置
  # endpoint: https://your-resource.openai.azure.com
  # deployment: your-deployment-name
  # api_version: 2023-05-15

# 分析器配置
analyzer:
  # 并发处理文件数
  concurrency: 8
  
  # 输出文件路径，不设置则默认为项目目录下的.codeaskdata
  output_file: "./analysis_result"

# 文件过滤器，指定要分析的文件
filters:
  # 支持glob模式语法
  - "*.py"                # 所有Python文件
  - "*.js"                # 所有JavaScript文件
  - "!**/node_modules/**" # 排除node_modules目录
  - "!**/__pycache__/**"  # 排除__pycache__目录
  - "!**/venv/**"         # 排除虚拟环境目录
  - "!**/.*/**"           # 排除隐藏目录

# 提示词模板
templates:
  # 单页分析提示词
  single_page: |
    你是一个专业的代码分析助手，当用户提供代码文件时，请分析此代码文件在项目中的角色。假定用户对代码不熟悉，并希望快速了解项目的目的和实现方式。请按照以下结构化框架进行分析：
    1. 功能概述：用简明语言（100字以内）总结代码核心功能，描述代码实现目标、应用场景及主要模块，强调关键功能和用途。
    2. 列出该文件依赖的其他文件或模块。
    3. 代码结构分析：分析代码中关键函数、类和方法，简要说明它们的功能和作用；基于代码内容和结构，选择合适的 Mermaid 图表（流程图、时序图、类图或状态图）展示执行流程或模块关系，确保图表符合 Mermaid 语法。
      
  # 总结分析提示词
  summary: |
    基于各文件分析，生成项目结构分析报告：

    1. **项目架构概览**
       - 描述项目的主要模块和组件。
       - 提供项目的目录结构树形图。
       - 说明项目采用的架构设计模式（如MVC、MVVM等）。
       - 使用Mermaid图表展示项目的分层关系。

    2. **模块依赖分析**
       - 使用Mermaid图表展示模块间的依赖关系。
       - 简述每个关键模块的职责。

    请确保分析清晰易懂，并使用Mermaid图表来可视化项目结构和依赖关系。

  # 也可以通过文件路径指定提示词模板
  # single_page_file: "./templates/single_page_prompt.txt"
  # summary_file: "./templates/summary_prompt.txt"
```

## 支持的命令行参数

- `folder_path`: 要分析的代码文件夹路径
- `--filter`: 文件过滤器，指定要分析的文件范围，支持glob模式
- `--provider`: AI服务提供商（openai, anthropic, azure, gemini）
- `--model`: 使用的模型名称
- `--concurrency`: 并发处理文件数
- `--output`: 输出文件路径
- `--single-page-prompt`: 单页分析提示词文件路径
- `--summary-prompt`: 总结分析提示词文件路径

更多参数和详细说明请使用 `--help` 参数查看。
