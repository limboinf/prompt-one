import json
from datetime import datetime
import streamlit as st
from app.ui.common import init_page, get_prompt_service, get_render_service
from app.llm.langchain_client import LangChainClient
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.settings import settings

init_page("Prompt Comparison")

prompt_service = get_prompt_service()
render_service = get_render_service()


def init_comparison_session_state():
    """初始化对比页面的session state"""
    # Prompt选择 - 现在分别存储 name 和 version
    if 'selected_prompt_name' not in st.session_state:
        st.session_state.selected_prompt_name = ""
    if 'left_prompt_version' not in st.session_state:
        st.session_state.left_prompt_version = ""
    if 'right_prompt_version' not in st.session_state:
        st.session_state.right_prompt_version = ""

    # 模型配置
    if 'left_model_name' not in st.session_state:
        st.session_state.left_model_name = settings.DEFAULT_MODEL_NAME
    if 'left_temperature' not in st.session_state:
        st.session_state.left_temperature = 0.7
    if 'right_model_name' not in st.session_state:
        st.session_state.right_model_name = settings.DEFAULT_MODEL_NAME
    if 'right_temperature' not in st.session_state:
        st.session_state.right_temperature = 0.7

    # 变量数据
    if 'comparison_variables' not in st.session_state:
        st.session_state.comparison_variables = {}

    # 对话历史
    if 'left_chat_history' not in st.session_state:
        st.session_state.left_chat_history = []
    if 'right_chat_history' not in st.session_state:
        st.session_state.right_chat_history = []

    # 渲染结果缓存
    if 'left_rendered_prompt' not in st.session_state:
        st.session_state.left_rendered_prompt = ""
    if 'right_rendered_prompt' not in st.session_state:
        st.session_state.right_rendered_prompt = ""


def merge_variables_meta(left_meta, right_meta):
    """
    合并两个Prompt的变量元数据

    策略：
    1. 变量名不冲突：直接合并
    2. 变量名相同且类型相同：保留一个（使用左侧定义）
    3. 变量名相同但类型不同：重命名为 {name}_left 和 {name}_right

    返回：(merged_schema, conflict_map)
    - merged_schema: 合并后的JSON Schema
    - conflict_map: 冲突变量映射 {original_name: {'left': new_name, 'right': new_name}}
    """
    if not left_meta:
        left_meta = {}
    if not right_meta:
        right_meta = {}

    # 兼容性处理：如果是list格式，转换为object格式
    if isinstance(left_meta, list):
        props = {}
        for item in left_meta:
            props[item["name"]] = {
                "type": item.get("type", "string"),
                "description": item.get("description", ""),
                "default": item.get("default", ""),
                "choices": item.get("choices", [])
            }
        left_meta = {"type": "object", "properties": props}

    if isinstance(right_meta, list):
        props = {}
        for item in right_meta:
            props[item["name"]] = {
                "type": item.get("type", "string"),
                "description": item.get("description", ""),
                "default": item.get("default", ""),
                "choices": item.get("choices", [])
            }
        right_meta = {"type": "object", "properties": props}

    merged_properties = {}
    conflict_map = {}

    left_props = left_meta.get("properties", {})
    right_props = right_meta.get("properties", {})

    # 处理左侧变量
    for name, schema in left_props.items():
        if name not in right_props:
            # 不冲突，直接添加
            merged_properties[name] = schema.copy()
        elif right_props[name].get("type") == schema.get("type"):
            # 类型相同，保留左侧定义（合并description）
            merged_schema = schema.copy()
            if right_props[name].get("description") and not schema.get("description"):
                merged_schema["description"] = right_props[name].get("description")
            merged_properties[name] = merged_schema
        else:
            # 类型冲突，重命名
            left_name = f"{name}_left"
            merged_properties[left_name] = schema.copy()
            merged_properties[left_name]["description"] = f"[Left] {schema.get('description', name)}"
            conflict_map[name] = {'left': left_name}

    # 处理右侧变量
    for name, schema in right_props.items():
        if name not in left_props:
            # 不冲突，直接添加
            merged_properties[name] = schema.copy()
        elif name in conflict_map:
            # 已经在冲突处理中，添加右侧重命名版本
            right_name = f"{name}_right"
            merged_properties[right_name] = schema.copy()
            merged_properties[right_name]["description"] = f"[Right] {schema.get('description', name)}"
            conflict_map[name]['right'] = right_name
        # 类型相同的情况已经在左侧处理过了，跳过

    # 合并required字段
    left_required = left_meta.get("required", [])
    right_required = right_meta.get("required", [])
    merged_required = list(set(left_required + right_required))

    # 处理冲突变量的required
    for orig_name, mapping in conflict_map.items():
        if orig_name in merged_required:
            merged_required.remove(orig_name)
            if 'left' in mapping:
                merged_required.append(mapping['left'])
            if 'right' in mapping:
                merged_required.append(mapping['right'])

    merged_schema = {
        "type": "object",
        "properties": merged_properties,
        "required": merged_required
    }

    return merged_schema, conflict_map


def distribute_variables(variables, conflict_map, left_props, right_props):
    """
    根据冲突映射分发变量到左右两侧

    返回：(left_variables, right_variables)
    """
    left_variables = {}
    right_variables = {}

    # 处理冲突变量
    for orig_name, mapping in conflict_map.items():
        if 'left' in mapping and mapping['left'] in variables:
            left_variables[orig_name] = variables[mapping['left']]
        if 'right' in mapping and mapping['right'] in variables:
            right_variables[orig_name] = variables[mapping['right']]

    # 处理非冲突变量
    for name, value in variables.items():
        # 跳过已处理的冲突变量
        if any(name in [m.get('left'), m.get('right')] for m in conflict_map.values()):
            continue

        # 根据原始schema判断归属
        original_name = name.replace('_left', '').replace('_right', '')
        if name in left_props or original_name in left_props:
            left_variables[original_name if original_name in left_props else name] = value
        if name in right_props or original_name in right_props:
            right_variables[original_name if original_name in right_props else name] = value

    return left_variables, right_variables


def render_variable_form(merged_meta):
    """渲染变量输入表单，返回输入值"""
    input_values = {}

    if not merged_meta or not merged_meta.get("properties"):
        st.info("No variables to configure")
        return input_values

    properties = merged_meta.get("properties", {})
    required_list = merged_meta.get("required", [])

    for name, schema in properties.items():
        m_type = schema.get("type", "string")
        default = schema.get("default", "")
        desc = schema.get("description", "")
        choices = schema.get("enum", schema.get("choices", []))
        is_required = name in required_list

        label = f"{name} {'*' if is_required else ''}"

        if m_type == "string":
            if choices:
                input_values[name] = st.selectbox(label, options=choices, help=desc)
            else:
                if "text" in name.lower() or "content" in name.lower() or len(str(default)) > 50:
                    input_values[name] = st.text_area(label, value=str(default) if default else "", help=desc)
                else:
                    input_values[name] = st.text_input(label, value=str(default) if default else "", help=desc)
        elif m_type == "number" or m_type == "integer":
            val = float(default) if default else 0.0
            input_values[name] = st.number_input(label, value=val, help=desc)
        elif m_type == "boolean":
            val = bool(default) if default else False
            input_values[name] = st.checkbox(label, value=val, help=desc)
        elif m_type in ["array", "object"]:
            default_val = json.dumps(default, indent=2) if default else ("[]" if m_type == "array" else "{}")
            json_str = st.text_area(f"{label} (JSON)", value=default_val, help=f"{desc} (Enter valid JSON)")
            try:
                input_values[name] = json.loads(json_str)
            except:
                st.error(f"Invalid JSON format: {name}")
                input_values[name] = default_val
        else:
            input_values[name] = st.text_input(label, value=str(default) if default else "", help=desc)

    return input_values


def render_chat_panel(
    title,
    chat_history,
    rendered_prompt,
    show_system_prompt=True
):
    """渲染单个对比面板的聊天区域"""
    st.markdown(f"### {title}")

    if show_system_prompt and rendered_prompt:
        with st.expander("System Prompt", expanded=False):
            st.info(rendered_prompt)

    # 显示聊天历史
    if chat_history:
        for msg in chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "timestamp" in msg:
                    st.caption(f"🕒 {msg['timestamp']}")
    else:
        st.info("No conversation yet")


try:
    # 初始化session state
    init_comparison_session_state()

    # ==================== 顶部配置区 ====================
    st.subheader("⚙️ Comparison Configuration")

    # 第一行：选择提示词名称
    st.markdown("#### Select Prompts to Compare")
    prompt_names = prompt_service.list_prompt_names()
    selected_name = st.selectbox(
        "Prompt Name",
        [""] + prompt_names,
        key="prompt_name_select"
    )

    if selected_name:
        st.session_state.selected_prompt_name = selected_name
        # 获取该名称下的所有版本
        versions = prompt_service.list_versions_by_name(selected_name)

        if len(versions) < 2:
            st.warning(f"Prompt '{selected_name}' has only {len(versions)} version(s). At least 2 versions are required for comparison.")
        else:
            st.divider()

            # 第二行：选择左右两个版本
            col_left_config, col_right_config = st.columns(2)

            with col_left_config:
                st.markdown("#### 📝 Before Optimization")
                version_options = [f"{v.version} ({v.comment or 'No comment'})" for v in versions]
                left_version_idx = st.selectbox(
                    "Select Version",
                    range(len(versions)),
                    format_func=lambda i: version_options[i],
                    key="left_version_select"
                )

                if left_version_idx is not None:
                    st.session_state.left_prompt_version = versions[left_version_idx].version
                    st.caption(f"Created At: {versions[left_version_idx].created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.caption(f"Created By: {versions[left_version_idx].created_by}")

                with st.expander("Model Settings", expanded=False):
                    st.session_state.left_model_name = st.text_input(
                        "Model Name",
                        value=st.session_state.left_model_name,
                        key="left_model"
                    )
                    st.session_state.left_temperature = st.slider(
                        "Temperature",
                        0.0, 2.0,
                        st.session_state.left_temperature,
                        0.1,
                        key="left_temp"
                    )

            with col_right_config:
                st.markdown("#### ✨ After Optimization")
                right_version_idx = st.selectbox(
                    "Select Version",
                    range(len(versions)),
                    format_func=lambda i: version_options[i],
                    key="right_version_select",
                    index=1 if len(versions) > 1 else 0
                )

                if right_version_idx is not None:
                    st.session_state.right_prompt_version = versions[right_version_idx].version
                    st.caption(f"Created At: {versions[right_version_idx].created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.caption(f"Created By: {versions[right_version_idx].created_by}")

                with st.expander("Model Settings", expanded=False):
                    st.session_state.right_model_name = st.text_input(
                        "Model Name",
                        value=st.session_state.right_model_name,
                        key="right_model"
                    )
                    st.session_state.right_temperature = st.slider(
                        "Temperature",
                        0.0, 2.0,
                        st.session_state.right_temperature,
                        0.1,
                        key="right_temp"
                    )

    st.divider()

    # ==================== 变量输入区 ====================
    if (st.session_state.selected_prompt_name and
        st.session_state.left_prompt_version and
        st.session_state.right_prompt_version):

        left_prompt = prompt_service.get_prompt_details(
            st.session_state.selected_prompt_name,
            st.session_state.left_prompt_version
        )
        right_prompt = prompt_service.get_prompt_details(
            st.session_state.selected_prompt_name,
            st.session_state.right_prompt_version
        )

        if left_prompt and right_prompt:
            # 合并变量元数据
            merged_meta, conflict_map = merge_variables_meta(
                left_prompt.variables_meta,
                right_prompt.variables_meta
            )

            with st.expander("🎛️ Variable Configuration", expanded=True):
                if conflict_map:
                    st.warning(f"Detected {len(conflict_map)} variable name conflict(s). Automatically renamed with _left and _right suffixes.")

                with st.form("variables_form"):
                    input_values = render_variable_form(merged_meta)
                    submitted = st.form_submit_button("Update Variables", use_container_width=True)

                    if submitted:
                        # 渲染两个Prompt
                        try:
                            # 分发变量
                            left_vars, right_vars = distribute_variables(
                                input_values,
                                conflict_map,
                                left_prompt.variables_meta.get("properties", {}) if isinstance(left_prompt.variables_meta, dict) else {},
                                right_prompt.variables_meta.get("properties", {}) if isinstance(right_prompt.variables_meta, dict) else {}
                            )

                            # 使用 name + version 来渲染
                            st.session_state.left_rendered_prompt = render_service.render_by_version(
                                st.session_state.selected_prompt_name,
                                st.session_state.left_prompt_version,
                                left_vars
                            )
                            st.session_state.right_rendered_prompt = render_service.render_by_version(
                                st.session_state.selected_prompt_name,
                                st.session_state.right_prompt_version,
                                right_vars
                            )
                            # Update comparison_variables after successful rendering
                            st.session_state.comparison_variables = input_values
                            st.success("Variables updated. System prompts rendered successfully.")
                        except Exception as e:
                            st.error(f"Rendering error: {e}")

            st.divider()

            # ==================== 对比显示区 ====================
            col_left, col_right = st.columns(2)

            with col_left:
                render_chat_panel(
                    "📝 Before Optimization",
                    st.session_state.left_chat_history,
                    st.session_state.left_rendered_prompt
                )

            with col_right:
                render_chat_panel(
                    "✨ After Optimization",
                    st.session_state.right_chat_history,
                    st.session_state.right_rendered_prompt
                )

            # ==================== 底部输入区 ====================
            st.divider()

            col_reset, col_spacer = st.columns([1, 3])
            with col_reset:
                if st.button("🔄 Reset Conversation", use_container_width=True):
                    st.session_state.left_chat_history = []
                    st.session_state.right_chat_history = []
                    st.rerun()

            # 聊天输入
            if user_input := st.chat_input("Enter message for comparison testing... (Shift+Enter for newline)"):
                if not st.session_state.left_rendered_prompt or not st.session_state.right_rendered_prompt:
                    st.error("Please configure variables and update system prompts first.")
                else:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 添加用户消息到两侧历史
                    user_msg = {
                        "role": "user",
                        "content": user_input,
                        "timestamp": current_time
                    }
                    st.session_state.left_chat_history.append(user_msg.copy())
                    st.session_state.right_chat_history.append(user_msg.copy())

                    # 调用左侧LLM
                    with col_left:
                        with st.chat_message("user"):
                            st.markdown(user_input)
                            st.caption(f"🕒 {current_time}")

                        with st.chat_message("assistant"):
                            try:
                                # 构建消息（包含所有历史消息）
                                messages = [SystemMessage(content=st.session_state.left_rendered_prompt)]
                                for msg in st.session_state.left_chat_history:
                                    if msg["role"] == "user":
                                        messages.append(HumanMessage(content=msg["content"]))
                                    elif msg["role"] == "assistant":
                                        messages.append(AIMessage(content=msg["content"]))

                                # 调用LLM
                                client = LangChainClient(
                                    model_name=st.session_state.left_model_name,
                                    temperature=st.session_state.left_temperature
                                )
                                stream = client.stream(messages)
                                left_response = st.write_stream(stream)

                                response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                st.caption(f"🕒 {response_time}")

                                st.session_state.left_chat_history.append({
                                    "role": "assistant",
                                    "content": left_response,
                                    "timestamp": response_time
                                })
                            except Exception as e:
                                st.error(f"Call failed: {e}")
                                # 如果LLM调用失败，移除刚添加的用户消息
                                if st.session_state.left_chat_history and st.session_state.left_chat_history[-1]["role"] == "user":
                                    st.session_state.left_chat_history.pop()

                    # 调用右侧LLM
                    with col_right:
                        with st.chat_message("user"):
                            st.markdown(user_input)
                            st.caption(f"🕒 {current_time}")

                        with st.chat_message("assistant"):
                            try:
                                # 构建消息（包含所有历史消息）
                                messages = [SystemMessage(content=st.session_state.right_rendered_prompt)]
                                for msg in st.session_state.right_chat_history:
                                    if msg["role"] == "user":
                                        messages.append(HumanMessage(content=msg["content"]))
                                    elif msg["role"] == "assistant":
                                        messages.append(AIMessage(content=msg["content"]))

                                # 调用LLM
                                client = LangChainClient(
                                    model_name=st.session_state.right_model_name,
                                    temperature=st.session_state.right_temperature
                                )
                                stream = client.stream(messages)
                                right_response = st.write_stream(stream)

                                response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                st.caption(f"🕒 {response_time}")

                                st.session_state.right_chat_history.append({
                                    "role": "assistant",
                                    "content": right_response,
                                    "timestamp": response_time
                                })
                            except Exception as e:
                                st.error(f"Call failed: {e}")
                                # 如果LLM调用失败，移除刚添加的用户消息
                                if st.session_state.right_chat_history and st.session_state.right_chat_history[-1]["role"] == "user":
                                    st.session_state.right_chat_history.pop()
        else:
            st.error("Unable to load selected prompt versions")
    else:
        st.info("👆 Please select a prompt and its versions for comparison above")

finally:
    prompt_service.db.close()
    render_service.db.close()
