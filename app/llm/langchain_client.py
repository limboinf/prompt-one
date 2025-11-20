from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LangChainClient:
    def __init__(self, model_name: str | None = None, temperature: float = 0.7):
        self.model_name = model_name or settings.DEFAULT_MODEL_NAME
        self.temperature = temperature
        self._init_llm()

    def _init_llm(self):
        # Ensure API Key is present (or handle gracefully)
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. LLM calls might fail.")
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            temperature=self.temperature
        )

    def invoke(self, input_data: str | list[BaseMessage]) -> str:
        try:
            if isinstance(input_data, str):
                messages = [HumanMessage(content=input_data)]
            else:
                messages = input_data
                
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM Invoke Error: {e}")
            raise e

    def stream(self, input_data: str | list[BaseMessage]):
        try:
            if isinstance(input_data, str):
                messages = [HumanMessage(content=input_data)]
            else:
                messages = input_data
                
            for chunk in self.llm.stream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM Stream Error: {e}")
            raise e
