"""
Форматирование и запись G-code файлов.

Содержит:
- PreheadParams — структура параметров для заголовка файла
- GCodeFormatter — класс для записи команд в файл
"""

from typing import TextIO, Any, List
from dataclasses import dataclass
from .commands import GCodeCommand, Layer


@dataclass
class PreheadParams:
    """
    Параметры для записи заголовка (prehead) файла.

    Все параметры, которые выводятся в комментариях в начале файла.
    """
    head_name: str
    needles_x: int
    needles_y: int
    frame_length_x: float
    frame_length_y: float
    num_step_x: int
    num_row_y: int
    frame_height: int
    amount_layers: int
    num_pitch: int
    cell_size_x: float
    cell_size_y: float
    nx: int
    ny: int
    is_random_offsets: bool
    coefficient_random_offsets: float
    is_frame_by_dimensions: bool  # True = 'По габаритам', False = 'По шагам'
    work_time: str = ""  # Время работы файла на станке


class GCodeFormatter:
    """
    Форматирует и записывает G-code команды в файл.

    Отвечает за:
    - Форматирование prehead (заголовка с параметрами)
    - Запись команд с комментариями номеров слоёв
    - Форматирование отдельных команд
    """

    FIELD_WIDTH_NORMAL = 20
    FIELD_WIDTH_EXTENDED = 35
    COMMAND_WIDTH = 16

    def __init__(self, file_handle: TextIO, total_layers: int):
        """
        Args:
            file_handle: Открытый файл для записи
            total_layers: Общее количество реальных слоёв (для комментариев)
        """
        self._file = file_handle
        self._total_layers = total_layers

    def write_prehead(self, params: PreheadParams) -> None:
        """
        Записывает заголовок файла с параметрами.

        Args:
            params: Структура с параметрами для заголовка
        """
        w = self.FIELD_WIDTH_NORMAL

        self._write_empty_line()
        self._write_info('ИП голова', params.head_name, w)
        self._write_empty_line()
        if params.work_time:
            self._write_info('Время работы', params.work_time, w)
            self._write_empty_line()
        self._write_info('Иглы по Х', params.needles_x, w)
        self._write_info('Иглы по Y', params.needles_y, w)
        self._write_empty_line()

        if params.is_frame_by_dimensions:
            self._write_info('Длина каркаса по X', params.frame_length_x, w)
            self._write_info('Длина каркаса по Y', params.frame_length_y, w)
        else:
            self._write_info('Шаги по X', params.num_step_x, w)
            self._write_info('Шаги по Y', params.num_row_y, w)

        self._write_info('Высота каркаса по Z', int(params.frame_height), w)
        self._write_empty_line()
        self._write_info('Слои', params.amount_layers, w)
        self._write_empty_line()

        # Расширенное форматирование для длинных названий
        w = self.FIELD_WIDTH_EXTENDED
        hits_per_layer = params.num_pitch * params.num_step_x * params.num_row_y
        self._write_info('Количество ударов на 1 слой', hits_per_layer, w)
        self._write_info("Количество слоёв для 50'000 ударов",
                        50000 // hits_per_layer if hits_per_layer > 0 else 0, w)
        self._write_empty_line()

        # Плотность пробивки
        density = params.num_pitch / params.cell_size_x / params.cell_size_y * 100
        self._write_info('Плотность пробивки (уд/кв.см)', density, w)
        self._write_info('Количество ударов в элементарную ячейку', f'{params.num_pitch}', w)
        self._write_empty_line()
        self._write_info('Параметры паттерна nx, ny', f'{params.nx}, {params.ny}', w)

        if params.is_random_offsets:
            self._file.write(
                f'; Есть смещения перед каждым ударом на случайную величину '
                f'от 0 до {params.coefficient_random_offsets} мм вдоль Х и Y в любом направлении\n'
            )

        self._write_empty_line()
        clarification = "c погрешностью на случайные смещения" if params.is_random_offsets else ""
        repeat_layers = int(params.nx * params.ny / params.num_pitch)
        self._file.write(f'; Через каждые {repeat_layers} слоёв бьём в теже точки {clarification}\n')
        self._write_empty_line()

    def write_speed(self, speed: float) -> None:
        """
        Записывает команду установки скорости.

        Args:
            speed: Скорость в мм/мин
        """
        self._file.write(f'F {speed:.1f}\n')

    def write_layer_header(self, layer_number: int, is_virtual: bool) -> None:
        """
        Записывает заголовок слоя (комментарий с номером).

        Args:
            layer_number: Номер слоя (начиная с 1)
            is_virtual: True если это виртуальный (холостой) слой
        """
        layer_type = 'layer (holostoy)' if is_virtual else 'layer'
        self._file.write(f";\n; {'<' * 10} [{layer_number}] {layer_type} {'>' * 10}\n;\n")

    def write_command(self, command: GCodeCommand, layer_number: int) -> None:
        """
        Записывает одну команду с комментарием номера слоя.

        Args:
            command: Команда для записи
            layer_number: Номер текущего слоя (для комментария)
        """
        cmd_str = command.to_string()
        comment = f';{layer_number}/{self._total_layers}\n'
        self._file.write(f'{cmd_str:{self.COMMAND_WIDTH}}{comment}')

    def write_layer(self, layer: Layer) -> None:
        """
        Записывает все команды слоя с заголовком.

        Args:
            layer: Объект Layer с командами
        """
        self.write_layer_header(layer.layer_number, layer.is_virtual)
        for cmd in layer.commands:
            self.write_command(cmd, layer.layer_number)

    def _write_empty_line(self) -> None:
        """Записывает пустую строку комментария."""
        self._file.write(';\n')

    def _write_info(self, name: str, value: Any, width: int) -> None:
        """
        Записывает строку информации в формате '; name: value'.

        Args:
            name: Название параметра
            value: Значение параметра
            width: Ширина поля для выравнивания
        """
        self._file.write(f'; {name:{width}}: {value}\n')
