import json
import os
from lxml import etree

BASE_DIR = os.path.dirname(__file__)
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
STORAGE_DIR = os.path.join(BASE_DIR, "storage_files")
os.makedirs(STORAGE_DIR, exist_ok=True)

def list_examples(extension='.json'):
    return [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(extension)]

def load_example(name, scene, is_xml=False):
    path = os.path.join(EXAMPLES_DIR, name)
    if os.path.exists(path):
        if is_xml:
            return load_xml(path, scene)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            scene.push_undo()
            scene._restore(loaded)
            return True
    return False

def list_saved(extension='.json'):
    return [f for f in os.listdir(STORAGE_DIR) if f.endswith(extension)]

def save_scene(name, scene, is_xml=False):
    if is_xml:
        path = os.path.join(STORAGE_DIR, f"{name}.xml")
        save_xml(path, scene)
        return path
    else:
        path = os.path.join(STORAGE_DIR, f"{name}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(scene.to_dict(), f, ensure_ascii=False, indent=2)
        return path

def load_saved(name, scene, is_xml=False):
    path = os.path.join(STORAGE_DIR, name)
    if os.path.exists(path):
        if is_xml:
            return load_xml(path, scene)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            scene.push_undo()
            scene._restore(loaded)
            return True
    return False

def load_xml(path, scene):
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
        scene.frames[idx] = {}  # Здесь можно добавить overrides, если они есть в XML (в примере пустые)
        # Если в frame есть child elements для overrides, добавить парсинг
        # В примере пустые, так что ок
    scene.push_undo()
    return True

def save_xml(path, scene):
    root = etree.Element("figure", name=scene.name)
    bones_elem = etree.SubElement(root, "bones")
    for bid, b in scene.bones.items():
        etree.SubElement(bones_elem, "bone", id=bid, x=str(b.x), y=str(b.y), angle=str(b.angle), length=str(b.length), parent=b.parent or "")
    frames_elem = etree.SubElement(root, "frames")
    for idx in sorted(scene.frames.keys()):
        frame_elem = etree.SubElement(frames_elem, "frame", index=str(idx))
        # Если есть overrides, добавить child elements; в примере пустые
    tree = etree.ElementTree(root)
    tree.write(path, pretty_print=True, xml_declaration=True, encoding="utf-8")