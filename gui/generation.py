'''
Контроллер генерации G-кодов.

Содержит класс GenerationController для управления процессом генерации
с отображением прогресса.
'''

import threading
from tkinter import Toplevel, messagebox
from tkinter.ttk import Progressbar
from gui.state import AppState
from gui.data_manager import recursion_saver
from gui.validation import validate_generation_params
from gui.ui_helpers import centered_win
from core import generate_G_codes_file, get_filename, get_message
from utils.crossplatform_utils import get_resource_path


class GenerationController:
    """Контроллер для управления генерацией G-кодов."""

    def __init__(self, parent, state: AppState):
        """
        Инициализирует контроллер.

        Args:
            parent: Родительское окно (Tk)
            state: Состояние приложения
        """
        self.parent = parent
        self.state = state

    def _get_data_for_generating(self):
        """
        Собирает все данные для генерации.

        Returns:
            dict с параметрами генерации
        """
        data = recursion_saver(self.state.wd_left)

        # Получаем текущие значения enum параметров
        data["Порядок прохождения рядов"] = self.state.wd_right["Комбобокс порядок рядов"].get()
        frame_size_index = data.pop("Номер радиокнопки типа задания размера каркаса")
        data["Задание размеров каркаса"] = self.state.type_frame_size_list[frame_size_index]
        combo = self.state.wd_right["Комбобокс выбор головы"]
        head_name = combo.get()
        self.state.heads['Выбранная игольница (ИП игольница)'] = head_name
        return {**data, **self.state.heads}

    def start_generation(self):
        """Начинает процесс генерации G-кодов."""
        # Обновляем данные
        try:
            data_dict = self._get_data_for_generating()
        except ValueError:
            return

        # Проверяем входные данные
        if not validate_generation_params(data_dict):
            return

        # Окно с progress bar
        win = Toplevel(self.parent)
        try:
            # На linux системах tkinter не отображает иконку в title bar окна
            win.iconbitmap(get_resource_path('symbol.ico'))
        except Exception:
            pass

        def window_deleted():
            # Блокируем закрытие, пока идёт генерация
            pass

        win.protocol('WM_DELETE_WINDOW', window_deleted)
        bar = Progressbar(win, length=300)
        bar.pack()
        centered_win(win)

        # Вычисляем g коды в отдельном потоке для отображения прогресса на progress bar
        threading.Thread(target=lambda: self._run_generation_thread(win, bar, data_dict)).start()

    def _run_generation_thread(self, win_with_progress, bar, data_dict):
        """
        Выполняет генерацию в отдельном потоке.

        Args:
            win_with_progress: Окно с progress bar
            bar: Progressbar виджет
            data_dict: Параметры генерации
        """
        # Создаём функцию для отображения процесса на progressbar
        def display_progress(progress):
            bar['value'] = progress

        # Генерируем
        try:
            result = generate_G_codes_file(data_dict, display_progress)
        except BaseException as e:
            win_with_progress.destroy()
            messagebox.showerror('Всё. Херня. Звони Артёму', e)
            return

        # Формируем сообщение с информацией
        message = f"Сгенерирован файл\n{get_filename(data_dict)}\n\n"
        message += f"Время одного слоя: {result['layer_time_str']}\n"
        message += f"Время всех слоёв: {result['work_time_str']}\n\n"
        message += f"Плотность пробивки: {result['density']:.2f} уд/кв.см\n\n"
        message += get_message(data_dict)

        # Закрываем окно
        win_with_progress.destroy()
        messagebox.showinfo('Всё прошло удачно', message)
