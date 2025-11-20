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

    # Create table header
    header_cols = st.columns([2, 2, 3, 1, 2, 1, 1, 1])
    with header_cols[0]:
        st.markdown("**Name**")
    with header_cols[1]:
        st.markdown("**Display Name**")
    with header_cols[2]:
        st.markdown("**Description**")
    with header_cols[3]:
        st.markdown("**Version**")
    with header_cols[4]:
        st.markdown("**Updated At**")
    with header_cols[5]:
        st.markdown("**View**")
    with header_cols[6]:
        st.markdown("**Edit**")
    with header_cols[7]:
        st.markdown("**Delete**")

    st.divider()

    # Create table rows
    for p in prompts:
        row_cols = st.columns([2, 2, 3, 1, 2, 1, 1, 1])
        with row_cols[0]:
            st.text(p.name)
        with row_cols[1]:
            st.text(p.display_name or "-")
        with row_cols[2]:
            st.text(p.description[:50] + "..." if p.description and len(p.description) > 50 else p.description or "-")
        with row_cols[3]:
            st.text(p.version)
        with row_cols[4]:
            st.text(p.updated_at.strftime("%Y-%m-%d %H:%M") if p.updated_at else "-")
        with row_cols[5]:
            if st.button("👁️", key=f"view_{p.name}_{p.version}", help="View"):
                st.session_state.selected_prompt_name = p.name
                st.session_state.selected_prompt_version = p.version
                st.session_state.view_mode = True
                st.rerun()
        with row_cols[6]:
            if st.button("✏️", key=f"edit_{p.name}_{p.version}", help="Edit"):
                st.session_state.selected_prompt_name = p.name
                st.session_state.selected_prompt_version = p.version
                st.session_state.view_mode = False
                st.rerun()
        with row_cols[7]:
            if st.button("🗑️", key=f"delete_{p.name}_{p.version}", help="Delete"):
                try:
                    service.delete_prompt(p.name, p.version)
                    st.success(f"Deleted prompt '{p.name}' version '{p.version}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting prompt: {e}")

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

def prompt_details_view(service, prompt_name, prompt_version, view_mode=False):
    st.subheader(f"Prompt: {prompt_name} ({prompt_version})")
    if st.button("← Back to List"):
        del st.session_state.selected_prompt_name
        if 'selected_prompt_version' in st.session_state:
            del st.session_state.selected_prompt_version
        if 'view_mode' in st.session_state:
            del st.session_state.view_mode
        st.rerun()

    prompt = service.get_prompt_details(prompt_name, prompt_version)
    if not prompt:
        st.error("Prompt not found")
        return

    st.write(f"**Display Name:** {prompt.display_name}")
    st.write(f"**Description:** {prompt.description}")
    st.write(f"**Version:** {prompt.version}")
    st.write(f"**Last Updated:** {prompt.updated_at}")
    st.write(f"**Created By:** {prompt.created_by}")
    st.write(f"**Comment:** {prompt.comment or '-'}")

    # View mode - show template and metadata as read-only
    if view_mode:
        st.divider()
        st.write("### Template")
        st.code(prompt.template, language="jinja2")

        st.write("### Variables Meta")
        st.json(prompt.variables_meta)

        if st.button("Switch to Edit Mode"):
            st.session_state.view_mode = False
            st.rerun()
    else:
        # Edit mode
        st.divider()
        st.write("### Edit Prompt")

        # Initialize form state if switching prompts
        prompt_key = f"{prompt_name}_{prompt_version}"
        if st.session_state.get("current_prompt_key") != prompt_key:
            st.session_state.current_prompt_key = prompt_key
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
                    service.update_prompt(
                        prompt_name,
                        st.session_state.edit_template,
                        meta_json,
                        st.session_state.edit_version,
                        st.session_state.edit_comment
                    )
                    st.success("Prompt updated!")
                    # Clear state to force reload or just rerun
                    del st.session_state.current_prompt_key
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# Main Logic
service = get_prompt_service()
try:
    if 'selected_prompt_name' in st.session_state and 'selected_prompt_version' in st.session_state:
        view_mode = st.session_state.get('view_mode', False)
        prompt_details_view(
            service,
            st.session_state.selected_prompt_name,
            st.session_state.selected_prompt_version,
            view_mode
        )
    else:
        tab1, tab2 = st.tabs(["List Prompts", "Create Prompt"])
        with tab1:
            list_prompts_view(service)
        with tab2:
            create_prompt_view(service)
finally:
    service.db.close()
