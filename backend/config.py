import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MCP_URL: str = os.getenv("SELLERSPRITE_MCP_URL", "https://mcp.sellersprite.com/mcp")
    MCP_SECRET: str = os.getenv("SELLERSPRITE_MCP_SECRET", "0b43e279a6bf4e4387d2a6013eebbcc8")
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CACHE_DB_PATH: str = os.path.join(os.path.dirname(__file__), "cache.db")
    CACHE_EXPIRE_HOURS: int = 24

settings = Settings()
