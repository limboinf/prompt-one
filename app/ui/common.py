import streamlit as st
from app.db.session import SessionLocal
from app.services.prompt_service import PromptService
from app.services.template_engine import PromptRenderService

def get_db():
    return SessionLocal()

def get_prompt_service():
    db = get_db()
    return PromptService(db)

def get_render_service():
    db = get_db()
    return PromptRenderService(db)

def init_page(page_title: str):
    st.set_page_config(
        page_title=f"Prompt One - {page_title}",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(page_title)
