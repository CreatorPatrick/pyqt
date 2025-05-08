"""
Модуль конфигурации приложения.

Этот модуль содержит настройки приложения, которые могут быть переопределены
с помощью переменных окружения или файла .env
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env, если он существует
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
# Создаем директорию для данных, если она не существует
DATA_DIR.mkdir(exist_ok=True)

# Настройки интерфейса
UI_SETTINGS = {
    "theme": os.getenv("UI_THEME", "dark_cyan.xml"),
    "font_family": os.getenv("UI_FONT_FAMILY", "Roboto"),
    "font_size": os.getenv("UI_FONT_SIZE", "12px"),
    "density_scale": os.getenv("UI_DENSITY_SCALE", "0"),
}

# Настройки приложения
APP_SETTINGS = {
    "organization": os.getenv("APP_ORGANIZATION", "rateOrganization"),
    "application": os.getenv("APP_NAME", "rateApp"),
    "update_interval": int(os.getenv("UPDATE_INTERVAL_MS", "1000")),
}

# Настройки API
API_SETTINGS = {
    "server_host": os.getenv("API_SERVER_HOST", "127.0.0.1"),
    "server_port": int(os.getenv("API_SERVER_PORT", "5000")),
    "debug_mode": os.getenv("API_DEBUG_MODE", "False").lower() == "true",
}

# Биржи
EXCHANGES = {
    "bybit": {
        "enabled": os.getenv("BYBIT_ENABLED", "True").lower() == "true",
        "base_url": os.getenv("BYBIT_API_URL", "https://api.bybit.com"),
        "ws_url": os.getenv("BYBIT_WS_URL", "wss://stream.bybit.com/v5/public"),
        "assets": ["USDT", "BTC", "ETH"],
    },
    "binance": {
        "enabled": os.getenv("BINANCE_ENABLED", "False").lower() == "true",
        "base_url": os.getenv("BINANCE_API_URL", "https://api.binance.com"),
        "ws_url": os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws"),
        "assets": ["USDT", "BTC", "ETH"],
    },
    "garantex": {
        "enabled": os.getenv("GARANTEX_ENABLED", "False").lower() == "true",
        "base_url": os.getenv("GARANTEX_API_URL", "https://garantex.io/api/v2"),
        "assets": ["USDT", "BTC", "ETH"],
    },
    "commex": {
        "enabled": os.getenv("COMMEX_ENABLED", "False").lower() == "true",
        "base_url": os.getenv("COMMEX_API_URL", "https://api.commex.com"),
        "ws_url": os.getenv("COMMEX_WS_URL", "wss://stream.commex.com/stream"),
        "assets": ["USDT", "BTC", "ETH"],
    },
}

# Параметры логирования
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": os.getenv("FILE_LOG_LEVEL", "INFO"),
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "app.log"),
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": True,
        },
    },
}


def get_exchange_config(exchange_name: str) -> Optional[Dict[str, Any]]:
    """
    Получить конфигурацию для конкретной биржи.
    
    Args:
        exchange_name: Имя биржи
        
    Returns:
        Конфигурация биржи или None, если биржа не найдена
    """
    return EXCHANGES.get(exchange_name.lower()) 