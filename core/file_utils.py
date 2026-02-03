"""
Утилиты для работы с файлами и путями.

Содержит функции для:
- Генерации имени выходного файла
- Создания директорий
- Формирования информационных сообщений
"""

import os
from typing import Dict, Any
from math import ceil as round_to_greater

from utils.crossplatform_utils import get_desktop_path


def get_filename(data_dict: Dict[str, Any]) -> str:
    """
    Генерирует имя файла на основе параметров.

    Формат автоматического имени:
    '{длина_X}x{длина_Y}x{высота} {кол-во_ударов} ударов {имя_головы}.tap'

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        Имя файла с расширением .tap
    """
    is_automatic_name = data_dict["Автоматическая генерация имени файла"]

    if not is_automatic_name:
        return data_dict["Имя файла"]

    head_name = data_dict['Выбранная игольница (ИП игольница)']
    frame_length_x = data_dict['Габариты каркаса']['X']
    frame_length_y = data_dict['Габариты каркаса']['Y']
    selected_type_frame_size = data_dict['Задание размеров каркаса']
    amount_layers = data_dict['Количество слоёв']
    layer_thickness = data_dict['Толщина слоя (мм)']
    num_pitch = data_dict['Параметры паттерна']['Кол-во ударов']

    frame_height = int(amount_layers * layer_thickness)

    if selected_type_frame_size == 'По шагам головы':
        cell_size_x = data_dict['Расстояние между иглами (мм)']['X']
        cell_size_y = data_dict['Расстояние между иглами (мм)']['Y']
        needles_x = data_dict['Игольницы (ИП головы)'][head_name]['X']
        needles_y = data_dict['Игольницы (ИП головы)'][head_name]['Y']
        num_step_x = data_dict['Количество шагов головы']['X']
        num_row_y = data_dict['Количество шагов головы']['Y']

        head_width_x = cell_size_x * needles_x
        head_width_y = cell_size_y * needles_y
        frame_length_x = num_step_x * head_width_x
        frame_length_y = num_row_y * head_width_y

    return f'{frame_length_x}x{frame_length_y}x{frame_height} {num_pitch} ударов {head_name}.tap'


def get_filename_path_and_create_directory_if_need(data_dict: Dict[str, Any]) -> str:
    """
    Создаёт полный путь к файлу и директорию если нужно.

    Файлы сохраняются в папку с именем головы на рабочем столе
    (или в текущей директории, если отключено сохранение на рабочий стол).

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        Полный путь к файлу
    """
    on_the_desktop = data_dict["Создание файла на рабочем столе"]
    head_name = data_dict['Выбранная игольница (ИП игольница)']
    path_desktop = str(get_desktop_path()) if on_the_desktop else ''
    path_head = os.path.join(path_desktop, head_name)
    filename = get_filename(data_dict)

    if not os.path.exists(path_head):
        os.mkdir(path_head)

    path = os.path.join(path_desktop, head_name, filename)
    print(path)
    return path


def get_message(data_dict: Dict[str, Any]) -> str:
    """
    Генерирует информационное сообщение о параметрах генерации.

    Показывает свесы и количество шагов при задании каркаса по габаритам.

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        Информационное сообщение или пустая строка
    """
    cell_size_x = data_dict['Расстояние между иглами (мм)']['X']
    cell_size_y = data_dict['Расстояние между иглами (мм)']['Y']
    head_name = data_dict['Выбранная игольница (ИП игольница)']
    needles_x = data_dict['Игольницы (ИП головы)'][head_name]['X']
    needles_y = data_dict['Игольницы (ИП головы)'][head_name]['Y']
    frame_length_x = data_dict['Габариты каркаса']['X']
    frame_length_y = data_dict['Габариты каркаса']['Y']
    selected_type_frame_size = data_dict['Задание размеров каркаса']
    num_step_x = data_dict['Количество шагов головы']['X']
    num_row_y = data_dict['Количество шагов головы']['Y']

    head_width_x = cell_size_x * needles_x
    head_width_y = cell_size_y * needles_y

    if selected_type_frame_size == 'По габаритам':
        num_step_x = round_to_greater(frame_length_x / head_width_x)
        num_row_y = round_to_greater(frame_length_y / head_width_y)

    overhangs_x = (num_step_x * head_width_x - frame_length_x) / 2
    overhangs_y = (num_row_y * head_width_y - frame_length_y) / 2

    message = ''
    if selected_type_frame_size == 'По габаритам':
        message = (
            f'Свесы по Х: {overhangs_x}\n'
            f'Свесы по Y: {overhangs_y}\n\n'
            f'Количество шагов по Х: {num_step_x}\n'
            f'Количество шагов по Y: {num_row_y}\n'
        )
    return message
