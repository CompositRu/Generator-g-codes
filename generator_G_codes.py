import random


def write_to_f(file_name, *args):
    for arg in args:
        file_name.write(str(arg))


def check_dict_keys(data_dict):
    base_list = ["Количество слоёв",
                "Количество слоёв",
                "Количество пустых слоёв",
                "Толщина слоя (мм)",
                "Глубина удара (мм)",
                "Расстояние от каркаса до головы перед ударом (мм)",
                "Пауза в конце слоя (сек)",
                "Скорость движения осей станка",
                "Параметры паттерна",
                "Количество шагов головы", 
                "Начальное положение головы", 
                "Отъезд после слоя",
                "Расстояние между иглами (мм)", 
                "Случайный порядок ударов",
                "Случайные смещения",
                "Коэффициент случайных смещений",
                "Чередование направлений прохода слоя"]
    heads_list = ["Количество рядов игл на голове", "Выбранная голова"]
    pattern_list = ['nx', 'ny', 'Кол-во ударов']
    xy_list = ['X', 'Y']
    xyz_list = ['X', 'Y', 'Z']
    head_parameters_list = ['X', 'Y', 'path']

    for item in base_list:
        if item not in data_dict:
            return item
    for item in pattern_list:
        if item not in data_dict["Параметры паттерна"]:
            return item + ' в ' + "Параметры паттерна"
    for item in xy_list:
        if item not in data_dict["Количество шагов головы"]:
            return item + ' в ' + "Количество шагов головы"
    for item in xyz_list:
        if item not in data_dict["Начальное положение головы"]:
            return item + ' в ' + "Начальное положение головы"
    for item in xyz_list:
        if item not in data_dict["Отъезд после слоя"]:
            return item + ' в ' + "Отъезд после слоя"
    for item in xy_list:
        if item not in data_dict["Расстояние между иглами (мм)"]:
            return item + ' в ' + "Расстояние между иглами (мм)"
    for item in heads_list:
        if item not in data_dict:
            return item
    for item in head_parameters_list:
        if item not in data_dict["Количество рядов игл на голове"][data_dict["Выбранная голова"]]:
            return item + ' в ' + "Количество рядов игл на голове"
    return ''


def generate_offset_list(nx, ny, cell_size_x, cell_size_y):
    offset_x = cell_size_x / nx;
    offset_y = cell_size_y / ny;
    snake_step = 1.5 * offset_y # коэффициент 1.5 взят с потолка
    offset_list = []
    for j in range(ny):
        flag = False
        for i in range(nx):
            x = offset_x * i
            y = offset_y * j
            if flag:
                y += snake_step
            offset_list.append([x, y])
            flag = not flag
    return offset_list


def r(x):
    return round(x, 1)


def generate_G_codes_file(data_dict, display_percent_progress_func):
    cell_size_x = data_dict['Расстояние между иглами (мм)']['X']
    cell_size_y = data_dict['Расстояние между иглами (мм)']['Y']
    nx = data_dict['Параметры паттерна']['nx']
    ny = data_dict['Параметры паттерна']['ny']
    num_pitch = data_dict['Параметры паттерна']['Кол-во ударов']
    num_step_x = data_dict['Количество шагов головы']['X']
    num_row_y = data_dict['Количество шагов головы']['Y']
    needle_depth = data_dict['Глубина удара (мм)']
    amount_layers = data_dict['Количество слоёв']
    amount_virtual_layers = data_dict['Количество пустых слоёв']
    dist_to_material = data_dict['Расстояние от каркаса до головы перед ударом (мм)']
    head_name = data_dict['Выбранная голова']
    needles_x = data_dict['Количество рядов игл на голове'][head_name]['X']
    needles_y = data_dict['Количество рядов игл на голове'][head_name]['Y']
    layer_thickness = data_dict['Толщина слоя (мм)']
    start_x = data_dict['Начальное положение головы']['X']
    start_y = data_dict['Начальное положение головы']['Y']
    start_z = data_dict['Начальное положение головы']['Z']
    x_after_layer = data_dict['Отъезд после слоя']['X']
    y_after_layer = data_dict['Отъезд после слоя']['Y']
    z_after_layer = data_dict['Отъезд после слоя']['Z']
    pause = data_dict['Пауза в конце слоя (сек)']
    is_random_order = data_dict['Случайный порядок ударов']
    is_random_offsets = data_dict['Случайные смещения']
    is_rotation_direction = data_dict['Чередование направлений прохода слоя']
    coefficient_random_offsets = data_dict['Коэффициент случайных смещений']
    speed = data_dict['Скорость движения осей станка']
    order = data_dict["Порядок прохождения рядов"]
    filename = data_dict["Имя файла"]

    # Открываем файл
    gcode_file = open(filename, 'w')

    # Prehead с описанием файла
    write_to_f(gcode_file, ';\n')
    write_to_f(gcode_file, '; {:18}: {}\n'.format('needles_x', needles_x))
    write_to_f(gcode_file, '; {:18}: {}\n'.format('needles_y', needles_y))
    write_to_f(gcode_file, ';\n')
    write_to_f(gcode_file, '; {:18}: {}\n'.format('steps_X', num_step_x))
    write_to_f(gcode_file, '; {:18}: {}\n'.format('steps_Y', num_row_y))
    write_to_f(gcode_file, '; {:18}: {}\n'.format('layers', amount_layers))
    write_to_f(gcode_file, ';\n')
    write_to_f(gcode_file, '; {:18}: {}\n'.format('hits to 1 layer', num_pitch * num_step_x * num_row_y))
    write_to_f(gcode_file, '; {:18}: {}\n'.format('hits to all layers', num_pitch * num_step_x * num_row_y * amount_layers))
    write_to_f(gcode_file, ';\n')

    # Установка скорости и начального положения
    gcode_file.write(f'F {speed:.1f}\n')

    # Вспомогательные параметры
    offset_list = generate_offset_list(nx, ny, cell_size_x, cell_size_y)

    # Если выбран чекбокс "случайный порядок ударов", то перемешиваем список координат ударов
    if is_random_order:
        random.shuffle(offset_list)
    
    # Формируем список с порядком прохождения рядов
    rows = list(range(num_row_y))
    if order == 'По очереди':
        pass
    elif order == 'Сначала чётные':
        rows = rows[1::2] + rows[::2]
    elif order == 'Сначала нечётные':
        rows = rows[::2] + rows[1::2] 
    elif order == 'Из центра':
        center = (len(rows) - 1) // 2
        rows = rows[center::-1] + rows[center + 1:]
    elif order == 'В центр':
        center = (len(rows) - 1) // 2
        rows = rows[:center] + rows[:center - 1:-1]
    else:
        raise KeyError('Для данного порядка не написан алгоритм прохождения рядов')
    
    # Пишем g-коды
    start_hit = 0
    finsh_hit = num_pitch
    for layer in range(amount_layers + amount_virtual_layers):
        # Вычисляем смещение по высоте
        z_offset = layer_thickness * layer
        # Комментарий с номером слоя
        if layer < amount_layers:
            write_to_f(gcode_file, 
                       f";\n; {'<' * 10}   [{layer + 1}] layer   {'>' * 10}\n;\n")
        else:
            write_to_f(gcode_file, 
                       f";\n; {'<' * 10}   [{layer + 1}] layer (holostoy)  {'>' * 10}\n;\n")

        # Выезд на стартовую точку
        command = f'G1 X{r(start_x)} Y{r(start_y)} Z{r(start_z + z_offset)}'
        write_to_f(gcode_file, 
                    '{:16}'.format(command), 
                    '; Start position\n')

        # Цикл рядов по Y
        for row in rows:
            y = cell_size_y * needles_y * row
            x = 0

            # Цикл шагов по Х
            step_range = list(range(num_step_x))
            if is_rotation_direction and (layer + 1) % 2:
                step_range = reversed(step_range)

            print(list(step_range))
            for step in step_range:
                x = 0 + cell_size_x * needles_x * step

                # Цикл микрошагов внутри ячейки между иглами
                # Нанесение num_pitch ударов каждой иглой в область
                # cell_size_x * cell_size_y (Обычно 8 на 8 мм)
                offset_range = offset_list[start_hit:finsh_hit]
                if is_rotation_direction and (layer + 1) % 2:
                    offset_range = reversed(offset_range)

                for offs in offset_range:
                    current_x = x + offs[0]
                    current_y = y + offs[1]
                    # Если выбран чекбокс "случайные смещения"
                    if is_random_offsets:
                        current_x += coefficient_random_offsets * (random.random() - 0.5) * 2
                        current_y += coefficient_random_offsets * (random.random() - 0.5) * 2

                    str_count_layers = f'; {layer + 1}/{amount_layers}\n'
                    command = f'G1 X{r(current_x)} Y{r(current_y)}'
                    write_to_f(gcode_file, f'{command:16}', str_count_layers)
                    command = f'G1 Z{r(z_offset - needle_depth)}'
                    write_to_f(gcode_file, f'{command:16}', str_count_layers)
                    command = f'G1 Z{r(dist_to_material + z_offset)}'
                    write_to_f(gcode_file, f'{command:16}', str_count_layers)
                
        # Смещение координат ударов на новом слое
        if (finsh_hit < len(offset_list)):
            start_hit += num_pitch
            finsh_hit += num_pitch
        else:
            start_hit = 0
            finsh_hit = num_pitch

        # Отъезд после прохождения слоя
        command = f'G1 X{r(x_after_layer)} Y{r(y_after_layer)} Z{r(z_after_layer + z_offset)}'
        write_to_f(gcode_file, 
                    '{:21}'.format(command), 
                    '; Position after layer\n')
        # Пауза P секунд
        command = f'G4 P{r(pause * 1000)}'
        write_to_f(gcode_file, 
                    '{:16}'.format(command),
                    '; Pause\n;\n')
        #Отображаем процесс на progressbar
        display_percent_progress_func(layer / (amount_layers + amount_virtual_layers) * 100)

    # закрытие файлов
    gcode_file.close()


if __name__ == "__main__":
    print("Этот файл самостоятельно не работает. Запускай <Generator_GUI.pyw>")
    input()