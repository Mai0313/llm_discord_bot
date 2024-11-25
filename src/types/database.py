from typing import Optional

from pydantic import Field, BaseModel, AliasChoices, computed_field
from pydantic_settings import BaseSettings


class PostgreSQLConfig(BaseSettings):
    postgres_host: str = Field(
        ...,
        validation_alias=AliasChoices("POSTGRES_HOST"),
        title="PostgreSQL Host",
        description="The hostname or IP address of the PostgreSQL server.",
    )
    postgres_port: str = Field(
        ...,
        validation_alias=AliasChoices("POSTGRES_PORT"),
        title="PostgreSQL Port",
        description="The port number on which the PostgreSQL server is listening.",
    )
    postgres_db: str = Field(
        ...,
        validation_alias=AliasChoices("POSTGRES_DB"),
        title="PostgreSQL Database Name",
        description="The name of the PostgreSQL database to connect to.",
    )
    postgres_user: str = Field(
        ...,
        validation_alias=AliasChoices("POSTGRES_USER"),
        title="PostgreSQL User",
        description="The username used to authenticate with the PostgreSQL server.",
    )
    postgres_password: str = Field(
        ...,
        validation_alias=AliasChoices("POSTGRES_PASSWORD"),
        title="PostgreSQL Password",
        description="The password used to authenticate with the PostgreSQL server.",
    )

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class SQLiteConfig(BaseSettings):
    sqlite_file_path: str = Field(
        ...,
        validation_alias=AliasChoices("SQLITE_FILE_PATH"),
        title="SQLite File Path",
        description="The file path to the SQLite database file.",
    )
    sqlite_timeout: int = Field(
        default=30,
        validation_alias=AliasChoices("SQLITE_TIMEOUT"),
        title="SQLite Timeout",
        description="The timeout duration (in seconds) for SQLite operations. Defaults to 30 seconds.",
    )


class RedisConfig(BaseSettings):
    redis_host: str = Field(
        ...,
        validation_alias=AliasChoices("REDIS_HOST"),
        title="Redis Host",
        description="The hostname or IP address of the Redis server.",
    )
    redis_port: int = Field(
        default=6379,
        validation_alias=AliasChoices("REDIS_PORT"),
        title="Redis Port",
        description="The port number on which the Redis server is listening. Defaults to 6379.",
    )
    redis_db: int = Field(
        default=0,
        validation_alias=AliasChoices("REDIS_DB"),
        title="Redis Database Index",
        description="The database index to connect to on the Redis server. Defaults to 0.",
    )
    redis_password: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("REDIS_PASSWORD"),
        title="Redis Password",
        description="The password used to authenticate with the Redis server, if required.",
    )


class DatabaseConfig(BaseModel):
    postgres: PostgreSQLConfig = PostgreSQLConfig()
    sqlite: SQLiteConfig = SQLiteConfig()
    redis: RedisConfig = RedisConfig()
