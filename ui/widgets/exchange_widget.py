from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QColor


class ExchangeWidget(QFrame):
    """
    Виджет для отображения информации о бирже и её криптовалютах.
    """
    
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        """
        Инициализация виджета биржи.
        
        Args:
            title: Название биржи
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.title = title
        
        # Настройка внешнего вида
        self.setObjectName("exchangeWidget")
        self.setFrameShape(QFrame.NoFrame)
        
        # Добавляем эффект тени
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(200, 200, 200, 50))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Создаем и инициализируем интерфейс
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация интерфейса."""
        # Основной макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Заголовок биржи
        header = QLabel(self.title, self)
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # header.setStyleSheet("color: #303030;") # Убираем жесткий цвет, будет наследоваться из CSS
        main_layout.addWidget(header)
        
        # Создаем контейнер для содержимого
        content_container = QWidget(self)
        content_container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)
        
        # Добавляем контейнер содержимого в основной макет
        main_layout.addWidget(content_container) 