'''
Состояние приложения.

Содержит AppState для централизованного хранения состояния.
'''

from dataclasses import dataclass, field


@dataclass
class AppState:
    """Централизованное хранилище состояния приложения."""

    # Словари виджетов
    wd_left: dict = field(default_factory=dict)
    wd_labels: dict = field(default_factory=dict)
    wd_right: dict = field(default_factory=dict)

    # Данные конфигурации
    heads: dict = field(default_factory=dict)
    order_list: list = field(default_factory=list)
    type_frame_size_list: list = field(default_factory=list)
    second_dict: dict = field(default_factory=dict)
    filename: str = ""

    # Выбранные значения
    selected_order: str = ""
    selected_type_frame_size: str = ""

    def __repr__(self):
        """Упрощённое представление для отладки."""
        return (f"AppState(wd_left_keys={list(self.wd_left.keys())}, "
                f"wd_right_keys={list(self.wd_right.keys())}, "
                f"filename='{self.filename}')")
