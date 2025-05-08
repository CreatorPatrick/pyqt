"""
Главное окно приложения.
"""
import logging
import os
import sys
from typing import Optional, Dict, Set, Any

from PyQt5.QtCore import QSettings, QSize, QTimer, Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox, QSizePolicy, QAction, QMenu,
    QStatusBar, QFrame, QSplitter, QTabWidget, QGraphicsDropShadowEffect,
    QApplication, QMessageBox, QTabBar,
    QDialog
)

from config import APP_SETTINGS, UI_SETTINGS
from ui.widgets.info_widget import InfoWidget
from ui.dialogs.settings_dialog import SettingsDialog
import asyncio
import threading
from exchanges.bybit.connector import BybitConnector

# Переносим определение логгера сюда, ДО блока try-except
logger = logging.getLogger(__name__)

# Импортируем функцию применения темы (путь может отличаться)
# Предполагаем, что она в main.py в корне проекта
import sys
import os
# Добавляем корень проекта в sys.path, если main.py там
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
try:
    from main import apply_application_theme
except ImportError as e:
    logger.error(f"Не удалось импортировать apply_application_theme: {e}. Тема не будет меняться динамически.")
    def apply_application_theme(): pass # Заглушка

# logger = logging.getLogger(__name__) # Убираем дублирующее определение отсюда

class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    
    Управляет основным интерфейсом пользователя.
    """
    
    _instance_count = 0
    
    _instance = None
    
    _initialized = False
    
    _connectors: Dict[str, Any] = {}
    
    @classmethod
    def get_instance(cls):
        """
        Возвращает существующий экземпляр окна или создает новый.
        
        Returns:
            Экземпляр главного окна
        """
        if cls._instance is None or not cls._instance.isVisible():
            cls._instance = MainWindow()
        else:
            logger.info("Запрос существующего экземпляра главного окна")
            cls._instance.activateWindow()
            cls._instance.raise_()
            
        return cls._instance
    
    def __new__(cls, *args: Any, **kwargs: Any):
        """
        Реализация паттерна Singleton для главного окна.
        
        Returns:
            Единственный экземпляр главного окна
        """
        cls._instance_count += 1
        logger.info(f"Попытка создания экземпляра MainWindow #{cls._instance_count}")
        
        if cls._instance is None:
            logger.info("Создание нового экземпляра главного окна")
            cls._instance = super(MainWindow, cls).__new__(cls)
        else:
            try:
                if not cls._instance.isVisible():
                    logger.info("Окно существует, но не отображается - пересоздаем его")
                    cls._initialized = False
                else:
                    logger.info("Возвращение существующего экземпляра главного окна")
                    cls._instance.activateWindow()
                    cls._instance.raise_()
            except RuntimeError:
                logger.info("Старый экземпляр был удален, создаем новый")
                cls._instance = super(MainWindow, cls).__new__(cls)
                cls._initialized = False
                
        return cls._instance
    
    def __init__(self):
        """Инициализация главного окна."""
        if self._initialized:
            logger.info("Повторная инициализация пропущена - окно уже инициализировано")
            if self.isVisible():
                self.activateWindow()
                self.raise_()
            return
            
        logger.info("Инициализация главного окна")
        super().__init__()
        
        QApplication.setQuitOnLastWindowClosed(False)
        
        self.settings = QSettings()
        self.info_widget = None
        self._initializing = False
        self._init_ui()
        self._load_window_settings()
        
        self._init_connectors()
        
        MainWindow._initialized = True
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        if self._initializing:
            logger.warning("Попытка повторной инициализации UI. Инициализация отменена.")
            return
            
        self._initializing = True
        
        try:
            old_menu = self.menuBar()
            if old_menu:
                old_menu.clear()
            
            self.setWindowTitle("Crypto Monitor Pro")
            self.setWindowIcon(QIcon(os.path.join("image", "Vector.ico")))
            
            central_widget = QWidget(self)
            central_widget.setObjectName("centralWidget")
            
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            top_panel = self._create_top_panel()
            main_layout.addLayout(top_panel)
            
            
            content_widget = QWidget()
            
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            
            main_splitter = QSplitter(Qt.Orientation.Horizontal)
            
            
            self.side_panel = self._create_side_panel()
            main_splitter.addWidget(self.side_panel)
            
            tab_widget = QTabWidget()
            tab_widget.setObjectName("mainTabs")
            tab_widget.setTabPosition(QTabWidget.North)
            tab_widget.setTabsClosable(False)
            tab_widget.setMovable(True)
            
            
            self.info_widget = InfoWidget(self)
            self.info_widget.setObjectName("infoWidgetInstance")
            tab_widget.addTab(self.info_widget, "Курсы")
            
            charts_widget = self._create_charts_widget()
            charts_widget.setObjectName("chartsWidget")
            tab_widget.addTab(charts_widget, "Графики")
            
            stats_widget = self._create_stats_widget()
            stats_widget.setObjectName("statsWidget")
            tab_widget.addTab(stats_widget, "Статистика")
            
            main_splitter.addWidget(tab_widget)
            
            main_splitter.setSizes([200, 800])
            
            content_layout.addWidget(main_splitter)
            
            # Добавляем content_widget в главный макет
            main_layout.addWidget(content_widget, 1)
            
            self.setCentralWidget(central_widget)
            
            self._create_status_bar()
            
            self._create_menu()
            
            self.resize(1200, 800)
            
            self._apply_styles()
            
            self._load_and_apply_filter_settings()
            
            app_instance = QApplication.instance()
            if app_instance:
                app_instance.aboutToQuit.connect(self._handle_app_quit)
            else:
                logger.error("QApplication.instance() is None во время _init_ui, не могу подключить сигнал aboutToQuit.")
        finally:
            self._initializing = False
    
    def _handle_app_quit(self):
        logger.info("Приложение завершается")
        
        logger.info("Остановка коннекторов...")
        for name, connector_instance in self._connectors.items():
            if hasattr(connector_instance, 'stop'):
                try:
                    if asyncio.iscoroutinefunction(connector_instance.stop):
                        asyncio.run(connector_instance.stop()) 
                    else:
                        connector_instance.stop()
                    logger.info(f"Коннектор {name} остановлен.")
                except Exception as e:
                    logger.error(f"Ошибка при остановке коннектора {name}: {e}")
        
        MainWindow._instance = None
        MainWindow._initialized = False
    
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        logger.info("Окно показано пользователю")
        
    
    def _create_top_panel(self) -> QHBoxLayout:
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        top_panel = QFrame()
        top_panel.setObjectName("topPanel")
        top_panel.setFrameShape(QFrame.NoFrame)
        top_panel.setFixedHeight(60)
        
        panel_layout = QHBoxLayout(top_panel)
        panel_layout.setContentsMargins(20, 5, 20, 5)
        
        title_layout = QHBoxLayout()
        
        app_icon = QLabel()
        icon_pixmap = QPixmap(os.path.join("image", "Vector.svg"))
        if not icon_pixmap.isNull():
            app_icon.setPixmap(icon_pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        app_icon.setFixedSize(28, 28)
        title_layout.addWidget(app_icon)
        
        app_title = QLabel("Crypto Monitor Pro")
        app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #303030; margin-left: 10px;")
        title_layout.addWidget(app_title)
        
        panel_layout.addLayout(title_layout)
        
        panel_layout.addStretch()
        
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(12)
        
        scale_layout = QHBoxLayout()
        scale_layout.setContentsMargins(0, 0, 0, 0)
        scale_layout.setSpacing(5)
        
        
        settings_btn = QPushButton("Настройки")
        settings_btn.setObjectName("settingsButton")
        settings_btn.setToolTip("Открыть настройки приложения")
        settings_btn.clicked.connect(self._open_settings)
        buttons_layout.addWidget(settings_btn)
        
        panel_layout.addWidget(buttons_container)
        
        container_layout.addWidget(top_panel)
        
        top_layout.addWidget(container)
        
        return top_layout
    
    def _create_side_panel(self) -> QWidget:
        side_panel = QFrame()
        side_panel.setObjectName("sidePanel")
        side_panel.setFrameShape(QFrame.NoFrame)
        side_panel.setMinimumWidth(220)
        side_panel.setMaximumWidth(280)
        
        layout = QVBoxLayout(side_panel)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(25)
        
        header = QLabel("Фильтры")
        header.setObjectName("header")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #303030;")
        layout.addWidget(header)
        
        exchange_group = QFrame(side_panel)
        exchange_group.setObjectName("exchangeGroup")
        exchange_group.setFrameShape(QFrame.NoFrame)
        
        exchange_layout = QVBoxLayout(exchange_group)
        exchange_layout.setContentsMargins(0, 0, 0, 0)
        exchange_layout.setSpacing(10)
        
        exchange_header = QLabel("Биржи", exchange_group)
        exchange_header.setFont(QFont("Arial", 14, QFont.Bold))
        exchange_header.setStyleSheet("color: #303030;")
        exchange_layout.addWidget(exchange_header)
        
        for exchange in ["Binance", "Bybit", "CommEX", "Garantex"]:
            btn = QPushButton(exchange, exchange_group)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setObjectName(f"{exchange.lower()}Button")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 15px;
                    background-color: #f8f8f5;
                    color: #303030;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #ffebeb;
                    color: #ff6b6b;
                    border-left: 4px solid #ff6b6b;
                }
                QPushButton:hover {
                    background-color: #ffebeb;
                }
            """)
            btn.toggled.connect(lambda checked, e=exchange.lower(): self._toggle_exchange(e, checked))
            exchange_layout.addWidget(btn)
        
        layout.addWidget(exchange_group)
        
        crypto_group = QFrame(side_panel)
        crypto_group.setObjectName("cryptoGroup")
        crypto_group.setFrameShape(QFrame.NoFrame)
        
        crypto_layout = QVBoxLayout(crypto_group)
        crypto_layout.setContentsMargins(0, 0, 0, 0)
        crypto_layout.setSpacing(10)
        
        crypto_header = QLabel("Криптовалюты", crypto_group)
        crypto_header.setFont(QFont("Arial", 14, QFont.Bold))
        crypto_header.setStyleSheet("color: #303030;")
        crypto_layout.addWidget(crypto_header)
        
        for crypto in ["BTC", "ETH", "USDT"]:
            btn = QPushButton(crypto, crypto_group)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setObjectName(f"{crypto.lower()}Button")
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 15px;
                    background-color: #f8f8f5;
                    color: #303030;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #ffebeb;
                    color: #ff6b6b;
                    border-left: 4px solid #ff6b6b;
                }
                QPushButton:hover {
                    background-color: #ffebeb;
                }
            """)
            btn.toggled.connect(lambda checked, c=crypto.lower(): self._toggle_crypto(c, checked))
            crypto_layout.addWidget(btn)
        
        layout.addWidget(crypto_group)
        
        info_group = QFrame(side_panel)
        info_group.setObjectName("infoGroup")
        info_group.setFrameShape(QFrame.NoFrame)
        
        info_layout = QVBoxLayout(info_group)
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setSpacing(10)
        
        info_header = QLabel("Информация", info_group)
        info_header.setFont(QFont("Arial", 14, QFont.Bold))
        info_header.setStyleSheet("color: #303030;")
        info_layout.addWidget(info_header)
        
        status_layout = QHBoxLayout()
        status_icon = QLabel("●")
        status_icon.setStyleSheet("color: #4CAF50; font-size: 16px;")
        status_layout.addWidget(status_icon)
        
        status_label = QLabel("Статус: активно")
        status_label.setStyleSheet("color: #303030;")
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        info_layout.addLayout(status_layout)
        
        update_layout = QHBoxLayout()
        update_icon = QLabel("⟳")
        update_icon.setStyleSheet("color: #ff6b6b; font-size: 16px;")
        update_layout.addWidget(update_icon)
        
        update_label = QLabel("Последнее: сейчас")
        update_label.setStyleSheet("color: #303030;")
        update_layout.addWidget(update_label)
        update_layout.addStretch()
        
        info_layout.addLayout(update_layout)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return side_panel
    
    def _create_charts_widget(self) -> QWidget:
        charts_widget = QWidget()
        layout = QVBoxLayout(charts_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Графики динамики цен", charts_widget)
        header.setStyleSheet("color: #303030; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        placeholder = QLabel("График будет отображаться здесь", charts_widget)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            color: #303030;
            font-size: 16px;
            background-color: #ffebeb;
            border-radius: 10px;
            padding: 40px;
            margin: 20px;
        """)
        placeholder.setMinimumHeight(300)
        
        layout.addWidget(placeholder)
        
        return charts_widget
    
    def _create_stats_widget(self) -> QWidget:
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("Статистика и аналитика", stats_widget)
        header.setStyleSheet("color: #303030; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        cards_layout = QHBoxLayout()
        
        market_card = QFrame()
        market_card.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 10px;
            border: 1px solid #efefef;
            padding: 15px;
        """)
        market_layout = QVBoxLayout(market_card)
        
        market_header = QLabel("Рыночный обзор")
        market_header.setStyleSheet("color: #303030; font-weight: bold; font-size: 14px;")
        market_layout.addWidget(market_header)
        
        market_content = QLabel("Данные будут доступны после первого обновления")
        market_content.setStyleSheet("color: #303030; padding: 10px 0;")
        market_content.setWordWrap(True)
        market_layout.addWidget(market_content)
        
        cards_layout.addWidget(market_card)
        
        price_card = QFrame()
        price_card.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 10px;
            border: 1px solid #efefef;
            padding: 15px;
        """)
        price_layout = QVBoxLayout(price_card)
        
        price_header = QLabel("Изменения цен")
        price_header.setStyleSheet("color: #303030; font-weight: bold; font-size: 14px;")
        price_layout.addWidget(price_header)
        
        price_content = QLabel("Данные будут доступны после первого обновления")
        price_content.setStyleSheet("color: #303030; padding: 10px 0;")
        price_content.setWordWrap(True)
        price_layout.addWidget(price_content)
        
        cards_layout.addWidget(price_card)
        
        spread_card = QFrame()
        spread_card.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 10px;
            border: 1px solid #efefef;
            padding: 15px;
        """)
        spread_layout = QVBoxLayout(spread_card)
        
        spread_header = QLabel("Анализ спредов")
        spread_header.setStyleSheet("color: #303030; font-weight: bold; font-size: 14px;")
        spread_layout.addWidget(spread_header)
        
        spread_content = QLabel("Данные будут доступны после первого обновления")
        spread_content.setStyleSheet("color: #303030; padding: 10px 0;")
        spread_content.setWordWrap(True)
        spread_layout.addWidget(spread_content)
        
        cards_layout.addWidget(spread_card)
        
        layout.addLayout(cards_layout)
        
        detail_placeholder = QLabel("Детальная статистика будет отображаться здесь", stats_widget)
        detail_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail_placeholder.setStyleSheet("""
            color: #303030;
            font-size: 16px;
            background-color: #ffebeb;
            border-radius: 10px;
            padding: 30px;
            margin-top: 20px;
        """)
        detail_placeholder.setMinimumHeight(200)
        
        layout.addWidget(detail_placeholder)
        
        return stats_widget
    
    def _create_menu(self):
        main_menu = self.menuBar()
        if not main_menu:
            logger.warning("Не удалось создать главное меню")
            return
        
        file_menu = main_menu.addMenu("Файл")
        
        if file_menu:
            refresh_action = QAction("Обновить данные", self)
            refresh_action.setShortcut("F5")
            refresh_action.triggered.connect(self._refresh_data)
            file_menu.addAction(refresh_action)
            
            settings_action = QAction("Настройки", self)
            settings_action.setShortcut("Ctrl+P")
            settings_action.triggered.connect(self._open_settings)
            file_menu.addAction(settings_action)
            
            file_menu.addSeparator()
            
            exit_action = QAction("Выход", self)
            exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(self._handle_exit_action)
            file_menu.addAction(exit_action)
        else:
            logger.error("main_menu.addMenu('Файл') вернуло None. Меню 'Файл' не будет создано.")
        
        view_menu = main_menu.addMenu("Вид")
        if view_menu:
            scale_menu = QMenu("Масштаб", self)
            for scale in ['70%', '85%', '100%', '115%', '130%']:
                scale_action = QAction(scale, self)
                scale_action.triggered.connect(lambda checked, s=scale: self.scale_box.setCurrentText(s))
                scale_menu.addAction(scale_action)
            view_menu.addMenu(scale_menu)
            
            exchanges_menu = QMenu("Биржи", self)
            for exchange in ["Binance", "Bybit", "CommEX", "Garantex"]:
                exchange_action = QAction(exchange, self)
                exchange_action.setCheckable(True)
                exchange_action.setChecked(True)
                exchange_action.triggered.connect(lambda checked, e=exchange.lower(): self._toggle_exchange(e, checked))
                exchanges_menu.addAction(exchange_action)
            view_menu.addMenu(exchanges_menu)
        else:
            logger.error("main_menu.addMenu('Вид') вернуло None. Меню 'Вид' не будет создано.")
            
        help_menu = main_menu.addMenu("Справка")
        if help_menu:
            about_action = QAction("О программе", self)
            about_action.triggered.connect(self._show_about)
            help_menu.addAction(about_action)
        else:
            logger.error("main_menu.addMenu('Справка') вернуло None. Меню 'Справка' не будет создано.")
    
    def _create_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        self.status_label = QLabel("Готово")
        status_bar.addWidget(self.status_label, 1)
        
        self.activity_label = QLabel("●")
        self.activity_label.setStyleSheet("color: green;")
        status_bar.addPermanentWidget(self.activity_label)
        
        self.update_time_label = QLabel("Последнее обновление: --:--:--")
        status_bar.addPermanentWidget(self.update_time_label)
    
    def _apply_styles(self):
        # Этот метод пока не используется, т.к. тема применяется глобально
        # Его можно будет использовать для применения НЕ цветовых стилей (тени и т.д.)
        # logger.debug("MainWindow._apply_styles called (currently inactive)")
        pass
        # button_style = """ ... """ 
        # panel_style = """ ... """ 
        # combo_style = """ ... """ 
        # general_style = """ ... """ 
        # tab_style = """ ... """ 
        # self.setStyleSheet(button_style + panel_style + combo_style + general_style + tab_style)
        
        # shadow = QGraphicsDropShadowEffect()
        # shadow.setBlurRadius(15)
        # shadow.setColor(QColor(0, 0, 0, 60))
        # shadow.setOffset(0, 2)
        
        # top_panel = self.findChild(QFrame, "topPanel")
        # if top_panel:
        #     top_panel.setGraphicsEffect(shadow)
    
    def _toggle_exchange(self, exchange_name: str, visible: bool):
        self.settings.setValue(f"filters/exchange_{exchange_name}", visible)
        
        if self.info_widget:
            self.info_widget.set_exchange_visibility(exchange_name, visible)
        self.status_label.setText(f"Биржа {exchange_name.upper()} {'показана' if visible else 'скрыта'}")
    
    def _toggle_crypto(self, crypto_name: str, visible: bool):
        self.settings.setValue(f"filters/crypto_{crypto_name}", visible)
        
        exchanges = ["binance", "bybit", "commex", "garantex"]
        for exchange in exchanges:
            if self.info_widget:
                self.info_widget.set_asset_visibility(exchange, crypto_name.upper(), visible)
        
        self.status_label.setText(f"Криптовалюта {crypto_name.upper()} {'показана' if visible else 'скрыта'}")
    
    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        # Напрямую устанавливаем (сбрасываем) флаг на самом диалоговом окне
        dialog.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        
        # Применяем изменения только если диалог был принят (OK или Apply)
        if dialog.exec_() == QDialog.DialogCode.Accepted:
            logger.info("Настройки приняты. Применение изменений...")
            
            # 1. Применяем глобальную тему
            try:
                apply_application_theme() 
                logger.info("Глобальная тема применена.")
            except Exception as e:
                logger.error(f"Ошибка применения темы: {e}", exc_info=True)

            # 2. Применяем изменения шрифта/визуала и обновляем UI CryptoLabels
            if self.info_widget:
                try:
                    # Получаем все виджеты CryptoLabel
                    crypto_labels = self.info_widget.get_crypto_labels()
                    logger.info(f"Найдено {len(crypto_labels)} CryptoLabel виджетов для обновления настроек.")
                    for label in crypto_labels:
                        if hasattr(label, '_apply_visual_settings'):
                            label._apply_visual_settings() 
                        # Обновляем UI, чтобы перерисовались спреды с новыми настройками
                        if hasattr(label, '_update_ui'):
                            label._update_ui()
                    logger.info("Визуальные настройки и UI для CryptoLabel обновлены.")
                except Exception as e:
                     logger.error(f"Ошибка при обновлении CryptoLabel после настроек: {e}", exc_info=True)
            
            # Можно оставить вызов _refresh_data, если он нужен для других целей,
            # но обновление CryptoLabel уже должно было произойти.
            # self._refresh_data() 
        else:
            logger.info("Диалог настроек закрыт без сохранения (нажата Cancel).)")
    
    def _apply_scale(self, scale_text: str):
        self.settings.setValue("window/scale", scale_text)
        
        try:
            scale = float(scale_text.strip('%')) / 100.0
        except ValueError:
            logger.error(f"Invalid scale value: {scale_text}")
            return
        
        base_width = 1200
        base_height = 800
        self.resize(int(base_width * scale), int(base_height * scale))
    
    def _show_about(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("О программе")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(
            "<h2>Crypto Monitor Pro</h2>"
            "<p>Версия 1.0.0</p>"
            "<p>Современное приложение для отслеживания цен криптовалют на различных биржах.</p>"
            "<p>&copy; 2023-2025 CryptoSoft Inc. Все права защищены.</p>"
        )
        msg_box.setWindowModality(Qt.WindowModality.ApplicationModal)
        msg_box.exec_()
    
    def _refresh_data(self):
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.activity_label.setStyleSheet("color: orange;")
        
        QTimer.singleShot(500, lambda: self.activity_label.setStyleSheet("color: green;"))
        
        self.update_time_label.setText(f"Последнее обновление: {current_time}")
        
        self.status_label.setText("Данные обновлены")
        
        if self.info_widget:
            self.info_widget._update_data()
        
    def _handle_exit_action(self):
        """Обработчик для действия выхода из меню."""
        self.close()
    
    def _load_window_settings(self):
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        scale = self.settings.value("window/scale", "100%")
        self._apply_scale(scale)
    
    def _save_window_settings(self):
        self.settings.setValue("window/geometry", self.saveGeometry())
    
    def closeEvent(self, event):
        try:
            logger.info("Окно закрывается. Остановка сервисов...")
            self._handle_app_quit() 
            
            self._save_window_settings()
            
            super().closeEvent(event)
            
            logger.info("Завершение работы QApplication...")
            app_instance = QApplication.instance()
            if app_instance:
                app_instance.quit()
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии окна: {e}")
            event.accept()
            app_instance = QApplication.instance()
            if app_instance:
                 app_instance.quit()

    def _load_and_apply_filter_settings(self):
        logger.info("Загрузка и применение настроек фильтров...")
        
        if not self.side_panel or not self.info_widget:
            logger.warning("Боковая панель или виджет информации еще не созданы. Пропуск загрузки фильтров.")
            return

        exchanges = ["binance", "bybit", "commex", "garantex"]
        for exchange_key in exchanges:
            visible_str = self.settings.value(f"filters/exchange_{exchange_key}", "true")
            visible = str(visible_str).lower() == 'true'
            
            button = self.side_panel.findChild(QPushButton, f"{exchange_key}Button")
            if button:
                button.blockSignals(True)
                button.setChecked(visible) 
                button.blockSignals(False)
            else:
                 logger.warning(f"Кнопка для биржи {exchange_key} не найдена.")

            self.info_widget.set_exchange_visibility(exchange_key, visible)

        cryptos = ["btc", "eth", "usdt"]
        for crypto_key in cryptos:
            visible_str = self.settings.value(f"filters/crypto_{crypto_key}", "true")
            visible = str(visible_str).lower() == 'true'

            button = self.side_panel.findChild(QPushButton, f"{crypto_key}Button")
            if button:
                button.blockSignals(True)
                button.setChecked(visible)
                button.blockSignals(False)
            else:
                logger.warning(f"Кнопка для криптовалюты {crypto_key} не найдена.")

            for exchange_key in exchanges:
                self.info_widget.set_asset_visibility(exchange_key, crypto_key.upper(), visible)
                 
        logger.info("Настройки фильтров загружены и применены.") 

    def _position_line_cover(self, tab_widget, line_cover):
        tab_bar = tab_widget.findChild(QTabBar)
        if tab_bar:
            tab_bar_rect = tab_bar.geometry()
            tab_widget_rect = tab_widget.geometry()
            
            line_cover.move(tab_widget_rect.left(), tab_bar_rect.bottom())
            line_cover.setFixedWidth(tab_widget_rect.width())
        else:
            logger.warning("Не удалось найти QTabBar в QTabWidget") 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        QTimer.singleShot(10, self._update_tab_line_cover)
    
    def _update_tab_line_cover(self):
        tab_widget = self.findChild(QTabWidget, "mainTabs")
        if not tab_widget:
            return
            
        cover_line = tab_widget.findChild(QFrame, "tabLineCover")
        if not cover_line:
            cover_line = QFrame(tab_widget)
            cover_line.setObjectName("tabLineCover")
            cover_line.setStyleSheet("""
                background-color: #f8f8f5;
                border: none;
            """)
            
        tab_bar = tab_widget.tabBar()
        if tab_bar:
            cover_line.setFixedHeight(6)
            cover_line.setFixedWidth(tab_widget.width())
            
            cover_line.move(0, tab_bar.height() - 1)
            cover_line.show()
            cover_line.raise_()
            
            cover_line2 = tab_widget.findChild(QFrame, "tabLineCover2")
            if not cover_line2:
                cover_line2 = QFrame(tab_widget)
                cover_line2.setObjectName("tabLineCover2")
                cover_line2.setStyleSheet("""
                    background-color: #f8f8f5;
                    border: none;
                """)
            
            cover_line2.setFixedHeight(4)
            cover_line2.setFixedWidth(tab_widget.width())
            cover_line2.move(0, tab_bar.height() + 2)
            cover_line2.show()
            cover_line2.raise_()
            
            content_widget = tab_widget.currentWidget()
            if content_widget:
                content_widget.setStyleSheet("""
                    background-color: #f8f8f5;
                    border-top: none;
                    margin-top: -1px;
                """)
                content_widget.update() 

    def _init_connectors(self):
        logger.info("Инициализация коннекторов...")
        
        bybit_config = {
            'base_url': 'https://api.bybit.com',
            'assets': ['BTC', 'ETH'],
            'api_key': '',
            'api_secret': ''
        }
        
        if bybit_config:
            logger.info(f"Используется жестко заданная конфигурация для Bybit. Запуск коннектора... Base URL: {bybit_config['base_url']}")
            self._connectors['bybit'] = BybitConnector(exchange_name="bybit", config=bybit_config)
            
            connector_thread = threading.Thread(
                target=lambda: asyncio.run(self._connectors['bybit'].start()),
                daemon=True
            )
            connector_thread.start()
        else:
            logger.warning("Конфигурация для Bybit не определена (это неожиданно, т.к. она задана в коде).")
            
        # Здесь можно добавить инициализацию других коннекторов по аналогии 

    def _handle_visibility_changed(self, crypto_key: str, visible: bool):
        # Implementation of _handle_visibility_changed method
        pass 