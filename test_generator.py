"""
Модуль тестирования для генератора G-кодов.

Содержит:
- Интеграционный тест сравнения с reference.tap
- Unit-тесты для функций алгоритма
"""

import unittest
import os
import json
import warnings
from typing import List, Tuple
from generator_G_codes import (
    generate_G_codes_file,
    generate_offset_list,
    get_nx_ny,
    get_ordered_list_of_rows,
    check_nums_x_y,
    get_result_offset_list
)


def parse_gcode_line(line: str) -> Tuple[str, str]:
    """
    Парсит строку G-code, разделяя команду и комментарий.

    Args:
        line: Строка G-code

    Returns:
        Кортеж (команда, комментарий)
    """
    line = line.strip()

    # Проверяем, есть ли точка с запятой
    if ';' in line:
        parts = line.split(';', 1)
        command = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ''
        return command, comment
    else:
        return line, ''


def extract_commands_from_file(filepath: str) -> List[str]:
    """
    Извлекает список команд из G-code файла, игнорируя комментарии.

    Args:
        filepath: Путь к .tap файлу

    Returns:
        Список команд (строки без комментариев)
    """
    commands = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            command, _ = parse_gcode_line(line)

            # Игнорируем пустые строки и строки только с комментариями
            if command:
                commands.append(command)

    return commands


def compare_gcode_files(file1: str, file2: str, show_warnings: bool = True) -> Tuple[bool, List[str]]:
    """
    Сравнивает два G-code файла, игнорируя комментарии.

    Args:
        file1: Путь к первому файлу
        file2: Путь ко второму файлу
        show_warnings: Показывать ли предупреждения о различиях в комментариях

    Returns:
        Кортеж (файлы_идентичны, список_предупреждений)
    """
    warnings_list = []

    # Извлекаем команды из обоих файлов
    commands1 = extract_commands_from_file(file1)
    commands2 = extract_commands_from_file(file2)

    # Сравниваем количество команд
    if len(commands1) != len(commands2):
        return False, [f"Разное количество команд: {len(commands1)} vs {len(commands2)}"]

    # Сравниваем команды построчно
    files_identical = True

    with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

        max_lines = max(len(lines1), len(lines2))

        for i in range(max_lines):
            line1 = lines1[i].strip() if i < len(lines1) else ''
            line2 = lines2[i].strip() if i < len(lines2) else ''

            cmd1, cmt1 = parse_gcode_line(line1)
            cmd2, cmt2 = parse_gcode_line(line2)

            # Сравниваем команды
            if cmd1 != cmd2:
                files_identical = False
                warnings_list.append(
                    f"Строка {i+1}: Различие в командах\n"
                    f"  Файл 1: '{cmd1}'\n"
                    f"  Файл 2: '{cmd2}'"
                )
            # Проверяем комментарии (только для warning)
            elif show_warnings and cmt1 != cmt2:
                # Если обе строки - только комментарии
                if not cmd1 and not cmd2:
                    warnings_list.append(
                        f"Строка {i+1}: Различие в заголовке (только комментарий)\n"
                        f"  Файл 1: ';{cmt1}'\n"
                        f"  Файл 2: ';{cmt2}'"
                    )
                # Если есть команда, но комментарии разные
                elif cmd1:
                    warnings_list.append(
                        f"Строка {i+1}: Различие в комментарии к команде '{cmd1}'\n"
                        f"  Файл 1: ';{cmt1}'\n"
                        f"  Файл 2: ';{cmt2}'"
                    )

    return files_identical, warnings_list


class TestGCodeComparison(unittest.TestCase):
    """Тесты для сравнения G-code файлов."""

    def test_parse_gcode_line(self):
        """Тест парсинга строк G-code."""
        # Строка только с комментарием
        cmd, cmt = parse_gcode_line('; Комментарий 1')
        self.assertEqual(cmd, '')
        self.assertEqual(cmt, 'Комментарий 1')

        # Строка с командой и комментарием
        cmd, cmt = parse_gcode_line('G1 X100.0 Y200.0 ; Движение')
        self.assertEqual(cmd, 'G1 X100.0 Y200.0')
        self.assertEqual(cmt, 'Движение')

        # Строка только с командой
        cmd, cmt = parse_gcode_line('G1 Z50.0')
        self.assertEqual(cmd, 'G1 Z50.0')
        self.assertEqual(cmt, '')

        # Пустая строка
        cmd, cmt = parse_gcode_line('')
        self.assertEqual(cmd, '')
        self.assertEqual(cmt, '')

    def test_files_with_different_comments_are_identical(self):
        """Тест: файлы с разными комментариями должны считаться идентичными."""
        # Создаем временные тестовые файлы
        test_file1 = 'test_temp1.tap'
        test_file2 = 'test_temp2.tap'

        try:
            with open(test_file1, 'w', encoding='utf-8') as f:
                f.write('; Комментарий 1\n')
                f.write('; Комментарий 2\n')
                f.write('G1 X100.0 ; Комментарий 3\n')
                f.write('G1 Y200.0 ; Комментарий 4\n')

            with open(test_file2, 'w', encoding='utf-8') as f:
                f.write('; Другой комментарий 1\n')
                f.write('; Другой комментарий 2\n')
                f.write('G1 X100.0 ; Другой комментарий 3\n')
                f.write('G1 Y200.0 ; Другой комментарий 4\n')

            identical, warnings_list = compare_gcode_files(test_file1, test_file2, show_warnings=True)

            # Файлы должны быть идентичны по командам
            self.assertTrue(identical)
            # Но должны быть предупреждения о различиях в комментариях
            self.assertGreater(len(warnings_list), 0)

        finally:
            # Удаляем временные файлы
            if os.path.exists(test_file1):
                os.remove(test_file1)
            if os.path.exists(test_file2):
                os.remove(test_file2)

    def test_files_with_different_commands_are_not_identical(self):
        """Тест: файлы с разными командами не должны быть идентичны."""
        test_file1 = 'test_temp1.tap'
        test_file2 = 'test_temp2.tap'

        try:
            with open(test_file1, 'w', encoding='utf-8') as f:
                f.write('G1 X100.0\n')
                f.write('G1 Y200.0\n')

            with open(test_file2, 'w', encoding='utf-8') as f:
                f.write('G1 X100.0\n')
                f.write('G1 Y300.0\n')  # Другая команда

            identical, warnings_list = compare_gcode_files(test_file1, test_file2)

            # Файлы не должны быть идентичны
            self.assertFalse(identical)
            self.assertGreater(len(warnings_list), 0)

        finally:
            if os.path.exists(test_file1):
                os.remove(test_file1)
            if os.path.exists(test_file2):
                os.remove(test_file2)


class TestGeneratorAlgorithm(unittest.TestCase):
    """Unit-тесты для функций алгоритма генератора."""

    def test_generate_offset_list(self):
        """Тест генерации списка смещений."""
        nx, ny = 2, 2
        cell_size_x, cell_size_y = 8.0, 8.0

        offset_list = generate_offset_list(nx, ny, cell_size_x, cell_size_y)

        # Проверяем количество элементов
        self.assertEqual(len(offset_list), nx * ny)

        # Проверяем, что все элементы - это списки с двумя числами
        for offset in offset_list:
            self.assertEqual(len(offset), 2)
            self.assertIsInstance(offset[0], (int, float))
            self.assertIsInstance(offset[1], (int, float))

    def test_get_nx_ny(self):
        """Тест автоматического определения nx и ny."""
        # Для num_pitch = 10
        nx, ny = get_nx_ny(10)

        # Проверяем, что произведение nx * ny кратно num_pitch
        self.assertEqual((nx * ny) % 10, 0)

        # Проверяем, что nx > ny (для правильного паттерна)
        self.assertGreater(nx, ny)

        # Для num_pitch = 20
        nx, ny = get_nx_ny(20)
        self.assertEqual((nx * ny) % 20, 0)
        self.assertGreater(nx, ny)

    def test_get_ordered_list_of_rows(self):
        """Тест разных порядков прохождения рядов."""
        num_rows = 5

        # Тест "По очереди"
        rows = get_ordered_list_of_rows(num_rows, 'По очереди')
        self.assertEqual(rows, [0, 1, 2, 3, 4])

        # Тест "Сначала чётные"
        rows = get_ordered_list_of_rows(num_rows, 'Сначала чётные')
        self.assertEqual(rows, [1, 3, 0, 2, 4])

        # Тест "Сначала нечётные"
        rows = get_ordered_list_of_rows(num_rows, 'Сначала нечётные')
        self.assertEqual(rows, [0, 2, 4, 1, 3])

        # Тест неизвестного порядка
        with self.assertRaises(KeyError):
            get_ordered_list_of_rows(num_rows, 'Несуществующий порядок')

    def test_check_nums_x_y(self):
        """Тест проверки кратности nx * ny и num_pitch."""
        # Кратные значения
        data_dict = {
            'Параметры паттерна': {
                'nx': 10,
                'ny': 10,
                'Кол-во ударов': 20
            }
        }
        self.assertFalse(check_nums_x_y(data_dict))

        # Некратные значения
        data_dict['Параметры паттерна']['Кол-во ударов'] = 30
        self.assertTrue(check_nums_x_y(data_dict))

    def test_get_result_offset_list_random_order(self):
        """Тест генерации смещений со случайным порядком."""
        nx, ny = 3, 3
        cell_size_x, cell_size_y = 8.0, 8.0

        # Без случайного порядка
        offset_list1 = get_result_offset_list(nx, ny, cell_size_x, cell_size_y, False, 0.15, False)
        offset_list2 = get_result_offset_list(nx, ny, cell_size_x, cell_size_y, False, 0.15, False)

        # Списки должны быть одинаковыми
        self.assertEqual(offset_list1, offset_list2)

        # Со случайным порядком (может быть одинаковым, но маловероятно для больших списков)
        offset_list3 = get_result_offset_list(nx, ny, cell_size_x, cell_size_y, False, 0.15, True)

        # Проверяем количество элементов
        self.assertEqual(len(offset_list3), nx * ny)


class TestEdgeCases(unittest.TestCase):
    """Тесты граничных случаев и валидации."""

    def get_minimal_config(self):
        """Возвращает минимальную рабочую конфигурацию."""
        return {
            "Количество слоёв": 1,
            "Количество пустых слоёв": 0,
            "Толщина слоя (мм)": 0.82,
            "Расстояние от каркаса до головы перед ударом (мм)": 30,
            "Скорость движения осей станка": 3000,
            "Пробивка": {
                "Пробивка с нарастанием глубины": False,
                "Начальная глубина удара (мм)": 8,
                "Глубина удара (мм)": 18
            },
            "Параметры паттерна": {
                "Автоматическое определение формы паттерна": True,
                "nx": 12,
                "ny": 10,
                "Кол-во ударов": 10
            },
            "Позиция при ручной укладки слоя": {
                "X": 0,
                "Y": -400,
                "Z": 100,
                "Пауза в конце слоя (сек)": 0,
                "Рост Z с каждым слоем": True
            },
            "Расстояние между иглами (мм)": {
                "X": 8.0,
                "Y": 8.0
            },
            "Количество шагов головы": {
                "X": 2,
                "Y": 2
            },
            "Габариты каркаса": {
                "X": 100,
                "Y": 100
            },
            "Случайный порядок ударов": False,
            "Случайные смещения": False,
            "Коэффициент случайных смещений": 0.15,
            "Чередование направлений прохода слоя": False,
            "Создание файла на рабочем столе": False,
            "Автоматическая генерация имени файла": False,
            "Имя файла": "test_edge_case.tap",
            "Порядок прохождения рядов": "По очереди",
            "Задание размеров каркаса": "По шагам головы",
            "Игольницы (ИП головы)": {
                "Тестовая_игольница": {
                    "X": 4,
                    "Y": 4,
                    "path": "test.png"
                }
            },
            "Выбранная игольница (ИП игольница)": "Тестовая_игольница"
        }

    def test_single_layer_generation(self):
        """Тест: генерация файла с одним слоем."""
        config = self.get_minimal_config()
        config["Количество слоёв"] = 1
        head_name = config["Выбранная игольница (ИП игольница)"]
        output_file = os.path.join(head_name, config["Имя файла"])

        try:
            generate_G_codes_file(config, lambda x: None)

            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(output_file))

            # Проверяем, что есть хотя бы одна команда
            commands = extract_commands_from_file(output_file)
            self.assertGreater(len(commands), 0)

            # Проверяем, что в файле ровно один слой
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                layer_count = content.count('layer')
                self.assertEqual(layer_count, 1)

        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(head_name) and not os.listdir(head_name):
                os.rmdir(head_name)

    def test_multiple_virtual_layers(self):
        """Тест: генерация с пустыми слоями (holostoy)."""
        config = self.get_minimal_config()
        config["Количество слоёв"] = 2
        config["Количество пустых слоёв"] = 3
        head_name = config["Выбранная игольница (ИП игольница)"]
        output_file = os.path.join(head_name, config["Имя файла"])

        try:
            generate_G_codes_file(config, lambda x: None)

            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Проверяем количество обычных слоев
                normal_layers = content.count('] layer >>')
                self.assertEqual(normal_layers, 2)

                # Проверяем количество пустых слоев
                virtual_layers = content.count('(holostoy)')
                self.assertEqual(virtual_layers, 3)

        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(head_name) and not os.listdir(head_name):
                os.rmdir(head_name)

    def test_progressive_depth_punching(self):
        """Тест: пробивка с нарастанием глубины."""
        config = self.get_minimal_config()
        config["Количество слоёв"] = 5
        config["Пробивка"]["Пробивка с нарастанием глубины"] = True
        config["Пробивка"]["Начальная глубина удара (мм)"] = 5
        config["Пробивка"]["Глубина удара (мм)"] = 20
        head_name = config["Выбранная игольница (ИП игольница)"]
        output_file = os.path.join(head_name, config["Имя файла"])

        try:
            generate_G_codes_file(config, lambda x: None)

            commands = extract_commands_from_file(output_file)

            # Находим все команды опускания (отрицательные Z)
            z_down_commands = [cmd for cmd in commands if cmd.startswith('G1 Z-')]

            # Проверяем, что есть команды опускания
            self.assertGreater(len(z_down_commands), 0)

            # Извлекаем глубины
            depths = []
            for cmd in z_down_commands[:10]:  # Берем первые 10 для проверки
                z_value = float(cmd.split('Z')[1])
                depths.append(abs(z_value))

            # Проверяем, что начальная глубина не меньше минимальной
            self.assertGreaterEqual(min(depths), config["Пробивка"]["Начальная глубина удара (мм)"])

        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(head_name) and not os.listdir(head_name):
                os.rmdir(head_name)

    def test_different_row_orders(self):
        """Тест: разные порядки прохождения рядов."""
        config = self.get_minimal_config()
        config["Количество шагов головы"]["Y"] = 5
        head_name = config["Выбранная игольница (ИП игольница)"]

        orders = [
            "По очереди",
            "Сначала чётные",
            "Сначала нечётные",
            "Из центра",
            "В центр"
        ]

        for order in orders:
            config["Порядок прохождения рядов"] = order
            config["Имя файла"] = f"test_order_{order.replace(' ', '_')}.tap"
            output_file = os.path.join(head_name, config["Имя файла"])

            try:
                # Генерация не должна вызывать ошибок
                generate_G_codes_file(config, lambda x: None)
                self.assertTrue(os.path.exists(output_file))

            finally:
                if os.path.exists(output_file):
                    os.remove(output_file)

        # Очистка папки
        if os.path.exists(head_name) and not os.listdir(head_name):
            os.rmdir(head_name)

    def test_gcode_file_structure(self):
        """Тест: проверка структуры G-code файла."""
        config = self.get_minimal_config()
        head_name = config["Выбранная игольница (ИП игольница)"]
        output_file = os.path.join(head_name, config["Имя файла"])

        try:
            generate_G_codes_file(config, lambda x: None)

            commands = extract_commands_from_file(output_file)

            # Проверяем наличие команды установки скорости
            speed_commands = [cmd for cmd in commands if cmd.startswith('F ')]
            self.assertGreater(len(speed_commands), 0)

            # Проверяем наличие команд движения
            g1_commands = [cmd for cmd in commands if cmd.startswith('G1 ')]
            self.assertGreater(len(g1_commands), 0)

            # Проверяем наличие команд паузы
            g4_commands = [cmd for cmd in commands if cmd.startswith('G4 P')]
            self.assertGreater(len(g4_commands), 0)

            # Проверяем, что все команды G1 имеют координаты
            for cmd in g1_commands[:10]:  # Проверяем первые 10
                self.assertTrue('X' in cmd or 'Y' in cmd or 'Z' in cmd,
                               f"Команда G1 без координат: {cmd}")

        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists(head_name) and not os.listdir(head_name):
                os.rmdir(head_name)


class TestIntegrationWithReference(unittest.TestCase):
    """Интеграционный тест сравнения с reference.tap."""

    @classmethod
    def setUpClass(cls):
        """Подготовка к тестам: загружаем данные для reference.tap."""
        cls.reference_file = 'reference.tap'

        # Проверяем существование reference.tap
        if not os.path.exists(cls.reference_file):
            raise FileNotFoundError(f"Файл {cls.reference_file} не найден!")

        # Загружаем конфигурацию для генерации reference файла
        # Эти параметры должны соответствовать тем, с которыми был создан reference.tap
        cls.reference_data = {
            "Количество слоёв": 10,
            "Количество пустых слоёв": 10,
            "Толщина слоя (мм)": 0.82,
            "Расстояние от каркаса до головы перед ударом (мм)": 30,
            "Скорость движения осей станка": 3000,
            "Пробивка": {
                "Пробивка с нарастанием глубины": False,
                "Начальная глубина удара (мм)": 8,
                "Глубина удара (мм)": 18
            },
            "Параметры паттерна": {
                "Автоматическое определение формы паттерна": True,
                "nx": 12,
                "ny": 10,
                "Кол-во ударов": 10
            },
            "Позиция при ручной укладки слоя": {
                "X": 0,
                "Y": -400,
                "Z": 100,
                "Пауза в конце слоя (сек)": 10,
                "Рост Z с каждым слоем": True
            },
            "Расстояние между иглами (мм)": {
                "X": 8.0,
                "Y": 8.0
            },
            "Количество шагов головы": {
                "X": 39,
                "Y": 1
            },
            "Габариты каркаса": {
                "X": 500,
                "Y": 500
            },
            "Случайный порядок ударов": False,  # Важно! Для детерминированного сравнения
            "Случайные смещения": False,  # Важно! Для детерминированного сравнения
            "Коэффициент случайных смещений": 0.15,
            "Чередование направлений прохода слоя": True,
            "Создание файла на рабочем столе": False,
            "Автоматическая генерация имени файла": False,
            "Имя файла": "test_generated.tap",
            "Порядок прохождения рядов": "По очереди",
            "Задание размеров каркаса": "По габаритам",
            "Игольницы (ИП головы)": {
                "Г1": {
                    "X": 4,
                    "Y": 33,
                    "path": "data/g1.png"
                }
            },
            "Выбранная игольница (ИП игольница)": "Г1"
        }

    def test_compare_with_reference(self):
        """
        Интеграционный тест: сравнение сгенерированного файла с reference.tap.

        Внимание: Этот тест может не пройти, если reference.tap был создан
        с другими параметрами. В таком случае нужно обновить self.reference_data
        в setUpClass.
        """
        # Файл создается в подкаталоге с именем головы
        head_name = self.reference_data["Выбранная игольница (ИП игольница)"]
        generated_file = os.path.join(head_name, 'test_generated.tap')

        try:
            # Генерируем файл
            generate_G_codes_file(self.reference_data, lambda x: None)

            # Проверяем, что файл создан
            self.assertTrue(
                os.path.exists(generated_file),
                f"Файл {generated_file} не был создан"
            )

            # Сравниваем с reference
            identical, warnings_list = compare_gcode_files(
                self.reference_file,
                generated_file,
                show_warnings=True
            )

            # Выводим предупреждения о различиях в комментариях
            if warnings_list:
                print("\n" + "="*70)
                print("ПРЕДУПРЕЖДЕНИЯ О РАЗЛИЧИЯХ:")
                print("="*70)

                # Группируем предупреждения
                comment_warnings = [w for w in warnings_list if 'комментари' in w.lower()]
                command_warnings = [w for w in warnings_list if 'команд' in w.lower()]

                if comment_warnings:
                    print(f"\nОбнаружено {len(comment_warnings)} различий в комментариях:")
                    # Показываем первые 5 примеров
                    for w in comment_warnings[:5]:
                        print(f"\n{w}")
                    if len(comment_warnings) > 5:
                        print(f"\n... и ещё {len(comment_warnings) - 5} различий в комментариях")

                if command_warnings:
                    print(f"\nОБНАРУЖЕНО {len(command_warnings)} РАЗЛИЧИЙ В КОМАНДАХ:")
                    for w in command_warnings:
                        print(f"\n{w}")

                print("\n" + "="*70)

            # Проверяем идентичность команд
            self.assertTrue(
                identical,
                "Файлы имеют различия в командах! См. предупреждения выше."
            )

            print(f"\n✓ Тест пройден: Сгенерированный файл идентичен {self.reference_file} (по командам)")
            if warnings_list and not any('команд' in w.lower() for w in warnings_list):
                print(f"  Найдено {len(warnings_list)} различий только в комментариях (это нормально)")

        finally:
            # Удаляем сгенерированный файл и папку
            if os.path.exists(generated_file):
                os.remove(generated_file)
            # Удаляем папку, если она пустая
            if os.path.exists(head_name) and not os.listdir(head_name):
                os.rmdir(head_name)


def run_tests(verbosity=2):
    """
    Запускает все тесты.

    Args:
        verbosity: Уровень детализации вывода (0, 1, 2)
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Добавляем все тестовые классы
    suite.addTests(loader.loadTestsFromTestCase(TestGCodeComparison))
    suite.addTests(loader.loadTestsFromTestCase(TestGeneratorAlgorithm))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithReference))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("="*70)
    print("МОДУЛЬ ТЕСТИРОВАНИЯ ГЕНЕРАТОРА G-КОДОВ")
    print("="*70)
    print()

    # Запускаем тесты
    result = run_tests(verbosity=2)

    # Выводим итоговую статистику
    print("\n" + "="*70)
    print("ИТОГИ ТЕСТИРОВАНИЯ:")
    print("="*70)
    print(f"Запущено тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    print("="*70)

    # Возвращаем код выхода
    exit(0 if result.wasSuccessful() else 1)
