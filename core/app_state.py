"""
Модуль для хранения состояния приложения.

Этот модуль содержит класс AppState, который отвечает за хранение и обновление
данных о биржах и криптовалютах.
"""
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional

from core.models import AssetPrice, ExchangeData

logger = logging.getLogger(__name__)


class AppState:
    """
    Состояние приложения с данными от всех бирж.
    Реализует паттерн Singleton.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            # Инициализация атрибутов будет осуществляться в __init__
        return cls._instance
    
    def __init__(self):
        # Инициализируем атрибут _exchanges только если он не существует
        if not hasattr(self, '_exchanges'):
            self._exchanges: Dict[str, ExchangeData] = {}
            # Убираем инициализацию демо-данными
            # self._initialize_demo_data()
    
    # --- Комментируем или удаляем методы демо-данных ---
    # def _initialize_demo_data(self):
    #     """Инициализация демонстрационных данных для бирж."""
    #     # Базовые значения цен для криптовалют
    #     base_values = {
    #         "BTC": 59000.0,   # Примерная цена BTC в USD
    #         "ETH": 3300.0,    # Примерная цена ETH в USD
    #         "USDT": 0.0      # Примерная цена USDT в RUB
    #     }
    #     
    #     # Добавляем биржи
    #     for exchange_name in ["binance", "bybit", "commex", "garantex"]:
    #         exchange = self.add_exchange(exchange_name)
    #         
    #         # Заполняем биржу данными о криптовалютах
    #         for crypto, base_value in base_values.items():
    #             # Добавляем случайное отклонение ±2% для разных бирж
    #             deviation = random.uniform(-0.02, 0.02)
    #             spot_price = base_value * (1 + deviation)
    #             
    #             # Для USDT используем цену напрямую, для остальных умножаем на курс USDT
    #             if crypto == "USDT":
    #                 rub_price = spot_price
    #                 usd_price = 1.0
    #             else:
    #                 rub_price = spot_price * base_values["USDT"] * (1 + deviation)
    #                 usd_price = spot_price
    #             
    #             exchange.update_asset(
    #                 symbol=crypto, 
    #                 price=rub_price,
    #                 usd_price=usd_price,
    #                 spot_price=spot_price
    #             )
    # 
    # def update_demo_data(self):
    #     """Обновление демонстрационных данных с случайными колебаниями."""
    #     for exchange_name, exchange in self._exchanges.items():
    #         for symbol, asset in exchange.assets.items():
    #             # Добавляем случайное колебание ±0.7%
    #             change = random.uniform(-0.007, 0.007)
    #             
    #             # Обновляем спот-цену
    #             spot_price = asset.spot_price * (1 + change) if asset.spot_price else 0.0
    #             
    #             # Обновляем цену в рублях
    #             if symbol == "USDT":
    #                 rub_price = spot_price
    #                 usd_price = 1.0
    #             else:
    #                 # Получаем текущий курс USDT с небольшим случайным изменением
    #                 usdt_asset = exchange.get_asset("USDT")
    #                 usdt_price = usdt_asset.base_price
    #                 
    #                 # Добавляем небольшое случайное изменение для курса рубля
    #                 rub_change = random.uniform(-0.003, 0.003)
    #                 rub_price = spot_price * usdt_price * (1 + rub_change)
    #                 usd_price = spot_price
    #             
    #             # Обновляем данные
    #             exchange.update_asset(
    #                 symbol=symbol,
    #                 price=rub_price,
    #                 usd_price=usd_price,
    #                 spot_price=spot_price
    #             )
    # --- Конец удаления демо-методов ---
    
    def get_exchange(self, name: str) -> Optional[ExchangeData]:
        """
        Получить данные по определенной бирже.
        
        Args:
            name: Название биржи
            
        Returns:
            Данные по бирже или None, если биржа не найдена
        """
        return self._exchanges.get(name.lower())
    
    def add_exchange(self, name: str, enabled: bool = True) -> ExchangeData:
        """
        Добавить новую биржу в состояние приложения.
        
        Args:
            name: Название биржи
            enabled: Активна ли биржа
            
        Returns:
            Данные новой биржи
        """
        exchange = ExchangeData(name=name.lower(), enabled=enabled)
        self._exchanges[name.lower()] = exchange
        return exchange
    
    def update_asset(self, exchange_name: str, symbol: str, price: float, 
                    usd_price: Optional[float] = None, spot_price: Optional[float] = None) -> None:
        """
        Обновить данные по активу на определенной бирже.
        
        Args:
            exchange_name: Название биржи
            symbol: Символ актива
            price: Цена актива
            usd_price: Цена в USD (опционально)
            spot_price: Спот цена (опционально)
        """
        exchange = self.get_exchange(exchange_name)
        if exchange is None:
            exchange = self.add_exchange(exchange_name)
        
        exchange.update_asset(symbol, price, usd_price, spot_price)
    
    def get_exchanges(self) -> List[ExchangeData]:
        """
        Получить список всех бирж.
        
        Returns:
            Список бирж
        """
        return list(self._exchanges.values())
    
    def get_asset_from_all_exchanges(self, symbol: str) -> Dict[str, Optional[AssetPrice]]:
        """
        Получить данные по активу со всех бирж.
        
        Args:
            symbol: Символ актива
            
        Returns:
            Словарь с данными по активу для каждой биржи
        """
        result = {}
        for name, exchange in self._exchanges.items():
            result[name] = exchange.get_asset(symbol)
        return result


# Singleton instance
app_state = AppState() 