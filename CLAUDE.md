# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

Prompt One 是一个与模型无关的 LLM Prompt 管理系统，用于管理和测试 Jinja2 模板化的 Prompt。

## 开发命令

### 数据库初始化
```bash
# 首先在 MySQL 中创建数据库
# CREATE DATABASE prompt_manager;

# 初始化数据库表
python scripts/init_db.py
```

### 运行应用
```bash
# 启动 Streamlit 应用
streamlit run main.py

# 应用将在 http://localhost:8501 运行
```

### 环境配置
复制 `config/.env.example` 到项目根目录的 `.env` 并配置：
- `DB_*`: MySQL 连接配置
- `OPENAI_API_KEY`: OpenAI API 密钥（Playground 功能必需）

## 架构概览

### 核心数据模型
- **Prompt** (`app/models/prompt.py`): 单表模型，包含 name（唯一标识）、display_name、version、template（Jinja2 模板）和 variables_meta（JSON Schema 格式的变量元数据）

### 关键服务
- **PromptRenderService** (`app/services/template_engine.py`): 使用 Jinja2 渲染 Prompt 模板，支持变量默认值和验证
- **meta_generator.py**: LLM 自动生成变量元数据（JSON Schema 格式）
- **prompt_service.py**: Prompt 的 CRUD 操作

### 数据库交互模式
```python
from app.db.session import SessionLocal

# 使用上下文管理器获取数据库 session
db = SessionLocal()
try:
    # 数据库操作
    pass
finally:
    db.close()
```

### 页面结构
- `main.py`: 主页
- `pages/01_Prompt_Manager.py`: Prompt CRUD 管理
- `pages/02_Prompt_Preview.py`: 变量替换和 Markdown 预览
- `pages/03_Playground.py`: LangChain 集成的 LLM 测试
- `pages/04_Prompt_Comparison.py`: Prompt 版本并排对比

## 技术栈
- Frontend: Streamlit
- ORM: SQLAlchemy（使用 Mapped 类型注解）
- 数据验证: Pydantic
- 模板引擎: Jinja2
- LLM 集成: LangChain

## 开发原则
- 保持简单：不要过度设计，优先可读性和可维护性
- 最小化文档：代码应自解释，避免创建不必要的文档文件
