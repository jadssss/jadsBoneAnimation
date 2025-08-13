from copy import deepcopy
from typing import Dict
import numpy as np


class Bone:
    def __init__(self, id, x=0, y=0, angle=0, length=0, parent=None):
        print(f"Отладка: Создание Bone {id}")
        self.id = id
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.length = float(length)
        self.parent = parent

    def to_dict(self):
        print(f"Отладка: Bone {self.id} в словарь")
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "angle": self.angle,
            "length": self.length,
            "parent": self.parent,
        }


class Scene:
    def __init__(self):
        print("Отладка: Инициализация Scene")
        self.bones: Dict[str, Bone] = {}
        self.frames: Dict[int, Dict[str, Dict[str, float]]] = {0: {}}
        self.name = "unnamed"
        self.undo_stack = []
        self.redo_stack = []
        self.cache: Dict[int, Dict[str, tuple]] = {}

    def snapshot(self):
        print("Отладка: Создание снапшота Scene")
        return deepcopy({
            "bones": {k: v.to_dict() for k, v in self.bones.items()},
            "frames": deepcopy(self.frames),
            "name": self.name,
        })

    def push_undo(self):
        print("Отладка: Push undo в Scene")
        self.undo_stack.append(self.snapshot())
        self.redo_stack.clear()
        self.clear_cache()

    def undo(self):
        print("Отладка: Undo в Scene")
        if not self.undo_stack:
            return False
        state = self.undo_stack.pop()
        self.redo_stack.append(self.snapshot())
        self._restore(state)
        return True

    def redo(self):
        print("Отладка: Redo в Scene")
        if not self.redo_stack:
            return False
        state = self.redo_stack.pop()
        self.undo_stack.append(self.snapshot())
        self._restore(state)
        return True

    def _restore(self, state):
        print("Отладка: Restore состояния Scene")
        self.bones = {k: Bone(**v) for k, v in state["bones"].items()}
        self.frames = state["frames"]
        self.name = state.get("name", "unnamed")
        self.clear_cache()

    def clear_cache(self):
        print("Отладка: Очистка кэша в Scene")
        self.cache = {}

    def compute_abs_positions(self, frame_idx: int) -> Dict[str, tuple]:
        print(f"Отладка: Вычисление позиций для кадра {frame_idx}")
        if frame_idx in self.cache:
            return self.cache[frame_idx]

        abs_pos = {}

        def get_bone_state(bid):
            b = self.bones[bid]
            overrides = self.frames.get(frame_idx, {}).get(bid, {})
            return {
                "x": overrides.get("x", b.x),
                "y": overrides.get("y", b.y),
                "angle": overrides.get("angle", b.angle),
                "length": overrides.get("length", b.length),
                "parent": b.parent
            }

        def compute(bid):
            if bid in abs_pos:
                return abs_pos[bid]
            bs = get_bone_state(bid)
            if bs['parent']:
                px, py, pangle = compute(bs['parent'])[:3]
                rad = np.radians(pangle)
                ax = px + bs['x'] * np.cos(rad) - bs['y'] * np.sin(rad)
                ay = py + bs['x'] * np.sin(rad) + bs['y'] * np.cos(rad)
                aangle = bs['angle'] + pangle
            else:
                ax, ay, aangle = bs['x'], bs['y'], bs['angle']
            alength = bs['length']
            abs_pos[bid] = (ax, ay, aangle, alength)
            return ax, ay, aangle, alength

        for bid in self.bones:
            compute(bid)
        self.cache[frame_idx] = abs_pos
        return abs_pos

    def to_dict(self):
        print("Отладка: Scene в словарь")
        return {
            "name": self.name,
            "bones": {k: v.to_dict() for k, v in self.bones.items()},
            "frames": deepcopy(self.frames),
        }

    def add_frame(self):
        print("Отладка: Добавление кадра в Scene")
        idx = max(self.frames.keys()) + 1
        self.frames[idx] = {}
        return idx

    def update_frame_bone(self, frame_idx: int, bid: str, updates: Dict[str, float]):
        print(f"Отладка: Обновление кости {bid} в кадре {frame_idx}")
        if frame_idx not in self.frames:
            self.frames[frame_idx] = {}
        if bid not in self.frames[frame_idx]:
            self.frames[frame_idx][bid] = {}
        self.frames[frame_idx][bid].update(updates)
        self.clear_cache()

    def delete_bone(self, bid: str):
        print(f"Отладка: Удаление кости {bid}")
        if bid in self.bones:
            del self.bones[bid]
            for f in self.frames.values():
                f.pop(bid, None)
            self.clear_cache()