import core
import storage
import render
from gui import setup_gui

scene = core.Scene()
scene.Bone = core.Bone  # Для использования в gui

setup_gui(scene, storage, render)