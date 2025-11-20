import streamlit as st
import json
import pandas as pd
from jinja2 import Environment, meta
from app.ui.common import init_page, get_prompt_service

init_page("Prompt Manager")

def list_prompts_view(service):
    st.subheader("Prompt List")
    prompts = service.list_prompts()
    
    if not prompts:
        st.info("No prompts found.")
        return

    data = []
    for p in prompts:
        data.append({
            "Name": p.name,
            "Display Name": p.display_name,
            "Description": p.description,
            "Updated At": p.updated_at
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    prompt_names = [p.name for p in prompts]
    selected_name = st.selectbox("Select Prompt to View/Edit", [""] + prompt_names)
    
    if selected_name:
        if st.button("Go to Details"):
            st.session_state.selected_prompt_name = selected_name
            st.rerun()

def create_prompt_view(service):
    st.subheader("Create New Prompt")
    with st.form("create_prompt_form"):
        name = st.text_input("Unique Name (e.g. chat_summary)")
        display_name = st.text_input("Display Name")
        description = st.text_area("Description")
        template = st.text_area("Template (Jinja2)", height=200, value="Hello {{ name }}!")
        variables_meta_str = st.text_area("Variables Meta (JSON)", value='[{"name": "name", "type": "string", "required": true}]', help="List of variable definitions")
        
        submitted = st.form_submit_button("Create Prompt")
        if submitted:
            if not name or not template:
                st.error("Name and Template are required.")
            else:
                try:
                    variables_meta = json.loads(variables_meta_str)
                    service.create_prompt(name, display_name, description, template, variables_meta)
                    st.success(f"Prompt {name} created!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def prompt_details_view(service, prompt_name):
    st.subheader(f"Prompt: {prompt_name}")
    if st.button("← Back to List"):
        del st.session_state.selected_prompt_name
        st.rerun()

    prompt = service.get_prompt_details(prompt_name)
    if not prompt:
        st.error("Prompt not found")
        return

    st.write(f"**Display Name:** {prompt.display_name}")
    st.write(f"**Description:** {prompt.description}")
    
    st.divider()
    
    st.write("### Versions")
    versions = service.get_versions(prompt_name)
    
    v_data = []
    latest_ver = None
    for v in versions:
        if v.is_latest:
            latest_ver = v
        v_data.append({
            "Version": v.version,
            "Latest": "✅" if v.is_latest else "",
            "Created At": v.created_at.strftime("%Y-%m-%d %H:%M"),
            "Comment": v.comment
        })
    st.table(pd.DataFrame(v_data))

    st.divider()
    st.write("### Create New Version")
    
    # Initialize form state if switching prompts
    if st.session_state.get("current_prompt_name_view") != prompt_name:
        st.session_state.current_prompt_name_view = prompt_name
        st.session_state.nv_version = ""
        st.session_state.nv_comment = ""
        st.session_state.nv_template = latest_ver.template if latest_ver else ""
        st.session_state.nv_meta = json.dumps(latest_ver.variables_meta, indent=2) if latest_ver and latest_ver.variables_meta else "[]"
    
    with st.form("new_version_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_version_str = st.text_input("New Version (e.g. v2)", key="nv_version")
        with col2:
            comment = st.text_input("Comment", key="nv_comment")
            
        new_template = st.text_area("Template", height=300, key="nv_template")
        
        # Button to generate meta from template
        if st.form_submit_button("Generate Variables Meta"):
            try:
                env = Environment()
                ast = env.parse(st.session_state.nv_template)
                variables = meta.find_undeclared_variables(ast)
                
                meta_list = []
                for var in variables:
                    meta_list.append({
                        "name": var,
                        "type": "string",
                        "required": True
                    })
                st.session_state.nv_meta = json.dumps(meta_list, indent=2)
                st.rerun()
            except Exception as e:
                st.error(f"Error generating meta: {e}")

        new_meta_str = st.text_area("Variables Meta (JSON)", height=150, key="nv_meta")
        
        if st.form_submit_button("Publish New Version"):
            try:
                meta_json = json.loads(st.session_state.nv_meta)
                service.create_new_version(prompt_name, st.session_state.nv_template, meta_json, st.session_state.nv_version, st.session_state.nv_comment)
                st.success("Version created!")
                # Clear state to force reload or just rerun
                del st.session_state.current_prompt_name_view
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Main Logic
service = get_prompt_service()
try:
    if 'selected_prompt_name' in st.session_state:
        prompt_details_view(service, st.session_state.selected_prompt_name)
    else:
        tab1, tab2 = st.tabs(["List Prompts", "Create Prompt"])
        with tab1:
            list_prompts_view(service)
        with tab2:
            create_prompt_view(service)
finally:
    service.db.close()
