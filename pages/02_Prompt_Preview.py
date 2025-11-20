import streamlit as st
from app.ui.common import init_page, get_prompt_service, get_render_service

init_page("Prompt Preview")

prompt_service = get_prompt_service()
render_service = get_render_service()

try:
    # 1. Select Prompt
    prompts = prompt_service.list_prompts()
    prompt_names = [p.name for p in prompts]
    
    selected_name = st.selectbox("Select Prompt", [""] + prompt_names)
    
    if selected_name:
        # 2. Select Version
        versions = prompt_service.get_versions(selected_name)
        if not versions:
            st.warning("No versions found for this prompt.")
        else:
            version_opts = [v.version for v in versions]
            # Find latest index
            latest_idx = 0
            for idx, v in enumerate(versions):
                if v.is_latest:
                    latest_idx = idx
                    break
            
            selected_version = st.selectbox("Select Version", version_opts, index=latest_idx)
            
            version_obj = next(v for v in versions if v.version == selected_version)
            
            st.divider()
            
            col_vars, col_preview = st.columns([1, 2])
            
            with col_vars:
                st.subheader("Variables")
                variables_meta = version_obj.variables_meta or []
                input_values = {}
                
                with st.form("preview_form"):
                    if not variables_meta:
                        st.info("No variables defined.")
                    
                    for meta in variables_meta:
                        name = meta.get("name")
                        m_type = meta.get("type", "string")
                        default = meta.get("default", "")
                        desc = meta.get("description", "")
                        choices = meta.get("choices", [])
                        required = meta.get("required", True)
                        
                        label = f"{name} {'*' if required else ''}"
                        
                        if m_type == "text":
                            input_values[name] = st.text_area(label, value=str(default) if default else "", help=desc)
                        elif m_type == "number":
                            if name == "pages":
                                input_values[name] = st.text_input(label, value=str(default) if default else "", help=desc)
                            else:
                                val = float(default) if default else 0.0
                                input_values[name] = st.number_input(label, value=val, help=desc)
                        elif m_type == "choice":
                            input_values[name] = st.selectbox(label, options=choices, help=desc)
                        else:
                            input_values[name] = st.text_input(label, value=str(default) if default else "", help=desc)
                    
                    submitted = st.form_submit_button("Render Preview")
            
            with col_preview:
                st.subheader("Preview")
                if submitted or not variables_meta:
                    try:
                        rendered = render_service.render(selected_name, input_values, selected_version)
                        
                        tab1, tab2 = st.tabs(["Rendered Markdown", "Source Template"])
                        
                        with tab1:
                            st.markdown(rendered)
                            st.divider()
                            with st.expander("Raw Output"):
                                st.text(rendered)
                                
                        with tab2:
                            st.code(version_obj.template, language="jinja2")
                            
                    except Exception as e:
                        st.error(f"Rendering Error: {e}")
                else:
                    st.info("Fill variables and click Render Preview")

finally:
    prompt_service.db.close()
    render_service.db.close()
