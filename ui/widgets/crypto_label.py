"""
Виджет для отображения информации о криптовалюте.
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
from PyQt5.QtCore import QSettings, Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from PyQt5.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, 
    QGraphicsDropShadowEffect, QWidget
)

from core.utils import format_number, format_currency, format_percentage, get_trend_color
from core.models import AppState, AssetPrice

logger = logging.getLogger(__name__)


class CryptoLabel(QFrame):
    """
    Виджет для отображения информации о криптовалюте с ценой и опциональными спредами.
    """
    
    # Сигнал, который испускается при нажатии на виджет
    clicked = pyqtSignal()
    
    def __init__(self, currency: str, exchange: str, parent=None):
        """
        Инициализация виджета CryptoLabel.
        
        Args:
            currency: Название криптовалюты (BTC, ETH, USDT)
            exchange: Название биржи
            parent: Родительский виджет
        """
        super().__init__(parent)
        
        self.currency = currency
        self.exchange = exchange
        self.settings = QSettings()
        self.price = 0.0
        self.spot_price = 0.0  # Цена в USD для BTC/ETH
        self.prev_price = 0.0
        self.trend = 0  # 0 = нет изменений, 1 = рост, -1 = падение
        self._spread_labels = []
        self._price_history = []  # История изменения цены для обнаружения тренда
        
        # Получаем доступ к глобальному AppState
        self.app_state = AppState()
        
        # Инициализируем таймер для сброса тренда (он уже был)
        self.trend_timer = QTimer(self)
        self.trend_timer.timeout.connect(self._reset_trend)
        self.trend_timer.setSingleShot(True)
        
        # Инициализируем UI
        self._init_ui()
        
        # Инициализируем и запускаем таймер для обновления UI из AppState
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self._update_from_app_state)
        self.ui_update_timer.start(1000) # Обновляем UI каждую секунду
        
        # Вызываем первое обновление сразу, чтобы не ждать секунду
        self._update_from_app_state()
        # Применяем начальные визуальные настройки
        self._apply_visual_settings()
    
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Настройка внешнего вида
        # self.setFixedSize(280, 250) # Убираем фиксированный размер
        self.setMinimumWidth(280) # Установим минимальную ширину, высота будет авто
        self.setMinimumHeight(240) # Устанавливаем минимальную высоту для выравнивания
        self.setObjectName("cryptoWidget")
        
        # Добавляем эффект тени
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(200, 200, 200, 50))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Шрифты
        font_title = QFont('Segoe UI', 16, QFont.Bold)
        font_value = QFont('Segoe UI', 18, QFont.Bold)
        font_label = QFont('Segoe UI', 12)
        
        # Создаем основной компоновщик
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Верхняя панель с заголовком и иконкой
        top_panel = QHBoxLayout()
        
        # Заголовок (символ криптовалюты)
        self.currency_label = QLabel(self.currency, self)
        self.currency_label.setFont(font_title)
        self.currency_label.setStyleSheet("color: #303030; font-weight: bold;")
        top_panel.addWidget(self.currency_label)
        
        # Добавляем индикатор тренда
        self.trend_label = QLabel("●", self)
        self.trend_label.setFont(QFont('Segoe UI', 14))
        self.trend_label.setStyleSheet("color: #FFC107; font-size: 14px; qproperty-alignment: AlignCenter;")
        self.trend_label.setFixedSize(22, 22)
        top_panel.addWidget(self.trend_label)
        
        # Название биржи (справа)
        self.exchange_label = QLabel(self.exchange.capitalize(), self)
        self.exchange_label.setFont(font_label)
        self.exchange_label.setStyleSheet("color: #909090; qproperty-alignment: AlignRight;")
        top_panel.addWidget(self.exchange_label)
        
        # Добавляем верхнюю панель в основной компоновщик
        main_layout.addLayout(top_panel)
        
        # Виджет для текущей цены
        price_widget = QFrame(self)
        price_widget.setObjectName("priceWidget")
        price_widget.setStyleSheet("""
            QFrame#priceWidget {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #efefef;
            }
        """)
        price_layout = QVBoxLayout(price_widget)
        price_layout.setContentsMargins(12, 12, 12, 12)
        price_layout.setSpacing(6)
        
        # Метка "Цена"
        price_label = QLabel("Цена", price_widget)
        price_label.setFont(font_label)
        price_layout.addWidget(price_label)
        
        # Значение цены
        self.price_value = QLabel("0 ₽", price_widget)
        self.price_value.setObjectName("priceValueLabel")
        self.price_value.setFont(font_value)
        self.price_value.setStyleSheet("color: #303030; font-weight: bold; qproperty-alignment: AlignRight;")
        self.price_value.setMinimumWidth(150)
        self.price_value.setWordWrap(True)
        price_layout.addWidget(self.price_value)
        
        # Цена в долларах (для BTC, ETH) или информация для USDT
        self.spot_price_label = QLabel(price_widget)
        self.spot_price_label.setObjectName("spot_price")
        # Общий стиль для метки спотовой цены
        self.spot_price_label.setStyleSheet("""
            QLabel#spot_price {
                font-size: 14px; 
                /* Цвет будет наследоваться от темы */
                qproperty-alignment: AlignLeft;
            }
        """)
        price_layout.addWidget(self.spot_price_label)
        
        if self.currency == "USDT":
            self.spot_price_label.setText("Нет спотовой цены")
            self.spot_price_label.setVisible(True) 
        elif self.currency in ["BTC", "ETH"]:
            # Текст будет установлен при обновлении. Убедимся, что метка видима.
            self.spot_price_label.setText("- $") # Начальный плейсхолдер
            self.spot_price_label.setVisible(True)
        else:
            # Поведение для других валют (если появятся)
            self.spot_price_label.setVisible(False)
        
        # Добавляем виджет цены в основной компоновщик
        main_layout.addWidget(price_widget)
        
        # Добавляем спреды, если нужно (теперь и для USDT)
        self._init_spreads(main_layout, font_label)
        
        # Добавляем таймер для последнего обновления
        update_layout = QHBoxLayout()
        update_label = QLabel("Обновлено:", self)
        update_label.setFont(QFont('Segoe UI', 9))
        update_label.setStyleSheet("color: #909090;")
        
        self.update_time = QLabel("21:15:09", self)
        self.update_time.setFont(QFont('Segoe UI', 9))
        self.update_time.setStyleSheet("color: #606060; qproperty-alignment: AlignRight;")
        
        update_layout.addWidget(update_label)
        update_layout.addWidget(self.update_time, 1)
        
        # Добавляем информацию об обновлении в нижнюю часть компоновщика
        main_layout.addStretch()
        main_layout.addLayout(update_layout)
        
        # Запускаем таймер
        self.trend_timer.start(3000)
    
    def _start_trend_timer(self):
        """Запуск таймера для сброса индикатора тренда."""
        # Таймер уже инициализирован в __init__, просто перезапускаем
        if self.trend_timer.isActive():
            self.trend_timer.stop()
        self.trend_timer.start(3000)
    
    def _reset_trend(self):
        """Сброс индикатора тренда."""
        self.trend = 0
        self._update_trend_icon()
    
    def _init_spreads(self, layout, font):
        """
        Инициализация меток для спредов.
        
        Args:
            layout: Компоновщик для размещения меток
            font: Шрифт для меток
        """
        # Создаем фрейм для спредов
        spread_frame = QFrame(self)
        spread_frame.setObjectName("spreadWidget")
        spread_frame.setStyleSheet("""
            QFrame#spreadWidget {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #efefef;
            }
        """)
        spread_layout = QVBoxLayout(spread_frame)
        spread_layout.setContentsMargins(12, 12, 12, 12)
        spread_layout.setSpacing(6)
        
        # Заголовок для спредов
        spread_title = QLabel("Спреды", spread_frame)
        spread_title.setFont(font)
        spread_layout.addWidget(spread_title)
        
        # Создаем метки для трех разных спредов
        self._spread_labels = [] # Теперь будет список словарей
        for i in range(1, 4):
            spread_row = QHBoxLayout()
            spread_row.setSpacing(8) # Добавим немного места между элементами строки
            
            # Метка для названия спреда (текст будет установлен в _update_spreads)
            name_label = QLabel(f"Спред {i}:", spread_frame) 
            name_label.setFont(font)
            name_label.setAlignment(Qt.AlignmentFlag.AlignRight) # Выравниваем название вправо
            
            # Метка со значением спреда в процентах
            pct_label = QLabel("0.00%", spread_frame) # Начинаем с заглушки
            pct_label.setFont(font)
            # pct_label.setStyleSheet("color: #303030;") # Убираем жесткий цвет, будет наследоваться
            pct_label.setFixedWidth(55) # Немного уменьшим ширину для процентов
            pct_label.setAlignment(Qt.AlignmentFlag.AlignRight) # Выровняем проценты вправо
            
            # Метка со значением спреда в валюте
            value_label = QLabel("0 ₽", spread_frame) # Начинаем с заглушки
            value_label.setFont(font)
            value_label.setStyleSheet("color: #303030; qproperty-alignment: AlignRight;")
            
            # Добавляем метки в компоновщик строки
            spread_row.addWidget(name_label)       # Название
            spread_row.addStretch(1)             # Растяжение между названием и процентом
            spread_row.addWidget(pct_label)        # Процент
            spread_row.addWidget(value_label)      # Значение (убрали коэфф. растяжения 2)
            
            spread_layout.addLayout(spread_row)
            
            # Сохраняем все три метки для строки
            self._spread_labels.append({
                "name_label": name_label, 
                "pct_label": pct_label, 
                "value_label": value_label
            })
        
        # Добавляем фрейм спредов в основной компоновщик
        layout.addWidget(spread_frame)
    
    def update_price(self, price: float, spot_price: Optional[float] = None):
        """
        Обновление отображаемой цены.
        
        Args:
            price: Новое значение цены в рублях
            spot_price: Цена в долларах (для BTC и ETH)
        """
        self.prev_price = self.price
        self.price = price
        
        if spot_price is not None:
            self.spot_price = spot_price
        
        # Определяем тренд
        if self.price > self.prev_price:
            self.trend = 1
        elif self.price < self.prev_price:
            self.trend = -1
        
        # Обновляем отображаемые значения
        self._update_ui()
        
        # Обновляем время последнего обновления
        current_time = datetime.now().strftime("%H:%M:%S")
        self.update_time.setText(current_time)
        
        # Запускаем таймер для сброса иконки тренда
        self._start_trend_timer()
    
    def _update_ui(self):
        """Обновление всех элементов UI на основе текущих данных."""
        # Обновляем основную цену
        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Updating UI. Price value: {self.price}, type: {type(self.price)}")
        formatted_price = format_currency(self.price, "₽") 
        self.price_value.setText(formatted_price)
        
        # Обновляем спотовую цену или информационное сообщение
        if self.currency == "USDT":
            # Текст "Нет спотовой цены" уже установлен в _init_ui и не должен меняться здесь
            self.spot_price_label.setVisible(True) # Просто убедимся, что видимо
        elif self.currency in ["BTC", "ETH"]:
            if self.spot_price > 0:
                self.spot_price_label.setText(f"{self.spot_price:,.0f} $")
            else:
                self.spot_price_label.setText("- $") # Плейсхолдер, если спот цена невалидна или 0
            self.spot_price_label.setVisible(True)
        else:
            # Для других валют (если появятся), метка будет скрыта (согласно _init_ui)
            self.spot_price_label.setVisible(False) 
        
        # Обновляем иконку тренда
        self._update_trend_icon()
        
        # Обновляем спреды (теперь для всех, если они инициализированы)
        self._update_spreads()
        
        # Обновляем размер всего виджета после обновления контента
        # self.adjustSize() # Убираем adjustSize, компоновщик должен справиться сам
    
    def _update_trend_icon(self):
        """Обновление иконки тренда и цвета цены в зависимости от изменения цены."""
        # Сначала применяем актуальные настройки шрифта (размер, семейство)
        # Это гарантирует, что цвет не перезапишет нужный шрифт
        # (Дублирует часть логики _apply_visual_settings, но обеспечивает надежность)
        font_size = self.settings.value("ui/font_size", 10, type=int)
        font_family = self.settings.value("ui/font", "Segoe UI", type=str)
        base_style = f"font-family: '{font_family}'; font-size: {font_size}pt; font-weight: bold; qproperty-alignment: AlignRight;"

        if self.trend > 0:
            # Тренд вверх - зеленая индикация
            self.trend_label.setText("▲")
            self.trend_label.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: bold; qproperty-alignment: AlignCenter;")
            self.price_value.setStyleSheet(f"color: #4CAF50; {base_style}") # Комбинируем цвет и базовый стиль
        elif self.trend < 0:
            # Тренд вниз - красная индикация
            self.trend_label.setText("▼")
            self.trend_label.setStyleSheet("color: #F44336; font-size: 14px; font-weight: bold; qproperty-alignment: AlignCenter;")
            self.price_value.setStyleSheet(f"color: #F44336; {base_style}") # Комбинируем цвет и базовый стиль
        else:
            # Нет тренда - нейтральная индикация
            self.trend_label.setText("●")
            self.trend_label.setStyleSheet("color: #FFC107; font-size: 14px; qproperty-alignment: AlignCenter;")
            # Используем цвет по умолчанию (из темы/родителя) или задаем явно (#303030)
            self.price_value.setStyleSheet(f"color: #303030; {base_style}") # Комбинируем цвет и базовый стиль
    
    def _update_spreads(self):
        """Обновление значений спредов на основе настроек."""
        # TODO: Сделать комиссию настраиваемой
        commission = 0.5 + 0.2  # Default комиссия
        
        base_rub_price = self.price 

        # Получаем настроенные проценты спреда из QSettings
        spread_pct1 = self.settings.value("spreads/percent1", 0.50, type=float)
        spread_pct2 = self.settings.value("spreads/percent2", 1.00, type=float)
        spread_pct3 = self.settings.value("spreads/percent3", 1.50, type=float)
        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Loaded spread_pcts from QSettings: {spread_pct1}%, {spread_pct2}%, {spread_pct3}%")
        
        # Получаем настроенные названия спреда из QSettings
        spread_name1 = self.settings.value("spreads/name1", "Спред 1", type=str)
        spread_name2 = self.settings.value("spreads/name2", "Спред 2", type=str)
        spread_name3 = self.settings.value("spreads/name3", "Спред 3", type=str)
        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Loaded spread names from QSettings: '{spread_name1}', '{spread_name2}', '{spread_name3}'")

        configured_spread_percents = [spread_pct1, spread_pct2, spread_pct3]
        configured_spread_names = [spread_name1, spread_name2, spread_name3]
        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: configured_spread_percents list: {configured_spread_percents}")
        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: configured_spread_names list: {configured_spread_names}")

        for idx, labels_dict in enumerate(self._spread_labels):
            name_label = labels_dict['name_label']
            pct_label = labels_dict['pct_label']
            value_label = labels_dict['value_label']

            if idx < len(configured_spread_percents):
                spread_pct = configured_spread_percents[idx]
                spread_name = configured_spread_names[idx] if idx < len(configured_spread_names) else f"Спред {idx+1}" # Имя по умолчанию, если что-то пошло не так
                
                logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Spread_UI_element {idx+1} using name '{spread_name}' and percent {spread_pct}%")
            else:
                spread_pct = 0 
                spread_name = f"Спред {idx+1}"
                logger.warning(f"CryptoLabel {self.currency}/{self.exchange}: Spread_UI_element {idx+1} has no configured percent, using 0%.")
            
            # Обновляем все три метки
            name_label.setText(f"{spread_name}:")
            pct_label.setText(f"{spread_pct:.2f}%")
            
            raw_net_price_rub = base_rub_price * (1 + (spread_pct) / 100)
            # Добавим лог для расчета рублевой цены спреда
            logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Spread_UI_element {idx+1} - base_rub_price: {base_rub_price}, spread_pct: {spread_pct}, commission: {commission}, raw_net_price_rub: {raw_net_price_rub}")
            formatted_net_price = format_currency(raw_net_price_rub, "₽")

            value_label.setText(formatted_net_price)
    
    def hideContents(self):
        """Скрыть содержимое виджета."""
        self.price_value.setText("")
        if hasattr(self, 'spot_price_label'):
            self.spot_price_label.setText("")
        if self.currency in ["BTC", "ETH"]:
            for _, value_label in self._spread_labels:
                value_label.setText("")
        self.setStyleSheet("""
            QFrame#cryptoWidget {
                background-color: rgba(255, 255, 255, 0.5);
                border-radius: 12px;
                border: 1px solid #efefef;
            }
        """)
    
    def showContents(self):
        """Показать содержимое виджета."""
        self.setStyleSheet("")
        self._update_ui()
    
    def setSizeConstraint(self, width: int, height: int):
        """
        Установка ограничений размера виджета.
        
        Args:
            width: Ширина виджета
            height: Высота виджета
        """
        self.setFixedSize(width, height)

    def mousePressEvent(self, event):
        """Обработка нажатий на виджет."""
        self.clicked.emit()
        super().mousePressEvent(event)

    # НОВЫЙ МЕТОД для обновления из AppState
    def _update_from_app_state(self):
        """Обновляет UI виджета на основе данных из глобального AppState."""
        exchange_data = self.app_state.get_exchange(self.exchange)
        if exchange_data:
            asset_data = exchange_data.get_asset(self.currency)
            if asset_data:
                # logger.debug(f"Updating {self.exchange}-{self.currency} from AppState: RUB={asset_data.base_price}, SPOT={asset_data.spot_price}")
                # Вызываем существующий метод update_price с данными из AppState
                # Передаем base_price как 'price' и spot_price как 'spot_price'
                self.update_price(price=asset_data.base_price, spot_price=asset_data.spot_price)
            else:
                # Если данных по активу еще нет, можно показать заглушку или ничего не делать
                # logger.debug(f"No asset data in AppState for {self.exchange}-{self.currency}")
                pass 
        else:
            # Если данных по бирже еще нет
            # logger.debug(f"No exchange data in AppState for {self.exchange}")
            pass 

    def _apply_visual_settings(self):
        """Применяет настройки шрифта к нужным элементам через setStyleSheet."""
        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Applying visual settings via CSS...")
        try:
            font_size = self.settings.value("ui/font_size", 10, type=int)
            font_family = self.settings.value("ui/font", "Segoe UI", type=str)
            logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Using font: {font_family}, size: {font_size}pt for CSS")

            # Стиль для основной цены (жирный шрифт)
            price_value_style = f"font-family: '{font_family}'; font-size: {font_size}pt; font-weight: bold;"
            # Стиль для значений спредов (обычный шрифт, если нужно)
            # Пока оставим жирным, как и основную цену для единообразия
            spread_value_style = price_value_style 

            # Применяем к основной цене
            if hasattr(self, 'price_value'):
                # Важно: Сохраняем текущий цвет, чтобы не перезаписать его
                current_color = self.price_value.palette().color(QPalette.ColorRole.WindowText).name()
                self.price_value.setStyleSheet(f"color: {current_color}; {price_value_style}")
                logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Applied CSS font to price_value.")
            else:
                logger.warning(f"CryptoLabel {self.currency}/{self.exchange}: price_value not found during CSS font apply.")

            # Применяем к рублевым значениям спредов
            if hasattr(self, '_spread_labels'):
                for idx, labels_dict in enumerate(self._spread_labels):
                    value_label = labels_dict.get('value_label')
                    if value_label:
                        # Устанавливаем стиль, цвет по умолчанию будет черным (#303030), что нас устраивает
                        value_label.setStyleSheet(spread_value_style)
                        logger.debug(f"CryptoLabel {self.currency}/{self.exchange}: Applied CSS font to spread value_label {idx+1}.")
                    else:
                        logger.warning(f"CryptoLabel {self.currency}/{self.exchange}: value_label not found for spread {idx+1}.")
            else:
                 logger.warning(f"CryptoLabel {self.currency}/{self.exchange}: _spread_labels not found during CSS font apply.")

        except Exception as e:
            logger.error(f"CryptoLabel {self.currency}/{self.exchange}: Error applying visual settings via CSS: {e}")