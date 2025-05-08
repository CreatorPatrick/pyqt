"""
Конфигурация приложения.

Этот модуль содержит константы и настройки для всего приложения.
"""
import os
from typing import Dict, Any, List


APP_SETTINGS: Dict[str, Any] = {
    "application": "UmbrellaPro",
    "organization": "UmbrellaSoft",
    "version": "1.0.0",
    "update_interval": 3000,  
    "data_dir": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"),
    "log_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.log"),
}


UI_SETTINGS: Dict[str, Any] = {
    "theme": "light",  
    "font_family": "Arial",
    "font_size": 12,
    "density_scale": 1.0,
    "default_window_width": 1200,
    "default_window_height": 800,
}


EXCHANGE_SETTINGS: Dict[str, Dict[str, Any]] = {
    "binance": {
        "enabled": True,
        "api_url": "https://api.binance.com",
        "ws_url": "wss://stream.binance.com:9443/ws",
        "assets": ["BTC", "ETH", "USDT"]
    },
    "bybit": {
        "enabled": True,
        "api_url": "https://api.bybit.com",
        "ws_url": "wss://stream.bybit.com/realtime",
        "assets": ["BTC", "ETH", "USDT"]
    },
    "commex": {
        "enabled": True,
        "api_url": "https://api.commex.com",
        "ws_url": "wss://stream.commex.com/ws",
        "assets": ["BTC", "ETH", "USDT"]
    },
    "garantex": {
        "enabled": True,
        "api_url": "https://garantex.io/api/v2",
        "ws_url": "wss://garantex.io/ws",
        "assets": ["BTC", "ETH", "USDT"]
    }
}


CRYPTO_SETTINGS: Dict[str, Dict[str, Any]] = {
    "btc": {
        "commission": 0.5,
        "trade_fee": 0.2,
        "spreads": [0.5, 1.0, 1.5]
    },
    "eth": {
        "commission": 0.6,
        "trade_fee": 0.2,
        "spreads": [0.6, 1.2, 1.8]
    },
    "usdt": {
        "commission": 0.3,
        "trade_fee": 0.1,
        "spreads": [0.3, 0.6, 0.9]
    }
} 