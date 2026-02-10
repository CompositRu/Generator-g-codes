"""
Классы G-code команд для генератора.

Содержит типизированные команды:
- MoveCommand (G1) — линейное перемещение
- PauseCommand (G4) — пауза
- SetSpeedCommand (F) — установка скорости
- Layer — группа команд для одного слоя
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List


class CommandType(Enum):
    """Типы G-code команд."""
    MOVE = "G1"       # Линейное перемещение
    PAUSE = "G4"      # Пауза
    SET_SPEED = "F"   # Установка скорости


@dataclass(frozen=True)
class GCodeCommand:
    """Базовый класс G-code команды."""
    command_type: CommandType

    def to_string(self) -> str:
        """Преобразует команду в строку G-code."""
        raise NotImplementedError


@dataclass(frozen=True)
class MoveCommand(GCodeCommand):
    """
    Команда линейного перемещения G1.

    Attributes:
        x: Координата X (мм), None если не меняется
        y: Координата Y (мм), None если не меняется
        z: Координата Z (мм), None если не меняется
    """
    command_type: CommandType = field(default=CommandType.MOVE, repr=False)
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    f: Optional[float] = None

    def to_string(self) -> str:
        """Преобразует команду в строку 'G1 X... Y... Z... F...'."""
        parts = ["G1"]
        if self.x is not None:
            parts.append(f"X{round(self.x, 1)}")
        if self.y is not None:
            parts.append(f"Y{round(self.y, 1)}")
        if self.z is not None:
            parts.append(f"Z{round(self.z, 1)}")
        if self.f is not None:
            parts.append(f"F{round(self.f, 1)}")
        return " ".join(parts)

    def distance_to(self, other: 'MoveCommand') -> float:
        """
        Вычисляет евклидово расстояние до другой позиции.

        Args:
            other: Другая команда перемещения

        Returns:
            Расстояние в мм
        """
        dx = (other.x or 0) - (self.x or 0)
        dy = (other.y or 0) - (self.y or 0)
        dz = (other.z or 0) - (self.z or 0)
        return (dx**2 + dy**2 + dz**2) ** 0.5


@dataclass(frozen=True)
class PauseCommand(GCodeCommand):
    """
    Команда паузы G4.

    Attributes:
        milliseconds: Длительность паузы в миллисекундах
    """
    command_type: CommandType = field(default=CommandType.PAUSE, repr=False)
    milliseconds: float = 0

    def to_string(self) -> str:
        """Преобразует команду в строку 'G4 P...'."""
        return f"G4 P{round(self.milliseconds, 1)}"


@dataclass(frozen=True)
class SetSpeedCommand(GCodeCommand):
    """
    Команда установки скорости F.

    Attributes:
        speed: Скорость в мм/мин
    """
    command_type: CommandType = field(default=CommandType.SET_SPEED, repr=False)
    speed: float = 0

    def to_string(self) -> str:
        """Преобразует команду в строку 'F ...'."""
        return f"F {self.speed:.1f}"


@dataclass
class Layer:
    """
    Группа команд для одного слоя.

    Attributes:
        layer_number: Номер слоя (начиная с 1)
        is_virtual: True если это виртуальный (холостой) слой
        commands: Список команд слоя
    """
    layer_number: int
    is_virtual: bool = False
    commands: List[GCodeCommand] = field(default_factory=list)

    @property
    def layer_type(self) -> str:
        """Возвращает тип слоя для комментария."""
        return "layer (holostoy)" if self.is_virtual else "layer"
