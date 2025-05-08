"""
Основной модуль приложения.

Этот модуль является точкой входа в приложение.
"""
import sys
import logging
import os

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QSettings, Qt # Добавляем Qt для AlignmentFlag, если понадобится где-то еще
from PyQt5.QtGui import QColor, QPalette # Добавляем QPalette

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='a'
)

logger = logging.getLogger(__name__)

# Импорт конфигурации
from config import APP_SETTINGS
from ui.main_window import MainWindow

# --- УДАЛЯЕМ ИЛИ КОММЕНТИРУЕМ LIGHT_STYLE и DARK_STYLE --- #
# LIGHT_STYLE = """ ... """
# DARK_STYLE = """ ... """

def apply_application_theme(main_window: MainWindow):
    """Применяет атрибут темы к главному окну для CSS-стилизации."""
    settings = QSettings()
    theme_setting = settings.value("general/theme", "Светлая", type=str)
    app = QApplication.instance() # app может понадобиться для других вещей, но не для setStyleSheet здесь
    if not app or not main_window:
        logger.warning("QApplication instance or MainWindow not found. Cannot apply theme attribute.")
        return

    logger.info(f"Setting theme attribute for MainWindow based on setting: {theme_setting}")
    current_theme_prop = "light" # По умолчанию
    if theme_setting == "Тёмная":
        current_theme_prop = "dark"
    
    main_window.setProperty("theme", current_theme_prop)
    
    # Обновляем стиль, чтобы применились изменения из CSS по атрибуту
    style = main_window.style()
    if style:
        style.unpolish(main_window)
        style.polish(main_window)
        # Также для всех дочерних виджетов, если это необходимо
        for widget in main_window.findChildren(QWidget):
            style.unpolish(widget)
            style.polish(widget)

    logger.info(f"MainWindow 'theme' property set to: {current_theme_prop}")

    # Обновление палитры для InfoWidget (перенесено сюда для корректного порядка)
    # Этот код должен выполняться ПОСЛЕ того, как MainWindow создано и тема для него установлена.
    info_widget_instance = main_window.findChild(QWidget, "infoWidgetInstance") 
    if info_widget_instance:
        logger.info(f"Attempting to update palette for InfoWidget based on theme: {current_theme_prop}")
        palette = info_widget_instance.palette()
        if current_theme_prop == "dark":
            palette.setColor(QPalette.Window, QColor("#363636")) # Темный фон для InfoWidget
            palette.setColor(QPalette.WindowText, QColor("#e0e0e0")) # Светлый текст для InfoWidget
        else:
            palette.setColor(QPalette.Window, QColor("#f8f8f5")) # Светлый фон (стандартный)
            palette.setColor(QPalette.WindowText, QColor("#303030")) # Темный текст
        info_widget_instance.setPalette(palette)
        info_widget_instance.update() # Принудительное обновление виджета
        logger.info(f"Palette updated for InfoWidget.")
    else:
        logger.warning("infoWidgetInstance not found, cannot update its palette.")

def main():
    """
    Основная функция приложения.
    
    Returns:
        Код возврата приложения
    """
    try:
        logger.info("Application starting...")
        app = QApplication(sys.argv)
        
        app.setOrganizationName(APP_SETTINGS["organization"])
        app.setApplicationName(APP_SETTINGS["application"])
        
        # Загружаем custom.css ОДИН РАЗ. Он должен содержать все стили, включая для тем.
        if os.path.exists('custom.css'):
            with open('custom.css', 'r', encoding='utf-8') as f:
                styles = f.read()
                app.setStyleSheet(styles) # Этот стиль будет базовым
                logger.info("custom.css loaded and applied to application.")
        else:
            logger.warning("custom.css not found.")

        main_window = MainWindow() # Создаем главное окно
        
        # Применяем атрибут темы к главному окну ПОСЛЕ его создания
        # и ПОСЛЕ применения основного app.setStyleSheet
        try:
            apply_application_theme(main_window)
        except Exception as e:
            logger.error(f"Error applying theme attribute on startup: {e}", exc_info=True)

        main_window.show()
        return app.exec_()
        
    except Exception as e:
        logger.exception(f"Ошибка при запуске приложения: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 