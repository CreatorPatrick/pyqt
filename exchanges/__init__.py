"""
Модуль для работы с биржами криптовалют.

Содержит интерфейсы для взаимодействия с различными биржами.
"""
import logging
from typing import List, Dict, Any, Optional

from config import EXCHANGE_SETTINGS
from core.app_state import app_state
from core.models import AssetPrice

logger = logging.getLogger(__name__)


class BaseConnector:
    """
    Базовый класс для подключения к биржам.
    """
    
    def __init__(self, exchange_name: str):
        """
        Инициализация базового коннектора.
        
        Args:
            exchange_name: Название биржи
        """
        self.exchange_name = exchange_name.lower()
        self.settings = EXCHANGE_SETTINGS.get(self.exchange_name, {})
        self.is_connected = False
        
        exchange = app_state.get_exchange(self.exchange_name)
        if not exchange:
            app_state.add_exchange(self.exchange_name, enabled=self.settings.get("enabled", True))
    
    async def start(self) -> None:
        """Запуск коннектора."""
        logger.info(f"Starting connector for {self.exchange_name}")
        self.is_connected = True
    
    async def stop(self) -> None:
        """Остановка коннектора."""
        logger.info(f"Stopping connector for {self.exchange_name}")
        self.is_connected = False
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Получение информации о тикере.
        
        Args:
            symbol: Символ криптовалюты
            
        Returns:
            Словарь с информацией о тикере
        """
        exchange = app_state.get_exchange(self.exchange_name)
        asset: Optional[AssetPrice] = None
        if exchange:
            asset = exchange.get_asset(symbol)
        
        result = {
            "symbol": symbol,
            "price": asset.base_price if asset else 0.0,
            "volume": 0.0,
            "timestamp": 0
        }
        
        return result


class BinanceConnector(BaseConnector):
    """Коннектор для биржи Binance."""
    
    def __init__(self):
        super().__init__("binance")


class BybitConnector(BaseConnector):
    """Коннектор для биржи Bybit."""
    
    def __init__(self):
        super().__init__("bybit")


class CommEXConnector(BaseConnector):
    """Коннектор для биржи CommEX."""
    
    def __init__(self):
        super().__init__("commex")


class GarantexConnector(BaseConnector):
    """Коннектор для биржи Garantex."""
    
    def __init__(self):
        super().__init__("garantex")


def create_all_connectors() -> List[BaseConnector]:
    """
    Создание коннекторов для всех поддерживаемых бирж.
    
    Returns:
        Список коннекторов
    """
    connectors = [
        BinanceConnector(),
        BybitConnector(),
        CommEXConnector(),
        GarantexConnector()
    ]
    
    logger.info(f"Created {len(connectors)} exchange connectors")
    return connectors
