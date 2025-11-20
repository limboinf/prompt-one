结论：按你给的技术栈，可以做成一个极薄后端 + Streamlit 前端的一体项目，把 Prompt 管理从模型调用层彻底剥离。下面给出项目目标、背景和一个可直接拆成 issue 的详细 TODO 列表。

---

## 一、项目目标

* 建立一个**模型无关、平台无关**的 LLM Prompt 管理系统
* 支持 Prompt 的**增删改查 + 变量插值**，统一存储在 MySQL
* 支持在页面中通过变量填充后**实时渲染 Markdown Prompt 预览**
* 提供一个 Prompt Playground，用 LangChain 调用任意模型，对当前 Prompt 进行测试与快速迭代
* 为后续接入任意业务后台或微服务提供**统一 Prompt 服务接口**

---

## 二、项目背景

* 当前 LLM 应用大多直接在代码里写死 Prompt，导致：

  * 难以版本控制，难以回滚
  * 环境（dev/staging/prod）与 Prompt 混杂
  * 不同模型/框架下的 Prompt 无法统一管理
* 现有 LLM 框架（LangChain 等）把“Prompt 管理”和“模型调用”绑死在一起，不利于：

  * 换模型
  * 多语言 / 多环境切换
  * 非该框架应用的复用
* 本项目通过：**Jinja2（模板） + MySQL（存储与版本） + Streamlit（管理 UI） + LangChain（仅用作 Playground 调用器）**
  实现一套可被任何上层服务调用的 Prompt 管理基础设施。

---

## 三、详细 TODO LIST

按模块拆分，直接可转为 issue。

### 0. 项目基础结构

1. 初始化代码仓库结构

   * `app/`（业务代码）

     * `db/`：数据库会话、模型
     * `models/`：Pydantic 数据模型
     * `services/`：业务服务（prompt_service、playground_service）
     * `ui/`：Streamlit 页面
     * `llm/`：LangChain 封装
     * `templates/`：Jinja2 基础模版（如公共片段，可选）
   * `config/`

     * `config.toml` 或 `.env`：数据库、LLM API Key、默认模型配置
   * `main.py`：Streamlit 入口
   * `requirements.txt` / `pyproject.toml`

2. 配置管理

   * 使用 `pydantic-settings` 或 `python-dotenv` 管理：

     * MySQL 连接串
     * 默认模型名称（如 `gpt-4.1-mini`/`gpt-4o-mini`）
     * LangChain 使用的 LLM 端点和 API Key

3. 依赖

   * Python 3.11+
   * `streamlit`
   * `SQLAlchemy` 或 `SQLModel`
   * `pydantic`
   * `jinja2`
   * `langchain` + 对应 LLM provider（如 `langchain-openai`）
   * `mysqlclient` 或 `pymysql`

---

### 1. 数据库设计与实现

1. 创建 MySQL 数据库

   * 库名示例：`prompt_manager`

2. 设计表结构（最小可用）

   表一：`t_prompt`

   ```sql
   CREATE TABLE t_prompt (
       id              BIGINT PRIMARY KEY AUTO_INCREMENT,
       name            VARCHAR(128) NOT NULL COMMENT '内部唯一标识，如: chat_summarize',
       display_name    VARCHAR(128) NOT NULL COMMENT '展示名，如: 对话总结提示词',
       description     VARCHAR(255) NULL COMMENT '使用说明',
       is_enabled      TINYINT(1) NOT NULL DEFAULT 1,
       created_at      DATETIME NOT NULL,
       updated_at      DATETIME NOT NULL,
       UNIQUE KEY uk_name (name)
   );
   ```

   表二：`t_prompt_version`

   ```sql
   CREATE TABLE t_prompt_version (
       id              BIGINT PRIMARY KEY AUTO_INCREMENT,
       prompt_id       BIGINT NOT NULL,
       version         VARCHAR(32) NOT NULL COMMENT '版本号，如 v1, v2, 2025.11.20-1',
       template        TEXT NOT NULL COMMENT 'Jinja2 模板内容',
       variables_meta  JSON NULL COMMENT '变量定义/示例，便于 UI 渲染表单',
       is_latest       TINYINT(1) NOT NULL DEFAULT 0,
       created_by      VARCHAR(64) NULL,
       created_at      DATETIME NOT NULL,
       comment         VARCHAR(255) NULL,
       UNIQUE KEY uk_prompt_version (prompt_id, version),
       KEY idx_prompt_latest (prompt_id, is_latest)
   );
   ```

3. 编写 SQLAlchemy/SQLModel ORM

   * 对应 `Prompt` 实体、`PromptVersion` 实体
   * 创建数据库 Session 工具：`get_session()`

4. 初始化表结构脚本

   * 编写 `scripts/init_db.py`，用于建表和初始化测试数据

---

### 2. Jinja2 渲染与变量插值层

1. 创建 `app/services/template_engine.py`

   * 初始化 Jinja2 `Environment`（`autoescape=False`）
   * 暴露方法：

     * `render_template(template_str: str, variables: dict) -> str`
   * 控制：

     * 禁止模板访问危险内置（可用 `Environment` 配置或沙盒）

2. 定义变量元数据结构（用于 UI）

   * 使用 Pydantic 模型：

     * `PromptVariableMeta`：`name`, `type`, `required`, `default`, `description`
   * 存入 `t_prompt_version.variables_meta`（JSON）

3. 定义统一的渲染服务 `PromptRenderService`

   * `get_latest_version(prompt_name)`
   * `get_specific_version(prompt_name, version)`
   * `render(prompt_name, variables, version=None)`：

     1. 查询版本
     2. 校验变量（与 `variables_meta` 对齐，可选）
     3. 调用 Jinja2 渲染并返回字符串

---

### 3. Prompt CRUD 后端服务

1. `app/services/prompt_service.py`

   * 创建 Prompt

     * `create_prompt(name, display_name, description, template, variables_meta, created_by)`

       * 插入 `t_prompt`
       * 插入 `t_prompt_version`，version 默认 `v1`，`is_latest=1`
   * 更新 Prompt（新增版本而非覆盖）

     * `create_new_version(prompt_name, template, variables_meta, comment, created_by)`

       * 给同一 `prompt_id` 新增一条 `t_prompt_version`
       * 设置老版本 `is_latest=0`，新版本 `is_latest=1`
   * 删除 Prompt（软删）

     * `disable_prompt(prompt_name)` → `t_prompt.is_enabled=0`
   * 查询列表

     * 支持按 `name`, `display_name` 模糊搜索
   * 查询单条 Prompt 的所有版本

2. 保证 service 层不依赖 Streamlit，只做纯 Python 逻辑，方便将来迁移成独立 API 服务。

---

### 4. Streamlit UI：整体路由与布局

1. 设计页面结构

   * 左侧菜单：

     * 「Prompt 列表 / 管理」
     * 「Prompt 详情 / 编辑 / 版本」
     * 「Preview 预览」
     * 「Playground」
   * 或使用多页结构：`pages/01_manage.py`, `pages/02_preview.py`, `pages/03_playground.py`

2. 实现全局状态

   * 使用 `st.session_state` 存 `selected_prompt_name`, `selected_version`

---

### 5. 功能 1：CRUD 提示词（含变量插值定义）

页面：`Prompt 管理`

1. Prompt 列表

   * 表格展示：

     * `name`, `display_name`, `description`, `is_enabled`, `latest_version`, `updated_at`
   * 操作：

     * 查看详情
     * 新增 Prompt
     * 禁用/启用 Prompt

2. 新增 Prompt 表单

   * 输入：

     * `name`（唯一标识）
     * `display_name`
     * `description`
     * `template`（多行文本区）
     * `variables_meta`（可以做一个简单 JSON 编辑区，初期无需复杂 UI）
   * 提交后：

     * 调用 `create_prompt`

3. Prompt 详情 + 版本管理

   * 显示：

     * 基本信息
     * 版本列表（version、created_by、created_at、comment、is_latest）
   * 操作：

     * 选择版本 → 进入编辑/预览
     * 克隆版本为新版本（自动生成 `v_next`）
     * 标记某版本为 `latest`（可选）

4. 新版本编辑页面

   * 显示原始模板
   * 可修改：

     * `template`
     * `variables_meta`
     * `comment`
   * 提交 → `create_new_version`

---

### 6. 功能 2：提示词回显 / 动态渲染（Markdown 形式）

页面：`Prompt 预览`

1. 选择 Prompt + 版本

   * 左侧下拉：`prompt_name`
   * 右侧下拉：`version`（默认选中 `is_latest=1`）

2. 根据 `variables_meta` 动态生成变量输入表单

   * 遍历 `variables_meta` JSON
   * 对不同类型生成不同控件：

     * `string` → `st.text_input`
     * `text` → `st.text_area`
     * `int/float` → `st.number_input`
     * `choice` → `st.selectbox`
   * 使用默认值填充

3. 点击「渲染」按钮

   * 调用 `PromptRenderService.render(...)`
   * 将返回字符串通过 `st.markdown(prompt_text)` 渲染到页面

4. 显示原模板对照（可选）

   * 上半部分：模板源码（`st.code(template_str, language="jinja2")`）
   * 下半部分：渲染后的 Prompt（Markdown）

---

### 7. 功能 3：Prompt Playground（集成 LangChain）

页面：`Prompt Playground`

目标：用当前 Prompt + 填写变量 + 选择模型 → 实时调用 LLM。

1. 选择 Prompt + 版本

   * 同预览页逻辑

2. 填写变量（同预览页）

3. 模型配置区域

   * 选择模型提供方（初版可以只支持一个，如 OpenAI）
   * 选择模型名称（下拉：`gpt-4.1-mini` / `gpt-4.1` 等）
   * 设置 temperature、max_tokens（基础参数）

4. 显示渲染后的 Prompt

   * 用户可以先确认 Prompt 文本

5. 调用 LangChain

   * 封装 `app/llm/langchain_client.py`：

     * 提供 `invoke_llm(model_name, prompt_text, **kwargs) -> str`
     * 内部使用 `langchain-openai` 的 `ChatOpenAI` / `LLM` 等
   * Playground 页面：

     * 点击「Run」按钮
     * `render_prompt` → `invoke_llm` → 显示模型输出

6. 输出展示

   * 使用 `st.markdown`/`st.code` 显示模型响应
   * 展示本次调用的参数摘要（模型名、temperature、token 限制等）

7. 可选增强

   * 把调用日志写入 MySQL：`t_prompt_playground_log`

     * 字段：prompt_name, version, variables, model_name, response_snippet, created_at
   * 支持“重新运行”上一次调用（复现性）

---


整体结构就是：
MySQL 做 Prompt + 版本存储 → Jinja2 做插值 → Streamlit 做管理 UI + 预览 → LangChain 只在 Playground 中出场做 LLM 调用。
你后续任何业务服务都只需要调用这套 Prompt Service，而不用关心 LangChain 等上层框架的存在。

