'''
Валидация параметров перед генерацией G-кодов.

Содержит функции для проверки входных данных.
'''

from tkinter import messagebox
from core import check_dict_keys
from gui.data_manager import is_opened_file


def is_big_size_future_file(data_dict):
    """
    Проверяет, будет ли создан большой файл.

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        True если файл будет содержать более 500,000 ударов
    """
    l = data_dict['Количество слоёв']
    e = data_dict['Количество пустых слоёв']
    x = data_dict['Количество шагов головы']['X']
    y = data_dict['Количество шагов головы']['Y']
    n = data_dict['Параметры паттерна']['Кол-во ударов']
    hits = (l + e) * x * y * n
    if hits > 500_000:
        return True
    return False


def validate_generation_params(data_dict):
    """
    Проверяет все условия перед генерацией.

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        True если все проверки пройдены, False если есть ошибки
    """
    # Проверяем наличие всех ключей в json файле
    message = check_dict_keys(data_dict)
    if message != '':
        messagebox.showerror('Отсутствует параметр в json файле', message)
        return False

    # Проверяем файл
    if is_opened_file(data_dict["Имя файла"]):
        messagebox.showerror('Файл открыт в другой программе', f'Закройте файл {data_dict["Имя файла"]}.')
        return False

    # Проверяем размер будущего файла
    if is_big_size_future_file(data_dict):
        res = messagebox.askyesno('Создаётся большой файл',
            'Файл с g кодами содержит больше 500 000 ударов. Вы уверены, что хотите его создать?')
        return res

    return True
