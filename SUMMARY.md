### CodeAskCLI 项目结构分析报告

#### 一、项目架构概览

##### 1. 主要模块和组件
| 模块分类       | 包含组件                          | 核心职责                                                                 |
|----------------|-----------------------------------|--------------------------------------------------------------------------|
| **入口层**     | main.py                          | CLI启动入口，参数解析与任务调度                                          |
| **CLI控制层**  | cli.py                           | 参数解析、配置加载、AI客户端初始化、分析任务编排                          |
| **核心逻辑层** | analyzer.py                      | 代码分析主逻辑（增量分析、多线程处理、报告生成）                          |
| **服务层**     | api.py                           | 多AI服务适配（OpenAI/Anthropic/Azure/Gemini）                            |
| **配置层**     | config.py                        | 配置文件管理（自动发现、多格式解析、优先级处理）                          |
| **工具层**     | file_utils.py<br>templates.py    | 文件操作/哈希计算<br>提示词模板管理                                       |
| **界面层**     | tui.py                           | 终端可视化界面（进度条、状态反馈、动画效果）                              |

##### 2. 目录结构树形图
bash
.
├── main.py                      # 命令行入口
└── codeaskcli/                  # 核心包
    ├── __init__.py              # 包元数据
    ├── cli.py                   # 命令行控制
    ├── analyzer.py              # 分析引擎
    ├── api.py                   # AI服务适配
    ├── config.py                # 配置管理
    ├── file_utils.py            # 文件工具
    ├── templates.py             # 模板管理
    ├── tui.py                   # 终端界面
    └── data/                    # 示例数据（假设存在）
        └── default_templates.md


##### 3. 架构设计模式
**分层架构 + 工厂模式**
- **分层架构**：
  - **表示层**：cli.py + tui.py（用户交互）
  - **业务层**：analyzer.py（核心分析逻辑）
  - **服务层**：api.py（AI服务抽象）
  - **基础设施层**：file_utils.py + config.py（工具支持）
- **工厂模式**：
  - `AIClientFactory` 动态创建不同AI服务客户端
- **策略模式**：
  - 多模板加载策略（默认/文件/配置）

##### 4. 分层关系图（Mermaid）
mermaid
flowchart TD
    subgraph 表示层
        CLI[cli.py] --> TUI[tui.py]
    end
    
    subgraph 业务层
        CLI --> Analyzer[analyzer.py]
        Analyzer -->|调用| API[api.py]
    end
    
    subgraph 服务层
        API --> Factory[AIClientFactory]
    end
    
    subgraph 基础设施层
        Analyzer --> FileUtils[file_utils.py]
        CLI --> Config[config.py]
        CLI --> Templates[templates.py]
    end
    
    用户 --> CLI
    FileUtils --> 文件系统
    Config --> 配置文件


#### 二、模块依赖分析

##### 1. 模块依赖关系图（Mermaid）
mermaid
graph TD
    main.py --> codeaskcli.cli
    codeaskcli.cli --> analyzer
    codeaskcli.cli --> api
    codeaskcli.cli --> config
    codeaskcli.cli --> templates
    codeaskcli.cli --> tui
    
    analyzer --> api
    analyzer --> file_utils
    analyzer --> tui
    
    api -->|工厂模式| AIClientFactory
    
    config --> file_utils
    tui --> rich库
    
    style main.py fill:#f9f,stroke:#333
    style codeaskcli.cli fill:#f96,stroke:#333


##### 2. 关键模块职责说明

| 模块               | 核心职责                                                                 | 关键依赖                  |
|--------------------|--------------------------------------------------------------------------|---------------------------|
| **cli.py**         | 命令行参数解析、配置加载、分析任务编排                                   | analyzer, api, config     |
| **analyzer.py**    | 执行多线程代码分析、生成结构化报告、增量分析优化                         | api, file_utils, tui      |
| **api.py**         | 统一多AI服务接口、处理协议差异、实现重试机制                             | requests, 配置管理        |
| **config.py**      | 自动发现配置文件、支持多格式解析（YAML/TOML/JSON）、配置优先级管理       | os, yaml, tomli           |
| **file_utils.py**  | 文件哈希计算、通配符匹配、分析结果持久化（JSON/Markdown）                | os, glob, hashlib         |
| **templates.py**   | 管理AI提示模板（默认模板+自定义模板）                                    | 无                        |
| **tui.py**         | 实时显示分析进度、错误状态可视化、总结生成动画                           | rich库                    |

#### 三、关键架构特性总结

1. **可扩展的AI服务支持**
   - 通过工厂模式轻松接入新AI服务
   - 统一接口规范（`BaseAIClient`）

2. **高效分析机制**
   - 增量分析避免重复处理
   - 多线程加速文件处理
   - 智能重试策略（指数退避）

3. **灵活的配置系统**
   - 多格式配置文件支持
   - 环境变量覆盖机制
   - 自动发现配置文件

4. **用户体验优化**
   - 交互式终端界面
   - 彩色状态反馈
   - 多级进度显示

该架构通过清晰的分层设计和模块化组件，实现了高内聚低耦合的目标，同时保持了良好的可扩展性和可维护性。