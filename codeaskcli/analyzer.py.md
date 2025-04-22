### 代码分析报告

#### 1. 功能概述
该代码是代码分析工具的核心模块，通过AI接口自动分析项目代码文件，支持增量分析和多线程处理。主要功能包括：扫描匹配文件、调用AI模型进行代码分析、生成单文件分析报告和项目总结报告、支持增量更新（仅分析修改过的文件）和终端可视化进度展示。适用于代码质量检查、项目文档生成等场景。

#### 2. 依赖项

- 内部模块：
  codeaskcli.api.BaseAIClient/AIApiClient（AI服务接口）
  codeaskcli.file_utils（文件操作工具集）
  codeaskcli.tui.AnalysisTUI（终端UI组件）

- 标准库：
  os, json, time, concurrent.futures
  typing（类型注解）


#### 3. 代码结构分析

**关键组件说明**：
- `analyze_single_file()`：单文件分析核心方法，包含：
  - 文件读取与哈希计算
  - AI接口调用（3次重试机制）
  - 分析进度状态更新
  - 错误处理与指数退避策略

- `analyze_project()`：项目分析入口，实现：
  - 文件模式匹配（`find_matching_files`）
  - 增量分析（`load_previous_analysis`）
  - 多线程并发处理（ThreadPoolExecutor）
  - 结果合并与清理（`remove_analysis_file`）

- `generate_summary()`：聚合分析结果生成总结报告，包含：
  - 多文件内容拼接
  - AI总结生成接口调用
  - 总结生成状态跟踪

**执行流程图**：
mermaid
graph TD
    A[开始项目分析] --> B[查找匹配文件]
    B --> C{增量模式?}
    C -->|是| D[加载历史分析]
    C -->|否| E[分析所有文件]
    D --> F[识别变更文件]
    F --> E
    E --> G[创建线程池]
    G --> H[并发分析文件]
    H --> I{发生错误?}
    I -->|是| J[重试机制]
    I -->|否| K[收集结果]
    J --> K
    K --> L[生成总结报告]
    L --> M[保存分析结果]
    M --> N[显示分析耗时]
    N --> O[结束]


**核心类关系**：
mermaid
classDiagram
    class CodeAnalyzer{
        +analyze_single_file()
        +generate_summary()
        +analyze_project()
        +load_previous_analysis()
        -api_client: BaseAIClient
        -concurrency: int
    }
    
    class BaseAIClient{
        +chat_completion()
        +clean_response()
    }
    
    class AnalysisTUI{
        +update_file_progress()
        +start_summary_generation()
    }
    
    CodeAnalyzer --> BaseAIClient: 依赖
    CodeAnalyzer --> AnalysisTUI: 可选依赖
    CodeAnalyzer ..> file_utils: 工具调用
