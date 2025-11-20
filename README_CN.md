# Prompt One

一个模型无关、平台无关的 LLM Prompt 管理系统，旨在将 Prompt 管理与模型调用层彻底剥离。

## 功能特性

- **Prompt 管理**：支持 Prompt 的增删改查 + 版本控制，统一存储在 MySQL 中。
- **Jinja2 模版**：支持使用 Jinja2 语法进行变量插值。
- **实时预览**：支持在页面中通过变量填充后实时渲染 Prompt（支持 Markdown）。
- **Playground**：集成 LangChain，支持调用任意模型（如 OpenAI）对当前 Prompt 进行测试与快速迭代。
- **统一服务**：为后续接入任意业务后台或微服务提供统一 Prompt 服务接口。

## 技术栈

- **前端**：Streamlit
- **后端逻辑**：Python (Pydantic, SQLAlchemy)
- **数据库**：MySQL
- **模版引擎**：Jinja2
- **LLM 集成**：LangChain

## 环境要求

- Python 3.11+
- MySQL Server

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件，配置数据库和 LLM 信息：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=prompt_manager

# LLM 配置 (用于 Playground 功能)
OPENAI_API_KEY=sk-...
# 可选配置
# OPENAI_API_BASE=https://api.openai.com/v1
# DEFAULT_MODEL_NAME=gpt-3.5-turbo
```

### 3. 数据库初始化

首先，请确保在 MySQL 中创建了对应的数据库：

```sql
CREATE DATABASE prompt_manager;
```

然后运行初始化脚本，创建必要的数据表：

```bash
python scripts/init_db.py
```

### 4. 运行应用

启动 Streamlit 应用：

```bash
streamlit run main.py
```

## 项目结构

- `app/`：核心业务代码
    - `db/`：数据库会话与模型
    - `models/`：Pydantic 数据模型
    - `services/`：业务逻辑服务
    - `ui/`：Streamlit UI 组件
    - `llm/`：LangChain 封装
- `pages/`：Streamlit 页面（Prompt 管理, 预览, Playground）
- `config/`：配置管理
- `scripts/`：工具脚本
