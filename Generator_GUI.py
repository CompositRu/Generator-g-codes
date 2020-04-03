from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Combobox
import json
from generator_G_codes import *
from os import rename as rename_file
#from PIL import ImageTk


def is_opened_file(filename):
    try: 
        rename_file(filename, 'test.test')
        rename_file('test.test', filename)
        return False
    except OSError:
        messagebox.showerror('Закрой файл ' + filename, 'файл ' + filename + ' открыт в другой программе')
        return True


def centered_win(win):
    win.update_idletasks()
    positionRight = int(win.winfo_screenwidth()/2 - win.winfo_reqwidth()/2)
    positionDown = int(win.winfo_screenheight()/2 - win.winfo_reqheight()/2) - 30
    win.geometry("+{}+{}".format(positionRight, positionDown))


def set_text(text_field, text):
    text_field.delete(0,END)
    text_field.insert(0,text)


def recursion_saver(widget_dict):
    data_dict = {}
    for section, item in widget_dict.items():
        if isinstance(item, dict):
            data_dict[section] = recursion_saver(item)
        elif isinstance(item, BooleanVar):
            data_dict[section] = bool(item.get())
        else:
            try:
                data_dict[section] = int(item.get())
            except ValueError:
                try:
                    data_dict[section] = float(item.get())
                except ValueError:
                    messagebox.showerror('Смотри, что пишешь!', item.get() + ' не является числом')
    return data_dict


def write_json_file(file_name, data_dict):
    if is_opened_file(file_name):
        return
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data_dict, 
                            ensure_ascii=False,
                            indent=4))


def click_save():
    data_to_json = recursion_saver(wd_left)
    write_json_file('data.json', data_to_json)

    combo = wl_right[1][1]
    head_name = combo.get()
    heads['Выбранная голова'] = head_name
    write_json_file('heads.json', heads)


def click_setup():
    messagebox.showwarning('Вот так вот', 'Эта функция пока не работает') 


def is_big_size_futute_file(data_dict):
    l = data_dict['Количество слоёв']
    i = data_dict['Количество пустых слоёв']
    x = data_dict['Количество шагов головы']['X']
    y = data_dict['Количество шагов головы']['Y']
    n = data_dict['Параметры паттерна']['Кол-во ударов']
    hits = (l + i) * x * y * n
    print(hits)
    if hits > 100000:
        return True
    return False


def click_generate():
    # Обновляем данные
    data = recursion_saver(wd_left)
    combo = wl_right[1][1]
    head_name = combo.get()
    heads['Выбранная голова'] = head_name    
    data_dict = {**data, **second_dict, **heads}

    # Проверяем данные
    message = check_dict_keys(data_dict)
    if message != '':
        messagebox.showerror('Отсутствует в json файле', message)
        return
    if is_big_size_futute_file(data_dict):
        res = messagebox.askyesno('Создаётся большой файл', 
            'Файл с g кодами содержит больше 100 000 ударов. Вы уверены, что хотите его создать?')
        if res == False:
            return
    
    # Проверяем файл
    if is_opened_file("G-code.tap"):
        return

    # Генерируем
    generate_G_codes_file(data_dict)
    messagebox.showinfo('Всё прошло удачно! Наверно...', 'Сгенерирован файл с g кодами') 


def display_parameters(frame, data_dict, i_row):
    widget_dict = {}
    i = i_row
    for section, item in data_dict.items():
        if isinstance(item, dict): 
            l = Label(frame, text='\n'+section, font=("Arial Bold", 10, 'bold'))
            l.grid(columnspan=2, row=i)
            i+=1
            widget_dict[section], i = display_parameters(frame, item, i)         
            '''
        elif isinstance(item, bool):
            var = BooleanVar()
            var.set(item)
            chkb = Checkbutton(frame, text=section, variable=var, onvalue=1, offvalue=0, font=("Arial Bold", 10, 'bold'))
            chkb.grid(columnspan=2, row=i, sticky=W)
            i+=1
            widget_dict[section] = var'''
        else:
            lab = Label(frame, text = section)
            lab.grid(column=0, row=i)
            text_field = Entry(frame, width = 8)
            text_field.grid(column=1, row=i)
            set_text(text_field, item)
            widget_dict[section] = text_field
            i+=1
    return widget_dict, i


def change_pic(event):
    canvas = wl_right[0][1]
    combo = wl_right[1][1]
    label_x_needle = wl_right[2][0]
    label_y_needle = wl_right[2][1]

    canvas.delete("all")
    head_name = combo.get()
    heads['Выбранная голова'] = head_name
    new_x_needle = heads['Количество рядов игл на голове'][head_name]['X']
    new_y_needle = heads['Количество рядов игл на голове'][head_name]['Y']
    label_x_needle.config(text = 'Х      ' + str(new_x_needle))
    label_y_needle.config(text = 'Y      ' + str(new_y_needle))
    filename = heads['Количество рядов игл на голове'][head_name]['dir']
    try:
        img = PhotoImage(file=filename)
        canvas.image = img
        canvas.create_image(0,0, anchor=NW, image=img)
    except:
        messagebox.showerror('Опять что-то менял в файлах?', 'Отсутствует файл с изображением ' + head_name)


def display_right_side(frame):
    widget_list = []

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
    filename = heads['Количество рядов игл на голове'][head_name]['dir']     
    img = PhotoImage(file=filename)   
    canvas.create_image(0,0, anchor=NW, image=img)

    combo.bind('<<ComboboxSelected>>', change_pic)

    widget_list.append((img, canvas))
    widget_list.append((lab, combo))

    lab_1 = Label(frame, text = '\nКоличество рядов игл на голове', font=("Arial Bold", 10, 'bold'))
    lab_1.grid(columnspan=2, row=2)

    X_needles = heads['Количество рядов игл на голове'][head_name]['X']
    lab_2 = Label(frame, text = 'Х      ' + str(X_needles))
    lab_2.grid(columnspan=2, row=3)

    Y_needles = heads['Количество рядов игл на голове'][head_name]['Y']
    lab_3 = Label(frame, text = 'Y      ' + str(Y_needles))
    lab_3.grid(columnspan=2, row=4)

    widget_list.append((lab_2, lab_3))
    return widget_list


#Открываем файл с конфигами
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

second_dict = {}
second_dict["Случайный порядок ударов"] = data.pop("Случайный порядок ударов")
second_dict["Случайные смещения"] = data.pop("Случайные смещения")
second_dict["Коэффициент случайных смещений"] = data.pop("Коэффициент случайных смещений")

#Открываем файл с конфигами голов
with open('heads.json', 'r', encoding='utf-8') as f:
    heads = json.load(f)

#for section, item in test_dict.items():
#    print(section, item)

window = Tk()  
window.title("Генератор G кодов для ИП станка v.1.0")
window.iconbitmap('test.ico')

left_desk = Frame(window, padx=5, pady=5)
left_desk.grid(column=0, row=0)
right_desk = Frame(window, padx=5, pady=5)
right_desk.grid(column=1, row=0, sticky=N+S)

wd_left = {}
wd_left, i = display_parameters(left_desk,  data, 0)
#for section, item in wd_left.items():
#    print(section, type(item))
wl_right = []
wl_right = display_right_side(right_desk)


label_empty = Label(right_desk, text='\n'*7)
label_empty.grid(columnspan=2, row=9, sticky=N+S)

var1 = BooleanVar()
wd_left["Случайный порядок ударов"] = var1
var1.set(second_dict["Случайный порядок ударов"])
chkb1 = Checkbutton(right_desk, text="Случайный порядок ударов", variable=var1, font=("Arial Bold", 10, 'bold'))
chkb1.grid(columnspan=2, row=11, sticky=W)

lab = Label(right_desk, text = "Коэффициент")
lab.grid(column=0, row=13)

text_field = Entry(right_desk, width = 8)
text_field.grid(column=1, row=13)
set_text(text_field, second_dict["Коэффициент случайных смещений"])

var2 = BooleanVar()
wd_left["Случайные смещения"] = var2
wd_left["Коэффициент случайных смещений"] = text_field
var2.set(second_dict["Случайные смещения"])
chkb2 = Checkbutton(right_desk, text="Случайные смещения", variable=var2, font=("Arial Bold", 10, 'bold'))
chkb2.grid(columnspan=2, row=12, sticky=W)

label_empty = Label(right_desk, text='\n'*1)
label_empty.grid(columnspan=2, row=14, sticky=N+S)

bt_save = Button(right_desk, text='Сохранить', width = 15, bg='ivory4', command=click_save)
bt_save.grid(column=0, row=15, padx=3, pady=3, sticky=W+E)

bt_setup = Button(right_desk, text='Настроить', width = 15, bg='ivory4', command=click_setup)
bt_setup.grid(column=1, row=15, padx=3, pady=3, sticky=W+E)

bt_generate = Button(right_desk, text='Генерировать g-code файл', bg='lime green', command=click_generate)
bt_generate.grid(columnspan=2, row=16, padx=3, pady=3, sticky=W+E)

centered_win(window)
window.resizable(False, False)

window.mainloop()