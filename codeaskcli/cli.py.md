### 代码分析报告：codeaskcli\cli.py

#### 1. 功能概述
该文件是CodeAsk CLI工具的命令行入口，主要功能是：  
**通过命令行参数配置代码分析任务，整合AI服务（OpenAI/Azure等），分析指定代码库并生成结构化报告**。核心模块包括参数解析器、配置加载器、AI客户端工厂、提示词模板系统。关键功能包括增量分析、多AI供应商支持、并发处理、终端用户界面（TUI）控制等。

#### 2. 依赖关系
python
# 主要依赖模块
argparse            # 命令行参数解析
os                  # 文件系统操作
codeaskcli.api      # AI服务客户端工厂
codeaskcli.analyzer # 核心分析逻辑
codeaskcli.templates# 提示词模板管理
codeaskcli.config   # 配置文件管理


#### 3. 代码结构分析

**关键函数说明**：
| 函数/类             | 功能描述                                                                 |
|---------------------|------------------------------------------------------------------------|
| `parse_arguments()` | 定义23个命令行参数，处理路径/过滤器/AI参数/分析模式等配置               |
| `prepare_prompts()` | 三层级提示词加载（默认模板→配置文件→命令行指定文件）                    |
| `create_api_client()` | 动态创建AI客户端，支持OpenAI/Anthropic/Azure/Gemini的差异化配置逻辑 |
| `run_analysis()`    | 主执行流：验证配置→加载模板→初始化分析器→启动并发分析→输出结果          |

**执行流程图** (Mermaid):
mermaid
graph TD
    A[用户执行命令] --> B[parse_arguments解析参数]
    B --> C{配置文件存在?}
    C -->|是| D[加载配置]
    C -->|否| E[使用默认配置]
    D & E --> F[prepare_prompts准备提示词]
    B --> G[prepare_file_patterns生成文件过滤器]
    F & G --> H[create_api_client创建AI客户端]
    H --> I[初始化CodeAnalyzer]
    I --> J[analyze_project执行分析]
    J --> K{启用TUI?}
    K -->|是| L[显示交互式界面]
    K -->|否| M[生成文本报告]


**关键设计特点**：
1. **配置优先级链**：环境变量 > 命令行参数 > 配置文件 > 默认值
2. **多AI供应商适配**：通过工厂模式支持不同API的参数结构
3. **增量分析优化**：通过配置文件哈希值跟踪变更，避免重复分析
4. **并发控制**：可调节的线程数应对大规模代码库分析