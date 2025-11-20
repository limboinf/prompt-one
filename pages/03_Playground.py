import streamlit as st
from app.ui.common import init_page, get_prompt_service, get_render_service
from app.llm.langchain_client import LangChainClient
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.settings import settings

init_page("Playground")

prompt_service = get_prompt_service()
render_service = get_render_service()

try:
    col_conf, col_main = st.columns([1, 2])

    with col_conf:
        st.subheader("Configuration")
        # 1. Select Prompt
        prompts = prompt_service.list_prompts()
        prompt_names = [p.name for p in prompts]
        selected_name = st.selectbox("Select Prompt", [""] + prompt_names)
        
        selected_version = None
        version_obj = None
        
        if selected_name:
            versions = prompt_service.get_versions(selected_name)
            if versions:
                version_opts = [v.version for v in versions]
                latest_idx = 0
                for idx, v in enumerate(versions):
                    if v.is_latest:
                        latest_idx = idx
                        break
                selected_version = st.selectbox("Version", version_opts, index=latest_idx)
                version_obj = next(v for v in versions if v.version == selected_version)

        st.divider()
        st.subheader("Model Settings")
        model_name = st.text_input("Model Name", value=settings.DEFAULT_MODEL_NAME)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

    with col_main:
        st.subheader("Execution")
        
        if selected_name and version_obj:
            # Initialize chat history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            if "last_prompt" not in st.session_state:
                st.session_state.last_prompt = selected_name
            
            if st.session_state.last_prompt != selected_name:
                st.session_state.chat_history = []
                st.session_state.last_prompt = selected_name

            # Variable Inputs
            with st.expander("Variables", expanded=True):
                variables_meta = version_obj.variables_meta or []
                input_values = {}
                
                if not variables_meta:
                    st.info("No variables defined.")
                
                # Use form for variables so it doesn't re-run on every keystroke
                with st.form("playground_vars"):
                    for meta in variables_meta:
                        name = meta.get("name")
                        m_type = meta.get("type", "string")
                        default = meta.get("default", "")
                        desc = meta.get("description", "")
                        choices = meta.get("choices", [])
                        
                        label = f"{name}"
                        
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
                    
                    submit_vars = st.form_submit_button("Update Variables")

            # Prepare prompt
            if submit_vars or True: # Always try to render current state
                try:
                    rendered_prompt = render_service.render(selected_name, input_values, selected_version)
                    
                    st.markdown("### System Prompt")
                    st.info(rendered_prompt)
                    
                    st.divider()
                    
                    # Display chat history
                    for msg in st.session_state.chat_history:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])

                    # Chat Input
                    if user_input := st.chat_input("Type your message here..."):
                        # Add user message
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        with st.chat_message("user"):
                            st.markdown(user_input)

                        # Prepare messages for LLM
                        messages = [SystemMessage(content=rendered_prompt)]
                        
                        for msg in st.session_state.chat_history:
                            if msg["role"] == "user":
                                messages.append(HumanMessage(content=msg["content"]))
                            else:
                                messages.append(AIMessage(content=msg["content"]))

                        # Call LLM
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                try:
                                    client = LangChainClient(model_name=model_name, temperature=temperature)
                                    
                                    # Debug: Show messages sent to LLM
                                    with st.expander("Debug: Context sent to LLM"):
                                        st.json([{"type": m.type, "content": m.content} for m in messages])
                                    
                                    response = client.invoke(messages)
                                    st.markdown(response)
                                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                                except Exception as e:
                                    st.error(f"Error calling LLM: {e}")
                            
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("Please select a prompt from the configuration sidebar.")

finally:
    prompt_service.db.close()
    render_service.db.close()
