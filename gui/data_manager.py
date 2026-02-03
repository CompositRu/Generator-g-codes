'''
Управление данными приложения.

Содержит функции для загрузки и сохранения конфигурации из/в JSON файлы.
'''

import json
from tkinter import BooleanVar, messagebox
from os import rename as rename_file
from os.path import exists as is_existed
from utils.crossplatform_utils import get_resource_path


def is_opened_file(filename):
    """
    Проверяет, открыт ли файл в другой программе.

    Returns:
        True если файл заблокирован, False если свободен или не существует
    """
    if is_existed(filename):
        try:
            rename_file(filename, 'test.test')
            rename_file('test.test', filename)
            return False
        except OSError:
            return True
    return False


def recursion_saver(widget_dict):
    """
    Рекурсивно извлекает данные из словаря виджетов.

    Args:
        widget_dict: Словарь с виджетами (может быть вложенным)

    Returns:
        Словарь с данными из виджетов

    Raises:
        ValueError: Если значение не является числом там, где ожидается число
    """
    data_dict = {}
    for section, item in widget_dict.items():
        if isinstance(item, dict):
            data_dict[section] = recursion_saver(item)
        elif isinstance(item, BooleanVar):
            data_dict[section] = bool(item.get())
        else:
            if section != "Имя файла":
                # Код ниже работает одновременно и для Entry, и для IntVar
                try:
                    data_dict[section] = int(item.get())
                except ValueError:
                    try:
                        data_dict[section] = float(item.get())
                    except ValueError:
                        print(section, item)
                        messagebox.showerror('Смотри, что пишешь!',  f'Значение {item.get()} параметра {section}  не является числом')
                        raise ValueError
            else:
                data_dict[section] = item.get()
    return data_dict


def write_to_json_file(file_name, data_dict):
    """
    Записывает данные в JSON файл.

    Args:
        file_name: Путь к файлу
        data_dict: Словарь с данными для записи
    """
    if is_opened_file(file_name):
        return
    with open(file_name, 'w', encoding='utf-8-sig') as f:
        f.write(json.dumps(data_dict,
                            ensure_ascii=False,
                            indent=4))


def load_data_json():
    """
    Загружает данные из data.json.

    Returns:
        Словарь с данными конфигурации
    """
    with open(get_resource_path('data/data.json'), 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def load_heads_json():
    """
    Загружает данные из heads.json.

    Returns:
        Словарь с конфигурацией игольниц
    """
    with open(get_resource_path('data/heads.json'), 'r', encoding='utf-8-sig') as f:
        return json.load(f)
