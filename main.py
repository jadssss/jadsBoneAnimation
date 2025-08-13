import core
import storage
import render
from gui import setup_gui

try:
    print("Отладка: Начало main.py")
    scene = core.Scene()
    scene.Bone = core.Bone
    print("Отладка: Сцена инициализирована")
    setup_gui(scene, storage, render)
    print("Отладка: GUI запущен")
except Exception as e:
    print(f"Отладка: Ошибка в main.py: {e}")