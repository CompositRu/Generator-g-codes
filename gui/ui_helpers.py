'''
Утилиты для работы с UI.

Содержит вспомогательные функции для работы с Tkinter виджетами.
'''

from tkinter import Tk, Entry, Canvas, PhotoImage, NW, messagebox
from utils.crossplatform_utils import get_resource_path


def centered_win(win: Tk):
    """Центрирует окно на экране."""
    win.update_idletasks()
    positionRight = int(win.winfo_screenwidth() / 2 - win.winfo_reqwidth() / 2)
    positionDown = int(win.winfo_screenheight() / 2 - win.winfo_reqheight() / 2) - 30
    win.geometry(f'+{positionRight}+{positionDown}')


def set_text(text_field: Entry, text):
    """Устанавливает текст в текстовое поле."""
    text_field.delete(0, 'end')
    text_field.insert(0, text)


def show_image(canvas: Canvas, filename: str):
    """
    Отображает изображение на canvas.

    Args:
        canvas: Canvas виджет для отображения
        filename: Имя файла изображения (ищется в data/)
    """
    img = None
    try:
        img = PhotoImage(file=get_resource_path('data/' + filename))
    except:
        try:
            img = PhotoImage(file=get_resource_path('data/undefined.png'))
        except:
            title = "Отсутствует изображение головы"
            message = (
                "Нет файла изображения головы (200×200, .png) и файла undefined.png "
                "для голов без указанной фотографии."
            )
            messagebox.showerror(title, message)
            canvas.create_rectangle(0, 0, 200, 200, fill='white')
    if img is not None:
        canvas.image = img
        canvas.create_image(0, 0, anchor=NW, image=img)
