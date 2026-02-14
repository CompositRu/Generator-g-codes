'''
Создание виджетов UI.

Содержит функции для построения левой и правой панелей приложения.
'''

from tkinter import (Frame, Label, Entry, Checkbutton, Radiobutton, Button,
                      Canvas, IntVar, BooleanVar, N, S, W, E)
from tkinter.ttk import Combobox
from gui.ui_helpers import set_text, show_image
from gui.tooltips import add_tooltip_by_name


def display_parameters_recursion(frame, data_dict, i_row):
    """
    Рекурсивно создаёт виджеты для параметров.

    Args:
        frame: Родительский фрейм
        data_dict: Словарь с данными для отображения
        i_row: Начальная строка для размещения

    Returns:
        (widget_dict, labels_dict, next_row) - словари виджетов и лейблов, следующая строка
    """
    widget_dict = {}
    labels_dict = {}
    i = i_row
    for section, item in data_dict.items():
        # Проверяем, является ли dict enum параметром (имеет ключи 'value' и 'options')
        if isinstance(item, dict) and 'value' in item and 'options' in item:
            # Это enum параметр - создаем комбобокс
            lab = Label(frame, text=section)
            lab.grid(column=0, row=i, sticky=N)
            add_tooltip_by_name(lab, section)
            combo = Combobox(frame, width=15, values=item['options'], state='readonly')
            try:
                combo.current(item['options'].index(item['value']))
            except (ValueError, IndexError):
                combo.current(0)
            combo.grid(column=1, row=i, sticky=N)
            add_tooltip_by_name(combo, section)
            widget_dict[section] = combo
            labels_dict[section] = lab
            i += 1
        elif isinstance(item, dict):
            # Обычный вложенный словарь - создаем секцию
            l = Label(frame, text='\n'+section, font=("Arial Bold", 10, 'bold'))
            l.grid(columnspan=2, row=i, sticky=N)
            add_tooltip_by_name(l, section)  # Добавляем tooltip к заголовку секции
            i += 1
            labels_dict[section + ' label'] = l
            widget_dict[section], labels_dict[section], i = display_parameters_recursion(frame, item, i)
        elif isinstance(item, bool):
            var = BooleanVar(value=item)
            cb = Checkbutton(frame, text=section, variable=var)
            cb.grid(columnspan=2, row=i, sticky=W)
            add_tooltip_by_name(cb, section)  # Добавляем tooltip к чекбоксу
            widget_dict[section] = var
            # сохраним сам чекбокс в labels_dict — у него тоже есть grid()/grid_remove()
            labels_dict[section] = cb
            i += 1
        elif isinstance(item, list):
            lab = Label(frame, text=section)
            lab.grid(column=0, row=i, sticky=N)
            add_tooltip_by_name(lab, section)  # Добавляем tooltip к лейблу
            combo = Combobox(frame, width=15, values=item, state='readonly')
            combo.current(0)
            combo.grid(column=1, row=i, sticky=N)
            add_tooltip_by_name(combo, section)  # Добавляем tooltip к combobox
            widget_dict[section] = combo
            labels_dict[section] = lab
            i += 1
        else:
            lab = Label(frame, text=section)
            lab.grid(column=0, row=i, sticky=N)
            add_tooltip_by_name(lab, section)  # Добавляем tooltip к лейблу
            text_field = Entry(frame, width=8, justify='center')
            text_field.grid(column=1, row=i, sticky=N)
            set_text(text_field, item)
            add_tooltip_by_name(text_field, section)  # Добавляем tooltip к полю ввода
            widget_dict[section] = text_field
            labels_dict[section] = lab
            i += 1
    return widget_dict, labels_dict, i


def create_left_panel(frame, data_dict, type_frame_size_list, selected_type_frame_size,
                      on_frame_size_change_callback):
    """
    Создаёт левую панель с параметрами.

    Args:
        frame: Родительский фрейм
        data_dict: Данные для виджетов
        type_frame_size_list: Список вариантов задания размеров каркаса
        selected_type_frame_size: Выбранный вариант
        on_frame_size_change_callback: Callback для изменения типа размера каркаса

    Returns:
        (widget_dict, labels_dict) - словари виджетов и их лейблов
    """
    part_data_dict = {}
    part_data_dict['Количество шагов головы'] = data_dict.pop('Количество шагов головы')
    part_data_dict['Габариты каркаса'] = data_dict.pop('Габариты каркаса')

    widget_dict, labels_dict, i = display_parameters_recursion(frame, data_dict, 0)

    label_empty = Label(frame)
    label_empty.grid(columnspan=2, row=i, sticky=N+S)
    frame.rowconfigure(i, weight=1)  # Эта строка нужна, чтобы виджет мог растягиваться
    i += 1

    l = Label(frame, text="\nТип задания размеров каркаса:", font=("Arial Bold", 10, 'bold'))
    l.grid(columnspan=2, row=i)
    i += 1
    var = IntVar()
    var.set(type_frame_size_list.index(selected_type_frame_size))
    for j, order in enumerate(type_frame_size_list):
        r = Radiobutton(frame, text=order, value=j, variable=var, command=on_frame_size_change_callback)
        r.grid(columnspan=2, row=i, padx=50, sticky=W)
        i += 1
    widget_dict['Номер радиокнопки типа задания размера каркаса'] = var

    wd, wl, i = display_parameters_recursion(frame, part_data_dict, i)
    widget_dict = {**widget_dict, **wd}
    labels_dict = {**labels_dict, **wl}
    return widget_dict, labels_dict


def create_right_panel_top(frame, heads):
    """
    Создаёт верхнюю часть правой панели (выбор головы).

    Args:
        frame: Родительский фрейм
        heads: Словарь с данными игольниц

    Returns:
        dict с виджетами ("Полотно", "Комбобокс выбор головы", "Лейблы с количеством игл")
    """
    canvas = Canvas(frame, width=200, height=200)
    canvas.grid(columnspan=2, row=0)

    lab = Label(frame, text="ИП голова:", padx=20, font=("Arial Bold", 10))
    lab.grid(column=0, row=1)

    val = []
    for section, item in heads["Игольницы (ИП головы)"].items():
        val.append(section)
    combo = Combobox(frame, width=10, values=val, state='readonly')
    combo.current(val.index(heads["Выбранная игольница (ИП игольница)"]))
    combo.grid(column=1, row=1)
    add_tooltip_by_name(lab, "ИП голова")  # Добавляем tooltip к лейблу
    add_tooltip_by_name(combo, "ИП голова")  # Добавляем tooltip к комбобоксу

    head_name = combo.get()
    filename = heads['Игольницы (ИП головы)'][head_name]['path']
    show_image(canvas, filename)

    lab = Label(frame, text='Игольницы (ИП головы):', font=("Arial Bold", 10, 'bold'))
    lab.grid(columnspan=2, row=2)

    X_needles = heads['Игольницы (ИП головы)'][head_name]['X']
    lab_x = Label(frame, text='Х      ' + str(X_needles))
    lab_x.grid(columnspan=2, row=3)

    Y_needles = heads['Игольницы (ИП головы)'][head_name]['Y']
    lab_y = Label(frame, text='Y      ' + str(Y_needles))
    lab_y.grid(columnspan=2, row=4)

    widget_dict = {}
    widget_dict["Полотно"] = canvas
    widget_dict["Комбобокс выбор головы"] = combo
    widget_dict["Лейблы с количеством игл"] = (lab_x, lab_y)

    # Примечание: обработчик change_pic будет привязан позже в event_handlers

    return widget_dict


def create_order_combobox(frame, order_list, selected_order):
    """
    Создаёт комбобокс для выбора порядка прохождения рядов.

    Args:
        frame: Родительский фрейм
        order_list: Список вариантов порядка
        selected_order: Выбранный порядок

    Returns:
        Combobox виджет
    """
    lbl = Label(frame, text="Порядок прохождения рядов:", font=("Arial Bold", 10, "bold"))
    lbl.grid(columnspan=2, row=5)
    add_tooltip_by_name(lbl, "Порядок прохождения рядов")

    combo = Combobox(frame, width=18, values=order_list, state="readonly")
    try:
        combo.current(order_list.index(selected_order))
    except Exception:
        combo.current(0)
    combo.grid(columnspan=2, row=6, padx=50, sticky=E+W)
    add_tooltip_by_name(combo, "Порядок прохождения рядов")

    return combo


def create_right_panel_bottom(frame, second_dict, filename,
                               on_save_callback, on_setup_callback,
                               on_show_offsets_callback, on_generate_callback,
                               on_filename_change_callback):
    """
    Создаёт нижнюю часть правой панели (опции и кнопки).

    Args:
        frame: Родительский фрейм
        second_dict: Словарь с данными чекбоксов
        filename: Имя файла по умолчанию
        on_save_callback: Callback для кнопки Сохранить
        on_setup_callback: Callback для кнопки Настроить
        on_show_offsets_callback: Callback для кнопки Показать точки
        on_generate_callback: Callback для кнопки Генерировать
        on_filename_change_callback: Callback для изменения автогенерации имени

    Returns:
        dict с виджетами
    """
    widget_dict = {}

    def create_check_box(section, row, func=None):
        v = BooleanVar()
        v.set(second_dict[section])
        widget_dict[section] = v
        checkbox = Checkbutton(frame, text=section, variable=v, font=("Arial Bold", 10, 'bold'), command=func)
        checkbox.grid(columnspan=2, row=row, sticky=W)
        add_tooltip_by_name(checkbox, section)  # Добавляем tooltip к чекбоксу
        return checkbox

    create_check_box("Случайный порядок ударов", 11)
    create_check_box("Случайные смещения", 12)

    lab = Label(frame, text="Коэффициент")
    lab.grid(column=0, row=13)
    add_tooltip_by_name(lab, "Коэффициент случайных смещений")

    text_field1 = Entry(frame, width=8, justify='center')
    text_field1.grid(column=1, row=13)
    set_text(text_field1, second_dict["Коэффициент случайных смещений"])
    add_tooltip_by_name(text_field1, "Коэффициент случайных смещений")
    widget_dict["Коэффициент случайных смещений"] = text_field1

    create_check_box("Чередование направлений прохода слоя", 14)
    create_check_box("Создание файла на рабочем столе", 15)
    create_check_box("Автоматическая генерация имени файла", 16, on_filename_change_callback)

    bt_save = Button(frame, text='Сохранить', width=15, bg='ivory4', command=on_save_callback)
    bt_save.grid(column=0, row=17, padx=3, pady=3, sticky=W+E)

    bt_setup = Button(frame, text='Настроить', width=15, bg='ivory4', command=on_setup_callback)
    bt_setup.grid(column=1, row=17, padx=3, pady=3, sticky=W+E)

    lab = Label(frame, text="Имя файла")
    lab.grid(column=0, row=18)
    add_tooltip_by_name(lab, "Имя файла")

    text_field2 = Entry(frame, width=8, justify='center')
    text_field2.grid(column=1, row=18, sticky=W+E)
    set_text(text_field2, filename)
    add_tooltip_by_name(text_field2, "Имя файла")
    widget_dict["Имя файла"] = text_field2

    bt_show = Button(frame, text="Показать точки", bg="deep sky blue", command=on_show_offsets_callback)
    bt_show.grid(columnspan=2, row=21, padx=3, pady=3, sticky=W+E)

    bt_generate = Button(frame, text='Генерировать g-code файл', bg='lime green', command=on_generate_callback)
    bt_generate.grid(columnspan=2, row=22, padx=3, pady=3, sticky=W+E)

    return widget_dict
