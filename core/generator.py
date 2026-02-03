"""
Генератор G-кодов для станка игольной пробивки.

Содержит:
- generate_G_codes_file — главная функция генерации файла
"""

from typing import Dict, Any, Callable

from .command_generator import CommandGenerator
from .formatter import GCodeFormatter
from .file_utils import get_filename_path_and_create_directory_if_need
# from .time_estimator import TimeEstimator


def generate_G_codes_file(data_dict: Dict[str, Any],
                          display_percent_progress_func: Callable[[float], None]) -> None:
    """
    Генерирует G-code файл.

    Args:
        data_dict: Словарь с параметрами генерации
        display_percent_progress_func: Функция для отображения прогресса (0-100)
    """
    # Создаём генератор команд
    generator = CommandGenerator(data_dict)

    # Генерируем слои
    layers = generator.generate_layers()
    total_layers = generator.amount_layers + generator.amount_virtual_layers

    # Рассчитываем время работы
    # time_estimator = TimeEstimator(speed_mm_per_min=generator.speed)
    # time_estimate = time_estimator.estimate_by_one_layer(layers)
    # work_time_str = time_estimate.to_dhms()
    work_time_str = ""

    # Открываем файл и записываем
    path = get_filename_path_and_create_directory_if_need(data_dict)

    with open(path, 'w', encoding='utf-8') as gcode_file:
        formatter = GCodeFormatter(gcode_file, generator.amount_layers)

        # Записываем заголовок
        formatter.write_prehead(generator.get_prehead_params(work_time=work_time_str))
        formatter.write_speed(generator.speed)

        # Записываем слои
        for i, layer in enumerate(layers):
            formatter.write_layer(layer)
            # Отображаем процесс на progressbar
            display_percent_progress_func(i / total_layers * 100)
