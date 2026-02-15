#!/usr/bin/env python3
'''
Точка входа для генератора G-кодов.

Запускает GUI приложение.
'''

import sys
import logging
from tkinter import Tk, messagebox
from gui import GeneratorApp
from utils.crossplatform_utils import get_resource_path


def setup_logging():
    """Настраивает логирование для приложения."""
    # Создаём логгер
    logger = logging.getLogger()

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def main():
    """Главная функция приложения."""
    # Настраиваем логирование
    setup_logging()

    window = Tk()
    window.title("Генератор G кодов для ИП станка v.1.12.0")

    try:
        # На linux системах tkinter не отображает иконку в title bar окна
        window.iconbitmap(get_resource_path('symbol.ico'))
    except Exception as e:
        print(f"Ошибка загрузки иконки: {e}")

    try:
        app = GeneratorApp(window)
        app.run()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
