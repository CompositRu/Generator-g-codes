#!/usr/bin/env python3
'''
Точка входа для генератора G-кодов.

Запускает GUI приложение.
'''

import sys
from tkinter import Tk, messagebox
from gui import GeneratorApp
from utils.crossplatform_utils import get_resource_path


def main():
    """Главная функция приложения."""
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
