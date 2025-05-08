"""
Модуль с утилитарными функциями.

Содержит вспомогательные функции, используемые в разных частях приложения.
"""
import asyncio
import logging
import time
import functools
import concurrent.futures
import random
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast, Tuple
from datetime import datetime, timedelta
import locale

from core.exceptions import RateLimitError, NetworkError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def format_number(value: float, decimal_places: int = 2) -> str:
    """
    Форматирует число с разделителями групп разрядов и фиксированным 
    количеством десятичных знаков.
    
    Args:
        value: Значение для форматирования
        decimal_places: Количество десятичных знаков
        
    Returns:
        Отформатированная строка
    """
    logger.debug(f"format_number called with: value={value}, type={type(value)}, decimal_places={decimal_places}")
    try:
        if value is None:
            return "0"
        formatted_str = f"{value:,.{decimal_places}f}"
        logger.debug(f"format_number returning: {formatted_str}")
        return formatted_str
    except Exception as e:
        logger.error(f"Ошибка форматирования числа {value}: {e}")
        return str(value)


def format_currency(value: float, currency: str = "₽", decimal_places: int = 2) -> str:
    """
    Форматирует значение как валюту.
    
    Args:
        value: Значение для форматирования
        currency: Символ валюты (₽, $, €)
        decimal_places: Количество десятичных знаков (по умолчанию 2)
        
    Returns:
        Отформатированная строка с символом валюты
    """
    logger.debug(f"format_currency called with: value={value}, type={type(value)}, decimal_places={decimal_places}")
    try:
        if value is None:
            return f"0 {currency}"
            
        formatted = format_number(value, decimal_places)
        return f"{formatted} {currency}"
    except Exception as e:
        logger.error(f"Ошибка форматирования валюты {value}: {e}")
        return f"{value} {currency}"


def format_percentage(value: float, include_sign: bool = True) -> str:
    """
    Форматирует значение как процент.
    
    Args:
        value: Значение для форматирования (0.01 = 1%)
        include_sign: Включать ли знак + для положительных значений
        
    Returns:
        Отформатированная строка с символом %
    """
    try:
        if value is None:
            return "0%"
            
        percentage = value * 100
        
        sign = ""
        if include_sign and percentage > 0:
            sign = "+"
        
        if abs(percentage) < 0.1:
            decimal_places = 3
        elif abs(percentage) < 1:
            decimal_places = 2
        elif abs(percentage) < 10:
            decimal_places = 1
        else:
            decimal_places = 0
            
        return f"{sign}{percentage:.{decimal_places}f}%"
    except Exception as e:
        logger.error(f"Ошибка форматирования процента {value}: {e}")
        return f"{value}%"


def get_trend_color(trend: int) -> str:
    """
    Возвращает цвет для отображения тренда.
    
    Args:
        trend: Направление тренда (-1: падение, 0: нет изменений, 1: рост)
        
    Returns:
        Строка с кодом цвета в формате HEX или именем цвета CSS
    """
    if trend > 0:
        return "#4CAF50"
    elif trend < 0:
        return "#F44336"
    else:
        return "#FFC107"


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs: Any
) -> Any:
    """
    Выполняет асинхронную функцию с повторными попытками в случае исключения.
    
    Args:
        func: Асинхронная функция для выполнения
        *args: Позиционные аргументы для функции
        retries: Максимальное количество повторных попыток
        delay: Начальная задержка между попытками (в секундах)
        backoff_factor: Множитель для увеличения задержки с каждой попыткой
        exceptions: Кортеж исключений, при которых следует повторять попытки
        **kwargs: Именованные аргументы для функции
        
    Returns:
        Результат выполнения функции
        
    Raises:
        Последнее возникшее исключение, если все попытки неудачны
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(retries + 1):
        try:
            return await func(*args, **kwargs)
        except RateLimitError as e:
            if e.retry_after:
                current_delay = e.retry_after
            
            last_exception = e
            if attempt < retries:
                logger.warning(
                    f"Rate limit exceeded, retrying in {current_delay:.2f}s "
                    f"(attempt {attempt + 1}/{retries})"
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(f"Rate limit exceeded, max retries reached: {e}")
                raise
        except exceptions as e:
            last_exception = e
            if attempt < retries:
                logger.warning(
                    f"Error occurred, retrying in {current_delay:.2f}s "
                    f"(attempt {attempt + 1}/{retries}): {e}"
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(f"Error occurred, max retries reached: {e}")
                raise
    
    assert last_exception is not None
    raise last_exception


def timed_lru_cache(seconds: int, maxsize: int = 128):
    """
    Декоратор, реализующий LRU-кеш с ограничением по времени.
    
    Args:
        seconds: Время жизни элементов в кеше (в секундах)
        maxsize: Максимальный размер кеша
        
    Returns:
        Декорированная функция с кешированием результатов
    """
    def decorator(func):
        @functools.lru_cache(maxsize=maxsize)
        def cached_func(*args, **kwargs):
            return func(*args, **kwargs), time.time()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result, timestamp = cached_func(*args, **kwargs)
            if time.time() - timestamp > seconds:
                cached_func.cache_clear()
                result, _ = cached_func(*args, **kwargs)
            return result
        
        cache_info_func = getattr(cached_func, 'cache_info', None)
        cache_clear_func = getattr(cached_func, 'cache_clear', None)
        
        if cache_info_func is not None:
            wrapper.cache_info = cache_info_func
        if cache_clear_func is not None:
            wrapper.cache_clear = cache_clear_func
        
        return wrapper
    
    return decorator


def debounce(wait_time: float):
    """
    Декоратор для ограничения частоты вызовов функции (debounce).
    
    Args:
        wait_time: Минимальное время между вызовами (в секундах)
        
    Returns:
        Декорированная функция с ограничением частоты вызовов
    """
    def decorator(func):
        last_call_time = 0
        pending_task: Optional[asyncio.TimerHandle] = None
        lock = asyncio.Lock()

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_call_time, pending_task
            now = time.monotonic()
            remaining_time = wait_time - (now - last_call_time)

            async with lock:
                if pending_task:
                    pending_task.cancel()
                    pending_task = None

                if remaining_time <= 0:
                    last_call_time = now
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    pending_task = loop.call_later(
                        remaining_time, 
                        functools.partial(asyncio.ensure_future, _delayed_call(func, args, kwargs))
                    )

        async def _delayed_call(f, f_args, f_kwargs):
            nonlocal last_call_time, pending_task
            last_call_time = time.monotonic()
            await f(*f_args, **f_kwargs)
            async with lock:
                 pending_task = None
        
        return wrapper
    return decorator


def create_task_name(prefix: str) -> str:
    """
    Создает уникальное имя для задачи asyncio.
    
    Args:
        prefix: Префикс для имени задачи
        
    Returns:
        Уникальное имя задачи
    """
    return f"{prefix}-{time.monotonic_ns()}-{random.randint(1000, 9999)}"


class AsyncTaskManager:
    """
    Класс для управления асинхронными задачами.
    Позволяет создавать, отменять и отслеживать задачи.
    """
    def __init__(self) -> None:
        self._tasks: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, Any] = {}

    def create_task(self, coro: Any, name: Optional[str] = None) -> str:
        """
        Создает и запускает асинхронную задачу.
        
        Args:
            coro: Корутина для запуска
            name: Уникальное имя задачи (если не указано, генерируется автоматически)
            
        Returns:
            Имя созданной задачи
        """
        if name is None:
            prefix = getattr(coro, '__name__', 'task')
            name = create_task_name(prefix)
        
        if name in self._tasks and not self._tasks[name].done():
            logger.warning(f"Задача с именем '{name}' уже запущена. Отменяем предыдущую.")
            self.cancel_task(name)
        
        task = asyncio.create_task(coro, name=name)
        self._tasks[name] = task
        
        task.add_done_callback(functools.partial(self._task_done_callback, name))
        
        logger.debug(f"Задача '{name}' создана и запущена.")
        return name

    def _task_done_callback(self, name: str, task: asyncio.Task) -> None:
        """Callback-функция, вызываемая при завершении задачи."""
        logger.debug(f"Задача '{name}' завершена.")
        try:
            result = task.result()
            self._results[name] = result
        except asyncio.CancelledError:
            logger.info(f"Задача '{name}' была отменена.")
            if name in self._results:
                del self._results[name]
        except Exception as e:
            logger.exception(f"Задача '{name}' завершилась с ошибкой: {e}")
            if name in self._results:
                del self._results[name]
        
        if name in self._tasks and self._tasks[name] is task:
             del self._tasks[name]

    def cancel_task(self, name: str) -> bool:
        """
        Отменяет задачу по её имени.
        
        Args:
            name: Имя задачи для отмены
            
        Returns:
            True, если задача была найдена и отменена, иначе False
        """
        task = self._tasks.get(name)
        if task and not task.done():
            task.cancel()
            logger.info(f"Задача '{name}' отменена.")
            return True
        elif task:
             logger.warning(f"Задача '{name}' уже завершена.")
             return False
        else:
            logger.warning(f"Задача '{name}' не найдена.")
            return False

    def cancel_all_tasks(self) -> None:
        """Отменяет все запущенные задачи."""
        for name in list(self._tasks.keys()):
            self.cancel_task(name)

    def get_task_names(self) -> List[str]:
        """
        Возвращает список имен активных задач.
        
        Returns:
            Список имен задач
        """
        return list(self._tasks.keys())

    def is_task_running(self, name: str) -> bool:
        """
        Проверяет, запущена ли задача с указанным именем.
        
        Args:
            name: Имя задачи
            
        Returns:
            True, если задача активна, иначе False
        """
        task = self._tasks.get(name)
        return task is not None and not task.done()

    async def wait_for_task(self, name: str) -> Any:
        """
        Ожидает завершения задачи и возвращает её результат.
        
        Args:
            name: Имя задачи
            
        Returns:
            Результат выполнения задачи
            
        Raises:
            KeyError: Если задача с таким именем не найдена
            asyncio.CancelledError: Если задача была отменена
            Exception: Если задача завершилась с ошибкой
        """
        task = self._tasks.get(name)
        if task is None:
            if name in self._results:
                return self._results[name]
            else:
                 raise KeyError(f"Задача '{name}' не найдена.")
        
        try:
            return await task
        except asyncio.CancelledError:
            logger.info(f"Ожидание задачи '{name}' отменено.")
            raise
        except Exception as e:
            logger.error(f"Ошибка при ожидании задачи '{name}': {e}")
            raise


def format_timestamp(timestamp: Union[float, datetime], format_str: str = "%H:%M:%S") -> str:
    """
    Форматирует временную метку в строку.
    
    Args:
        timestamp: Временная метка (Unix timestamp или объект datetime)
        format_str: Строка формата для strftime
        
    Returns:
        Отформатированная строка времени
    """
    try:
        if isinstance(timestamp, (int, float)):
            dt_object = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            dt_object = timestamp
        else:
            return str(timestamp)
        
        return dt_object.strftime(format_str)
    except Exception as e:
        logger.error(f"Ошибка форматирования времени {timestamp}: {e}")
        return str(timestamp) 