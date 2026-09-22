import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root if it exists
project_root = Path(__file__).resolve().parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

class Settings:
    MCP_URL: str = os.getenv("SELLERSPRITE_MCP_URL", "https://mcp.sellersprite.com/mcp").rstrip("?").rstrip("/")
    MCP_SECRET: str = os.getenv("SELLERSPRITE_MCP_SECRET", "").strip()
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # SQLite Database for V2 business store & snapshots
    DB_PATH: str = os.path.join(os.path.dirname(__file__), "v2_store.db")
    CACHE_DB_PATH: str = os.path.join(os.path.dirname(__file__), "cache.db")
    CACHE_EXPIRE_HOURS: int = 24

    def validate(self):
        if not self.MCP_SECRET:
            raise RuntimeError(
                "CRITICAL: SELLERSPRITE_MCP_SECRET is missing!\n"
                "Please configure SELLERSPRITE_MCP_SECRET in .env or system environment variables.\n"
                "See .env.example for template."
            )

settings = Settings()
# Validate upon module load so failures are immediate and clear
settings.validate()
