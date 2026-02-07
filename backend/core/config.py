try:
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./backend/data.db"
    OPENAI_API_KEY: str | None = None
    GROK_API_KEY: str | None = None
    ATS_THRESHOLD: int = 10
    HELP_PENALTY_PER_HINT: int = 5
    ATS_MIN_MATCHES: int = 3
    ATS_MIN_SCORE_FOR_PASS: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
