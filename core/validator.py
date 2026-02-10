"""
Валидация входных данных для генератора G-кодов.

Проверяет наличие всех необходимых параметров в словаре конфигурации.
"""

from typing import Dict, Any


def check_dict_keys(data_dict: Dict[str, Any]) -> str:
    """
    Проверяет наличие всех необходимых ключей в словаре конфигурации.

    Args:
        data_dict: Словарь с параметрами генерации

    Returns:
        Пустая строка если всё ОК, иначе имя отсутствующего параметра
    """
    base_list = [
        "Количество слоёв",
        "Количество слоёв",
        "Количество пустых слоёв",
        "Толщина слоя (мм)",
        "Пробивка",
        "Расстояние от каркаса до головы перед ударом (мм)",
        "Скорость (мм/мин)",
        "Параметры паттерна",
        "Количество шагов головы",
        "Позиция при ручной укладки слоя",
        "Расстояние между иглами (мм)",
        "Случайный порядок ударов",
        "Случайные смещения",
        "Коэффициент случайных смещений",
        "Чередование направлений прохода слоя",
        "Автоматическая генерация имени файла"
    ]
    heads_list = ["Игольницы (ИП головы)", "Выбранная игольница (ИП игольница)"]
    pattern_list = ['Кол-во ударов']
    probivka_list = ['Пробивка с нарастанием глубины', 'Начальная глубина удара (мм)', 'Глубина удара (мм)']
    xy_list = ['X', 'Y']
    position_list = ['X', 'Y', 'Z', 'Пауза в конце слоя (сек)', 'Рост Z с каждым слоем']
    head_parameters_list = ['X', 'Y', 'path']

    for item in base_list:
        if item not in data_dict:
            return item

    for item in pattern_list:
        if item not in data_dict["Параметры паттерна"]:
            return item + ' в ' + "Параметры паттерна"

    for item in probivka_list:
        if item not in data_dict["Пробивка"]:
            return item + ' в ' + "Пробивка"

    for item in xy_list:
        if item not in data_dict["Количество шагов головы"]:
            return item + ' в ' + "Количество шагов головы"

    for item in position_list:
        if item not in data_dict["Позиция при ручной укладки слоя"]:
            return item + ' в ' + "Позиция при ручной укладки слоя"

    for item in xy_list:
        if item not in data_dict["Расстояние между иглами (мм)"]:
            return item + ' в ' + "Расстояние между иглами (мм)"

    for item in heads_list:
        if item not in data_dict:
            return item

    head_name = data_dict["Выбранная игольница (ИП игольница)"]
    for item in head_parameters_list:
        if item not in data_dict["Игольницы (ИП головы)"][head_name]:
            return item + ' в ' + "Игольницы (ИП головы)"

    return ''
