"""
Коннектор для биржи Bybit.

Модуль реализует взаимодействие с API биржи Bybit и обработку данных.
"""
import json
import asyncio
import logging
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any, Union, cast

import aiohttp

from core.models import TickerData, AssetPrice
from core.exceptions import APIError, WebSocketError
from core.utils import retry_async
from exchanges.base.connector import BaseConnector

logger = logging.getLogger(__name__)


class BybitConnector(BaseConnector):
    """
    Коннектор для биржи Bybit.
    
    Реализует методы для получения данных с биржи Bybit.
    """
    
    def __init__(self, exchange_name: str, config: Dict[str, Any]):
        """
        Инициализация коннектора.
        
        Args:
            exchange_name: Имя биржи
            config: Конфигурация биржи
        """
        super().__init__(exchange_name, config)
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.usdt_price = 0.0
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        
        if not self.api_key or not self.api_secret:
            logger.warning(f"{self.exchange_name}: API key или API secret не найдены в конфигурации. Получение реального курса USDT/RUB через P2P будет невозможно.")
    
    async def connect(self) -> bool:
        """
        Установка соединения с биржей.
        
        Returns:
            True, если соединение успешно установлено, иначе False
        """
        logger.info(f"Connecting to {self.exchange_name}...")
        try:
            
            self.session = aiohttp.ClientSession()
            
            
            await self._init_usdt_price()
            
            logger.info(f"Connected to {self.exchange_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_name}: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Закрытие соединения с биржей.
        
        Returns:
            True, если соединение успешно закрыто, иначе False
        """
        logger.info(f"Disconnecting from {self.exchange_name}...")
        try:
            
            if self.session:
                await self.session.close()
                self.session = None
            
            
            if self.ws:
                await self.ws.close()
                self.ws = None
            
            logger.info(f"Disconnected from {self.exchange_name}")
            return True
        except Exception as e:
            logger.error(f"Error during disconnection from {self.exchange_name}: {e}")
            return False
    
    async def _init_usdt_price(self) -> None:
        """Инициализация цены USDT в рублях."""
        try:
            
            if self.api_key and self.api_secret:
                price = await self._fetch_usdt_price_p2p("RUB")
                if price is not None:
                    self.usdt_price = price
                    logger.info(f"Initial USDT price from P2P: {self.usdt_price}")
                    return
            
            logger.warning(f"Using default USDT price: {self.usdt_price}")
        except Exception as e:
            logger.error(f"Error during initial USDT price fetch: {e}. Using default: {self.usdt_price}")
    
    async def _fetch_usdt_price_p2p(self, currency_id: str = "RUB", side: str = "1", page: str = "2") -> Optional[float]:
        """
        Получение курса USDT к указанной валюте через P2P API.
        
        Args:
            currency_id: ID фиатной валюты (например, "RUB").
            side: "0" для покупки USDT, "1" для продажи USDT.

        Returns:
            Курс USDT или None в случае ошибки.
        """
        if not self.api_key or not self.api_secret:
            logger.error(f"Bybit P2P: API key/secret не установлены для {self.exchange_name}.")
            return None

        endpoint = "/v5/p2p/item/online"
        url = f"{self.base_url}{endpoint}"
        
        timestamp = str(int(time.time() * 1000))
        recv_window = "20000"
        payload = {
            "tokenId": "USDT",
            "currencyId": currency_id,
            "page": page,
            "side": side,
            "payment": ["75"]
        }
        payload_json = json.dumps(payload)

        
        param_str = timestamp + self.api_key + recv_window + payload_json
        signature = hmac.new(
            bytes(self.api_secret, 'utf-8'),
            bytes(param_str, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        headers = {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'X-BAPI-SIGN': signature,
            'Content-Type': 'application/json'
        }

        try:
            if self.session is None:
                logger.error("HTTP session is not initialized for P2P request")
                return None

            logger.debug(f"Sending P2P request to {url} with payload: {payload_json}")
            async with self.session.post(url, headers=headers, data=payload_json) as response:
                if response.status != 200:
                    text = await response.text()
                    raise APIError(
                        f"Error fetching P2P USDT price for {currency_id}",
                        self.exchange_name,
                        endpoint,
                        response.status,
                        text
                    )
                
                data = await response.json()
                ret_code = data.get("ret_code")
                if ret_code is not None and ret_code != 0:
                    raise APIError(
                        f"P2P API returned error: {data.get('ret_msg')}",
                        self.exchange_name,
                        endpoint,
                        response.status,
                        json.dumps(data)
                    )

                result = data.get("result", {})
                items = result.get("items", []) if result else []
                if not items:
                    logger.warning(f"Bybit P2P: No ads found for USDT/{currency_id}, side={side}.")
                    return None

                
                first_ad_price_str = items[0].get("price")
                if first_ad_price_str:
                    try:
                        price = float(first_ad_price_str)
                        logger.debug(f"Fetched P2P USDT/{currency_id} price: {price}")
                        return price
                    except ValueError:
                        logger.error(f"Bybit P2P: Could not convert price '{first_ad_price_str}' to float.")
                        return None
                else:
                    logger.warning("Bybit P2P: Price not found in the first ad.")
                    return None

        except APIError as e:
            logger.error(f"Bybit P2P API error: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error fetching P2P USDT price for {currency_id}: {e}")
            return None
    
    async def fetch_ticker_data(self, symbol: str) -> Optional[TickerData]:
        """
        Получение данных тикера для указанного символа.
        
        Args:
            symbol: Символ торговой пары
            
        Returns:
            Данные тикера или None в случае ошибки
        """
        endpoint = "/v5/market/tickers"
        params = {
            "category": "spot",
            "symbol": symbol
        }
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if self.session is None:
                logger.error("HTTP session is not initialized")
                return None
                
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    raise APIError(
                        f"Error fetching ticker for {symbol}",
                        self.exchange_name,
                        endpoint,
                        response.status,
                        text
                    )
                
                data = await response.json()
                
                
                ret_code = data.get("retCode")
                if ret_code is not None and ret_code != 0:
                    raise APIError(
                        f"API returned error: {data.get('retMsg')}",
                        self.exchange_name,
                        endpoint,
                        response.status,
                        json.dumps(data)
                    )
                
                
                result = data.get("result", {})
                tickers = result.get("list", []) if result else []
                if not tickers:
                    logger.warning(f"No ticker data for {symbol}")
                    return None
                
                ticker = tickers[0]
                
                
                return TickerData(
                    symbol=symbol,
                    last_price=float(ticker.get("lastPrice", 0)),
                    volume_24h=float(ticker.get("volume24h", 0)),
                    price_change_24h=float(ticker.get("price24hPcnt", 0)) * 100,
                    high_24h=float(ticker.get("highPrice24h", 0)),
                    low_24h=float(ticker.get("lowPrice24h", 0))
                )
        except APIError as e:
            logger.error(f"API error: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error fetching ticker data for {symbol}: {e}")
            return None
    
    async def subscribe_to_tickers(self, symbols: List[str]) -> bool:
        """
        Подписка на обновления тикеров для указанных символов.
        
        Args:
            symbols: Список символов для подписки
            
        Returns:
            True, если подписка успешно оформлена, иначе False
        """
        logger.info(f"Subscribing to tickers: {symbols}")
        
        
        return True
    
    async def process_updates(self) -> None:
        """
        Обработка обновлений данных от биржи.
        
        Этот метод запускает периодическое обновление данных.
        """
        logger.info(f"Starting processing updates for {self.exchange_name}")
        
        try:
            
            await asyncio.gather(
                self._update_usdt_price_task(),
                self._update_ticker_data_task()
            )
        except asyncio.CancelledError:
            logger.info(f"Update tasks for {self.exchange_name} cancelled")
        except Exception as e:
            logger.exception(f"Error in process_updates for {self.exchange_name}: {e}")
    
    async def _update_usdt_price_task(self) -> None:
        """Задача для периодического обновления курса USDT."""
        if not self.api_key or not self.api_secret:
            logger.warning("USDT price update task skipped: API key/secret not configured.")
            return
            
        while not self.stop_event.is_set():
            try:
                price = await self._fetch_usdt_price_p2p("RUB")
                if price is not None:
                    self.usdt_price = price
                    
                    
                    self.update_app_state("USDT", self.usdt_price, spot_price=self.usdt_price)
                    logger.debug(f"Updated USDT price from P2P: {self.usdt_price}")
                else:
                    logger.warning("Failed to fetch P2P USDT/RUB price in update task.")
            except Exception as e:
                logger.error(f"Error updating USDT price from P2P: {e}")
            
            await asyncio.sleep(10)
    
    async def _update_ticker_data_task(self) -> None:
        """Задача для периодического обновления данных тикеров."""
        update_interval = 5
        logger.info(f"Starting ticker update task for {self.exchange_name}. Interval: {update_interval}s")
        while not self.stop_event.is_set():
            start_time = time.time()
            fetch_tasks = []
            symbols_to_fetch = list(self.trading_pairs)
            logger.debug(f"Fetching tickers for symbols: {symbols_to_fetch}")

            for symbol in symbols_to_fetch:
                
                fetch_tasks.append(self.fetch_ticker_data(symbol))
            
            
            results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
            
            usdt_rub_rate = self.usdt_price
            if usdt_rub_rate <= 0:
                logger.warning("Invalid USDT/RUB rate, skipping RUB price calculation.")
                usdt_rub_rate = 0

            for symbol, ticker_data in zip(symbols_to_fetch, results):
                if isinstance(ticker_data, Exception):
                    logger.error(f"Error fetching ticker for {symbol}: {ticker_data}")
                    continue
                
                if not ticker_data:
                    
                    continue
                
                base_asset = symbol.replace("USDT", "")
                spot_price_usdt = ticker_data.last_price if isinstance(ticker_data, TickerData) else 0.0
                rub_price = 0.0
                if usdt_rub_rate > 0:
                   rub_price = spot_price_usdt * usdt_rub_rate
                
                
                
                self.update_app_state(
                    base_asset,
                    rub_price, 
                    spot_price=spot_price_usdt
                    
                )
                logger.debug(f"Updated AppState for {self.exchange_name}-{base_asset}: RUB={rub_price:.2f}, SPOT_USDT={spot_price_usdt}")

            
            elapsed = time.time() - start_time
            sleep_duration = max(0, update_interval - elapsed)
            logger.debug(f"Ticker update cycle finished in {elapsed:.2f}s. Sleeping for {sleep_duration:.2f}s.")
            await asyncio.sleep(sleep_duration)
        logger.info(f"Ticker update task for {self.exchange_name} stopped.")
    
    def get_usdt_price(self) -> float:
        """
        Получение текущего курса USDT.
        
        Returns:
            Текущий курс USDT в рублях
        """
        return self.usdt_price 