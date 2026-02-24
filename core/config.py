from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    DISCORD_WEBHOOK_URL: str = ""
    DEDUP_INTERVAL_SECONDS: int = 300 # 5 minutes default

    class Config:
        env_file = ".env"

settings = Settings()
