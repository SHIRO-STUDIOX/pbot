import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    SIMULATION_DELAY: float = float(os.getenv("SIMULATION_DELAY", "2.0"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Proxy Relay Configurations (for censored/restricted servers)
    USE_PROXY_RELAY: bool = os.getenv("USE_PROXY_RELAY", "false").lower() == "true"
    LOCAL_PROXY_URL: str = os.getenv("LOCAL_PROXY_URL", "http://localhost:8080")
    
    # Template paths
    DELIVERY_EN_PATH: Path = BASE_DIR / "data" / "delivery_en.txt"
    DELIVERY_RU_PATH: Path = BASE_DIR / "data" / "delivery_ru.txt"

    @classmethod
    def validate(cls):
        """
        Validates the configuration. Raises a ValueError if essential parameters are missing.
        """
        if not cls.BOT_TOKEN:
            raise ValueError(
                "BOT_TOKEN is not set in environment variables or .env file! "
                "Please configure your bot token using @BotFather."
            )
        
        # Check if template files exist
        if not cls.DELIVERY_EN_PATH.exists():
            raise FileNotFoundError(f"English delivery template not found at: {cls.DELIVERY_EN_PATH}")
        if not cls.DELIVERY_RU_PATH.exists():
            raise FileNotFoundError(f"Russian delivery template not found at: {cls.DELIVERY_RU_PATH}")
