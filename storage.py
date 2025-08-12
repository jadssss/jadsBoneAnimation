import json
import os

BASE_DIR = os.path.dirname(__file__)
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
STORAGE_DIR = os.path.join(BASE_DIR, "storage_files")
os.makedirs(STORAGE_DIR, exist_ok=True)

def list_examples():
    return [f for f in os.listdir(EXAMPLES_DIR) if f.endswith('.json')]

def load_example(name, scene):
    path = os.path.join(EXAMPLES_DIR, name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        scene.push_undo()
        scene._restore(loaded)
        return True
    return False

def list_saved():
    return [f for f in os.listdir(STORAGE_DIR) if f.endswith('.json')]

def save_scene(name, scene):
    path = os.path.join(STORAGE_DIR, f"{name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(scene.to_dict(), f, ensure_ascii=False, indent=2)
    return path

def load_saved(name, scene):
    path = os.path.join(STORAGE_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        scene.push_undo()
        scene._restore(loaded)
        return True
    return False