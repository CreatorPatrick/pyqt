"""
Модели данных приложения.

Этот модуль содержит основные классы для работы с данными в приложении.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from datetime import datetime


@dataclass
class TickerData:
    """
    Данные тикера криптовалюты.
    """
    symbol: str
    last_price: float
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AssetPrice:
    """
    Цена актива с расчётом спредов.
    """
    symbol: str
    base_price: float
    spot_price: Optional[float] = None
    usd_price: Optional[float] = None
    spreads: Dict[str, float] = field(default_factory=dict)
    last_update: datetime = field(default_factory=datetime.now)

    def calculate_spread(self, spread_pct: float, commission: float = 0.0) -> float:
        """
        Расчет цены с учетом спреда и комиссии.
        
        Args:
            spread_pct: Процент спреда
            commission: Процент комиссии
            
        Returns:
            Цена с учетом спреда и комиссии
        """
        return self.base_price * (1 - (spread_pct + commission) / 100)


@dataclass
class ExchangeData:
    """
    Данные по бирже.
    """
    name: str
    assets: Dict[str, AssetPrice] = field(default_factory=dict)
    enabled: bool = True
    connected: bool = False
    last_update: datetime = field(default_factory=datetime.now)

    def update_asset(self, symbol: str, price: float, usd_price: Optional[float] = None, 
                    spot_price: Optional[float] = None) -> None:
        """
        Обновить данные по определенному активу.
        
        Args:
            symbol: Символ актива
            price: Цена актива
            usd_price: Цена в USD (опционально)
            spot_price: Спот цена (опционально)
        """
        if symbol not in self.assets:
            self.assets[symbol] = AssetPrice(symbol=symbol, base_price=price, 
                                           usd_price=usd_price, spot_price=spot_price)
        else:
            self.assets[symbol].base_price = price
            if usd_price is not None:
                self.assets[symbol].usd_price = usd_price
            if spot_price is not None:
                self.assets[symbol].spot_price = spot_price
            self.assets[symbol].last_update = datetime.now()
        
        self.last_update = datetime.now()
        
    def get_asset(self, symbol: str) -> Optional[AssetPrice]:
        """
        Получить данные по определенному активу.
        
        Args:
            symbol: Символ актива
            
        Returns:
            Данные по активу или None, если актив не найден
        """
        return self.assets.get(symbol)


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