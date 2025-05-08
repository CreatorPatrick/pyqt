"""
Коннектор для биржи Garantex.

Модуль реализует взаимодействие с API биржи Garantex и обработку данных.
"""
import json
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, cast

import aiohttp

from core.models import TickerData, AssetPrice
from core.exceptions import APIError, WebSocketError
from core.utils import retry_async
from exchanges.base.connector import BaseConnector
from exchanges.bybit.connector import BybitConnector

logger = logging.getLogger(__name__)


class GarantexConnector(BybitConnector):
    """
    Коннектор для биржи Garantex.
    
    Временная заглушка, использующая функциональность Bybit коннектора.
    """
    
    def __init__(self, exchange_name: str, config: Dict[str, Any]):
        """
        Инициализация коннектора.
        
        Args:
            exchange_name: Имя биржи
            config: Конфигурация биржи
        """
        super().__init__(exchange_name, config)
        logger.warning(f"Using Bybit connector as a fallback for {exchange_name}") 