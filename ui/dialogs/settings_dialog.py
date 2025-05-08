"""
Диалог настроек приложения.
"""
import logging
from typing import Dict, Any

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton,
    QGroupBox, QFormLayout, QDialogButtonBox, QCheckBox, QSpinBox,
    QSizePolicy
)

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Диалог настроек приложения.
    
    Позволяет пользователю настраивать параметры приложения.
    """
    
    def __init__(self, parent=None):
        """
        Инициализация диалога настроек.
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.settings = QSettings()
        self._exchange_widgets: Dict[str, Dict[str, Any]] = {}
        self._init_ui()
        self._load_settings()
        
        # Переопределяем стиль выделения для QDoubleSpinBox в этом диалоге
        self.setStyleSheet("""
            QDoubleSpinBox {
                selection-background-color: #a8c8f9; /* Светло-голубой */
                selection-color: black; /* Черный текст при выделении */
            }
        """)
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Настройка основного диалога
        self.setWindowTitle("Настройки приложения")
        self.setMinimumSize(650, 450)
        
        # Основной компоновщик
        main_layout = QVBoxLayout(self)
        
        # Создание вкладок
        tab_widget = QTabWidget()
        
        # Вкладка общих настроек
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "Общие")

        
        # Добавление вкладок в основной компоновщик
        main_layout.addWidget(tab_widget)
        
        # Кнопки диалога
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Получаем кнопку Apply и подключаем ее к слоту
        apply_button = button_box.button(QDialogButtonBox.Apply)
        if apply_button:
            apply_button.clicked.connect(self._apply_settings)
        
        # Добавление кнопок в основной компоновщик
        main_layout.addWidget(button_box)
        
        # Настройка сигналов
        self.accepted.connect(self._save_settings)
    
    def _create_general_tab(self) -> QWidget:
        """
        Создание вкладки общих настроек.
        
        Returns:
            Виджет вкладки общих настроек
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # -- Заголовок для Общих настроек --
        general_header_label = QLabel("Общие настройки")
        general_header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(general_header_label)

        # Группа общих настроек (без заголовка)
        general_group = QGroupBox("") 
        general_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        general_group.setMinimumHeight(250)
        general_layout = QFormLayout(general_group)
        general_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        general_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        general_layout.setVerticalSpacing(10)
        general_layout.setHorizontalSpacing(15)
        general_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Интервал обновления данных
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(500, 10000)
        self.update_interval_spin.setSingleStep(500)
        self.update_interval_spin.setSuffix(" мс")
        general_layout.addRow("Интервал обновления данных:", self.update_interval_spin)
        
        # Тема приложения
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Тёмная", "Системная"])
        general_layout.addRow("Тема оформления:", self.theme_combo)
        
        # Переключатель отображения спредов
        self.show_spreads_check = QCheckBox("Показывать спреды")
        general_layout.addRow("", self.show_spreads_check)
        
        # Добавляем группу в компоновщик вкладки
        layout.addWidget(general_group)
        layout.addSpacing(10) # Отступ после группы
        
        # -- Заголовок для Настроек интерфейса --
        ui_header_label = QLabel("Настройки интерфейса")
        ui_header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(ui_header_label)

        # Группа настроек интерфейса (без заголовка)
        ui_group = QGroupBox("")
        ui_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        ui_group.setMinimumHeight(150)
        ui_layout = QFormLayout(ui_group)
        ui_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        ui_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        ui_layout.setVerticalSpacing(10)
        ui_layout.setHorizontalSpacing(15)
        ui_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Размер шрифта
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setSuffix(" пт")
        ui_layout.addRow("Размер шрифта:", self.font_size_spin)
        
        # Шрифт
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Roboto", "Segoe UI", "Tahoma"])
        ui_layout.addRow("Шрифт:", self.font_combo)
        
        # Добавляем группу в компоновщик вкладки
        layout.addWidget(ui_group)
        layout.addSpacing(10)
        
        # -- Новая метка для заголовка спредов --
        spread_header_label = QLabel("Настройки спредов")
        spread_header_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        layout.addWidget(spread_header_label)

        # Группа настроек спредов (теперь без заголовка)
        spread_group = QGroupBox("")
        spread_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        spread_group.setMinimumHeight(150)
        # Используем QVBoxLayout вместо QFormLayout для большего контроля
        spread_layout = QVBoxLayout(spread_group)
        spread_layout.setContentsMargins(10, 10, 10, 10)
        spread_layout.setSpacing(8)

        # -- Строка Спред 1 --
        row1_layout = QHBoxLayout()
        self.spread1_name_edit = QLineEdit("Спред 1") 
        self.spread1_name_edit.setPlaceholderText("Название спреда 1")
        self.spread1_spin = QDoubleSpinBox()
        self.spread1_spin.setRange(0.00, 10.00)
        self.spread1_spin.setDecimals(2)
        self.spread1_spin.setSingleStep(0.1)
        self.spread1_spin.setSuffix(" %")
        self.spread1_spin.setMinimumWidth(80)
        row1_layout.addWidget(self.spread1_name_edit)
        row1_layout.addWidget(self.spread1_spin)
        spread_layout.addLayout(row1_layout)

        # -- Строка Спред 2 --
        row2_layout = QHBoxLayout()
        self.spread2_name_edit = QLineEdit("Спред 2") 
        self.spread2_name_edit.setPlaceholderText("Название спреда 2")
        self.spread2_spin = QDoubleSpinBox()
        self.spread2_spin.setRange(0.00, 10.00)
        self.spread2_spin.setDecimals(2)
        self.spread2_spin.setSingleStep(0.1)
        self.spread2_spin.setSuffix(" %")
        self.spread2_spin.setMinimumWidth(80)
        row2_layout.addWidget(self.spread2_name_edit)
        row2_layout.addWidget(self.spread2_spin)
        spread_layout.addLayout(row2_layout)

        # -- Строка Спред 3 --
        row3_layout = QHBoxLayout()
        self.spread3_name_edit = QLineEdit("Спред 3") 
        self.spread3_name_edit.setPlaceholderText("Название спреда 3")
        self.spread3_spin = QDoubleSpinBox()
        self.spread3_spin.setRange(0.00, 10.00)
        self.spread3_spin.setDecimals(2)
        self.spread3_spin.setSingleStep(0.1)
        self.spread3_spin.setSuffix(" %")
        self.spread3_spin.setMinimumWidth(80)
        row3_layout.addWidget(self.spread3_name_edit)
        row3_layout.addWidget(self.spread3_spin)
        spread_layout.addLayout(row3_layout)

        layout.addWidget(spread_group)
        
        return tab
    
    def _create_exchanges_tab(self) -> QWidget:
        """
        Создание вкладки настроек бирж.
        
        Returns:
            Виджет вкладки настроек бирж
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Создаем группу для каждой биржи
        for exchange_name in ["Binance", "Bybit", "CommEX", "Garantex"]:
            exchange_group = QGroupBox(exchange_name)
            exchange_layout = QFormLayout(exchange_group)
            
            # Переключатель активности биржи
            enabled_check = QCheckBox("Активна")
            exchange_layout.addRow("", enabled_check)
            
            # Поле ввода API URL
            api_url_edit = QLineEdit()
            exchange_layout.addRow("API URL:", api_url_edit)
            
            # Поле ввода WebSocket URL
            ws_url_edit = QLineEdit()
            exchange_layout.addRow("WebSocket URL:", ws_url_edit)
            
            # Сохраняем ссылки на виджеты
            self._exchange_widgets[exchange_name.lower()] = {
                "enabled": enabled_check,
                "api_url": api_url_edit,
                "ws_url": ws_url_edit
            }
            
            # Добавляем группу в компоновщик вкладки
            layout.addWidget(exchange_group)
        
        # Добавляем растягивающийся элемент внизу
        layout.addStretch()
        
        return tab
    
    def _create_crypto_tab(self) -> QWidget:
        """
        Создание вкладки настроек криптовалют.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Создаем группу для каждой криптовалюты
        for crypto_name in ["BTC", "ETH", "USDT"]:
            crypto_group = QGroupBox(crypto_name)
            crypto_layout = QFormLayout(crypto_group)
            
            # Комиссия (оставляем, если нужна индивидуальная комиссия на крипту)
            # Если комиссия общая, ее можно перенести на вкладку "Общие"
            commission_spin = QDoubleSpinBox()
            commission_spin.setRange(0.0, 5.0)
            commission_spin.setDecimals(2)
            commission_spin.setSingleStep(0.1)
            commission_spin.setSuffix("%")
            crypto_layout.addRow("Комиссия:", commission_spin)
            
            # Торговая комиссия (оставляем)
            trade_fee_spin = QDoubleSpinBox()
            trade_fee_spin.setRange(0.0, 2.0)
            trade_fee_spin.setDecimals(2)
            trade_fee_spin.setSingleStep(0.05)
            trade_fee_spin.setSuffix("%")
            crypto_layout.addRow("Торговая комиссия:", trade_fee_spin)
            
            layout.addWidget(crypto_group)
        
        layout.addStretch()
        return tab
    
    def _load_settings(self):
        """Загрузка настроек из QSettings."""
        # Общие настройки
        self.update_interval_spin.setValue(self.settings.value("general/update_interval", 1000, type=int))
        self.theme_combo.setCurrentText(self.settings.value("general/theme", "Светлая"))
        self.show_spreads_check.setChecked(self.settings.value("general/show_spreads", True, type=bool))
        
        # Настройки интерфейса
        self.font_size_spin.setValue(self.settings.value("ui/font_size", 10, type=int))
        self.font_combo.setCurrentText(self.settings.value("ui/font", "Segoe UI"))

        # Настройки спредов (загружаются с вкладки "Общие")
        self.spread1_name_edit.setText(self.settings.value("spreads/name1", "Спред 1", type=str))
        self.spread1_spin.setValue(self.settings.value("spreads/percent1", 0.50, type=float))
        
        self.spread2_name_edit.setText(self.settings.value("spreads/name2", "Спред 2", type=str))
        self.spread2_spin.setValue(self.settings.value("spreads/percent2", 1.00, type=float))
        
        self.spread3_name_edit.setText(self.settings.value("spreads/name3", "Спред 3", type=str))
        self.spread3_spin.setValue(self.settings.value("spreads/percent3", 1.50, type=float))

        # Настройки бирж
        for exchange_name, widgets in self._exchange_widgets.items():
            if exchange_name in ["binance", "bybit", "commex", "garantex"]:
                widgets["enabled"].setChecked(
                    self.settings.value(f"{exchange_name}/enabled", True, type=bool)
                )
                widgets["api_url"].setText(
                    self.settings.value(f"{exchange_name}/api_url", "")
                )
                widgets["ws_url"].setText(
                    self.settings.value(f"{exchange_name}/ws_url", "")
                )
    
    def _save_settings(self):
        """Сохранение текущих настроек в QSettings."""
        # Общие настройки
        self.settings.setValue("general/update_interval", self.update_interval_spin.value())
        self.settings.setValue("general/theme", self.theme_combo.currentText())
        self.settings.setValue("general/show_spreads", self.show_spreads_check.isChecked())
        
        # Настройки интерфейса
        self.settings.setValue("ui/font_size", self.font_size_spin.value())
        self.settings.setValue("ui/font", self.font_combo.currentText())

        # Настройки спредов (сохраняются с вкладки "Общие")
        self.settings.setValue("spreads/name1", self.spread1_name_edit.text())
        self.settings.setValue("spreads/percent1", self.spread1_spin.value())
        
        self.settings.setValue("spreads/name2", self.spread2_name_edit.text())
        self.settings.setValue("spreads/percent2", self.spread2_spin.value())
        
        self.settings.setValue("spreads/name3", self.spread3_name_edit.text())
        self.settings.setValue("spreads/percent3", self.spread3_spin.value())

        # Настройки бирж
        for exchange_name, widgets in self._exchange_widgets.items():
            if exchange_name in ["binance", "bybit", "commex", "garantex"]:
                self.settings.setValue(f"{exchange_name}/enabled", widgets["enabled"].isChecked())
                self.settings.setValue(f"{exchange_name}/api_url", widgets["api_url"].text())
                self.settings.setValue(f"{exchange_name}/ws_url", widgets["ws_url"].text())
        
        logger.info("Настройки сохранены")
    
    def _apply_settings(self):
        """Применение настроек."""
        # Просто вызываем _save_settings, так как логика сохранения уже там
        self._save_settings()
        logger.info("Настройки применены (через _save_settings)") 