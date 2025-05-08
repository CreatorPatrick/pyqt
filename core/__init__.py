"""
Основной функциональный пакет приложения.

Содержит базовые классы и функции, используемые во всем приложении.
"""
import logging

logger = logging.getLogger(__name__)

from core.utils import format_number, format_currency, format_percentage

class TaskManager:
    """
    Менеджер асинхронных задач.
    """
    def __init__(self):
        """Инициализация менеджера задач."""
        self.tasks = {}
    
    def cancel_all_tasks(self):
        """Отмена всех запущенных задач."""
        for task in self.tasks.values():
            if not task.done():
                task.cancel()
        self.tasks.clear()
        logger.info("All tasks cancelled")

task_manager = TaskManager() 