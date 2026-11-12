from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Обязательное значение: задается в backend/.env (см. .env.example)
    secret_key: str

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite:///./tickets.db"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Для локальной разработки по http кука не может быть Secure.
    # На проде (https) поставьте COOKIE_SECURE=true
    cookie_secure: bool = False

    # Демо-учетка администратора, создается при первом запуске
    admin_username: str = "admin"
    admin_password: str = "admin"


settings = Settings()
