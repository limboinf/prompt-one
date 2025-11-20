import streamlit as st
import json
import pandas as pd
from app.services.meta_generator import generate_variables_meta
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
    
    # Initialize defaults in session state if not present
    if "create_prompt_template" not in st.session_state:
        st.session_state.create_prompt_template = "Hello {{ name }}!"
    if "create_prompt_meta" not in st.session_state:
        st.session_state.create_prompt_meta = '{\n  "type": "object",\n  "properties": {\n    "name": {\n      "type": "string"\n    }\n  }\n}'
    
    with st.form("create_prompt_form"):
        name = st.text_input("Unique Name (e.g. chat_summary)", key="create_prompt_name")
        display_name = st.text_input("Display Name", key="create_prompt_display_name")
        description = st.text_area("Description", key="create_prompt_description")
        template = st.text_area("Template (Jinja2)", height=200, key="create_prompt_template")
        
        if st.form_submit_button("Generate Variables Meta"):
            try:
                meta_json_str = generate_variables_meta(st.session_state.create_prompt_template)
                st.session_state.create_prompt_meta = meta_json_str
                st.rerun()
            except Exception as e:
                st.error(f"Error generating meta: {e}")

        variables_meta_str = st.text_area("Variables Meta (JSON)", height=200, key="create_prompt_meta", help="JSON Schema definition of variables")
        
        submitted = st.form_submit_button("Create Prompt", type="primary")
        if submitted:
            if not name or not template:
                st.error("Name and Template are required.")
            else:
                try:
                    variables_meta = json.loads(variables_meta_str)
                    service.create_prompt(name, display_name, description, template, variables_meta)
                    st.success(f"Prompt {name} created!")
                    # Clear session state
                    keys_to_clear = ["create_prompt_name", "create_prompt_display_name", "create_prompt_description", "create_prompt_template", "create_prompt_meta"]
                    for k in keys_to_clear:
                        if k in st.session_state:
                            del st.session_state[k]
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
    st.write(f"**Version:** {prompt.version}")
    st.write(f"**Last Updated:** {prompt.updated_at}")
    
    st.divider()
    st.write("### Edit Prompt")
    
    # Initialize form state if switching prompts
    if st.session_state.get("current_prompt_name_view") != prompt_name:
        st.session_state.current_prompt_name_view = prompt_name
        st.session_state.original_version = prompt.version  # Store original version
        st.session_state.edit_version = prompt.version
        st.session_state.edit_comment = prompt.comment or ""
        st.session_state.edit_template = prompt.template
        st.session_state.edit_meta = json.dumps(prompt.variables_meta, indent=2) if prompt.variables_meta else "{}"
    
    with st.form("edit_prompt_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_version = st.text_input("Version (e.g. v2)", key="edit_version")
        with col2:
            comment = st.text_input("Comment", key="edit_comment")
            
        new_template = st.text_area("Template", height=300, key="edit_template")
        
        # Button to generate meta from template
        if st.form_submit_button("Generate Variables Meta"):
            try:
                meta_json_str = generate_variables_meta(st.session_state.edit_template)
                st.session_state.edit_meta = meta_json_str
                st.rerun()
            except Exception as e:
                st.error(f"Error generating meta: {e}")

        new_meta_str = st.text_area("Variables Meta (JSON)", height=150, key="edit_meta")
        
        if st.form_submit_button("Update Prompt", type="primary"):
            try:
                meta_json = json.loads(st.session_state.edit_meta)
                original_version = st.session_state.get("original_version", prompt.version)
                new_version = st.session_state.edit_version

                # Check if version changed
                if original_version != new_version:
                    # Create new version
                    service.create_new_version(
                        prompt_name,
                        st.session_state.edit_template,
                        meta_json,
                        new_version,
                        st.session_state.edit_comment
                    )
                    st.success(f"New version '{new_version}' created!")
                else:
                    # Update existing version
                    service.update_prompt(
                        prompt_name,
                        st.session_state.edit_template,
                        meta_json,
                        new_version,
                        st.session_state.edit_comment
                    )
                    st.success("Prompt updated!")

                # Clear state to force reload
                del st.session_state.current_prompt_name_view
                if "original_version" in st.session_state:
                    del st.session_state.original_version
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
