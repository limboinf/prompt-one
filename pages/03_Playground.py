import json
from datetime import datetime
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
        
        prompt = None
        if selected_name:
            prompt = prompt_service.get_prompt_details(selected_name)
            if prompt:
                st.caption(f"Version: {prompt.version}")

        st.divider()
        st.subheader("Model Settings")
        model_name = st.text_input("Model Name", value=settings.DEFAULT_MODEL_NAME)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    with col_main:
        st.subheader("Execution")
        
        if selected_name and prompt:
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
                variables_meta = prompt.variables_meta or {}
                input_values = {}
                
                if not variables_meta:
                    st.info("No variables defined.")
                
                # Use form for variables so it doesn't re-run on every keystroke
                with st.form("playground_vars"):
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
                                input_values[name] = default_val 
                        else:
                            input_values[name] = st.text_input(label, value=str(default) if default else "", help=desc)
                    
                    submit_vars = st.form_submit_button("Update Variables")

            # Prepare prompt
            if submit_vars or True: # Always try to render current state
                try:
                    rendered_prompt = render_service.render(selected_name, input_values)
                    
                    with st.expander("System Prompt", expanded=False):
                        st.info(rendered_prompt)
                    
                    st.divider()
                    
                    # Display chat history
                    for msg in st.session_state.chat_history:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                            if "timestamp" in msg:
                                st.caption(f"🕒 {msg['timestamp']}")

                    # Chat Input
                    if user_input := st.chat_input("Type your message here..."):
                        # Add user message
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.chat_history.append({
                            "role": "user", 
                            "content": user_input,
                            "timestamp": current_time
                        })
                        with st.chat_message("user"):
                            st.markdown(user_input)
                            st.caption(f"🕒 {current_time}")

                        # Prepare messages for LLM
                        messages = [SystemMessage(content=rendered_prompt)]
                        
                        for msg in st.session_state.chat_history:
                            # Skip the last one we just added to avoid duplication if we re-read history? 
                            # No, we just added it to history, so we should include it.
                            # But wait, we are iterating over session_state.chat_history to build messages.
                            # The user input is already in chat_history.
                            if msg["role"] == "user":
                                messages.append(HumanMessage(content=msg["content"]))
                            else:
                                messages.append(AIMessage(content=msg["content"]))

                        # Call LLM
                        with st.chat_message("assistant"):
                            try:
                                client = LangChainClient(model_name=model_name, temperature=temperature)
                                
                                # Debug: Show messages sent to LLM
                                with st.expander("Debug: Context sent to LLM"):
                                    st.json([{"type": m.type, "content": m.content} for m in messages])
                                
                                stream = client.stream(messages)
                                response = st.write_stream(stream)
                                
                                response_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                st.caption(f"🕒 {response_time}")
                                
                                st.session_state.chat_history.append({
                                    "role": "assistant", 
                                    "content": response,
                                    "timestamp": response_time
                                })
                            except Exception as e:
                                st.error(f"Error calling LLM: {e}")
                            
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("Please select a prompt from the configuration sidebar.")

finally:
    prompt_service.db.close()
    render_service.db.close()
