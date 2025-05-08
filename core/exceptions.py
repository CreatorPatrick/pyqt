"""
Модуль с пользовательскими исключениями приложения.

Этот модуль содержит все пользовательские исключения, используемые в приложении.
"""
from typing import Optional, Any


class RateAppError(Exception):
    """Базовый класс для всех исключений приложения."""
    
    def __init__(self, message: str, *args: Any):
        self.message = message
        super().__init__(message, *args)


class ConfigError(RateAppError):
    """Ошибка конфигурации приложения."""
    pass


class NetworkError(RateAppError):
    """Ошибка сетевого взаимодействия."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, *args: Any):
        self.status_code = status_code
        super().__init__(message, *args)


class APIError(NetworkError):
    """Ошибка при обращении к API биржи."""
    
    def __init__(self, message: str, exchange: str, endpoint: str, 
                 status_code: Optional[int] = None, response: Optional[str] = None, 
                 *args: Any):
        self.exchange = exchange
        self.endpoint = endpoint
        self.response = response
        super().__init__(message, status_code, *args)


class WebSocketError(NetworkError):
    """Ошибка WebSocket соединения."""
    
    def __init__(self, message: str, exchange: str, *args: Any):
        self.exchange = exchange
        super().__init__(message, *args)


class AuthenticationError(APIError):
    """Ошибка аутентификации при обращении к API."""
    pass


class RateLimitError(APIError):
    """Превышение лимита запросов к API."""
    
    def __init__(self, message: str, exchange: str, endpoint: str, 
                 status_code: Optional[int] = None, response: Optional[str] = None, 
                 retry_after: Optional[int] = None, *args: Any):
        self.retry_after = retry_after
        super().__init__(message, exchange, endpoint, status_code, response, *args)


class DataError(RateAppError):
    """Ошибка при обработке данных."""
    pass


class ExchangeNotFoundError(RateAppError):
    """Указанная биржа не найдена."""
    
    def __init__(self, exchange: str, *args: Any):
        self.exchange = exchange
        message = f"Exchange not found: {exchange}"
        super().__init__(message, *args)


class AssetNotFoundError(RateAppError):
    """Указанный актив не найден."""
    
    def __init__(self, asset: str, exchange: Optional[str] = None, *args: Any):
        self.asset = asset
        self.exchange = exchange
        
        if exchange:
            message = f"Asset not found: {asset} on {exchange}"
        else:
            message = f"Asset not found: {asset}"
            
        super().__init__(message, *args)


class ValidationError(RateAppError):
    """Ошибка валидации данных."""
    pass 