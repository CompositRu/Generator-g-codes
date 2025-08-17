'''
    This is program for creating g-codes files for CNC needlepunching machine.

    This is algorithm module. 
'''


import random
from math import ceil as round_to_greater, sqrt
import os


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
                "Расстояние между иглами (мм)", 
                "Случайный порядок ударов",
                "Случайные смещения",
                "Коэффициент случайных смещений",
                "Чередование направлений прохода слоя",
                "Автоматическая генерация имени файла"]
    heads_list = ["Игольницы (ИП головы)", "Выбранная игольница (ИП игольница)"]
    pattern_list = ['Кол-во ударов']
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
    for item in xy_list:
        if item not in data_dict["Расстояние между иглами (мм)"]:
            return item + ' в ' + "Расстояние между иглами (мм)"
    for item in heads_list:
        if item not in data_dict:
            return item
    for item in head_parameters_list:
        if item not in data_dict["Игольницы (ИП головы)"][data_dict["Выбранная игольница (ИП игольница)"]]:
            return item + ' в ' + "Игольницы (ИП головы)"
    return ''


def generate_offset_list(nx, ny, cell_size_x, cell_size_y):
    offset_x = cell_size_x / nx
    offset_y = cell_size_y / ny
    snake_step = 1.5 * offset_y # коэффициент 1.5 взят с потолка
    offset_list = []
    for j in range(ny):
        for i in range(nx):
            x = offset_x * i
            y = offset_y * j
            y = y + snake_step if i % 2 != 0 else y
            offset_list.append([x, y])
    return offset_list


def r(x):
    return round(x, 1)


# Алгоритм предполагает, что через (nx * ny) / num_pitch слоёв мы начинаем бить в теже точки
# Если nx * ny не кратно num_pitch, то каждые несколько слоёв будет идти слой с неполным количество ударов
# Например, при nx = 5 ny = 10 num_pitch = 20 мы будем получать слои количеством ударов 20, 20, 10, 20, 20, 10...
def check_nums_x_y(data_dict):
    nx = data_dict['Параметры паттерна']['nx']
    ny = data_dict['Параметры паттерна']['ny']
    num_pitch = data_dict['Параметры паттерна']['Кол-во ударов']
    return (nx * ny) % num_pitch != 0


# Подбираем значения nx и ny таким образом, чтобы их произведение было кратно количеству ударов
# и их отношение максимально было близко к корню из 3 пополам (или обратной величине)
def get_nx_ny(num_pitch):
    # Находим все возмные пары множителей для получения значения N
    def get_pairs(N):
        return [(x, int(N / x)) for x in range(1, N) if N % x == 0]
    # Составляем все комбинаии множителей (коэффициенты 5, 6, 8, 10 и 12 взяты на основании
    # многолетней практики, инженерной интуиции, сложных вычислений и капли гениального интеллекта
    gp = lambda n: get_pairs(n * num_pitch)
    pairs = gp(5) + gp(6) + gp(8) + gp(10) + gp(12)
    # Сортируем пары по приближению отношения коэффициентов x и y к корню из 3 пополам
    # Берём обратную величину, т.к. для правильного паттерна требуется nx > ny
    # Правильный паттерн - треугольники максимально приближенны к равносторонним
    k = sqrt(3) / 2
    pairs.sort(key = lambda pair: abs(pair[0] / pair[1] - 1 / k))
    return pairs[0]


def get_message(data_dict):
    cell_size_x = data_dict['Расстояние между иглами (мм)']['X']
    cell_size_y = data_dict['Расстояние между иглами (мм)']['Y']
    head_name = data_dict['Выбранная игольница (ИП игольница)']
    needles_x = data_dict['Игольницы (ИП головы)'][head_name]['X']
    needles_y = data_dict['Игольницы (ИП головы)'][head_name]['Y']
    frame_length_x = data_dict['Габариты каркаса']['X']
    frame_length_y = data_dict['Габариты каркаса']['Y']
    selected_type_frame_size = data_dict['Задание размеров каркаса']
    num_step_x = data_dict['Количество шагов головы']['X']
    num_row_y = data_dict['Количество шагов головы']['Y']

    head_width_x = cell_size_x * needles_x
    head_width_y = cell_size_y * needles_y
    if selected_type_frame_size == 'По габаритам':
        num_step_x = round_to_greater(frame_length_x / head_width_x)
        num_row_y  = round_to_greater(frame_length_y / head_width_y)
    overhangs_x = (num_step_x * head_width_x - frame_length_x) / 2
    overhangs_y = (num_row_y * head_width_y - frame_length_y) / 2

    message = ''
    if selected_type_frame_size == 'По габаритам':
        message =   (
                        f'Свесы по Х: {overhangs_x}\n'
                        f'Свесы по Y: {overhangs_y}\n\n'
                        f'Количество шагов по Х: {num_step_x}\n'
                        f'Количество шагов по Y: {num_row_y}\n'
                    )
    return message


def get_filename(data_dict):
    is_automatic_name = data_dict["Автоматическая генерация имени файла"]
    if is_automatic_name == False:
        return data_dict["Имя файла"]
    else:        
        head_name = data_dict['Выбранная игольница (ИП игольница)']
        frame_length_x = data_dict['Габариты каркаса']['X']
        frame_length_y = data_dict['Габариты каркаса']['Y']
        selected_type_frame_size = data_dict['Задание размеров каркаса']
        amount_layers = data_dict['Количество слоёв']
        layer_thickness = data_dict['Толщина слоя (мм)']
        num_pitch = data_dict['Параметры паттерна']['Кол-во ударов']
        
        frame_height = int(amount_layers * layer_thickness)

        if selected_type_frame_size == 'По шагам головы':
            cell_size_x = data_dict['Расстояние между иглами (мм)']['X']
            cell_size_y = data_dict['Расстояние между иглами (мм)']['Y']
            needles_x = data_dict['Игольницы (ИП головы)'][head_name]['X']
            needles_y = data_dict['Игольницы (ИП головы)'][head_name]['Y']
            num_step_x = data_dict['Количество шагов головы']['X']
            num_row_y = data_dict['Количество шагов головы']['Y']

            head_width_x = cell_size_x * needles_x
            head_width_y = cell_size_y * needles_y
            frame_length_x = num_step_x * head_width_x
            frame_length_y = num_row_y * head_width_y
        return f'{frame_length_x}x{frame_length_y}x{frame_height} {num_pitch} ударов {head_name}.tap'


def get_filename_path_and_create_directory_if_need(data_dict):
    on_the_desktop = data_dict["Создание файла на рабочем столе"]
    head_name = data_dict['Выбранная игольница (ИП игольница)']
    path_desktop = os.path.join(r'C:\Users', os.getlogin(), 'Desktop') if on_the_desktop else ''
    path_head = os.path.join(path_desktop, head_name)
    filename = get_filename(data_dict)
    if not os.path.exists(path_head):
        print('mkdir', path_head)
        os.mkdir(path_head)
    path = os.path.join(path_desktop, head_name, filename)
    print(path)
    return path


def get_ordered_list_of_rows(num_row_y, order):
    rows = list(range(num_row_y, ))
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
    return rows


def generate_G_codes_file(data_dict, display_percent_progress_func):
    cell_size_x = data_dict['Расстояние между иглами (мм)']['X']
    cell_size_y = data_dict['Расстояние между иглами (мм)']['Y']
    num_pitch = data_dict['Параметры паттерна']['Кол-во ударов']
    num_step_x = data_dict['Количество шагов головы']['X']
    num_row_y = data_dict['Количество шагов головы']['Y']
    frame_length_x = data_dict['Габариты каркаса']['X']
    frame_length_y = data_dict['Габариты каркаса']['Y']
    selected_type_frame_size = data_dict['Задание размеров каркаса']
    needle_depth = data_dict['Глубина удара (мм)']
    amount_layers = data_dict['Количество слоёв']
    amount_virtual_layers = data_dict['Количество пустых слоёв']
    dist_to_material = data_dict['Расстояние от каркаса до головы перед ударом (мм)']
    head_name = data_dict['Выбранная игольница (ИП игольница)']
    needles_x = data_dict['Игольницы (ИП головы)'][head_name]['X']
    needles_y = data_dict['Игольницы (ИП головы)'][head_name]['Y']
    layer_thickness = data_dict['Толщина слоя (мм)']
    start_x = data_dict['Начальное положение головы']['X']
    start_y = data_dict['Начальное положение головы']['Y']
    start_z = data_dict['Начальное положение головы']['Z']
    pause = data_dict['Пауза в конце слоя (сек)']
    is_random_order = data_dict['Случайный порядок ударов']
    is_random_offsets = data_dict['Случайные смещения']
    is_rotation_direction = data_dict['Чередование направлений прохода слоя']
    coefficient_random_offsets = data_dict['Коэффициент случайных смещений']
    speed = data_dict['Скорость движения осей станка']
    order = data_dict["Порядок прохождения рядов"]
    on_the_desktop = data_dict["Создание файла на рабочем столе"]
    is_automatic_name = data_dict["Автоматическая генерация имени файла"]

    # Вычисляем параметры паттерна
    nx, ny = get_nx_ny(num_pitch)

    # Вспомогательные параметры
    head_width_x = cell_size_x * needles_x
    head_width_y = cell_size_y * needles_y
    frame_height = int(amount_layers * layer_thickness)

    # Определяем количество шагов головы, если каркас задан габаритами
    if selected_type_frame_size == 'По габаритам':
        num_step_x = round_to_greater(frame_length_x / head_width_x)
        num_row_y  = round_to_greater(frame_length_y / head_width_y)
        
    # Открываем файл
    path = get_filename_path_and_create_directory_if_need(data_dict)
    gcode_file = open(path, 'w')

    # Prehead с описанием файла
    write_empty_line = lambda : gcode_file.write(';\n')
    string_field_width = 20
    write_info_to_prehead = lambda name, value : gcode_file.write(f'; {name:{string_field_width}}: {value}\n')       

    write_empty_line()
    write_info_to_prehead('ИП голова', head_name)
    write_empty_line()
    write_info_to_prehead('Иглы по Х', needles_x)
    write_info_to_prehead('Иглы по Y', needles_y)
    write_empty_line()
    if selected_type_frame_size == 'По габаритам':
        write_info_to_prehead('Длина каркаса по X', frame_length_x)
        write_info_to_prehead('Длина каркаса по Y', frame_length_y)
    else:
        write_info_to_prehead('Шаги по X', num_step_x)
        write_info_to_prehead('Шаги по Y', num_row_y)
    write_info_to_prehead('Высота каркаса по Z', int(frame_height))
    write_empty_line()
    write_info_to_prehead('Слои', amount_layers)
    write_empty_line()
    string_field_width = 35
    write_info_to_prehead('Количество ударов на 1 слой', num_pitch * num_step_x * num_row_y)
    write_info_to_prehead("Количество слоёв для 50'000 ударов", 50000 // (num_pitch * num_step_x * num_row_y))
    write_empty_line()
    write_info_to_prehead("Параметры паттерна nx, ny", f'{nx}, {ny}')
    gcode_file.write(f'; Через каждые {int(nx * ny / num_pitch)} слоёв бьём в теже точки\n') 
    write_empty_line()

    # Установка скорости и начального положения
    gcode_file.write(f'F {speed:.1f}\n')

    # Формируем паттерн пробивки
    offset_list = generate_offset_list(nx, ny, cell_size_x, cell_size_y)

    # Если выбран чекбокс "случайный порядок ударов", то перемешиваем список координат ударов
    if is_random_order:
        random.shuffle(offset_list)
   
    # Формируем список с номерами рядов в порядке их прохождения
    rows = get_ordered_list_of_rows(num_row_y, order)
    
    # Пишем g-коды
    start_hit = 0
    finish_hit = num_pitch
    for layer in range(amount_layers + amount_virtual_layers):
        # Вычисляем смещение по высоте
        z_offset = layer_thickness * layer
        
        # Комментарий с номером слоя
        layer_type = 'layer' if layer < amount_layers else 'layer (holostoy)'
        gcode_file.write(f";\n; {'<' * 10} [{layer + 1}] {layer_type} {'>' * 10}\n;\n")

        # Подъём головы и выезд на стартовые координаты
        str_count_layers = f';{layer + 1}/{amount_layers}\n'
        write_g_code_line = lambda line: gcode_file.write(f'{line:{16}}{str_count_layers}')

        write_g_code_line(f'G1 Z{r(start_z + z_offset)}')
        write_g_code_line(f'G1 X{r(start_x)} Y{r(start_y)}')

        # Цикл рядов по Y
        for row in rows:
            y = head_width_y * row

            # Цикл шагов по Х
            step_range = list(range(num_step_x))
            if is_rotation_direction and (layer + 1) % 2:
                step_range = reversed(step_range)

            for step in step_range:
                x = head_width_x * step

                # Цикл микрошагов внутри ячейки между иглами
                # Нанесение num_pitch ударов каждой иглой в область
                # cell_size_x * cell_size_y (Обычно 8 на 8 мм)
                offset_range = offset_list[start_hit:finish_hit]
                if is_rotation_direction and (layer + 1) % 2:
                    offset_range = reversed(offset_range)

                for offs_x, offs_y in offset_range:
                    current_x = x + offs_x
                    current_y = y + offs_y

                    # Если выбран чекбокс "случайные смещения"
                    if is_random_offsets:
                        current_x += coefficient_random_offsets * (random.random() - 0.5) * 2
                        current_y += coefficient_random_offsets * (random.random() - 0.5) * 2
                    
                    write_g_code_line(f'G1 X{r(current_x)} Y{r(current_y)}')
                    write_g_code_line(f'G1 Z{r(z_offset - needle_depth)}')
                    write_g_code_line(f'G1 Z{r(dist_to_material + z_offset)}')
                
        # Смещение координат ударов на новом слое
        if (finish_hit < len(offset_list)):
            start_hit += num_pitch
            finish_hit += num_pitch
        else:
            start_hit = 0
            finish_hit = num_pitch

        # Подъём головы и отъезд на стартовые координаты
        write_g_code_line(f'G1 Z{r(start_z + z_offset)}')
        write_g_code_line(f'G1 X{r(start_x)} Y{r(start_y)}')
        
        # Пауза P милисекунд
        write_g_code_line(f'G4 P{r(pause * 1000)}')
        
        #Отображаем процесс на progressbar
        display_percent_progress_func(layer / (amount_layers + amount_virtual_layers) * 100)

    # закрытие файлов
    gcode_file.close()


if __name__ == "__main__":
    print("Этот файл самостоятельно не работает. Запускай <Generator_GUI.pyw>")
    input()