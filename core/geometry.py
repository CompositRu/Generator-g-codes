"""
Геометрические вычисления для генерации паттернов пробивки.

Содержит функции для:
- Генерации списка смещений паттерна
- Автоматического расчёта параметров nx, ny
- Определения порядка прохождения рядов
"""

import random
from math import ceil as round_to_greater, sqrt
from typing import List, Tuple


def generate_offset_list(nx: int, ny: int,
                         cell_size_x: float, cell_size_y: float) -> List[List[float]]:
    """
    Генерирует список смещений для паттерна пробивки.

    Создаёт змейкообразный паттерн точек в пределах элементарной ячейки.

    Args:
        nx: Количество точек по X в паттерне
        ny: Количество точек по Y в паттерне
        cell_size_x: Размер ячейки по X (расстояние между иглами, мм)
        cell_size_y: Размер ячейки по Y (мм)

    Returns:
        Список [x, y] смещений для каждой точки паттерна
    """
    offset_x = cell_size_x / nx
    offset_y = cell_size_y / ny
    snake_step = 1.5 * offset_y  # коэффициент 1.5 для змейки
    offset_list = []
    for j in range(ny):
        for i in range(nx):
            x = offset_x * i
            y = offset_y * j
            y = y + snake_step if i % 2 != 0 else y
            offset_list.append([x, y])
    return offset_list


def get_result_offset_list(nx: int, ny: int,
                           cell_size_x: float, cell_size_y: float,
                           is_random_offsets: bool,
                           coefficient_random_offsets: float,
                           is_random_order: bool) -> List[List[float]]:
    """
    Генерирует итоговый список смещений с учётом случайности.

    Args:
        nx: Количество точек по X в паттерне
        ny: Количество точек по Y в паттерне
        cell_size_x: Размер ячейки по X (мм)
        cell_size_y: Размер ячейки по Y (мм)
        is_random_offsets: Добавлять случайные смещения к координатам
        coefficient_random_offsets: Максимальная величина случайного смещения (мм)
        is_random_order: Перемешать порядок ударов

    Returns:
        Список смещений паттерна
    """
    offset_list = generate_offset_list(nx, ny, cell_size_x, cell_size_y)

    # Если выбран чекбокс "случайный порядок ударов", то перемешиваем список координат ударов
    if is_random_order:
        random.shuffle(offset_list)

    # Добавляем случайные смещения
    if is_random_offsets:
        for p in offset_list:
            p[0] += coefficient_random_offsets * (random.random() - 0.5) * 2
            p[1] += coefficient_random_offsets * (random.random() - 0.5) * 2

    return offset_list


def get_nx_ny(num_pitch: int) -> Tuple[int, int]:
    """
    Подбирает оптимальные nx и ny для заданного количества ударов.

    Алгоритм предполагает, что через (nx * ny) / num_pitch слоёв
    мы начинаем бить в те же точки.

    Критерии выбора:
    - nx * ny кратно num_pitch (чтобы слои были равномерными)
    - Отношение nx/ny близко к 2/sqrt(3) для равносторонних треугольников

    Args:
        num_pitch: Количество ударов за один проход

    Returns:
        Кортеж (nx, ny) оптимальных параметров
    """
    def get_pairs(N):
        return [(x, int(N / x)) for x in range(1, N) if N % x == 0]

    # Коэффициенты 5, 6, 8, 10, 12 взяты на основании практики
    gp = lambda n: get_pairs(n * num_pitch)
    pairs = gp(5) + gp(6) + gp(8) + gp(10) + gp(12)

    # Сортируем по приближению к идеальному соотношению
    # k = sqrt(3) / 2 для равносторонних треугольников
    k = sqrt(3) / 2
    pairs.sort(key=lambda pair: abs(pair[0] / pair[1] - 1 / k))
    return pairs[0]


def check_nums_x_y(nx: int, ny: int, num_pitch: int) -> bool:
    """
    Проверяет, что nx*ny не кратно num_pitch.

    Если nx * ny не кратно num_pitch, то каждые несколько слоёв
    будет идти слой с неполным количеством ударов.

    Args:
        nx: Количество точек по X
        ny: Количество точек по Y
        num_pitch: Количество ударов за проход

    Returns:
        True если есть потенциальная проблема (не кратно)
    """
    return (nx * ny) % num_pitch != 0


def check_nums_x_y_from_dict(data_dict: dict) -> bool:
    """
    Проверяет кратность nx*ny и num_pitch из словаря параметров.

    Обёртка для обратной совместимости с существующим API.

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        True если есть потенциальная проблема
    """
    nx = data_dict['Параметры паттерна']['nx']
    ny = data_dict['Параметры паттерна']['ny']
    num_pitch = data_dict['Параметры паттерна']['Кол-во ударов']
    return check_nums_x_y(nx, ny, num_pitch)


def get_ordered_list_of_rows(num_row_y: int, order: str) -> List[int]:
    """
    Возвращает список номеров рядов в заданном порядке прохождения.

    Args:
        num_row_y: Количество рядов
        order: Тип порядка:
            - 'По очереди' — 0, 1, 2, 3, ...
            - 'Сначала чётные' — 1, 3, 5, ..., 0, 2, 4, ...
            - 'Сначала нечётные' — 0, 2, 4, ..., 1, 3, 5, ...
            - 'Из центра' — из центра к краям
            - 'В центр' — от краёв к центру

    Returns:
        Список индексов рядов в порядке прохождения

    Raises:
        KeyError: Если передан неизвестный тип порядка
    """
    rows = list(range(num_row_y))

    if order == 'По очереди':
        pass
    elif order == 'Сначала чётные':
        rows = rows[1::2] + rows[::2]
    elif order == 'Сначала нечётные':
        rows = rows[::2] + rows[1::2]
    elif order == 'Из центра':
        center = (len(rows) - 1) // 2
        rows = rows[center::-1] + rows[center + 1:]
    elif order == 'В центр':
        center = (len(rows) - 1) // 2
        rows = rows[:center] + rows[:center - 1:-1]
    else:
        raise KeyError('Для данного порядка не написан алгоритм прохождения рядов')

    return rows


def calculate_head_dimensions(cell_size_x: float, cell_size_y: float,
                              needles_x: int, needles_y: int) -> Tuple[float, float]:
    """
    Вычисляет размеры рабочей области головы в мм.

    Args:
        cell_size_x: Расстояние между иглами по X (мм)
        cell_size_y: Расстояние между иглами по Y (мм)
        needles_x: Количество игл по X
        needles_y: Количество игл по Y

    Returns:
        Кортеж (ширина_по_X, ширина_по_Y) в мм
    """
    return cell_size_x * needles_x, cell_size_y * needles_y


def calculate_steps_from_frame(frame_x: float, frame_y: float,
                               head_width_x: float, head_width_y: float) -> Tuple[int, int]:
    """
    Вычисляет количество шагов головы по габаритам каркаса.

    Args:
        frame_x: Длина каркаса по X (мм)
        frame_y: Длина каркаса по Y (мм)
        head_width_x: Ширина головы по X (мм)
        head_width_y: Ширина головы по Y (мм)

    Returns:
        Кортеж (шаги_по_X, шаги_по_Y)
    """
    return round_to_greater(frame_x / head_width_x), round_to_greater(frame_y / head_width_y)
