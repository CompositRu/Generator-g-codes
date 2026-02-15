'''
Диалог настройки игольниц (ИП головы).

Содержит класс HeadConfigDialog для управления конфигурацией игольниц.
'''

import logging
from tkinter import Toplevel, Entry, Canvas, Button, Label, W, E, messagebox
from gui.state import AppState
from gui.ui_helpers import set_text, show_image, centered_win
from gui.data_manager import write_to_json_file
from gui.tooltips import add_tooltip_by_name
from utils.crossplatform_utils import get_resource_path

logger = logging.getLogger(__name__)


class HeadConfigDialog:
    """Диалоговое окно для настройки игольниц."""

    def __init__(self, parent, state: AppState):
        """
        Инициализирует диалог.

        Args:
            parent: Родительское окно (Tk)
            state: Состояние приложения
        """
        self.parent = parent
        self.state = state
        self.win = None
        self.widgets = {}
        self.head_data = {}  # Словарь с данными игольниц {имя: {X, Y, path}}

    def _clear_all_widgets(self):
        """Удаляет все виджеты игольниц из окна."""
        for head_name, head_widgets in self.widgets.items():
            for widget_name, widget in head_widgets.items():
                try:
                    widget.destroy()
                except Exception as e:
                    logger.error(f"Ошибка при удалении виджета {widget_name} для {head_name}: {e}")
        self.widgets.clear()


    def _rebuild_layout(self):
        """Полностью пересоздаёт layout виджетов."""

        # Удаляем все существующие виджеты
        self._clear_all_widgets()

        # Создаём виджеты заново
        column_index = 0
        for head_name in sorted(self.head_data.keys()):
            item = self.head_data[head_name]
            self.widgets[head_name] = self._create_widgets_for_head(head_name, item, column_index)
            column_index += 2

        # Обновляем позицию кнопок
        total_columns = len(self.head_data) * 2
        if total_columns == 0:
            total_columns = 2  # Минимум 2 колонки даже если нет игольниц

        self.add_button.grid(columnspan=total_columns, row=8, sticky=W+E, padx=10, pady=0)
        self.save_button.grid(columnspan=total_columns, row=9, sticky=W+E, padx=10, pady=10)

    def _create_widgets_for_head(self, section, item, column_index):
        """
        Создаёт виджеты для одной игольницы.

        Args:
            section: Название головы
            item: Данные головы (X, Y, path)
            column_index: Колонка для размещения (чётное число)

        Returns:
            dict с виджетами для данной головы
        """
        i = column_index

        textfield_head_name = Entry(self.win, justify='center')
        set_text(textfield_head_name, section)
        textfield_head_name.grid(columnspan=2, column=i, row=0)

        c = Canvas(self.win, width=200, height=200)
        c.grid(columnspan=2, column=i, row=1)
        show_image(c, item['path'])

        label_x = Label(self.win, text='X')
        label_x.grid(column=i, row=2)
        add_tooltip_by_name(label_x, "Количество игл X")

        label_y = Label(self.win, text='Y')
        label_y.grid(column=i, row=3)
        add_tooltip_by_name(label_y, "Количество игл Y")
        label_path = Label(self.win, text='Файл')
        label_path.grid(column=i, row=4)

        textfield_x = Entry(self.win)
        set_text(textfield_x, item['X'])
        textfield_x.grid(column=i+1, row=2)
        add_tooltip_by_name(textfield_x, "Количество игл X")

        textfield_y = Entry(self.win)
        set_text(textfield_y, item['Y'])
        textfield_y.grid(column=i+1, row=3)
        add_tooltip_by_name(textfield_y, "Количество игл Y")

        path = Entry(self.win)
        set_text(path, item['path'])
        path.grid(column=i+1, row=4)

        # Поля для расстояния между иглами
        label_spacing_x = Label(self.win, text='Расст. X (мм)')
        label_spacing_x.grid(column=i, row=5)
        add_tooltip_by_name(label_spacing_x, "Расст. X (мм)")

        textfield_spacing_x = Entry(self.win)
        set_text(textfield_spacing_x, item.get('needle_spacing_x', 8.0))
        textfield_spacing_x.grid(column=i+1, row=5)
        add_tooltip_by_name(textfield_spacing_x, "Расст. X (мм)")

        label_spacing_y = Label(self.win, text='Расст. Y (мм)')
        label_spacing_y.grid(column=i, row=6)
        add_tooltip_by_name(label_spacing_y, "Расст. Y (мм)")

        textfield_spacing_y = Entry(self.win)
        set_text(textfield_spacing_y, item.get('needle_spacing_y', 8.0))
        textfield_spacing_y.grid(column=i+1, row=6)
        add_tooltip_by_name(textfield_spacing_y, "Расст. Y (мм)")

        delete_button = Button(self.win, text='Удалить', command=self._make_delete_func(section))
        delete_button.grid(columnspan=2, column=i, row=7, sticky=W+E, padx=10, pady=10)

        head_widgets = {
            "head_name": textfield_head_name,
            "canvas": c,
            "label_x": label_x,
            "label_y": label_y,
            "label_path": label_path,
            "label_spacing_x": label_spacing_x,
            "label_spacing_y": label_spacing_y,
            "delete_button": delete_button,
            "X": textfield_x,
            "Y": textfield_y,
            "path": path,
            "needle_spacing_x": textfield_spacing_x,
            "needle_spacing_y": textfield_spacing_y,
        }

        return head_widgets

    def _make_delete_func(self, head):
        """Создаёт функцию удаления для кнопки."""
        def f():
            if head not in self.head_data:
                messagebox.showerror("Ошибка", f"Игольница {head} не найдена")
                return

            # Удаляем из данных
            self.head_data.pop(head)

            # Пересоздаём весь layout
            self._rebuild_layout()
        return f

    def _add_widget(self):
        """Добавляет новую голову."""
        # Находим свободный индекс для новой головы
        existing_indices = []
        for name in self.head_data.keys():
            if name.startswith("Г") and name[1:].isdigit():
                existing_indices.append(int(name[1:]))

        idx = 1
        while idx in existing_indices:
            idx += 1

        name = f"Г{idx}"

        # Добавляем в данные
        self.head_data[name] = {
            "X": idx,
            "Y": idx,
            "needle_spacing_x": 8.0,
            "needle_spacing_y": 8.0,
            "path": "введите имя"
        }

        # Пересоздаём весь layout
        self._rebuild_layout()

    def _save_data_heads(self):
        """Сохраняет данные игольниц."""

        combo = self.state.wd_right["Комбобокс выбор головы"]
        current_head = combo.get()
        self.state.heads['Выбранная игольница (ИП игольница)'] = current_head

        # Проверка и сохранение данных из виджетов обратно в head_data
        for head_name, widget in self.widgets.items():
            try:
                x = int(widget['X'].get())
                y = int(widget['Y'].get())
                spacing_x = round(float(widget['needle_spacing_x'].get()), 2)
                spacing_y = round(float(widget['needle_spacing_y'].get()), 2)
                path = widget['path'].get()
                new_name = widget['head_name'].get()

                # Валидация количества игл
                if x <= 0 or y <= 0:
                    messagebox.showerror('Ошибка валидации',
                                       f'Количество игл должно быть больше нуля для {head_name}')
                    return

                # Валидация расстояния между иглами
                if spacing_x <= 0 or spacing_y <= 0:
                    messagebox.showerror('Ошибка валидации',
                                       f'Расстояние между иглами должно быть больше нуля для {head_name}')
                    return

                # Обновляем данные
                if new_name != head_name:
                    # Переименование
                    self.head_data[new_name] = self.head_data.pop(head_name)
                    head_name = new_name

                self.head_data[head_name] = {
                    "X": x,
                    "Y": y,
                    "needle_spacing_x": spacing_x,
                    "needle_spacing_y": spacing_y,
                    "path": path
                }

            except ValueError as e:
                messagebox.showerror('Смотри, что пишешь!',
                                   'Количеством игл может быть только целое число, '
                                   'расстояние между иглами - числом с точкой')
                return

        # Сохраняем в state
        self.state.heads["Игольницы (ИП головы)"].clear()
        self.state.heads["Игольницы (ИП головы)"].update(self.head_data)

        # Сохраняем в файл
        write_to_json_file(get_resource_path('data/heads.json'), self.state.heads)

        # Обновляем комбобокс
        combo = self.state.wd_right["Комбобокс выбор головы"]
        try:
            old_idx = combo['values'].index(current_head)
        except ValueError:
            old_idx = 0

        combo['values'] = list(self.head_data.keys())
        combo.current(old_idx if old_idx < len(combo['values']) else 0)

        # Обновляем главное окно - вызываем on_head_change
        from gui.event_handlers import EventHandlers
        handlers = EventHandlers(self.state)
        handlers.on_head_change(None)

    def show(self):
        """Отображает диалоговое окно."""

        self.win = Toplevel(self.parent)
        self.win.title("Игольницы (ИП головы)")
        try:
            # На linux системах tkinter не отображает иконку в title bar окна
            self.win.iconbitmap(get_resource_path('symbol.ico'))
        except Exception:
            pass

        self.win.grab_set()  # Блокирует другие окна Tkinter
        self.win.attributes('-topmost', 1)  # Окно поверх других

        # Копируем данные из state в head_data
        self.head_data = {}
        for section, item in self.state.heads["Игольницы (ИП головы)"].items():
            self.head_data[section] = dict(item)  # Копия словаря

        # Создаём кнопки (они будут использоваться в _rebuild_layout)
        self.add_button = Button(self.win,
                                  text='Добавить голову',
                                  command=self._add_widget)

        self.save_button = Button(self.win,
                                   text='Сохранить',
                                   bg='ivory4',
                                   command=self._save_data_heads)

        # Создаём виджеты
        self._rebuild_layout()

        centered_win(self.win)
        self.win.resizable(False, False)
