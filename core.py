# /core.py

from copy import deepcopy
from typing import Dict
import numpy as np
import logging

logger = logging.getLogger(__name__)

logger.debug('core.py run')
file_id = 'core'

class Bone:
    def __init__(self, id, x=0, y=0, angle=0, length=0, parent=None):
        logger.info(f'created bone {id} | {file_id}')
        self.id = id
        self.x = float(x)
        self.y = float(y)
        self.angle = float(angle)
        self.length = float(length)
        self.parent = parent

    def to_dict(self):
        logger.debug(f'bone {self.id} in dict | {file_id}')
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
        logger.info(f'initialization Scene | {file_id}')
        self.bones: Dict[str, Bone] = {}
        self.frames: Dict[int, Dict[str, Dict[str, float]]] = {0: {}}
        self.name = "unnamed"
        self.undo_stack = []
        self.redo_stack = []
        self.cache: Dict[int, Dict[str, tuple]] = {}

    def snapshot(self):
        logger.info(f'create scene snapshot | {file_id}')
        return deepcopy({
            "bones": {k: v.to_dict() for k, v in self.bones.items()},
            "frames": deepcopy(self.frames),
            "name": self.name,
        })

    def push_undo(self):
        logger.info(f'push undo scene | {file_id}')
        self.undo_stack.append(self.snapshot())
        self.redo_stack.clear()
        self.clear_cache()

    def undo(self):
        logger.info(f'undo to scene | {file_id}')
        if not self.undo_stack:
            return False
        state = self.undo_stack.pop()
        self.redo_stack.append(self.snapshot())
        self._restore(state)
        return True

    def redo(self):
        logger.debug(f'redo in scene | {file_id}')
        if not self.redo_stack:
            return False
        state = self.redo_stack.pop()
        self.undo_stack.append(self.snapshot())
        self._restore(state)
        return True

    def _restore(self, state):
        logger.info(f'restore state scene | {file_id}')
        self.bones = {k: Bone(**v) for k, v in state["bones"].items()}
        self.frames = state["frames"]
        self.name = state.get("name", "unnamed")
        self.clear_cache()

    def clear_cache(self):
        logger.info(f'clear cache | {file_id}')
        self.cache = {}

    def compute_abs_positions(self, frame_idx: int) -> Dict[str, tuple]:
        logger.info(f'calculating positions for a frame {frame_idx} | {file_id}')
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
        logger.info(f'scene to dict | {file_id}')
        return {
            "name": self.name,
            "bones": {k: v.to_dict() for k, v in self.bones.items()},
            "frames": deepcopy(self.frames),
        }

    def add_frame(self):
        logger.info(f'add frame to scene | {file_id}')
        idx = max(self.frames.keys()) + 1
        self.frames[idx] = {}
        return idx

    def update_frame_bone(self, frame_idx: int, bid: str, updates: Dict[str, float]):
        logger.debug(f'update bone {bid} on frame {frame_idx} | {file_id}')
        if frame_idx not in self.frames:
            self.frames[frame_idx] = {}
        if bid not in self.frames[frame_idx]:
            self.frames[frame_idx][bid] = {}
        self.frames[frame_idx][bid].update(updates)
        self.clear_cache()

    def delete_bone(self, bid: str):
        logger.info(f'delete bone {bid} | {file_id}')
        if bid in self.bones:
            del self.bones[bid]
            for f in self.frames.values():
                f.pop(bid, None)
            self.clear_cache()