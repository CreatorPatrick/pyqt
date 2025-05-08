"""
Виджет для отображения информации о биржах и криптовалютах.
"""
import logging
from typing import Dict, List, Optional, Union, cast
from PyQt5.QtCore import QSettings, Qt, QTimer
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QHBoxLayout, QVBoxLayout, QScrollArea, QFrame
from PyQt5.QtGui import QFont
from collections import defaultdict

from core.app_state import app_state
from core.models import AssetPrice
from config import APP_SETTINGS
from ui.widgets.crypto_label import CryptoLabel
from ui.widgets.exchange_widget import ExchangeWidget

logger = logging.getLogger(__name__)


class InfoWidget(QWidget):
    """
    Виджет для отображения информации о курсах криптовалют.
    """
    
    def __init__(self, parent=None):
        """Инициализация виджета информации."""
        super().__init__(parent)
        self.parent_widget = parent  # Переименовано, чтобы избежать конфликта с методом parent()
        self.exchange_widgets = defaultdict(dict)
        self.exchange_widget_refs = {}
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса."""
        # self.setAutoFillBackground(True) # Убираем или ставим False

        # Основной макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # Заголовок
        title_container = QWidget(self)
        title_container.setObjectName("titleContainer")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(5, 5, 5, 5)
        
        title = QLabel("Криптовалютные торговые пары", title_container)
        title.setObjectName("mainTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #303030;")
        title_layout.addWidget(title)
        
        main_layout.addWidget(title_container)
        
        # Создаем область прокрутки для контента
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""                
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        scroll_area.setObjectName("infoWidgetScrollArea")
        
        # Создаем контейнер для содержимого
        content_widget = QWidget(scroll_area)
        content_widget.setObjectName("infoContentWidget")
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(12)
        
        # Создаем виджеты для каждой биржи
        self._create_exchange_widgets(content_layout)
        
        # Устанавливаем виджет содержимого в область прокрутки
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_exchange_widgets(self, layout):
        """
        Создание виджетов для каждой биржи.
        
        Args:
            layout: Компоновщик для добавления виджетов
        """
        # Создаем виджеты для бирж
        exchanges = [
            {"name": "BINANCE", "key": "binance", "assets": ["BTC", "ETH", "USDT"]},
            {"name": "BYBIT", "key": "bybit", "assets": ["BTC", "ETH", "USDT"]},
            {"name": "COMMEX", "key": "commex", "assets": ["BTC", "ETH", "USDT"]},
            {"name": "GARANTEX", "key": "garantex", "assets": ["BTC", "ETH", "USDT"]}
        ]
        
        for exchange in exchanges:
            exchange_widget = self._create_exchange_widget(
                exchange["name"], 
                exchange["key"], 
                exchange["assets"]
            )
            layout.addWidget(exchange_widget)
    
    def _create_exchange_widget(self, title, key, assets):
        """
        Создание виджета одной биржи.
        
        Args:
            title: Название биржи
            key: Ключ биржи
            assets: Список активов
            
        Returns:
            Виджет биржи
        """
        exchange_widget = ExchangeWidget(title=title, parent=self)
        
        # Сохраняем ссылку на созданный виджет биржи
        self.exchange_widget_refs[key.lower()] = exchange_widget
        
        # Создаем grid layout для виджетов криптовалют
        grid = QGridLayout()
        grid.setContentsMargins(10, 8, 10, 10)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(12)
        
        # Добавляем виджеты криптовалют в сетку
        for i, asset in enumerate(assets):
            crypto_widget = CryptoLabel(
                currency=asset,
                exchange=key.lower(),
                parent=exchange_widget
            )
            # Сохраняем ссылку на виджет для последующего обновления
            self.exchange_widgets[key.lower()][asset] = crypto_widget
            
            # Добавляем виджет в сетку (по 3 виджета в ряд)
            grid.addWidget(crypto_widget, i // 3, i % 3)
        
        # Добавляем сетку в макет биржи
        exchange_widget.content_layout.addLayout(grid)
        
        return exchange_widget
    
    def set_exchange_visibility(self, exchange_name: str, visible: bool):
        """
        Установка видимости биржи.
        
        Args:
            exchange_name: Название биржи
            visible: Флаг видимости
        """
        logger.info(f"Attempting to set visibility for exchange '{exchange_name}' to {visible}")
        try:
            # Получаем виджет биржи напрямую из словаря ссылок
            exchange_widget_instance = self.exchange_widget_refs.get(exchange_name)
            
            if exchange_widget_instance:
                logger.info(f"Found ExchangeWidget instance for {exchange_name}. Setting visible={visible}")
                exchange_widget_instance.setVisible(visible) # Скрываем/показываем весь блок
            else:
                logger.warning(f"ExchangeWidget instance not found in refs for key '{exchange_name}'. Cannot set visibility.")
        except Exception as e: # Добавим общий Exception на всякий случай
            logger.error(f"Error setting visibility for exchange '{exchange_name}': {e}")
    
    def set_asset_visibility(self, exchange_name: str, asset_name: str, visible: bool):
        """
        Установка видимости криптовалюты.
        
        Args:
            exchange_name: Название биржи
            asset_name: Название криптовалюты
            visible: Флаг видимости
        """
        try:
            crypto_widget = self.exchange_widgets[exchange_name][asset_name]
            crypto_widget.setVisible(visible)
        except KeyError:
            logger.error(f"Не найден виджет для {exchange_name}/{asset_name}")
    
    # Новый метод для получения всех CryptoLabel
    def get_crypto_labels(self) -> List[CryptoLabel]:
        """Возвращает список всех виджетов CryptoLabel."""
        all_labels = []
        for exchange_assets in self.exchange_widgets.values():
            all_labels.extend(exchange_assets.values())
        return all_labels

    def _update_data(self):
        """Обновление данных в виджетах."""
        # В реальном приложении здесь будет получение актуальных данных
        # Для демонстрации обновляем через родительский класс
        if self.parent_widget and hasattr(self.parent_widget, "_update_demo_values"):
            getattr(self.parent_widget, "_update_demo_values")() 