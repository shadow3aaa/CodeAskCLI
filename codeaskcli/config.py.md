### 1. 功能概述  
该文件是配置文件管理模块，用于查找、加载和管理多种格式（YAML/TOML/JSON）的配置文件。其核心功能包括自动检测配置文件、解析配置内容，并提供统一接口获取API配置、分析器参数、文件过滤规则及提示词模板。主要服务于CLI工具，允许用户通过配置文件自定义工具行为。

---

### 2. 依赖项  
- **Python标准库**：`os`, `json`, `pathlib`  
- **第三方库**：`yaml`（处理YAML文件）、`tomli`（处理TOML文件）  
- **项目内部依赖**：无显式依赖，但可能被其他模块调用以获取配置信息（如API密钥、模板路径等）。

---

### 3. 代码结构分析  

#### 关键类与方法  
- **`ConfigManager`类**：  
  - **`find_config_file`**：遍历预定义文件名列表，查找项目目录下的配置文件。  
  - **`load_config`**：根据文件扩展名选择解析器（YAML/TOML/JSON），加载配置到字典。  
  - **`get_templates`**：从配置中提取单页/总结分析的提示词模板，支持从文件或直接配置读取。  
  - **`get_api_config`**、**`get_analyzer_config`**：分别返回API和分析器的子配置。  
  - **`get_filters`**：获取文件过滤规则，兼容旧版`extensions`字段并生成通配符模式。  

#### Mermaid 流程图  
mermaid
graph TD
    A[用户初始化ConfigManager] --> B[调用load_config]
    B --> C{是否指定config_path?}
    C -- 否 --> D[调用find_config_file遍历CONFIG_FILENAMES]
    C -- 是 --> E[直接使用指定路径]
    D --> F{找到文件?}
    F -- 是 --> G[按扩展名选择解析器]
    F -- 否 --> H[返回空配置]
    G --> I[加载配置到self.config]
    I --> J[返回配置字典]
    J --> K[用户调用get_*方法获取具体配置]
  
**说明**：流程图展示了从初始化到获取配置的完整流程，涵盖自动查找文件、格式解析及配置读取步骤。