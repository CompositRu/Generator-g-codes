'''
Визуализация паттерна пробивки.

Использует Plotly для построения интерактивного графика точек пробивки.
'''

from tkinter import messagebox
from core import get_nx_ny, get_result_offset_list

try:
    import plotly.express as px
except Exception:
    px = None  # покажем понятную ошибку при попытке построения


class VisualizationConfig:
    """Конфигурация для визуализации паттерна пробивки"""
    INCLUDE_PLOTLYJS = 'cdn'  # 'cdn' - меньший размер файла, требует интернет
                               # True - полный Plotly.js в файле (работает offline)
    OUTPUT_DIR = 'visualization'  # TODO: пока не применяется, файл сохраняется рядом со скриптом/exe
    OUTPUT_FILENAME = 'visualization_pattern.html'


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


def _plot_offsets(points, num_pitch, cell_size_x, cell_size_y, title="Паттерн"):
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

    # Сохраняем HTML файл рядом со скриптом/exe и открываем в браузере
    from utils.crossplatform_utils import get_resource_path
    html_path = get_resource_path(VisualizationConfig.OUTPUT_FILENAME)
    fig.write_html(
        html_path,
        include_plotlyjs=VisualizationConfig.INCLUDE_PLOTLYJS,
        auto_open=True
    )


def get_true_form_for_word_sloy(n):
    """Возвращает правильную форму слова 'слой' для числа n."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} слой"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return f"{n} слоя"
    else:
        return f"{n} слоёв"


def show_visualization(cell_size_x, cell_size_y, num_pitch, generate_nx_ny, nx, ny,
                       is_random_offsets, coefficient_random_offsets, is_random_order):
    """
    Отображает визуализацию паттерна пробивки.

    Args:
        cell_size_x: Расстояние между иглами по X
        cell_size_y: Расстояние между иглами по Y
        num_pitch: Количество ударов
        generate_nx_ny: Автоматическое определение формы паттерна
        nx: Размер паттерна по X
        ny: Размер паттерна по Y
        is_random_offsets: Случайные смещения
        coefficient_random_offsets: Коэффициент случайных смещений
        is_random_order: Случайный порядок ударов
    """
    # Вычисляем параметры паттерна, если необходимо
    if generate_nx_ny:
        nx, ny = get_nx_ny(num_pitch)

    # функция берётся из core (уже импортирован)
    points = get_result_offset_list(nx, ny, cell_size_x, cell_size_y,
                                    is_random_offsets, coefficient_random_offsets, is_random_order)

    layers = nx * ny // num_pitch
    title = f"<b>Паттерн {nx}/{ny}/{num_pitch}</b>"
    title += f"<br>- Ячейка между иглами полностью забивается за {get_true_form_for_word_sloy(layers)}"
    if is_random_order:
        title += "<br>- Случайный порядок ударов формируется один раз и повторяется при создании всего каркаса"
    if is_random_offsets:
        title += "<br>- Случайные смещения для каждого удара вычисляются заного и не повторяются на каждом слое"

    _plot_offsets(points, num_pitch, cell_size_x, cell_size_y, title)
