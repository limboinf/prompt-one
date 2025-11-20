from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "prompt_manager"
    
    # LLM
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str | None = None
    DEFAULT_MODEL_NAME: str = "gpt-3.5-turbo"

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
