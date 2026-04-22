from functools import lru_cache

from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.path_conf import BASE_PATH

load_dotenv()


class Settings(BaseSettings):
    """Global Settings"""

    model_config = SettingsConfigDict(
        env_file=f"{BASE_PATH}/.env", env_file_encoding="utf-8", extra="ignore"
    )

    # print(model_config)
    # Env Config
    ENVIRONMENT: str = "dev"
    FASTAPI_ROOT_PATH: str = ""

    DATABASE_RETRY_INTERVAL: int = 1
    DATABASE_MAX_RETRIES: int = 3
    DATABASE_ECHO: bool = False

    # PostgreSQL
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "research"

    @computed_field
    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DATABASE: int = 0
    REDIS_TIMEOUT: int = 5
    RESEARCH_STATUS_TTL_SECONDS: int = 3600
    RESEARCH_CACHE_TTL_SECONDS: int = 86400
    RESEARCH_SQS_WAIT_TIME_SECONDS: int = 20
    RESEARCH_SQS_VISIBILITY_TIMEOUT_SECONDS: int = 120
    RESEARCH_MAX_QUEUE_ATTEMPTS: int = 3

    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    SQS_ENDPOINT_URL: str = "http://127.0.0.1:9324"
    SQS_QUEUE_URL: str = "http://127.0.0.1:9324/000000000000/research-jobs"
    SQS_DLQ_URL: str = "http://127.0.0.1:9324/000000000000/research-jobs-dlq"

    # OpenAI API
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    # LLM Model
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    GITHUB_TOKEN: str = ""
    GITHUB_API_URL: str = "https://api.github.com/graphql"
    RESEARCH_POLL_INTERVAL_SECONDS: int = 2
    RESEARCH_AI_TOKEN_BUDGET: int = 32000
    RESEARCH_GITHUB_TIMEOUT: int = 15
    RESEARCH_LLM_TIMEOUT: int = 30
    RESEARCH_MAX_TREE_ENTRIES: int = 100

    # Env Token
    # TOKEN_SECRET_KEY: str

    # FastAPI
    FASTAPI_API_V1_PATH: str = "/api/v1"
    FASTAPI_TITLE: str = "FastAPI"
    FASTAPI_VERSION: str = "0.0.1"
    FASTAPI_DESCRIPTION: str = ""
    FASTAPI_DOCS_URL: str | None = "/docs"
    FASTAPI_REDOCS_URL: str | None = "/redocs"
    FASTAPI_OPENAPI_URL: str | None = "/openapi"
    FASTAPI_STATIC_FILES: bool = False

    # LLM Model
    MODEL_NAME: str = "gpt-4o-mini"
    TEMPERATURE: float = 0
    LLM_TIMEOUT: int = 10
    LLM_MAX_RETRIES: int = 3
    LLM_POOL_CONNECTION: int = 10
    LLM_POOL_MAXSIZE: int = 10

    POOL_EXECUTOR_MAX_WORKERS: int = 10

    # Task Queue Config
    TASK_MAX_RETRIES: int = 3
    TASK_RETRY_DELAY: int = 1
    TASK_BATCH_SIZE: int = 16
    MAX_CONCURRENT_BATCHES: int = 3

    PROJECT_NAME: str = "PFA"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sentiment Dashboard for Product"
    LOG_DIR: str = "logs"

    # Token
    TOKEN_ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 1
    TOKEN_REFRESH_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7
    TOKEN_REDIS_PREFIX: str = "pfa:token"
    TOKEN_REFRESH_REDIS_PREFIX: str = "pfa:refresh_token"
    TOKEN_REQUEST_PATH_EXCLUDE: list[str] = [
        f"{FASTAPI_API_V1_PATH}/auth/login",
    ]

    # JWT
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_IN: int = 60 * 60 * 24 * 7  # 1 week

    # Default User
    DEFAULT_USER: str = "admin"
    DEFAULT_PASSWORD: str = "admin"

    # Cookies
    COOKIE_REFRESH_TOKEN_KEY: str = ""
    COOKIE_REFRESH_TOKEN_EXPIRE_SECONDS: int = TOKEN_REFRESH_EXPIRE_SECONDS

    # Log
    LOG_ROOT_LEVEL: str = "NOTSET"
    LOG_STD_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | "
        "<cyan> {correlation_id} </> | <lvl>{message}</>"
    )
    LOG_LOGURU_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | "
        "<cyan> {correlation_id} </> | <lvl>{message}</>"
    )
    LOG_CID_DEFAULT_VALUE: str = "-"
    LOG_CID_UUID_LENGTH: int = 32
    LOG_STDOUT_LEVEL: str = "INFO"
    LOG_STDERR_LEVEL: str = "ERROR"
    LOG_STDOUT_FILENAME: str = "pfa_access.log"
    LOG_STDERR_FILENAME: str = "pfa_error.log"

    # Additional logging settings used by common/log.py
    # If True, log messages will be formatted as JSON
    LOG_JSON: bool = False
    # Whether to enable console logging (stdout/stderr)
    LOG_ENABLE_CONSOLE: bool = True
    # Disable file-based logging when True
    LOG_FILE_DISABLE: bool = False
    # Log level used specifically for SQLAlchemy noisy loggers
    SQLALCHEMY_LOG_LEVEL: str = "WARNING"
    # List of noisy third-party loggers to quiet down (can be comma separated in env)
    NOISY_LOGGERS: list[str] = ["sqlalchemy.engine"]

    # Middleware
    MIDDLEWARE_CORS: bool = True
    MIDDLEWARE_ACCESS: bool = False

    # Trace ID
    TRACE_ID_REQUEST_HEADER_KEY: str = "X-Request-ID"

    # CORS
    CORS_ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "https://test.propertyguru.vn",
    ]
    CORS_EXPOSE_HEADERS: list[str] = [
        TRACE_ID_REQUEST_HEADER_KEY,
    ]

    # DateTime
    DATETIME_TIMEZONE: str = "UTC"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"


@lru_cache
def get_settings() -> Settings:
    """Get settings"""
    return Settings()


# Global settings
settings = get_settings()
