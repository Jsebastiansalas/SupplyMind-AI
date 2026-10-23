import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "SupplyMind AI"
    VERSION: str = "0.1.0"
    
    # Credenciales del reto
    RETO_KEY: str = os.getenv("RETO_KEY", "")
    PLATICA_BASE_URL: str = os.getenv("PLATICA_BASE_URL", "https://api.reto.pltk.mx/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "grok-4.7")
    
    # Directorios base
    ROOT_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = ROOT_DIR / os.getenv("DATA_DIR", "data/cases")
    LOGS_DIR: Path = ROOT_DIR / "logs"
    
    # Configuración de negocio y presupuesto
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    BUDGET_LIMIT_USD: float = float(os.getenv("BUDGET_LIMIT_USD", "5.00"))
    
    @property
    def is_live_api_ready(self) -> bool:
        """Indica si el agente cuenta con una llave válida de Platica/Grok para modo en vivo."""
        return bool(self.RETO_KEY and self.RETO_KEY.strip() and not self.RETO_KEY.startswith("pk_demo_placeholder"))

settings = Settings()
