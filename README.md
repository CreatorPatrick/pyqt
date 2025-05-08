# Rate App

Приложение для мониторинга цен на криптовалютных биржах с удобным пользовательским интерфейсом.

## Особенности

- Мониторинг цен криптовалют в реальном времени
- Поддержка нескольких бирж (Bybit, Binance, CommEX, Garantex)
- Расчет спредов для трейдинга
- Пользовательские настройки для каждой биржи и криптовалюты
- Современный и настраиваемый пользовательский интерфейс

## Требования

- Python 3.9+
- PyQt5
- Дополнительные зависимости перечислены в `requirements.txt`

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/rate_app.git
cd rate_app
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

## Структура проекта

```
rate_app/
├── config/                     # Конфигурация приложения
│   ├── __init__.py
│   └── app_config.py
├── core/                       # Ядро приложения
│   ├── __init__.py
│   ├── models.py               # Модели данных
│   ├── exceptions.py           # Пользовательские исключения
│   └── utils.py                # Вспомогательные функции
├── exchanges/                  # Коннекторы к биржам
│   ├── __init__.py
│   ├── base.py                 # Базовый класс коннектора
│   ├── bybit/                  # Модуль Bybit
│   ├── binance/                # Модуль Binance
│   └── ...
├── ui/                         # UI компоненты
│   ├── __init__.py
│   ├── widgets/                # Пользовательские виджеты
│   ├── dialogs/                # Диалоговые окна
│   └── main_window.py          # Главное окно приложения
├── main.py                     # Точка входа в приложение
├── requirements.txt            # Зависимости
└── README.md                   # Документация
```

## Лицензия

MIT 