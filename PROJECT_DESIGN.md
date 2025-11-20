
## 一、项目目标

* 建立一个**模型无关、平台无关**的 LLM Prompt 管理系统
* 支持 Prompt 的**增删改查 + 变量插值**，统一存储在 MySQL
* 支持在页面中通过变量填充后**实时渲染 Markdown Prompt 预览**
* 提供一个 Prompt Playground，用 LangChain 调用任意模型，对当前 Prompt 进行测试与快速迭代
* 为后续接入任意业务后台或微服务提供**统一 Prompt 服务接口**

---

整体结构就是：
MySQL 做 Prompt + 版本存储 → Jinja2 做插值 → Streamlit 做管理 UI + 预览 → LangChain 只在 Playground 中出场做 LLM 调用。
你后续任何业务服务都只需要调用这套 Prompt Service，而不用关心 LangChain 等上层框架的存在。
