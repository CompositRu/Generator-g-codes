'''
    This is program for creating g-codes files for CNC needlepunching machine.

    This is gui module. 
'''


from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox, Progressbar
import json
from generator_G_codes import *
from os import rename as rename_file
from os.path import exists as is_existed
import threading

try:
    import plotly.express as px
except Exception:
    px = None  # покажем понятную ошибку при попытке построения


def expand_with_neighbors(points, cell_size_x, cell_size_y):
    """Для каждой точки добавляет 8 соседей (3×3 без центра). Возвращает список новых точек."""
    if not points:
        return []
    dxs = (-cell_size_x, 0.0, cell_size_x)
    dys = (-cell_size_y, 0.0, cell_size_y)
    others = []
    for x, y in points:
        for dx in dxs:
            for dy in dys:
                if dx == 0.0 and dy == 0.0:
                    continue  # пропускаем исходную точку
                others.append([x + dx, y + dy])
    return others


def _plot_offsets(points, num_pitch, cell_size_x, cell_size_y, title = "Паттерн"):
    """Рисует точки, окрашивая точки пробитые на одном слое (каждые num_pitch последовательных точек) в один цвет."""

    if px is None:
        messagebox.showerror(
            "Plotly не установлен",
            "Для визуализации необходимо установить пакет plotly (и, возможно, pandas):\n\npip install plotly\npip install pandas",
        )
        return
    if not points:
        messagebox.showerror("Пусто", "Список точек пуст.")
        return

    # Для каждой точки определим номер группы, таким образом чтобы в группах было по num_pitch точек.
    group_idx = [i // num_pitch for i in range(len(points))]
    # Подпишем группы диапазонами индексов
    labels = []
    for gi in group_idx:
        start = gi * num_pitch + 1
        end = min((gi + 1) * num_pitch, len(points))
        labels.append(f"{gi} ({start}–{end} удары)")

    # Формируем список из имён групп без повторений. Т.к. set теряет порядок элементов, то используем его как вспомогательный контейнер
    # Строгий порядок гарантирует, что при перезапуске алгоритма цвета для слоёв будут теже самые
    seen = set() # вспомогательно множество для
    groups = [x for x in labels if not (x in seen or seen.add(x))]
    # альтернативное решение
    # groups_in_order = []
    # for lab in labels:
    #     if lab not in groups_in_order:
    #         groups_in_order.append(lab)
    
    palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    ]
    color_map = {g: palette[i % len(palette)] for i, g in enumerate(groups)}

    # --- соседи (8 на каждую исходную точку) ---
    others = expand_with_neighbors(points, cell_size_x, cell_size_y)
    xs_others = [p[0] for p in others]
    ys_others = [p[1] for p in others]
    labels_others = ["Соседние"] * len(others)

    # --- исходные точки и их групповые ярлыки ---
    xs_base = [p[0] for p in points]
    ys_base = [p[1] for p in points]

    # --- общий набор данных ---
    xs_all = xs_base + xs_others
    ys_all = ys_base + ys_others
    labels_all = labels + labels_others

    # --- цвета: 
    # Для точек на каждом пробитом слое выбираем один цвет из палитры,
    # Все соседние точки (пробитые сеседними иглами) окрашиваем в светло-серый
    color_map = {g: palette[i % len(palette)] for i, g in enumerate(groups)}
    color_map["Соседние"] = "#d3d3d3"  # lightgray

    # хотим порядок легенды: все группы по порядку, затем "Соседние"
    groups = groups + ["Соседние"]

    fig = px.scatter(
        x=xs_all, y=ys_all, color=labels_all,
        color_discrete_map=color_map,
        category_orders={"color": groups},
        labels={"x": "X", "y": "Y", "color": f"Слои (по {num_pitch} ударов)"},
        title=title,
    )

    fig.update_traces(mode="markers", marker=dict(size=12))
    fig.update_yaxes(scaleanchor="x", scaleratio=1) # одинаковый масштаб по X и Y
    fig.show()


def get_true_form_for_word_sloy(n):
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} слой"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} слоя"
    else:
        return f"{n} слоёв"


def click_show_offsets():
    """Визуализация паттерна пробивки"""
    try:
        cell_size_x = float(wd_left["Расстояние между иглами (мм)"]["X"].get())
        cell_size_y = float(wd_left["Расстояние между иглами (мм)"]["Y"].get())
        num_pitch = int(wd_left["Параметры паттерна"]["Кол-во ударов"].get())
        generate_nx_ny = bool(wd_left['Параметры паттерна']['Автоматическое определение формы паттерна'].get())
        nx = int(wd_left['Параметры паттерна']['nx'].get())
        ny = int(wd_left['Параметры паттерна']['ny'].get())
        is_random_offsets = bool(wd_left['Случайные смещения'].get())
        coefficient_random_offsets = float(wd_left['Коэффициент случайных смещений'].get())
        is_random_order = bool(wd_left['Случайный порядок ударов'].get())
    except Exception as e:
        messagebox.showerror("Не удалось прочитать числовые параметры.", str(e))
        return

    # Вычисляем параметры паттерна, если необходимо
    if generate_nx_ny:
        nx, ny = get_nx_ny(num_pitch)

    # функция берётся из generator_G_codes (уже импортирован)
    points = get_result_offset_list(nx, ny, cell_size_x, cell_size_y, is_random_offsets, coefficient_random_offsets, is_random_order)

    layers = nx * ny // num_pitch
    title = f"<b>Паттерн {nx}/{ny}/{num_pitch}</b>"
    title += f"<br>- Ячейка между иглами полностью забивается за {get_true_form_for_word_sloy(layers)}"
    if is_random_order:
        title += "<br>- Случайный порядок ударов формируется один раз и повторяется при создании всего каркаса"
    if is_random_offsets:
        title += "<br>- Случайные смещения для каждого удара вычисляются заного и не повторяются на каждом слое"

    _plot_offsets(points, num_pitch, cell_size_x, cell_size_y, title)


def is_opened_file(filename):
    if is_existed(filename):
        try:
            rename_file(filename, 'test.test')
            rename_file('test.test', filename)
            return False
        except OSError:
            return True
    return False


def centered_win(win):
    win.update_idletasks()
    positionRight = int(win.winfo_screenwidth() / 2 - win.winfo_reqwidth() / 2)
    positionDown = int(win.winfo_screenheight() / 2 - win.winfo_reqheight() / 2) - 30
    win.geometry(f'+{positionRight}+{positionDown}')


def set_text(text_field, text):
    text_field.delete(0, END)
    text_field.insert(0, text)


def recursion_saver(widget_dict):
    ''' Get data from all widgets to dict  '''
    data_dict = {}
    for section, item in widget_dict.items():
        if isinstance(item, dict):
            data_dict[section] = recursion_saver(item)
        elif isinstance(item, BooleanVar):
            data_dict[section] = bool(item.get())
        else:
            if section !=  "Имя файла":
                # Код ниже работает одновременно и для Entry, и для IntVar
                try:
                    data_dict[section] = int(item.get())
                except ValueError:
                    try:
                        data_dict[section] = float(item.get())
                    except ValueError:
                        print(section, item)
                        messagebox.showerror('Смотри, что пишешь!',  f'Значение {item.get()} параметра {section}  не является числом')
                        raise ValueError
            else:
                data_dict[section] = item.get()
    return data_dict


def write_to_json_file(file_name, data_dict):
    if is_opened_file(file_name):
        return
    with open(file_name, 'w', encoding='utf-8-sig') as f:
        f.write(json.dumps(data_dict, 
                            ensure_ascii=False,
                            indent=4))


def click_save():
    data_to_json = recursion_saver(wd_left)
    data_to_json["Список вариантов порядка прохождения рядов"] = order_list
    data_to_json["Порядок прохождения рядов"] = wd_right["Комбобокс порядок рядов"].get()
    data_to_json["Список вариантов задания размеров каркаса"] = type_frame_size_list
    data_to_json["Задание размеров каркаса"] = type_frame_size_list[data_to_json.pop("Номер радиокнопки типа задания размера каркаса")]
    
    write_to_json_file('data/data.json', data_to_json)

    combo = wd_right["Комбобокс выбор головы"]
    head_name = combo.get()
    heads['Выбранная игольница (ИП игольница)'] = head_name

    write_to_json_file('data/heads.json', heads)


def create_widgets_for_setup_win(win, section, item, i, delete_head_func):
    textfield_head_name = Entry(win, justify='center')
    set_text(textfield_head_name, section)
    textfield_head_name.grid(columnspan = 2, column=i, row=0)

    c = Canvas(win, width = 200, height = 200)
    c.grid(columnspan = 2, column=i, row=1)
    show_image(c, item['path'])

    label_x = Label(win, text='X')
    label_x.grid(column=i, row=2)
    label_y = Label(win, text='Y')
    label_y.grid(column=i, row=3)
    label_path = Label(win, text='Файл')
    label_path.grid(column=i, row=4)

    textfield_x = Entry(win)
    set_text(textfield_x, item['X'])
    textfield_x.grid(column=i+1, row=2)

    textfield_y = Entry(win)
    set_text(textfield_y, item['Y'])
    textfield_y.grid(column=i+1, row=3)

    path = Entry(win)  
    set_text(path, item['path'])
    path.grid(column=i+1, row=4)

    delete_button = Button(win, text = 'Удалить', command = delete_head_func(section))
    delete_button.grid(columnspan = 2, column=i, row=5, sticky=W+E, padx=10, pady=10)

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


def click_setup():
    win = Toplevel(window)
    win.title("Игольницы (ИП головы)")
    try:
        #На linux системах tkinter не отображает иконку в title bar окна
        win.iconbitmap('symbol.ico')
    except Exception:
        pass

    win.grab_set() # Блокирует другие окна Tkinter
    win.attributes('-topmost', 1) # Окно поверх других

    ''' Function for buttons "delete nead" '''
    def delete_head_func(head):
        def f():
            # удаляем из словаря виджетов, а из хедс удаляем по факту при сохранении
            # heads['Игольницы (ИП головы)'].pop(head)
            for name, widget in widgets[head].items():
                widget.destroy()
            widgets.pop(head)
            columnspan = len(widgets) * 2 + 2
            add_button.grid(columnspan = columnspan, row=6, sticky=W+E, padx=10, pady=0)
            save_button.grid(columnspan = columnspan, row=7, sticky=W+E, padx=10, pady=10)
        return f

    i, widgets = 0, {}
    for section, item in heads["Игольницы (ИП головы)"].items():
        widgets[section] = create_widgets_for_setup_win(win, section, item, i, delete_head_func)
        i += 2

    def add_widget():
        idx = len(widgets) + 1
        i2 = len(widgets) * 2
        name = f"Г{idx}"
        parameters = {"X": idx, "Y": idx, "path": "введите имя"}
        widgets[name] = create_widgets_for_setup_win(win, name, parameters, i2, delete_head_func)
        add_button.grid(columnspan = i2 + 2, row=6, sticky=W+E, padx=10, pady=0)
        save_button.grid(columnspan = i2 + 2, row=7, sticky=W+E, padx=10, pady=10)

    add_button = Button(win, 
                        text = 'Добавить голову', 
                        command = add_widget)
    add_button.grid(columnspan = len(heads['Игольницы (ИП головы)'])*2 + 20,
                    row=6, 
                    sticky=W+E, 
                    padx=10, 
                    pady=0)

    def save_data_heads():
        combo = wd_right["Комбобокс выбор головы"]
        head_name = combo.get()
        heads['Выбранная игольница (ИП игольница)'] = head_name

        # Проверка данных
        for _, widget in widgets.items():
            try:
                x = int(widget['X'].get())
                y = int(widget['Y'].get())
            except ValueError:
                messagebox.showerror('Смотри, что пишешь!', 'Количеством игл может быть только целое число')
                return

        heads["Игольницы (ИП головы)"].clear()
        head_needles = heads["Игольницы (ИП головы)"]
 
        # Сохранение данных
        for head, widget in widgets.items():
            head_name = widget['head_name'].get()
            head_needles[head_name] = {}
            head_data = head_needles[head_name] 
            head_data['X'] = int(widget['X'].get())
            head_data['Y'] = int(widget['Y'].get())
            head_data['path'] = widget['path'].get()

        write_to_json_file('data/heads.json', heads)

        combo = wd_right["Комбобокс выбор головы"]
        idx = combo['values'].index(combo.get())

        combo['values'] = [section for section, item in heads["Игольницы (ИП головы)"].items()]

        combo.current(idx if idx < len(combo['values']) else 0)
        heads['Выбранная игольница (ИП игольница)'] = combo.get()

        # Обновляем главное окно. Событие не используется.
        change_pic(None);

    save_button = Button(win, 
                        text = 'Сохранить', 
                        bg='ivory4', 
                        command = save_data_heads)
    save_button.grid(columnspan = len(heads['Игольницы (ИП головы)']) * 2, 
                    row = 7, 
                    sticky = W + E, 
                    padx = 10, 
                    pady = 10)
    centered_win(win)
    win.resizable(False, False)


def is_big_size_future_file(data_dict):
    ''' For warning user that future file will be big '''
    l = data_dict['Количество слоёв']
    e = data_dict['Количество пустых слоёв']
    x = data_dict['Количество шагов головы']['X']
    y = data_dict['Количество шагов головы']['Y']
    n = data_dict['Параметры паттерна']['Кол-во ударов']
    hits = (l + e) * x * y * n
    if hits > 100_000:
        return True
    return False


def get_data_for_generating():
    ''' Get dict with all settings '''
    data = recursion_saver(wd_left)

    data["Порядок прохождения рядов"] = wd_right["Комбобокс порядок рядов"].get()
    data["Задание размеров каркаса"] = type_frame_size_list[data.pop("Номер радиокнопки типа задания размера каркаса")]
    combo = wd_right["Комбобокс выбор головы"]
    head_name = combo.get()
    heads['Выбранная игольница (ИП игольница)'] = head_name
    return {**data, **heads}


def check_all_conditions(data_dict):
    # Проверяем наличие всех ключей в json файле
    message = check_dict_keys(data_dict)
    if message != '':
        messagebox.showerror('Отсутствует параметр в json файле', message)
        return False

    #Проверяем файл
    if is_opened_file(data_dict["Имя файла"]):
        messagebox.showerror('Файл открыт в другой программе', f'Закройте файл {data_dict["Имя файла"]}.')  
        return False

    # Проверяем размер будущего файла   
    if is_big_size_future_file(data_dict):
        res = messagebox.askyesno('Создаётся большой файл', 
            'Файл с g кодами содержит больше 100 000 ударов. Вы уверены, что хотите его создать?')
        return res

    return True


def click_generate():
    # Обновляем данные   
    try:
        data_dict = get_data_for_generating()
    except ValueError:
        return

    # Проверяем входные данные
    if not check_all_conditions(data_dict):
        return

    # Окно с progress bar
    win = Toplevel(window)
    try:
        #На linux системах tkinter не отображает иконку в title bar окна
        win.iconbitmap('symbol.ico')
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
    threading.Thread(target=lambda : progress_generate(win, bar, data_dict)).start()


def progress_generate(win_with_progress, bar, data_dict):
    # Создаём функцию для отображения процесса на progressbar
    def display_progress(progress):
        bar['value'] = progress
    
    # Генерируем
    try:
        generate_G_codes_file(data_dict, display_progress)
    except BaseException as e:
        win_with_progress.destroy()
        messagebox.showerror('Всё. Херня. Звони Артёму', e)
        return

    # Закрываем окно
    win_with_progress.destroy()
    messagebox.showinfo('Всё прошло удачно', f"Сгенерирован файл\n{get_filename(data_dict)}\n\n{get_message(data_dict)}" ) 


def display_parameters_recursion(frame, data_dict, i_row):
    widget_dict = {}
    labels_dict = {}
    i = i_row
    for section, item in data_dict.items():
        if isinstance(item, dict): 
            l = Label(frame, text='\n'+section, font=("Arial Bold", 10, 'bold'))
            l.grid(columnspan=2, row=i, sticky=N)
            i += 1
            labels_dict[section + ' label'] = l
            widget_dict[section], labels_dict[section], i = display_parameters_recursion(frame, item, i)
        elif isinstance(item, bool):
            var = BooleanVar(value=item)
            cb = Checkbutton(frame, text=section, variable=var)
            cb.grid(columnspan=2, row=i, sticky=W)
            widget_dict[section] = var
            # сохраним сам чекбокс в labels_dict — у него тоже есть grid()/grid_remove()
            labels_dict[section] = cb
            i += 1        
        else:
            lab = Label(frame, text = section)
            lab.grid(column=0, row=i, sticky=N)
            text_field = Entry(frame, width = 8, justify='center')
            text_field.grid(column=1, row=i, sticky=N)
            set_text(text_field, item)
            widget_dict[section] = text_field
            labels_dict[section] = lab
            i += 1
    return widget_dict, labels_dict, i


def change_pattern_parameters_visibility():
    """Если включено 'Автоматическое определение формы паттерна',
    скрываем поля nx/ny и их лейблы; иначе показываем."""
    try:
        auto_var = wd_left["Параметры паттерна"]["Автоматическое определение формы паттерна"]
        nx_entry = wd_left["Параметры паттерна"]["nx"]
        ny_entry = wd_left["Параметры паттерна"]["ny"]
        nx_label = wd_labels["Параметры паттерна"]["nx"]
        ny_label = wd_labels["Параметры паттерна"]["ny"]
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


def change_probivka_visibility():
    """Если включено 'Пробивка с нарастанием глубины',
    показываем поле 'Начальная глубина удара'; иначе скрываем."""
    try:
        probivka_var = wd_left["Пробивка"]["Пробивка с нарастанием глубины"]
        depth_entry = wd_left["Пробивка"]["Начальная глубина удара (мм)"]
        depth_label = wd_labels["Пробивка"]["Начальная глубина удара (мм)"]
    except KeyError:
        return

    widgets = (depth_entry, depth_label)

    if isinstance(probivka_var, BooleanVar) and probivka_var.get():
        for w in widgets:
            w.grid()
    else:
        for w in widgets:
            w.grid_remove()


def change_visible():
    group_1 = [wd_left['Количество шагов головы']['X'],
               wd_left['Количество шагов головы']['Y'],
               wd_labels['Количество шагов головы']['X'],
               wd_labels['Количество шагов головы']['Y'],
               wd_labels['Количество шагов головы label']]
    group_2 = [wd_left['Габариты каркаса']['X'],
               wd_left['Габариты каркаса']['Y'],
               wd_labels['Габариты каркаса']['X'],
               wd_labels['Габариты каркаса']['Y'],
               wd_labels['Габариты каркаса label']]

    def group_grid_remove(group):
        for item in group:
            item.grid_remove()
    def group_grid(group):
        for item in group:
            item.grid()

    n = wd_left['Номер радиокнопки типа задания размера каркаса'].get()
    if n == 1:
        group_grid_remove(group_1)
        group_grid(group_2)
    else:
        group_grid_remove(group_2)
        group_grid(group_1)


def display_parameters(frame, data_dict, i_row):
    part_data_dict = {}
    part_data_dict['Количество шагов головы'] = data_dict.pop('Количество шагов головы')
    part_data_dict['Габариты каркаса'] = data_dict.pop('Габариты каркаса')

    widget_dict, labels_dict, i = display_parameters_recursion(frame, data_dict, i_row)

    label_empty = Label(frame)
    label_empty.grid(columnspan=2, row=i, sticky=N+S)
    frame.rowconfigure(i, weight=1) # Эта строка нужна, чтобы виджет мог растягиваться
    i += 1

    l = Label(frame, text = "\nТип задания размеров каркаса:", font=("Arial Bold", 10, 'bold'))
    l.grid(columnspan=2, row = i)
    i += 1
    var = IntVar()
    var.set(type_frame_size_list.index(selected_type_frame_size))
    for j, order in enumerate(type_frame_size_list):
        r = Radiobutton(frame, text = order, value = j, variable = var, command=change_visible)
        r.grid(columnspan=2, row = i, padx = 50, sticky=W)
        i += 1
    widget_dict['Номер радиокнопки типа задания размера каркаса'] = var

    wd, wl, i = display_parameters_recursion(frame, part_data_dict, i)
    widget_dict = {**widget_dict, **wd}
    labels_dict = {**labels_dict, **wl}
    return widget_dict, labels_dict


def show_image(canvas, filename):
    img = None
    try:
        img = PhotoImage(file='data/' + filename)
    except:
        try:
            img = PhotoImage(file='data/undefined.png')
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
        canvas.create_image(0,0, anchor=NW, image=img)


def change_pic(event):
    canvas = wd_right["Полотно"]
    combo = wd_right["Комбобокс выбор головы"]
    label_x_needle = wd_right["Лейблы с количеством игл"][0]
    label_y_needle = wd_right["Лейблы с количеством игл"][1]

    canvas.delete("all")
    head_name = combo.get()
    heads['Выбранная игольница (ИП игольница)'] = head_name
    new_x_needle = heads['Игольницы (ИП головы)'][head_name]['X']
    new_y_needle = heads['Игольницы (ИП головы)'][head_name]['Y']
    label_x_needle.config(text = 'Х      ' + str(new_x_needle))
    label_y_needle.config(text = 'Y      ' + str(new_y_needle))
    filename = heads['Игольницы (ИП головы)'][head_name]['path']
    show_image(canvas, filename)


def display_right_side_top(frame):
    canvas = Canvas(frame, width = 200, height = 200)
    canvas.grid(columnspan=2, row=0)
    
    lab = Label(frame, text="ИП голова:", padx= 20, font=("Arial Bold", 10))
    lab.grid(column=0, row=1)

    val = []
    for section, item in heads["Игольницы (ИП головы)"].items():
        val.append(section)
    combo = Combobox(frame, width = 10, values=val, state='readonly')
    combo.current(val.index(heads["Выбранная игольница (ИП игольница)"]))  
    combo.grid(column=1, row=1)

    head_name = combo.get()
    filename = heads['Игольницы (ИП головы)'][head_name]['path']
    show_image(canvas, filename) 

    combo.bind('<<ComboboxSelected>>', change_pic)

    lab = Label(frame, text = 'Игольницы (ИП головы):', font=("Arial Bold", 10, 'bold'))
    lab.grid(columnspan=2, row=2)

    X_needles = heads['Игольницы (ИП головы)'][head_name]['X']
    lab_x = Label(frame, text = 'Х      ' + str(X_needles))
    lab_x.grid(columnspan=2, row=3)

    Y_needles = heads['Игольницы (ИП головы)'][head_name]['Y']
    lab_y = Label(frame, text = 'Y      ' + str(Y_needles))
    lab_y.grid(columnspan=2, row=4)

    widget_dict = {}
    widget_dict["Полотно"] = canvas
    widget_dict["Комбобокс выбор головы"] = combo
    widget_dict["Лейблы с количеством игл"] = (lab_x, lab_y)

    return widget_dict


def display_order_combobox(frame):
    """Комбобокс 'Порядок прохождения рядов' вместо радиокнопок."""
    lbl = Label(frame, text="Порядок прохождения рядов:", font=("Arial Bold", 10, "bold"))
    lbl.grid(columnspan=2, row=5)

    combo = Combobox(frame, width=18, values=order_list, state="readonly")
    try:
        combo.current(order_list.index(selected_order))
    except Exception:
        combo.current(0)
    combo.grid(columnspan=2, row=6, padx=50, sticky=E+W)

    return combo


def change_visible_filename():
    n = wd_left['Автоматическая генерация имени файла'].get()
    state = 'normal' if n == 0 else 'disabled'
    wd_left['Имя файла'].config(state=state)


def display_right_side_bottom(frame):
    widget_dict = {}
    def create_check_box(section, row, func = None):
        v = BooleanVar()
        v.set(second_dict[section])
        widget_dict[section] = v
        checkbox = Checkbutton(frame, text=section, variable=v, font=("Arial Bold", 10, 'bold'), command=func)
        checkbox.grid(columnspan=2, row=row, sticky=W)

    create_check_box("Случайный порядок ударов", 11)
    create_check_box("Случайные смещения", 12)

    lab = Label(frame, text = "Коэффициент")
    lab.grid(column=0, row=13)

    text_field1 = Entry(frame, width = 8, justify='center')
    text_field1.grid(column=1, row=13)
    set_text(text_field1, second_dict["Коэффициент случайных смещений"])
    widget_dict["Коэффициент случайных смещений"] = text_field1

    create_check_box("Чередование направлений прохода слоя", 14)

    '''label_empty = Label(right_desk)
    label_empty.grid(columnspan=2, row=15, sticky=N+S)
    frame.rowconfigure(15, weight=1) # Эта строка нужна, чтобы виджет мог растягиваться '''

    create_check_box("Создание файла на рабочем столе", 15)
    create_check_box("Автоматическая генерация имени файла", 16, change_visible_filename)

    bt_save = Button(frame, text='Сохранить', width = 15, bg='ivory4', command=click_save)
    bt_save.grid(column=0, row=17, padx=3, pady=3, sticky=W+E)

    bt_setup = Button(frame, text='Настроить', width = 15, bg='ivory4', command=click_setup)
    bt_setup.grid(column=1, row=17, padx=3, pady=3, sticky=W+E)

    lab = Label(frame, text = "Имя файла")
    lab.grid(column=0, row=18)

    text_field2 = Entry(frame, width = 8, justify='center')
    text_field2.grid(column=1, row=18, sticky=W+E)
    set_text(text_field2, filename)
    widget_dict["Имя файла"] = text_field2

    bt_generate = Button(frame, text='Генерировать g-code файл', bg='lime green', command=click_generate)
    bt_generate.grid(columnspan=2, row=22, padx=3, pady=3, sticky=W+E)

    bt_show = Button(frame, text="Показать точки", bg="deep sky blue", command=click_show_offsets)
    bt_show.grid(columnspan=2, row=21, padx=3, pady=3, sticky=W + E)

    return widget_dict


if __name__ == "__main__":
    #Открываем файл с конфигами
    with open('data/data.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)

    filename = data.pop("Имя файла")

    second_dict = {}
    error_message = ''
    order_list, selected_order, type_frame_size_list, selected_type_frame_size = None, None, None, None
    try:
        second_dict["Случайный порядок ударов"] = data.pop("Случайный порядок ударов")
        second_dict["Случайные смещения"] = data.pop("Случайные смещения")
        second_dict["Коэффициент случайных смещений"] = data.pop("Коэффициент случайных смещений")
        second_dict["Чередование направлений прохода слоя"] = data.pop("Чередование направлений прохода слоя")
        second_dict["Автоматическая генерация имени файла"] = data.pop("Автоматическая генерация имени файла")
        second_dict["Создание файла на рабочем столе"] = data.pop("Создание файла на рабочем столе")

        order_list = data.pop("Список вариантов порядка прохождения рядов")
        selected_order = data.pop("Порядок прохождения рядов")
        type_frame_size_list = data.pop("Список вариантов задания размеров каркаса")
        selected_type_frame_size = data.pop("Задание размеров каркаса")
    except KeyError as ke:
        error_message = f'В data.json файле не хватает параметра {ke}'

    #Открываем файл с конфигами голов
    with open('data/heads.json', 'r', encoding='utf-8-sig') as f:
        heads = json.load(f)

    window = Tk()  
    window.title("Генератор G кодов для ИП станка v.1.9.0")

    try:
        #На linux системах tkinter не отображает иконку в title bar окна
        window.iconbitmap('symbol.ico')
    except Exception as e:
        print(f"Ошибка: {e}")

    if error_message == '':
        window.columnconfigure(0, weight=1)
        window.columnconfigure(1, weight=1)
        window.rowconfigure(0, weight=1)

        left_desk = Frame(window, padx=5, pady=5)
        left_desk.grid(column=0, row=0, sticky=N+S)
        right_desk = Frame(window, padx=5, pady=5)
        right_desk.grid(column=1, row=0, sticky=N+S)

        wd_left, wd_labels = display_parameters(left_desk,  data, 0)
        change_visible()

        # Добавляем колбэк на чекбокс на левой панеле
        try:
            auto_var = wd_left["Параметры паттерна"]["Автоматическое определение формы паттерна"]
            if isinstance(auto_var, BooleanVar):
                auto_var.trace_add("write", lambda *args: change_pattern_parameters_visibility())
            # первичная установка видимости
            change_pattern_parameters_visibility()
        except KeyError:
            pass

        # Колбэк для чекбокса "Пробивка с нарастанием глубины"
        try:
            probivka_var = wd_left["Пробивка"]["Пробивка с нарастанием глубины"]
            if isinstance(probivka_var, BooleanVar):
                probivka_var.trace_add("write", lambda *args: change_probivka_visibility())
            change_probivka_visibility()
        except KeyError:
            pass

        wd_right = display_right_side_top(right_desk)
        wd_right["Комбобокс порядок рядов"] = display_order_combobox(right_desk)
        wd_right_bottom = display_right_side_bottom(right_desk)
        wd_left = {**wd_left, **wd_right_bottom}
        change_visible_filename()
    else:
        messagebox.showerror('Отсутствует параметр в json файле', error_message)
    
    centered_win(window)
    window.resizable(False, False)
    window.mainloop()