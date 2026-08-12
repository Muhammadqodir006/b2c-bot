from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: int
    db_name: str

    client_bot_token: str
    master_bot_token: str
    support_bot_token: str
    admin_ids: str

    class Config:
        env_file = ".env"

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()