'''
Обработчики событий UI.

Содержит класс EventHandlers со всеми callback-функциями для UI событий.
'''

from tkinter import BooleanVar, messagebox
from gui.state import AppState
from gui.data_manager import recursion_saver, write_to_json_file
from gui.ui_helpers import show_image
from utils.crossplatform_utils import get_resource_path


class EventHandlers:
    """Класс с обработчиками событий UI."""

    def __init__(self, state: AppState):
        """
        Инициализирует обработчики с доступом к состоянию.

        Args:
            state: Состояние приложения
        """
        self.state = state

    def get_callbacks(self):
        """
        Возвращает словарь callbacks для регистрации в виджетах.

        Returns:
            dict с названиями callback и методами
        """
        return {
            'pattern_visibility': self.on_pattern_parameters_change,
            'probivka_visibility': self.on_probivka_change,
            'frame_size_visibility': self.on_frame_size_change,
            'filename_visibility': self.on_filename_change,
            'head_change': self.on_head_change,
            'save': self.on_save,
            'setup': self.on_setup,
            'show_offsets': self.on_show_offsets,
            'generate': self.on_generate,
        }

    def on_pattern_parameters_change(self):
        """Изменяет видимость параметров паттерна (nx/ny) в зависимости от чекбокса."""
        try:
            auto_var = self.state.wd_left["Параметры паттерна"]["Автоматическое определение формы паттерна"]
            nx_entry = self.state.wd_left["Параметры паттерна"]["nx"]
            ny_entry = self.state.wd_left["Параметры паттерна"]["ny"]
            nx_label = self.state.wd_labels["Параметры паттерна"]["nx"]
            ny_label = self.state.wd_labels["Параметры паттерна"]["ny"]
        except KeyError:
            return  # какая-то из позиций отсутствует — тихо выходим

        widgets = (nx_entry, ny_entry, nx_label, ny_label)

        def hide():
            for w in widgets:
                w.grid_remove()

        def show():
            for w in widgets:
                w.grid()

        if isinstance(auto_var, BooleanVar) and auto_var.get():
            hide()
        else:
            show()

    def on_probivka_change(self):
        """Изменяет видимость поля 'Начальная глубина удара'."""
        try:
            probivka_var = self.state.wd_left["Пробивка"]["Пробивка с нарастанием глубины"]
            depth_entry = self.state.wd_left["Пробивка"]["Начальная глубина удара (мм)"]
            depth_label = self.state.wd_labels["Пробивка"]["Начальная глубина удара (мм)"]
        except KeyError:
            return

        widgets = (depth_entry, depth_label)

        if isinstance(probivka_var, BooleanVar) and probivka_var.get():
            for w in widgets:
                w.grid()
        else:
            for w in widgets:
                w.grid_remove()

    def on_frame_size_change(self):
        """Переключает видимость между 'Количество шагов головы' и 'Габариты каркаса'."""
        group_1 = [self.state.wd_left['Количество шагов головы']['X'],
                   self.state.wd_left['Количество шагов головы']['Y'],
                   self.state.wd_labels['Количество шагов головы']['X'],
                   self.state.wd_labels['Количество шагов головы']['Y'],
                   self.state.wd_labels['Количество шагов головы label']]
        group_2 = [self.state.wd_left['Габариты каркаса']['X'],
                   self.state.wd_left['Габариты каркаса']['Y'],
                   self.state.wd_labels['Габариты каркаса']['X'],
                   self.state.wd_labels['Габариты каркаса']['Y'],
                   self.state.wd_labels['Габариты каркаса label']]

        def group_grid_remove(group):
            for item in group:
                item.grid_remove()

        def group_grid(group):
            for item in group:
                item.grid()

        n = self.state.wd_left['Номер радиокнопки типа задания размера каркаса'].get()
        if n == 1:
            group_grid_remove(group_1)
            group_grid(group_2)
        else:
            group_grid_remove(group_2)
            group_grid(group_1)

    def on_filename_change(self):
        """Переключает доступность поля имени файла."""
        n = self.state.wd_left['Автоматическая генерация имени файла'].get()
        state = 'normal' if n == 0 else 'disabled'
        self.state.wd_left['Имя файла'].config(state=state)

    def on_head_change(self, event):
        """Обрабатывает изменение выбранной головы."""
        canvas = self.state.wd_right["Полотно"]
        combo = self.state.wd_right["Комбобокс выбор головы"]
        label_x_needle = self.state.wd_right["Лейблы с количеством игл"][0]
        label_y_needle = self.state.wd_right["Лейблы с количеством игл"][1]

        canvas.delete("all")
        head_name = combo.get()
        self.state.heads['Выбранная игольница (ИП игольница)'] = head_name
        new_x_needle = self.state.heads['Игольницы (ИП головы)'][head_name]['X']
        new_y_needle = self.state.heads['Игольницы (ИП головы)'][head_name]['Y']
        label_x_needle.config(text='Х      ' + str(new_x_needle))
        label_y_needle.config(text='Y      ' + str(new_y_needle))
        filename = self.state.heads['Игольницы (ИП головы)'][head_name]['path']
        show_image(canvas, filename)

    def on_save(self):
        """Сохраняет данные в JSON файлы."""
        data_to_json = recursion_saver(self.state.wd_left)

        data_to_json["Порядок прохождения рядов"] = {
            "value": self.state.wd_right["Комбобокс порядок рядов"].get(),
            "options": self.state.order_list
        }

        frame_size_index = data_to_json.pop("Номер радиокнопки типа задания размера каркаса")
        data_to_json["Задание размеров каркаса"] = {
            "value": self.state.type_frame_size_list[frame_size_index],
            "options": self.state.type_frame_size_list
        }

        write_to_json_file(get_resource_path('data/data.json'), data_to_json)

        combo = self.state.wd_right["Комбобокс выбор головы"]
        head_name = combo.get()
        self.state.heads['Выбранная игольница (ИП игольница)'] = head_name

        write_to_json_file(get_resource_path('data/heads.json'), self.state.heads)

    def on_setup(self):
        """Открывает диалог настройки игольниц."""
        # Импорт здесь для избежания циркулярных зависимостей
        from gui.head_config import HeadConfigDialog

        dialog = HeadConfigDialog(None, self.state)  # window будет установлен позже
        dialog.show()

    def on_show_offsets(self):
        """Показывает визуализацию паттерна пробивки."""
        from gui.visualization import show_visualization

        try:
            # Получаем spacing из выбранной головы
            combo = self.state.wd_right["Комбобокс выбор головы"]
            head_name = combo.get()
            head_data = self.state.heads["Игольницы (ИП головы)"][head_name]
            cell_size_x = float(head_data.get('needle_spacing_x', 8.0))
            cell_size_y = float(head_data.get('needle_spacing_y', 8.0))

            num_pitch = int(self.state.wd_left["Параметры паттерна"]["Кол-во ударов"].get())
            generate_nx_ny = bool(self.state.wd_left['Параметры паттерна']['Автоматическое определение формы паттерна'].get())
            nx = int(self.state.wd_left['Параметры паттерна']['nx'].get())
            ny = int(self.state.wd_left['Параметры паттерна']['ny'].get())
            is_random_offsets = bool(self.state.wd_left['Случайные смещения'].get())
            coefficient_random_offsets = float(self.state.wd_left['Коэффициент случайных смещений'].get())
            is_random_order = bool(self.state.wd_left['Случайный порядок ударов'].get())
        except Exception as e:
            messagebox.showerror("Не удалось прочитать числовые параметры.", str(e))
            return

        show_visualization(cell_size_x, cell_size_y, num_pitch, generate_nx_ny, nx, ny,
                           is_random_offsets, coefficient_random_offsets, is_random_order)

    def on_generate(self):
        """Запускает генерацию G-кодов."""
        # Импорт здесь для избежания циркулярных зависимостей
        from gui.generation import GenerationController

        controller = GenerationController(None, self.state)  # window будет установлен позже
        controller.start_generation()
