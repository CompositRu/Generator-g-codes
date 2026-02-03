'''
Диалог настройки игольниц (ИП головы).

Содержит класс HeadConfigDialog для управления конфигурацией игольниц.
'''

from tkinter import Toplevel, Entry, Canvas, Button, Label, W, E, messagebox
from gui.state import AppState
from gui.ui_helpers import set_text, show_image, centered_win
from gui.data_manager import write_to_json_file
from utils.crossplatform_utils import get_resource_path


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
        label_y = Label(self.win, text='Y')
        label_y.grid(column=i, row=3)
        label_path = Label(self.win, text='Файл')
        label_path.grid(column=i, row=4)

        textfield_x = Entry(self.win)
        set_text(textfield_x, item['X'])
        textfield_x.grid(column=i+1, row=2)

        textfield_y = Entry(self.win)
        set_text(textfield_y, item['Y'])
        textfield_y.grid(column=i+1, row=3)

        path = Entry(self.win)
        set_text(path, item['path'])
        path.grid(column=i+1, row=4)

        delete_button = Button(self.win, text='Удалить', command=self._make_delete_func(section))
        delete_button.grid(columnspan=2, column=i, row=5, sticky=W+E, padx=10, pady=10)

        head_widgets = {
            "head_name": textfield_head_name,
            "canvas": c,
            "label_x": label_x,
            "label_y": label_y,
            "label_path": label_path,
            "delete_button": delete_button,
            "X": textfield_x,
            "Y": textfield_y,
            "path": path,
        }

        return head_widgets

    def _make_delete_func(self, head):
        """Создаёт функцию удаления для кнопки."""
        def f():
            # удаляем из словаря виджетов
            for name, widget in self.widgets[head].items():
                widget.destroy()
            self.widgets.pop(head)
            columnspan = len(self.widgets) * 2 + 2
            self.add_button.grid(columnspan=columnspan, row=6, sticky=W+E, padx=10, pady=0)
            self.save_button.grid(columnspan=columnspan, row=7, sticky=W+E, padx=10, pady=10)
        return f

    def _add_widget(self):
        """Добавляет новую голову."""
        idx = len(self.widgets) + 1
        i2 = len(self.widgets) * 2
        name = f"Г{idx}"
        parameters = {"X": idx, "Y": idx, "path": "введите имя"}
        self.widgets[name] = self._create_widgets_for_head(name, parameters, i2)
        self.add_button.grid(columnspan=i2 + 2, row=6, sticky=W+E, padx=10, pady=0)
        self.save_button.grid(columnspan=i2 + 2, row=7, sticky=W+E, padx=10, pady=10)

    def _save_data_heads(self):
        """Сохраняет данные игольниц."""
        combo = self.state.wd_right["Комбобокс выбор головы"]
        head_name = combo.get()
        self.state.heads['Выбранная игольница (ИП игольница)'] = head_name

        # Проверка данных
        for _, widget in self.widgets.items():
            try:
                x = int(widget['X'].get())
                y = int(widget['Y'].get())
            except ValueError:
                messagebox.showerror('Смотри, что пишешь!', 'Количеством игл может быть только целое число')
                return

        self.state.heads["Игольницы (ИП головы)"].clear()
        head_needles = self.state.heads["Игольницы (ИП головы)"]

        # Сохранение данных
        for head, widget in self.widgets.items():
            head_name = widget['head_name'].get()
            head_needles[head_name] = {}
            head_data = head_needles[head_name]
            head_data['X'] = int(widget['X'].get())
            head_data['Y'] = int(widget['Y'].get())
            head_data['path'] = widget['path'].get()

        write_to_json_file(get_resource_path('data/heads.json'), self.state.heads)

        combo = self.state.wd_right["Комбобокс выбор головы"]
        idx = combo['values'].index(combo.get())

        combo['values'] = [section for section, item in self.state.heads["Игольницы (ИП головы)"].items()]

        combo.current(idx if idx < len(combo['values']) else 0)
        self.state.heads['Выбранная игольница (ИП игольница)'] = combo.get()

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

        # Создаём виджеты для всех существующих голов
        i = 0
        self.widgets = {}
        for section, item in self.state.heads["Игольницы (ИП головы)"].items():
            self.widgets[section] = self._create_widgets_for_head(section, item, i)
            i += 2

        # Кнопка добавления
        self.add_button = Button(self.win,
                                  text='Добавить голову',
                                  command=self._add_widget)
        self.add_button.grid(columnspan=len(self.state.heads['Игольницы (ИП головы)']) * 2 + 20,
                             row=6,
                             sticky=W+E,
                             padx=10,
                             pady=0)

        # Кнопка сохранения
        self.save_button = Button(self.win,
                                   text='Сохранить',
                                   bg='ivory4',
                                   command=self._save_data_heads)
        self.save_button.grid(columnspan=len(self.state.heads['Игольницы (ИП головы)']) * 2,
                              row=7,
                              sticky=W+E,
                              padx=10,
                              pady=10)

        centered_win(self.win)
        self.win.resizable(False, False)
