"""
Расчёт времени выполнения G-code программы.

Учитывает:
- Ускорение и торможение (трапецеидальный/треугольный профиль скорости)
- Паузы G4
- Оптимизацию: время_слоя × количество_слоёв
"""

import math
from typing import List
from dataclasses import dataclass

from .commands import GCodeCommand, Layer, MoveCommand, PauseCommand


# Ускорение для линейных осей (мм/с²)
# Значение по умолчанию, можно переопределить при создании TimeEstimator
ACCEL_LINEAR_DEFAULT = 300.0


def _time_for_move(distance: float, velocity: float, acceleration: float) -> float:
    """
    Расчёт времени перемещения с учётом ускорения.

    Использует трапецеидальный или треугольный профиль скорости
    в зависимости от расстояния.

    Args:
        distance: Расстояние в мм
        velocity: Максимальная скорость в мм/с
        acceleration: Ускорение в мм/с²

    Returns:
        Время перемещения в секундах
    """
    if distance <= 0 or velocity <= 0 or acceleration <= 0:
        return 0.0

    # Расстояние разгона/торможения до максимальной скорости
    d_acc = (velocity * velocity) / acceleration

    if distance >= d_acc:
        # Трапецеидальный профиль скорости:
        # разгон + движение на макс. скорости + торможение
        t_acc = velocity / acceleration
        return 2.0 * t_acc + (distance - d_acc) / velocity
    else:
        # Треугольный профиль скорости:
        # не успеваем разогнаться до макс. скорости
        return 2.0 * math.sqrt(distance / acceleration)


def _seconds_to_dhms(seconds: float) -> str:
    """
    Конвертация секунд в формат 'дни часы:минуты:секунды'.

    Args:
        seconds: Время в секундах

    Returns:
        Строка в формате "HH:MM:SS" или "N д HH:MM:SS"
    """
    s = int(round(seconds))
    days, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if days:
        return f"{days} д {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class TimeEstimate:
    """
    Результат расчёта времени выполнения.

    Attributes:
        total_seconds: Общее время в секундах
        layer_seconds: Среднее время одного слоя в секундах
        movement_seconds: Время на перемещения (без пауз)
        pause_seconds: Время пауз
        total_distance_mm: Общее расстояние перемещений в мм
    """
    total_seconds: float
    layer_seconds: float
    movement_seconds: float
    pause_seconds: float
    total_distance_mm: float

    @property
    def total_minutes(self) -> float:
        """Общее время в минутах."""
        return self.total_seconds / 60

    @property
    def total_hours(self) -> float:
        """Общее время в часах."""
        return self.total_seconds / 3600

    def to_dhms(self) -> str:
        """
        Форматирует время в читаемую строку.

        Returns:
            Строка вида "HH:MM:SS" или "N д HH:MM:SS"
        """
        return _seconds_to_dhms(self.total_seconds)

    def __str__(self) -> str:
        return self.to_dhms()


class TimeEstimator:
    """
    Рассчитывает время выполнения G-code программы.

    Предположения:
    - 3-осевой станок с линейными осями
    - Все оси имеют одинаковую максимальную скорость и ускорение
    - Время на каждом слое примерно одинаковое

    Оптимизация:
        total_time = layer_time × (amount_layers + amount_virtual_layers)
    """

    def __init__(self, speed_mm_per_min: float,
                 acceleration: float = ACCEL_LINEAR_DEFAULT):
        """
        Args:
            speed_mm_per_min: Скорость перемещения в мм/мин (параметр F)
            acceleration: Ускорение в мм/с² (по умолчанию 300)
        """
        self._speed_mm_per_min = speed_mm_per_min
        self._speed_mm_per_sec = speed_mm_per_min / 60.0
        self._acceleration = acceleration

    def estimate_layer(self, commands: List[GCodeCommand]) -> TimeEstimate:
        """
        Оценивает время выполнения одного слоя.

        Args:
            commands: Список команд слоя

        Returns:
            TimeEstimate с оценкой времени
        """
        total_time = 0.0
        total_pause_ms = 0.0
        total_distance = 0.0

        # Текущая позиция (начинаем с нуля)
        current_x = 0.0
        current_y = 0.0
        current_z = 0.0

        for cmd in commands:
            if isinstance(cmd, MoveCommand):
                # Вычисляем новую позицию
                new_x = cmd.x if cmd.x is not None else current_x
                new_y = cmd.y if cmd.y is not None else current_y
                new_z = cmd.z if cmd.z is not None else current_z

                # Вычисляем расстояние
                dx = new_x - current_x
                dy = new_y - current_y
                dz = new_z - current_z
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)

                if distance > 0:
                    total_distance += distance
                    # Используем скорость из команды, если задана
                    if cmd.f is not None:
                        speed = cmd.f / 60.0
                    else:
                        speed = self._speed_mm_per_sec
                    move_time = _time_for_move(distance, speed,
                                               self._acceleration)
                    total_time += move_time

                # Обновляем текущую позицию
                current_x = new_x
                current_y = new_y
                current_z = new_z

            elif isinstance(cmd, PauseCommand):
                total_pause_ms += cmd.milliseconds

        pause_seconds = total_pause_ms / 1000.0
        movement_seconds = total_time
        total_time += pause_seconds

        return TimeEstimate(
            total_seconds=total_time,
            layer_seconds=total_time,
            movement_seconds=movement_seconds,
            pause_seconds=pause_seconds,
            total_distance_mm=total_distance
        )

    def estimate_total(self, layer_commands: List[GCodeCommand],
                       total_layers: int) -> TimeEstimate:
        """
        Оценивает общее время выполнения программы.

        Использует упрощённую формулу: время_слоя × количество_слоёв.
        Это работает, т.к. время на каждом слое практически одинаковое.

        Args:
            layer_commands: Команды одного типичного слоя
            total_layers: Общее количество слоёв (включая виртуальные)

        Returns:
            TimeEstimate с общей оценкой времени
        """
        layer_estimate = self.estimate_layer(layer_commands)

        return TimeEstimate(
            total_seconds=layer_estimate.total_seconds * total_layers,
            layer_seconds=layer_estimate.layer_seconds,
            movement_seconds=layer_estimate.movement_seconds * total_layers,
            pause_seconds=layer_estimate.pause_seconds * total_layers,
            total_distance_mm=layer_estimate.total_distance_mm * total_layers
        )

    def estimate_by_one_layer(self, layers: List[Layer]) -> TimeEstimate:
        """
        Оценивает общее время выполнения программы на основе одного слоя.

        Вычисляет время для первого реального слоя и умножает на общее
        количество слоёв (реальных + виртуальных). Это более эффективный
        метод, чем обработка всех слоёв по отдельности.

        Args:
            layers: Список объектов Layer

        Returns:
            TimeEstimate с общей оценкой
        """
        if not layers:
            return TimeEstimate(0, 0, 0, 0, 0)

        # Берем первый слой для расчета
        first_layer = layers[0]
        total_layers = len(layers)

        # Рассчитываем время для одного слоя
        layer_estimate = self.estimate_layer(first_layer.commands)

        # Умножаем на количество всех слоёв
        return TimeEstimate(
            total_seconds=layer_estimate.total_seconds * total_layers,
            layer_seconds=layer_estimate.layer_seconds,
            movement_seconds=layer_estimate.movement_seconds * total_layers,
            pause_seconds=layer_estimate.pause_seconds * total_layers,
            total_distance_mm=layer_estimate.total_distance_mm * total_layers
        )

    def estimate_from_layers(self, layers: List[Layer]) -> TimeEstimate:
        """
        Оценивает время по списку слоёв.

        УСТАРЕЛО: Используйте estimate_by_one_layer() для лучшей производительности.

        Более точный метод — суммирует время каждого слоя.
        Полезно если слои различаются (например, разная глубина пробивки).

        Args:
            layers: Список объектов Layer

        Returns:
            TimeEstimate с общей оценкой
        """
        if not layers:
            return TimeEstimate(0, 0, 0, 0, 0)

        total_seconds = 0.0
        total_movement = 0.0
        total_pause = 0.0
        total_distance = 0.0

        for layer in layers:
            layer_est = self.estimate_layer(layer.commands)
            total_seconds += layer_est.total_seconds
            total_movement += layer_est.movement_seconds
            total_pause += layer_est.pause_seconds
            total_distance += layer_est.total_distance_mm

        layer_avg = total_seconds / len(layers)

        return TimeEstimate(
            total_seconds=total_seconds,
            layer_seconds=layer_avg,
            movement_seconds=total_movement,
            pause_seconds=total_pause,
            total_distance_mm=total_distance
        )
