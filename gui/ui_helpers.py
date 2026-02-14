'''
Утилиты для работы с UI.

Содержит вспомогательные функции для работы с Tkinter виджетами.
'''

from tkinter import Tk, Entry, Canvas, PhotoImage, Frame, Scrollbar, NW, messagebox, VERTICAL, RIGHT, LEFT, Y, BOTH
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


def create_scrollable_frame(parent, width=300, height=600):
    """
    Создаёт прокручиваемый фрейм с вертикальным скроллбаром.

    Args:
        parent: Родительский виджет
        width: Начальная ширина canvas (по умолчанию 300)
        height: Начальная высота canvas (по умолчанию 600)

    Returns:
        Frame внутри canvas для размещения виджетов
    """
    # Контейнер для canvas и scrollbar
    container = Frame(parent)

    # Canvas для прокрутки (без фиксированной высоты, чтобы мог растягиваться)
    canvas = Canvas(container, width=width, height=height, highlightthickness=0)
    scrollbar = Scrollbar(container, orient=VERTICAL, command=canvas.yview)

    # Внутренний фрейм, который будет прокручиваться
    scrollable_frame = Frame(canvas)

    # Привязываем изменение размера фрейма к обновлению области прокрутки
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Создаём окно внутри canvas
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Привязываем прокрутку колесиком мыши
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(event):
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

    # Кроссплатформенная поддержка колесика мыши
    canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/MacOS
    canvas.bind_all("<Button-4>", _on_mousewheel_linux)  # Linux scroll up
    canvas.bind_all("<Button-5>", _on_mousewheel_linux)  # Linux scroll down

    # Размещаем canvas и scrollbar
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.pack(side=RIGHT, fill=Y)

    # Возвращаем контейнер и внутренний фрейм
    container.scrollable_frame = scrollable_frame
    return container
