"""
GUI модуль генератора G-кодов.

Публичный API:
- Приложение: GeneratorApp, AppState
- Визуализация: show_visualization, VisualizationConfig
"""

from .app import GeneratorApp
from .state import AppState
from .visualization import show_visualization, VisualizationConfig

__all__ = [
    # Приложение
    'GeneratorApp',
    'AppState',
    # Визуализация
    'show_visualization',
    'VisualizationConfig',
]
