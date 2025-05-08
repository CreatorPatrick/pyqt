"""
Базовый класс для коннекторов к биржам.

Этот модуль содержит абстрактный класс BaseConnector, который должен быть
реализован всеми конкретными коннекторами к биржам.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set

from core.models import TickerData, AppState, AssetPrice

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Абстрактный базовый класс для всех коннекторов к биржам.
    
    Определяет общий интерфейс и реализует общую функциональность для всех коннекторов.
    """
    
    def __init__(self, exchange_name: str, config: Dict[str, Any]):
        """
        Инициализация коннектора.
        
        Args:
            exchange_name: Имя биржи
            config: Конфигурация биржи
        """
        self.exchange_name = exchange_name.lower()
        self.config = config
        self.base_url = config.get('base_url', '')
        self.ws_url = config.get('ws_url', '')
        self.assets = config.get('assets', [])
        self.trading_pairs = self._generate_trading_pairs()
        self.stop_event = asyncio.Event()
        self.is_connected = False
        self.app_state = AppState()
        
    def _generate_trading_pairs(self) -> List[str]:
        """
        Генерирует список торговых пар на основе доступных активов.
        
        По умолчанию создает пары в формате {ASSET}USDT.
        Подклассы могут переопределить этот метод для специфичных форматов пар.
        
        Returns:
            Список торговых пар
        """
        return [f"{asset}USDT" for asset in self.assets if asset != "USDT"]
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Устанавливает соединение с биржей.
        
        Returns:
            True, если соединение успешно установлено, иначе False
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Закрывает соединение с биржей.
        
        Returns:
            True, если соединение успешно закрыто, иначе False
        """
        pass
    
    @abstractmethod
    async def fetch_ticker_data(self, symbol: str) -> Optional[TickerData]:
        """
        Получает данные тикера для указанного символа.
        
        Args:
            symbol: Символ торговой пары
            
        Returns:
            Данные тикера или None в случае ошибки
        """
        pass
    
    @abstractmethod
    async def subscribe_to_tickers(self, symbols: List[str]) -> bool:
        """
        Подписка на обновления тикеров для указанных символов.
        
        Args:
            symbols: Список символов для подписки
            
        Returns:
            True, если подписка успешно оформлена, иначе False
        """
        pass
    
    @abstractmethod
    async def process_updates(self) -> None:
        """
        Обрабатывает обновления данных от WebSocket.
        
        Этот метод обычно содержит бесконечный цикл, который ожидает и обрабатывает
        данные от WebSocket соединения.
        """
        pass
    
    async def start(self) -> None:
        """
        Запускает работу коннектора.
        
        Устанавливает соединение и начинает обработку обновлений.
        """
        try:
            connected = await self.connect()
            if not connected:
                logger.error(f"Failed to connect to {self.exchange_name}")
                return
            
            self.is_connected = True
            exchange = self.app_state.get_exchange(self.exchange_name)
            if exchange is None:
                exchange = self.app_state.add_exchange(self.exchange_name)
            exchange.connected = True
            
            await self.subscribe_to_tickers(self.trading_pairs)
            await self.process_updates()
        except Exception as e:
            logger.exception(f"Error in {self.exchange_name} connector: {e}")
        finally:
            await self.disconnect()
            self.is_connected = False
            exchange = self.app_state.get_exchange(self.exchange_name)
            if exchange:
                exchange.connected = False
    
    async def stop(self) -> None:
        """
        Останавливает работу коннектора.
        
        Устанавливает флаг остановки и ждет завершения всех операций.
        """
        self.stop_event.set()
        await self.disconnect()
    
    def update_app_state(self, symbol: str, price: float, 
                         usd_price: Optional[float] = None, 
                         spot_price: Optional[float] = None) -> None:
        """
        Обновляет состояние приложения с новыми данными.
        
        Args:
            symbol: Символ актива
            price: Цена актива
            usd_price: Цена в USD (опционально)
            spot_price: Спот цена (опционально)
        """
        self.app_state.update_asset(
            self.exchange_name, 
            symbol, 
            price,
            usd_price, 
            spot_price
        )
    
    def format_symbol(self, symbol: str) -> str:
        """
        Форматирует символ торговой пары в стандартный формат.
        
        Args:
            symbol: Исходный символ
            
        Returns:
            Отформатированный символ
        """
        return symbol 