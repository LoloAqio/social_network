from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Third Laba Social Network"
    app_debug: bool = True
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    postgres_user: str = "postgres"
    postgres_password: str
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_db: str
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
