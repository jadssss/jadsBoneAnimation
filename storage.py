# /storage.py
# Storage management / Управление хранением

import json
import os
from lxml import etree
import logging

logger = logging.getLogger(__name__)

logger.debug('storage.py run')
file_id = 'storage'

BASE_DIR = os.path.dirname(__file__)
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
STORAGE_DIR = os.path.join(BASE_DIR, "storage_files")
try:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    logger.info(f'STORAGE_DIR created or exists | {file_id}')
except Exception as e:
    logger.error(f'error creating STORAGE_DIR: {e} | {file_id}')

def list_examples(extension='.json'):
    try:
        files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(extension)]
        logger.info(f'list examples {extension}: {files} | {file_id}')
        return files
    except Exception as e:
        logger.error(f'error in list_examples: {e} | {file_id}')
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
                logger.info(f'loaded JSON example {name} | {file_id}')
                return True
        logger.warning(f'example {name} not found | {file_id}')
        return False
    except Exception as e:
        logger.error(f'error in load_example {name}: {e} | {file_id}')
        return False

def list_saved(extension='.json'):
    try:
        files = [f for f in os.listdir(STORAGE_DIR) if f.endswith(extension)]
        logger.info(f'list saved {extension}: {files} | {file_id}')
        return files
    except Exception as e:
        logger.error(f'error in list_saved: {e} | {file_id}')
        return []

def save_scene(name, scene, is_xml=False):
    try:
        if is_xml:
            path = os.path.join(STORAGE_DIR, f"{name}.xml")
            save_xml(path, scene)
            logger.info(f'saved XML to {path} | {file_id}')
            return path
        else:
            path = os.path.join(STORAGE_DIR, f"{name}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(scene.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f'saved JSON to {path} | {file_id}')
            return path
    except Exception as e:
        logger.error(f'error in save_scene {name}: {e} | {file_id}')
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
                logger.info(f'loaded saved JSON {name} | {file_id}')
                return True
        logger.warning(f'save {name} not found | {file_id}')
        return False
    except Exception as e:
        logger.error(f'error in load_saved {name}: {e} | {file_id}')
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
        logger.info(f'loaded XML from {path} | {file_id}')
        return True
    except Exception as e:
        logger.error(f'error in load_xml {path}: {e} | {file_id}')
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
        logger.info(f'saved XML to {path} | {file_id}')
    except Exception as e:
        logger.error(f'error in save_xml {path}: {e} | {file_id}')