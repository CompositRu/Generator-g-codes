'''
    This is program for creating g-codes files for CNC needlepunching machine.

    This module is gui. 
'''


from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox, Progressbar
import json
from generator_G_codes import *
from os import rename as rename_file
from os.path import exists as is_existed
import threading


def is_opened_file(filename):
    if is_existed(filename):
        try:
            rename_file(filename, 'test.test')
            rename_file('test.test', filename)
            return False
        except OSError:
            messagebox.showerror('Закрой файл ' + filename, 'файл ' + filename + ' открыт в другой программе')
            return True
    return False


def centered_win(win):
    win.update_idletasks()
    positionRight = int(win.winfo_screenwidth()/2 - win.winfo_reqwidth()/2)
    positionDown = int(win.winfo_screenheight()/2 - win.winfo_reqheight()/2) - 30
    win.geometry("+{}+{}".format(positionRight, positionDown))


def set_text(text_field, text):
    text_field.delete(0,END)
    text_field.insert(0,text)


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
                        messagebox.showerror('Смотри, что пишешь!', item.get() + ' не является числом')
            else:
                data_dict[section] = item.get()
    return data_dict


def write_to_json_file(file_name, data_dict):
    if is_opened_file(file_name):
        return
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data_dict, 
                            ensure_ascii=False,
                            indent=4))


def click_save():
    data_to_json = recursion_saver(wd_left)
    data_to_json["Список вариантов порядка прохождения рядов"] = order_list
    data_to_json["Порядок прохождения рядов"] = order_list[data_to_json.pop("Номер радиокнопки")]

    write_to_json_file('data.json', data_to_json)

    combo = wd_right["Комбобокс выбор головы"]
    head_name = combo.get()
    heads['Выбранная голова'] = head_name

    write_to_json_file('heads.json', heads)


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

    head_widgets = {}
    head_widgets['head_name'] = textfield_head_name 
    head_widgets['canvas'] = c
    head_widgets['label_x'] = label_x
    head_widgets['label_y'] = label_y
    head_widgets['label_path'] = label_path
    head_widgets['delete_button'] = delete_button
    head_widgets['X'] = textfield_x
    head_widgets['Y'] = textfield_y
    head_widgets['path'] = path

    return head_widgets


def click_setup():
    win = Toplevel(window)
    win.title("Количество рядов игл на голове")
    win.iconbitmap('symbol.ico')
    win.grab_set()
    win.resizable(False, False)
    
    i, widgets = 0, {}

    ''' Function for buttons "delete nead" '''
    def delete_head_func(head):
        def f():
            # удаляем из словаря виджетов, а из хедс удаляем по факту при сохранении
            # heads['Количество рядов игл на голове'].pop(head)
            for name, widget in widgets[head].items():
                widget.destroy()
            widgets.pop(head)
            add_button.grid(columnspan = len(widgets)*2, row=6, sticky=W+E, padx=10, pady=0)
            save_button.grid(columnspan = len(widgets)*2, row=7, sticky=W+E, padx=10, pady=10)
        return f

    for section, item in heads["Количество рядов игл на голове"].items():
        widgets[section] = create_widgets_for_setup_win(win, section, item, i, delete_head_func)
        i += 2

    def add_widget():
        i = len(widgets) * 2
        name = "Г" + str(len(widgets) + 1)
        parameters = {}
        parameters['X'] = len(widgets) + 1
        parameters['Y'] = len(widgets) + 1
        parameters['path'] = 'введите имя'
        widgets[name] = create_widgets_for_setup_win(win, name, parameters, i, delete_head_func)
        add_button.grid(columnspan = len(widgets)*2, row=6, sticky=W+E, padx=10, pady=0)
        save_button.grid(columnspan = len(widgets)*2, row=7, sticky=W+E, padx=10, pady=10)

    add_button = Button(win, 
                        text = 'Добавить голову', 
                        command = add_widget)
    add_button.grid(columnspan = len(heads['Количество рядов игл на голове'])*2, 
                    row=6, 
                    sticky=W+E, 
                    padx=10, 
                    pady=0)

    def save_data_heads():
        combo = wd_right["Комбобокс выбор головы"]
        head_name = combo.get()
        heads['Выбранная голова'] = head_name

        # Проверка данных
        for head, widget in widgets.items():
            try:
                x = int(widget['X'].get())
                y = int(widget['Y'].get())            
            except ValueError:
                messagebox.showerror('Смотри, что пишешь!', 'Количеством игл может быть только целое число')
                return

        heads["Количество рядов игл на голове"].clear()

        # Сохранение данных
        for head, widget in widgets.items():
            head_name = widget['head_name'].get()
            head_data = heads["Количество рядов игл на голове"][head_name]
            head_data = {}
            head_data['X'] = int(widget['X'].get())
            head_data['Y'] = int(widget['Y'].get())            
            head_data['path'] = widget['path'].get()  

        write_to_json_file('heads.json', heads)

        combo = wd_right["Комбобокс выбор головы"]
        val = []
        for section, item in heads["Количество рядов игл на голове"].items():
            val.append(section)
        combo['values'] = val

    save_button = Button(win, 
                        text = 'Сохранить', 
                        bg='ivory4', 
                        command = save_data_heads)
    save_button.grid(columnspan = len(heads['Количество рядов игл на голове'])*2, 
                    row=7, 
                    sticky=W+E, 
                    padx=10, 
                    pady=10)


def is_big_size_futute_file(data_dict):
    ''' For warning user that future file will be big'''
    l = data_dict['Количество слоёв']
    i = data_dict['Количество пустых слоёв']
    x = data_dict['Количество шагов головы']['X']
    y = data_dict['Количество шагов головы']['Y']
    n = data_dict['Параметры паттерна']['Кол-во ударов']
    hits = (l + i) * x * y * n
    if hits > 100000:
        return True
    return False


def get_data_for_generating():
    ''' Get dict with all settings'''
    data = recursion_saver(wd_left)
    data["Порядок прохождения рядов"] = order_list[data.pop("Номер радиокнопки")]
    combo = wd_right["Комбобокс выбор головы"]
    head_name = combo.get()
    heads['Выбранная голова'] = head_name    
    return {**data, **second_dict, **heads}


def click_generate():
    win = Toplevel(window)
    win.iconbitmap('symbol.ico')
    def window_deleted():
        pass
    win.protocol('WM_DELETE_WINDOW', window_deleted)
    bar = Progressbar(win, length=300)
    bar.pack()
    centered_win(win)
    ''' Use thread for showing progress bar in process generating '''
    threading.Thread(target=lambda : progress_generate(win, bar)).start()


def progress_generate(win_with_progress, bar):
    # Обновляем данные   
    data_dict = get_data_for_generating()

    # Проверяем наличие всех ключей в json файле
    message = check_dict_keys(data_dict)
    if message != '':
        messagebox.showerror('Отсутствует в json файле', message)
        return

    #Проверяем файл
    if is_opened_file(data_dict["Имя файла"]):  
        return

    # Проверяем размер будущего файла   
    if is_big_size_futute_file(data_dict):
        res = messagebox.askyesno('Создаётся большой файл', 
            'Файл с g кодами содержит больше 100 000 ударов. Вы уверены, что хотите его создать?')
        win_with_progress.lift()
        if res == False:
            win_with_progress.destroy()
            return       

    # Создаём функцию для отображения процесса на progressbar
    def display_progress(progress):
        bar['value'] = progress
    # Генерируем
    generate_G_codes_file(data_dict, display_progress)
    # Закрываем окно
    win_with_progress.destroy()
    messagebox.showinfo('Всё прошло удачно! Наверно...', 'Сгенерирован файл с g-кодами') 


def display_parameters(frame, data_dict, i_row):
    widget_dict = {}
    i = i_row
    for section, item in data_dict.items():
        if isinstance(item, dict): 
            l = Label(frame, text='\n'+section, font=("Arial Bold", 10, 'bold'))
            l.grid(columnspan=2, row=i)
            i+=1
            widget_dict[section], i = display_parameters(frame, item, i)         
        else:
            lab = Label(frame, text = section)
            lab.grid(column=0, row=i)
            text_field = Entry(frame, width = 8, justify='center')
            text_field.grid(column=1, row=i)
            set_text(text_field, item)
            widget_dict[section] = text_field
            i+=1
    return widget_dict, i


def show_image(canvas, filename):
    img = None
    try:
        img = PhotoImage(file=filename)
    except:
        try:
            img = PhotoImage(file='undefined.png')
        except:
            title = 'Опять что-то менял в файлах? Зовите'
            message = 'Отсутствует файл изображения головы (формат - 200х200, \
расширение - .png) и файл undefined.png для отображения иглопробивных голов, \
для которых ещё не указали файл с их фотографией'
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
    heads['Выбранная голова'] = head_name
    new_x_needle = heads['Количество рядов игл на голове'][head_name]['X']
    new_y_needle = heads['Количество рядов игл на голове'][head_name]['Y']
    label_x_needle.config(text = 'Х      ' + str(new_x_needle))
    label_y_needle.config(text = 'Y      ' + str(new_y_needle))
    filename = heads['Количество рядов игл на голове'][head_name]['path']
    show_image(canvas, filename)


def display_right_side_top(frame):
    canvas = Canvas(frame, width = 200, height = 200)      
    canvas.grid(columnspan=2, row=0)
    
    lab = Label(frame, text="ИП голова:", padx= 20, font=("Arial Bold", 10))   
    lab.grid(column=0, row=1)

    val = []
    for section, item in heads["Количество рядов игл на голове"].items():
        val.append(section)
    combo = Combobox(frame, width = 10, values=val, state='readonly')  
    combo.current(val.index(heads["Выбранная голова"]))  
    combo.grid(column=1, row=1)

    head_name = combo.get()
    filename = heads['Количество рядов игл на голове'][head_name]['path']
    show_image(canvas, filename) 

    combo.bind('<<ComboboxSelected>>', change_pic)

    lab = Label(frame, text = '\nКоличество рядов игл на голове:', font=("Arial Bold", 10, 'bold'))
    lab.grid(columnspan=2, row=2)

    X_needles = heads['Количество рядов игл на голове'][head_name]['X']
    lab_x = Label(frame, text = 'Х      ' + str(X_needles))
    lab_x.grid(columnspan=2, row=3)

    Y_needles = heads['Количество рядов игл на голове'][head_name]['Y']
    lab_y = Label(frame, text = 'Y      ' + str(Y_needles))
    lab_y.grid(columnspan=2, row=4)

    widget_dict = {}
    widget_dict["Полотно"] = canvas
    widget_dict["Комбобокс выбор головы"] = combo
    widget_dict["Лейблы с количеством игл"] = (lab_x, lab_y)

    return widget_dict


def display_radiobuttons(frame):
    l = Label(frame, text = "Порядок прохождения рядов:", font=("Arial Bold", 10, 'bold'))
    l.grid(columnspan=2, row = 5)
    v = IntVar()
    v.set(order_list.index(selected_order))
    for i, order in enumerate(order_list):
        r = Radiobutton(frame, text = order, value = i, variable = v)
        r.grid(columnspan=2, row = 6 + i, padx = 50, sticky=W)
    return v


def display_right_side_bottom(frame):
    var1 = BooleanVar()
    var1.set(second_dict["Случайный порядок ударов"])
    chkb1 = Checkbutton(right_desk, text="Случайный порядок ударов", variable=var1, font=("Arial Bold", 10, 'bold'))
    chkb1.grid(columnspan=2, row=11, sticky=W)

    lab = Label(right_desk, text = "Коэффициент")
    lab.grid(column=0, row=13)

    text_field1 = Entry(right_desk, width = 8, justify='center')
    text_field1.grid(column=1, row=13)
    set_text(text_field1, second_dict["Коэффициент случайных смещений"])

    var2 = BooleanVar()
    var2.set(second_dict["Случайные смещения"])
    chkb2 = Checkbutton(right_desk, text="Случайные смещения", variable=var2, font=("Arial Bold", 10, 'bold'))
    chkb2.grid(columnspan=2, row=12, sticky=W)

    label_empty = Label(right_desk, text='\n'*1)
    label_empty.grid(columnspan=2, row=14, sticky=N+S)

    bt_save = Button(right_desk, text='Сохранить', width = 15, bg='ivory4', command=click_save)
    bt_save.grid(column=0, row=15, padx=3, pady=3, sticky=W+E)

    bt_setup = Button(right_desk, text='Настроить', width = 15, bg='ivory4', command=click_setup)
    bt_setup.grid(column=1, row=15, padx=3, pady=3, sticky=W+E)

    lab = Label(right_desk, text = "Имя файла")
    lab.grid(column=0, row=16)

    text_field2 = Entry(right_desk, width = 8, justify='center')
    text_field2.grid(column=1, row=16, sticky=W+E)
    set_text(text_field2, filename)

    bt_generate = Button(right_desk, text='Генерировать g-code файл', bg='lime green', command=click_generate)
    bt_generate.grid(columnspan=2, row=17, padx=3, pady=3, sticky=W+E)

    widget_dict = {}
    widget_dict["Случайный порядок ударов"] = var1
    widget_dict["Случайные смещения"] = var2
    widget_dict["Коэффициент случайных смещений"] = text_field1
    widget_dict["Имя файла"] = text_field2

    return widget_dict


if __name__ == "__main__":
    #Открываем файл с конфигами
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    filename = data.pop("Имя файла")

    second_dict = {}
    second_dict["Случайный порядок ударов"] = data.pop("Случайный порядок ударов")
    second_dict["Случайные смещения"] = data.pop("Случайные смещения")
    second_dict["Коэффициент случайных смещений"] = data.pop("Коэффициент случайных смещений")

    order_list = data.pop("Список вариантов порядка прохождения рядов")
    selected_order = data.pop("Порядок прохождения рядов")

    #Открываем файл с конфигами голов
    with open('heads.json', 'r', encoding='utf-8') as f:
        heads = json.load(f)

    window = Tk()  
    window.title("Генератор G кодов для ИП станка v.1.3")
    window.iconbitmap('symbol.ico')

    left_desk = Frame(window, padx=5, pady=5)
    left_desk.grid(column=0, row=0)
    right_desk = Frame(window, padx=5, pady=5)
    right_desk.grid(column=1, row=0, sticky=N+S)

    wd_left, i = display_parameters(left_desk,  data, 0)
    wd_right = display_right_side_top(right_desk)
    wd_left["Номер радиокнопки"] = display_radiobuttons(right_desk)
    wd_right_bottom = display_right_side_bottom(right_desk)
    wd_left = {**wd_left, **wd_right_bottom}
    

    centered_win(window)
    window.resizable(False, False)
    window.mainloop()

