from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Research Assistant"
    environment: str = "development"
    api_base_url: str = "http://localhost:8000"

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@db:5432/ai_research",
        alias="DATABASE_URL",
    )
    jwt_secret: str = Field(default="dev_secret_change_me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
