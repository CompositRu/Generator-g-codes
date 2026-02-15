'''
Главный класс приложения.

Содержит GeneratorApp для управления жизненным циклом приложения.
'''

from tkinter import Tk, Frame, BooleanVar, messagebox, N, S

from gui.state import AppState
from gui.data_manager import load_data_json, load_heads_json, migrate_heads_data
from gui.widgets import (create_left_panel, create_right_panel_top,
                         create_right_panel_bottom, create_order_combobox)
from gui.event_handlers import EventHandlers
from gui.ui_helpers import centered_win, create_scrollable_frame


class GeneratorApp:
    """Главный класс приложения генератора G-кодов."""

    def __init__(self, master: Tk):
        """
        Инициализирует приложение.

        Args:
            master: Главное окно Tkinter
        """
        self.window = master
        self.state = AppState()
        self.handlers = None

        try:
            self._load_config()
            self._build_ui()
        except Exception as e:
            messagebox.showerror('Ошибка инициализации', str(e))
            raise

    def _load_config(self):
        """Загружает конфигурацию из JSON файлов."""
        # Загружаем данные
        data = load_data_json()
        self.state.heads = load_heads_json()

        # Миграция данных игольниц (добавляем needle_spacing если отсутствует)
        self.state.heads = migrate_heads_data(self.state.heads, data)

        # Извлекаем имя файла
        self.state.filename = data.pop("Имя файла")

        # Извлекаем данные для правой панели
        try:
            self.state.second_dict["Случайный порядок ударов"] = data.pop("Случайный порядок ударов")
            self.state.second_dict["Случайные смещения"] = data.pop("Случайные смещения")
            self.state.second_dict["Коэффициент случайных смещений"] = data.pop("Коэффициент случайных смещений")
            self.state.second_dict["Чередование направлений прохода слоя"] = data.pop("Чередование направлений прохода слоя")
            self.state.second_dict["Автоматическая генерация имени файла"] = data.pop("Автоматическая генерация имени файла")
            self.state.second_dict["Создание файла на рабочем столе"] = data.pop("Создание файла на рабочем столе")

            order_param = data.pop("Порядок прохождения рядов")
            self.state.order_list = order_param["options"]
            self.state.selected_order = order_param["value"]

            frame_size_param = data.pop("Задание размеров каркаса")
            self.state.type_frame_size_list = frame_size_param["options"]
            self.state.selected_type_frame_size = frame_size_param["value"]
        except KeyError as ke:
            raise KeyError(f'В data.json файле не хватает параметра {ke}')

        # Остальные данные остаются в data для левой панели

    def _build_ui(self):
        """Строит пользовательский интерфейс."""
        # Настройка grid layout
        self.window.columnconfigure(0, weight=1)
        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)

        # Создаём левую панель с прокруткой
        left_container = create_scrollable_frame(self.window, width=530, height=600)
        left_container.grid(column=0, row=0, sticky=N+S, padx=5, pady=5)
        left_desk = left_container.scrollable_frame

        # Создаём правую панель (обычный фрейм)
        right_desk = Frame(self.window, padx=5, pady=5)
        right_desk.grid(column=1, row=0, sticky=N+S)

        # Создаём обработчики событий
        self.handlers = EventHandlers(self.state)
        callbacks = self.handlers.get_callbacks()

        # Загружаем данные для левой панели
        data = load_data_json()
        data.pop("Имя файла")
        for key in ["Случайный порядок ударов", "Случайные смещения", "Коэффициент случайных смещений",
                    "Чередование направлений прохода слоя", "Автоматическая генерация имени файла",
                    "Создание файла на рабочем столе", "Порядок прохождения рядов",
                    "Задание размеров каркаса"]:
            data.pop(key, None)

        # Создаём левую панель
        self.state.wd_left, self.state.wd_labels = create_left_panel(
            left_desk, data, self.state.type_frame_size_list,
            self.state.selected_type_frame_size, callbacks['frame_size_visibility']
        )

        # Применяем начальную видимость
        callbacks['frame_size_visibility']()

        # Создаём правую панель (верх)
        self.state.wd_right = create_right_panel_top(right_desk, self.state.heads)

        # Привязываем обработчик смены головы
        combo = self.state.wd_right["Комбобокс выбор головы"]
        combo.bind('<<ComboboxSelected>>', callbacks['head_change'])

        # Создаём комбобокс порядка рядов
        self.state.wd_right["Комбобокс порядок рядов"] = create_order_combobox(
            right_desk, self.state.order_list, self.state.selected_order
        )

        # Создаём правую панель (низ)
        # Обновляем parent для компонентов, которым нужен доступ к window
        from gui.head_config import HeadConfigDialog
        from gui.generation import GenerationController

        # Патчим parent в handlers
        self.handlers.state = self.state

        wd_right_bottom = create_right_panel_bottom(
            right_desk, self.state.second_dict, self.state.filename,
            callbacks['save'], callbacks['setup'], callbacks['show_offsets'],
            callbacks['generate'], callbacks['filename_visibility']
        )

        self.state.wd_left = {**self.state.wd_left, **wd_right_bottom}
        callbacks['filename_visibility']()

        # Настраиваем trace callbacks для автоматической смены видимости
        try:
            auto_var = self.state.wd_left["Параметры паттерна"]["Автоматическое определение формы паттерна"]
            if isinstance(auto_var, BooleanVar):
                auto_var.trace_add("write", lambda *args: callbacks['pattern_visibility']())
            callbacks['pattern_visibility']()
        except KeyError:
            pass

        try:
            probivka_var = self.state.wd_left["Пробивка"]["Пробивка с нарастанием глубины"]
            if isinstance(probivka_var, BooleanVar):
                probivka_var.trace_add("write", lambda *args: callbacks['probivka_visibility']())
            callbacks['probivka_visibility']()
        except KeyError:
            pass

        # Центрируем окно
        centered_win(self.window)

        # Разрешаем изменять размер окна
        self.window.resizable(True, True)

        # Устанавливаем минимальный размер окна
        self.window.minsize(600, 400)

        # Обновляем ссылки на window в компонентах
        HeadConfigDialog.parent = self.window
        GenerationController.parent = self.window

    def run(self):
        """Запускает главный цикл приложения."""
        self.window.mainloop()
