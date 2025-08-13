import json
import os
from lxml import etree

BASE_DIR = os.path.dirname(__file__)
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
STORAGE_DIR = os.path.join(BASE_DIR, "storage_files")
try:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    print("Отладка: Директория STORAGE_DIR создана или существует")
except Exception as e:
    print(f"Отладка: Ошибка создания STORAGE_DIR: {e}")

def list_examples(extension='.json'):
    try:
        files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(extension)]
        print(f"Отладка: Список примеров {extension}: {files}")
        return files
    except Exception as e:
        print(f"Отладка: Ошибка в list_examples: {e}")
        return []

def load_example(name, scene, is_xml=False):
    path = os.path.join(EXAMPLES_DIR, name)
    try:
        if os.path.exists(path):
            if is_xml:
                return load_xml(path, scene)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                scene.push_undo()
                scene._restore(loaded)
                print(f"Отладка: Загружен JSON-пример {name}")
                return True
        print(f"Отладка: Пример {name} не найден")
        return False
    except Exception as e:
        print(f"Отладка: Ошибка в load_example {name}: {e}")
        return False

def list_saved(extension='.json'):
    try:
        files = [f for f in os.listdir(STORAGE_DIR) if f.endswith(extension)]
        print(f"Отладка: Список сохранений {extension}: {files}")
        return files
    except Exception as e:
        print(f"Отладка: Ошибка в list_saved: {e}")
        return []

def save_scene(name, scene, is_xml=False):
    try:
        if is_xml:
            path = os.path.join(STORAGE_DIR, f"{name}.xml")
            save_xml(path, scene)
            print(f"Отладка: Сохранён XML в {path}")
            return path
        else:
            path = os.path.join(STORAGE_DIR, f"{name}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(scene.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"Отладка: Сохранён JSON в {path}")
            return path
    except Exception as e:
        print(f"Отладка: Ошибка в save_scene {name}: {e}")
        return None

def load_saved(name, scene, is_xml=False):
    path = os.path.join(STORAGE_DIR, name)
    try:
        if os.path.exists(path):
            if is_xml:
                return load_xml(path, scene)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                scene.push_undo()
                scene._restore(loaded)
                print(f"Отладка: Загружен сохранённый JSON {name}")
                return True
        print(f"Отладка: Сохранение {name} не найдено")
        return False
    except Exception as e:
        print(f"Отладка: Ошибка в load_saved {name}: {e}")
        return False

def load_xml(path, scene):
    try:
        tree = etree.parse(path)
        root = tree.getroot()
        scene.name = root.get('name', 'unnamed')
        scene.bones.clear()
        scene.frames.clear()
        for b in root.findall('.//bone'):
            scene.bones[b.get('id')] = scene.Bone(
                id=b.get('id'),
                x=float(b.get('x', '0')),
                y=float(b.get('y', '0')),
                angle=float(b.get('angle', '0')),
                length=float(b.get('length', '0')),
                parent=b.get('parent')
            )
        for f in root.findall('.//frame'):
            idx = int(f.get('index', '0'))
            scene.frames[idx] = {}
        scene.push_undo()
        print(f"Отладка: Загружен XML из {path}")
        return True
    except Exception as e:
        print(f"Отладка: Ошибка в load_xml {path}: {e}")
        return False

def save_xml(path, scene):
    try:
        root = etree.Element("figure", name=scene.name)
        bones_elem = etree.SubElement(root, "bones")
        for bid, b in scene.bones.items():
            etree.SubElement(bones_elem, "bone", id=bid, x=str(b.x), y=str(b.y), angle=str(b.angle), length=str(b.length), parent=b.parent or "")
        frames_elem = etree.SubElement(root, "frames")
        for idx in sorted(scene.frames.keys()):
            frame_elem = etree.SubElement(frames_elem, "frame", index=str(idx))
        tree = etree.ElementTree(root)
        tree.write(path, pretty_print=True, xml_declaration=True, encoding="utf-8")
        print(f"Отладка: Сохранён XML в {path}")
    except Exception as e:
        print(f"Отладка: Ошибка в save_xml {path}: {e}")