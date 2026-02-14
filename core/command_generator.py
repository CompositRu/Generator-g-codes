"""
Генератор команд G-кода для станка игольной пробивки.

Содержит:
- CommandGenerator — класс для генерации команд послойно
"""

import logging
import random
from math import ceil as round_to_greater
from typing import Dict, Any, List

from .commands import MoveCommand, PauseCommand, RawCommand, Layer

logger = logging.getLogger(__name__)
from .formatter import PreheadParams
from .geometry import generate_offset_list, get_nx_ny, get_ordered_list_of_rows


def r(x):
    """Округление до 1 знака после запятой."""
    return round(x, 1)


class CommandGenerator:
    """
    Генерирует G-code команды, группируя их послойно.

    Responsibilities:
    - Разбор параметров из data_dict
    - Генерация команд перемещения для каждого слоя
    - Управление порядком обхода (rows, steps, offsets)
    """

    def __init__(self, data_dict: Dict[str, Any]):
        """
        Инициализирует генератор параметрами из data_dict.

        Args:
            data_dict: Словарь с параметрами генерации
        """
        self._data = data_dict
        self._parse_parameters()

    def _parse_parameters(self) -> None:
        """Извлекает и вычисляет все необходимые параметры."""
        d = self._data

        # Базовые параметры
        self.cell_size_x = d['Расстояние между иглами (мм)']['X']
        self.cell_size_y = d['Расстояние между иглами (мм)']['Y']
        self.num_pitch = d['Параметры паттерна']['Кол-во ударов']
        self.generate_nx_ny = d['Параметры паттерна']['Автоматическое определение формы паттерна']
        self.nx = d['Параметры паттерна']['nx']
        self.ny = d['Параметры паттерна']['ny']
        self.num_step_x = d['Количество шагов головы']['X']
        self.num_row_y = d['Количество шагов головы']['Y']
        self.frame_length_x = d['Габариты каркаса']['X']
        self.frame_length_y = d['Габариты каркаса']['Y']
        self.selected_type_frame_size = d['Задание размеров каркаса']

        # Параметры пробивки
        self.is_progressive_depth = d['Пробивка']['Пробивка с нарастанием глубины']
        self.initial_depth = d['Пробивка']['Начальная глубина удара (мм)']
        self.max_depth = d['Пробивка']['Глубина удара (мм)']

        # Слои
        self.amount_layers = d['Количество слоёв']
        self.amount_virtual_layers = d['Количество пустых слоёв']
        self.layer_thickness = d['Толщина слоя (мм)']
        self.dist_to_material = d['Расстояние от каркаса до головы перед ударом (мм)']

        # Голова
        self.head_name = d['Выбранная игольница (ИП игольница)']
        self.needles_x = d['Игольницы (ИП головы)'][self.head_name]['X']
        self.needles_y = d['Игольницы (ИП головы)'][self.head_name]['Y']

        # Позиция укладки
        self.layer_laying_position_x = d['Позиция при ручной укладки слоя']['X']
        self.layer_laying_position_y = d['Позиция при ручной укладки слоя']['Y']
        self.layer_laying_position_z = d['Позиция при ручной укладки слоя']['Z']
        self.pause = d['Позиция при ручной укладки слоя']['Пауза в конце слоя (сек)']
        self.sound_signal_duration = d['Позиция при ручной укладки слоя']['Звуковой сигнал (сек)']
        self.is_growing_z = d['Позиция при ручной укладки слоя']['Рост Z с каждым слоем']

        # Опции
        self.is_random_order = d['Случайный порядок ударов']
        self.is_random_offsets = d['Случайные смещения']
        self.is_rotation_direction = d['Чередование направлений прохода слоя']
        self.is_swap_xy = d['Смена осей X↔Y']
        self.coefficient_random_offsets = d['Коэффициент случайных смещений']
        self.speed_xy = d['Скорость (мм/мин)']['Движение осей X и Y']
        self.speed_z_insert = d['Скорость (мм/мин)']['Внедрение игл по Z']
        self.speed_z_extract = d['Скорость (мм/мин)']['Извлечение игл по Z']
        self.speed = self.speed_xy  # для совместимости с TimeEstimator
        self.acceleration = d['Ускорение осей станка (мм/с²)']
        self.order = d["Порядок прохождения рядов"]

        # Вычисляем параметры паттерна, если необходимо
        if self.generate_nx_ny:
            self.nx, self.ny = get_nx_ny(self.num_pitch)

        # Вспомогательные параметры
        self.head_width_x = self.cell_size_x * self.needles_x
        self.head_width_y = self.cell_size_y * self.needles_y
        self.frame_height = int(self.amount_layers * self.layer_thickness)

        # Определяем количество шагов головы, если каркас задан габаритами
        if self.selected_type_frame_size == 'По габаритам':
            self.num_step_x = round_to_greater(self.frame_length_x / self.head_width_x)
            self.num_row_y = round_to_greater(self.frame_length_y / self.head_width_y)

    def _move_cmd(self, x=None, y=None, z=None, f=None) -> MoveCommand:
        """
        Создаёт команду перемещения с учётом флага смены осей.

        Args:
            x: Координата X (или Y, если is_swap_xy=True)
            y: Координата Y (или X, если is_swap_xy=True)
            z: Координата Z
            f: Скорость подачи (мм/мин)

        Returns:
            MoveCommand с учётом смены осей
        """
        if self.is_swap_xy:
            return MoveCommand(x=y, y=x, z=z, f=f)
        return MoveCommand(x=x, y=y, z=z, f=f)

    def generate_layers(self) -> List[Layer]:
        """
        Генерирует все слои с командами.

        Returns:
            Список Layer объектов с командами
        """
        layers = []

        # Формируем паттерн пробивки
        offset_list = generate_offset_list(
            self.nx, self.ny, self.cell_size_x, self.cell_size_y
        )

        # Если выбран чекбокс "случайный порядок ударов", то перемешиваем
        if self.is_random_order:
            random.shuffle(offset_list)

        # Формируем список с номерами рядов в порядке их прохождения
        rows = get_ordered_list_of_rows(self.num_row_y, self.order)

        # Генерируем слои
        start_hit = 0
        finish_hit = self.num_pitch
        total_layers = self.amount_layers + self.amount_virtual_layers

        for layer_idx in range(total_layers):
            is_virtual = layer_idx >= self.amount_layers
            layer = self._generate_single_layer(
                layer_idx, is_virtual, offset_list, rows,
                start_hit, finish_hit
            )
            layers.append(layer)

            # Смещение координат ударов на новом слое
            if finish_hit < len(offset_list):
                start_hit += self.num_pitch
                finish_hit += self.num_pitch
            else:
                start_hit = 0
                finish_hit = self.num_pitch

        return layers

    def _generate_single_layer(self, layer_idx: int, is_virtual: bool,
                               offset_list: List, rows: List[int],
                               start_hit: int, finish_hit: int) -> Layer:
        """
        Генерирует команды для одного слоя.

        Args:
            layer_idx: Индекс слоя (0-based)
            is_virtual: True если виртуальный (холостой) слой
            offset_list: Список смещений паттерна
            rows: Порядок прохождения рядов
            start_hit: Начальный индекс в offset_list
            finish_hit: Конечный индекс в offset_list

        Returns:
            Layer с командами
        """
        commands = []

        # Вычисляем смещение по высоте
        z_offset = self.layer_thickness * layer_idx

        # Вычисляем глубину удара
        if self.is_progressive_depth:
            growing_depth = self.initial_depth + self.layer_thickness * layer_idx
            needle_depth = min(growing_depth, self.max_depth)
        else:
            needle_depth = self.max_depth

        # Вычисляем позицию Z для укладки слоя
        z_layer_position = (self.layer_laying_position_z + z_offset
                          if self.is_growing_z else self.layer_laying_position_z)

        # Выезд на позицию для укладки слоя
        commands.append(self._move_cmd(z=r(z_layer_position), f=self.speed_z_extract))
        commands.append(self._move_cmd(x=r(self.layer_laying_position_x),
                                       y=r(self.layer_laying_position_y),
                                       f=self.speed_xy))

        # Цикл рядов по Y
        for row in rows:
            y = self.head_width_y * row

            # Цикл шагов по Х
            step_range = list(range(self.num_step_x))
            if self.is_rotation_direction and (layer_idx + 1) % 2:
                step_range = list(reversed(step_range))

            for step in step_range:
                x = self.head_width_x * step

                # Цикл микрошагов внутри ячейки между иглами
                offset_range = offset_list[start_hit:finish_hit]
                if self.is_rotation_direction and (layer_idx + 1) % 2:
                    offset_range = list(reversed(offset_range))

                for offs_x, offs_y in offset_range:
                    current_x = x + offs_x
                    current_y = y + offs_y

                    # Если выбран чекбокс "случайные смещения"
                    if self.is_random_offsets:
                        current_x += self.coefficient_random_offsets * (random.random() - 0.5) * 2
                        current_y += self.coefficient_random_offsets * (random.random() - 0.5) * 2

                    commands.append(self._move_cmd(x=r(current_x), y=r(current_y),
                                                   f=self.speed_xy))
                    commands.append(self._move_cmd(z=r(z_offset - needle_depth),
                                                   f=self.speed_z_insert))
                    commands.append(self._move_cmd(z=r(self.dist_to_material + z_offset),
                                                   f=self.speed_z_extract))

        # Выезд на позицию для укладки слоя
        commands.append(self._move_cmd(z=r(z_layer_position), f=self.speed_z_extract))
        commands.append(self._move_cmd(x=r(self.layer_laying_position_x),
                                       y=r(self.layer_laying_position_y),
                                       f=self.speed_xy))

        # Звуковой сигнал и пауза
        pause_sec = self.pause
        signal_sec = self.sound_signal_duration

        if signal_sec > 0 and signal_sec > pause_sec:
            logger.warning(
                "Время звукового сигнала (%.1f сек) больше паузы в конце слоя (%.1f сек). "
                "Пауза увеличена до %.1f сек.",
                signal_sec, pause_sec, signal_sec
            )
            pause_sec = signal_sec

        if signal_sec > 0:
            commands.append(RawCommand(code="M3"))
            commands.append(PauseCommand(milliseconds=signal_sec * 1000))
            commands.append(RawCommand(code="M5"))
            remaining_pause = pause_sec - signal_sec
            if remaining_pause > 0:
                commands.append(PauseCommand(milliseconds=remaining_pause * 1000))
        else:
            commands.append(PauseCommand(milliseconds=pause_sec * 1000))

        return Layer(
            layer_number=layer_idx + 1,
            is_virtual=is_virtual,
            commands=commands
        )

    def get_prehead_params(self, work_time: str = "", layer_time: str = "") -> PreheadParams:
        """
        Возвращает параметры для записи заголовка файла.

        Args:
            work_time: Строка с временем работы файла на станке
            layer_time: Строка с временем работы над одним слоем

        Returns:
            PreheadParams с параметрами
        """
        return PreheadParams(
            head_name=self.head_name,
            needles_x=self.needles_x,
            needles_y=self.needles_y,
            frame_length_x=self.frame_length_x,
            frame_length_y=self.frame_length_y,
            num_step_x=self.num_step_x,
            num_row_y=self.num_row_y,
            frame_height=self.frame_height,
            amount_layers=self.amount_layers,
            amount_virtual_layers=self.amount_virtual_layers,
            num_pitch=self.num_pitch,
            cell_size_x=self.cell_size_x,
            cell_size_y=self.cell_size_y,
            nx=self.nx,
            ny=self.ny,
            is_random_offsets=self.is_random_offsets,
            coefficient_random_offsets=self.coefficient_random_offsets,
            is_frame_by_dimensions=(self.selected_type_frame_size == 'По габаритам'),
            work_time=work_time,
            layer_time=layer_time
        )
