"""
Core модуль генератора G-кодов.

Публичный API:
- Команды: MoveCommand, PauseCommand, SetSpeedCommand, RawCommand, Layer
- Форматирование: GCodeFormatter, PreheadParams
- Время: TimeEstimator, TimeEstimate
- Геометрия: generate_offset_list, get_result_offset_list, get_nx_ny, и др.
- Валидация: check_dict_keys
- Файлы: get_filename, get_filename_path_and_create_directory_if_need, get_message
"""

from .commands import (
    GCodeCommand,
    MoveCommand,
    PauseCommand,
    RawCommand,
    SetSpeedCommand,
    Layer,
)

from .formatter import (
    GCodeFormatter,
    PreheadParams,
)

from .time_estimator import (
    TimeEstimator,
    TimeEstimate,
    ACCEL_LINEAR_DEFAULT,
)

from .geometry import (
    generate_offset_list,
    get_result_offset_list,
    get_nx_ny,
    check_nums_x_y,
    check_nums_x_y_from_dict,
    get_ordered_list_of_rows,
    calculate_head_dimensions,
    calculate_steps_from_frame,
)

from .validator import check_dict_keys

from .file_utils import (
    get_filename,
    get_filename_path_and_create_directory_if_need,
    get_message,
)

from .command_generator import CommandGenerator
from .generator import generate_G_codes_file

__all__ = [
    # Commands
    'GCodeCommand',
    'MoveCommand',
    'PauseCommand',
    'RawCommand',
    'SetSpeedCommand',
    'Layer',
    # Formatter
    'GCodeFormatter',
    'PreheadParams',
    # Time
    'TimeEstimator',
    'TimeEstimate',
    'ACCEL_LINEAR_DEFAULT',
    # Geometry
    'generate_offset_list',
    'get_result_offset_list',
    'get_nx_ny',
    'check_nums_x_y',
    'check_nums_x_y_from_dict',
    'get_ordered_list_of_rows',
    'calculate_head_dimensions',
    'calculate_steps_from_frame',
    # Validator
    'check_dict_keys',
    # Files
    'get_filename',
    'get_filename_path_and_create_directory_if_need',
    'get_message',
    # Generator
    'CommandGenerator',
    'generate_G_codes_file',
]
