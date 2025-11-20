import json
import streamlit as st
from app.ui.common import init_page, get_prompt_service, get_render_service

init_page("Prompt Preview")

prompt_service = get_prompt_service()
render_service = get_render_service()

try:
    # 1. Select Prompt Name
    prompt_names = prompt_service.list_prompt_names()

    selected_name = st.selectbox("Select Prompt", [""] + prompt_names)

    if selected_name:
        # 2. Select Version
        versions = prompt_service.list_versions_by_name(selected_name)
        version_options = [v.version for v in versions]

        if not version_options:
            st.error("No versions found for this prompt.")
        else:
            selected_version = st.selectbox("Select Version", version_options)

            # 3. Get Prompt Details
            prompt = prompt_service.get_prompt_details(selected_name, selected_version)
            if not prompt:
                st.error("Prompt not found.")
            else:
                st.divider()

                col_vars, col_preview = st.columns([1, 2])

                with col_vars:
                    st.subheader("Variables")
                    st.caption(f"Version: {prompt.version}")
                    variables_meta = prompt.variables_meta or {}
                    input_values = {}

                    with st.form("preview_form"):
                        if not variables_meta:
                            st.info("No variables defined.")

                        # Compatibility: Convert list to schema if needed
                        if isinstance(variables_meta, list):
                            props = {}
                            for item in variables_meta:
                                props[item["name"]] = {
                                    "type": item.get("type", "string"),
                                    "description": item.get("description", ""),
                                    "default": item.get("default", ""),
                                    "choices": item.get("choices", [])
                                }
                            variables_meta = {"type": "object", "properties": props}

                        properties = variables_meta.get("properties", {})
                        required_list = variables_meta.get("required", [])

                        for name, schema in properties.items():
                            m_type = schema.get("type", "string")
                            default = schema.get("default", "")
                            desc = schema.get("description", "")
                            choices = schema.get("enum", schema.get("choices", [])) # Handle 'enum' in JSON Schema
                            is_required = name in required_list

                            label = f"{name} {'*' if is_required else ''}"

                            if m_type == "string":
                                if choices:
                                    input_values[name] = st.selectbox(label, options=choices, help=desc)
                                else:
                                    # Check if it looks like a long text from description or name
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
                                # For complex types, use a text area that expects JSON
                                default_val = json.dumps(default, indent=2) if default else ("[]" if m_type == "array" else "{}")
                                json_str = st.text_area(f"{label} (JSON)", value=default_val, help=f"{desc} (Enter valid JSON)")
                                try:
                                    input_values[name] = json.loads(json_str)
                                except:
                                    st.error(f"Invalid JSON for {name}")
                                    input_values[name] = default_val # Fallback, rendering might fail but user sees error
                            else:
                                input_values[name] = st.text_input(label, value=str(default) if default else "", help=desc)

                        submitted = st.form_submit_button("Render Preview")

                with col_preview:
                    st.subheader("Preview")
                    if submitted or not variables_meta:
                        try:
                            rendered = render_service.render(selected_name, input_values)

                            tab1, tab2 = st.tabs(["Rendered Markdown", "Source Template"])

                            with tab1:
                                st.markdown(rendered)
                                st.divider()
                                with st.expander("Raw Output"):
                                    st.text(rendered)

                            with tab2:
                                st.code(prompt.template, language="jinja2")

                        except Exception as e:
                            st.error(f"Rendering Error: {e}")
                    else:
                        st.info("Fill variables and click Render Preview")

finally:
    prompt_service.db.close()
    render_service.db.close()
