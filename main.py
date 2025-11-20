import streamlit as st
from app.ui.common import init_page

init_page("Home")

st.markdown("""
## Welcome to Prompt One

Manage your LLM prompts with version control and testing capabilities.

### Features
- **Prompt Management**: Create, update, and version control your prompts.
- **Preview**: Test your prompts with real-time variable interpolation.
- **Playground**: Run your prompts against LLMs (LangChain integrated).

Navigate using the sidebar to start.
""")
