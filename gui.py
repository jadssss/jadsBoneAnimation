import asyncio
import dearpygui.dearpygui as dpg
import numpy as np


def setup_gui(scene, storage, render):
    # Глобальные переменные для GUI
    state = {
        'current_frame': 0,
        'selected_bone': None,
        'tool_mode': "select",
        'playing': False,
        'fps': 12,
        'onion_prev': True,
        'onion_next': False,
        'onion_alpha': 0.3,
        'positions': {},
        'job_status': ""
    }

    def update_positions():
        state['positions'] = {
            k: {"x": v[0], "y": v[1], "angle": v[2], "length": v[3]}
            for k, v in scene.compute_abs_positions(state['current_frame']).items()
        }

    def update_ui():
        dpg.set_value("frame_slider", state['current_frame'])
        dpg.configure_item("frame_slider", max_value=max(scene.frames.keys()))
        dpg.set_value("bone_list", list(scene.bones.keys()))
        if state['selected_bone'] and state['selected_bone'] in scene.bones:
            b = scene.bones[state['selected_bone']]
            overrides = scene.frames.get(state['current_frame'], {}).get(state['selected_bone'], {})
            dpg.set_value("prop_x", overrides.get('x', b.x))
            dpg.set_value("prop_y", overrides.get('y', b.y))
            dpg.set_value("prop_angle", overrides.get('angle', b.angle))
            dpg.set_value("prop_length", overrides.get('length', b.length))
        dpg.set_value("status_text",
                      f"Frame: {state['current_frame']} | Bone: {state['selected_bone']} | Mode: {state['tool_mode']}")
        dpg.set_value("job_status_text", state['job_status'])

    def render_scene():
        dpg.delete_item("drawlist", children_only=True)
        for bid, pos in state['positions'].items():
            x, y = pos['x'], pos['y']
            ex = x + np.cos(np.radians(pos['angle'])) * pos['length']
            ey = y + np.sin(np.radians(pos['angle'])) * pos['length']
            dpg.draw_line((x, y), (ex, ey), color=(0, 0, 0, 255), thickness=4, parent="drawlist")
            dpg.draw_circle((x, y), 4, color=(0, 0, 0, 255), fill=(0, 0, 0, 255), parent="drawlist")
        if state['onion_prev'] and state['current_frame'] > 0:
            prev_pos = scene.compute_abs_positions(state['current_frame'] - 1)
            for bid, v in prev_pos.items():
                x, y = v[0], v[1]
                ex = x + np.cos(np.radians(v[2])) * v[3]
                ey = y + np.sin(np.radians(v[2])) * v[3]
                dpg.draw_line((x, y), (ex, ey), color=(128, 128, 128, int(255 * state['onion_alpha'])), thickness=2,
                              parent="drawlist")
        if state['onion_next'] and state['current_frame'] < max(scene.frames.keys()):
            next_pos = scene.compute_abs_positions(state['current_frame'] + 1)
            for bid, v in next_pos.items():
                x, y = v[0], v[1]
                ex = x + np.cos(np.radians(v[2])) * v[3]
                ey = y + np.sin(np.radians(v[2])) * v[3]
                dpg.draw_line((x, y), (ex, ey), color=(128, 128, 128, int(255 * state['onion_alpha'])), thickness=2,
                              parent="drawlist")

    async def play_animation():
        while state['playing']:
            state['current_frame'] = (state['current_frame'] + 1) % (max(scene.frames.keys()) + 1)
            update_positions()
            update_ui()
            render_scene()
            await asyncio.sleep(1 / state['fps'])

    def toggle_play():
        state['playing'] = not state['playing']
        if state['playing']:
            asyncio.create_task(play_animation())

    def change_frame(sender, data):
        state['current_frame'] = data
        update_positions()
        update_ui()
        render_scene()

    def select_bone(sender, data):
        state['selected_bone'] = data
        update_ui()

    def update_prop(sender, data):
        if state['selected_bone']:
            key = dpg.get_item_user_data(sender)
            updates = {key: data}
            scene.push_undo()
            scene.update_frame_bone(state['current_frame'], state['selected_bone'], updates)
            update_positions()
            update_ui()
            render_scene()

    def add_bone_cb():
        bid = dpg.get_value("new_bone_id")
        parent = dpg.get_value("new_bone_parent")
        if bid:
            scene.push_undo()
            scene.bones[bid] = scene.Bone(id=bid, x=0, y=0, angle=0, length=50, parent=parent)
            update_ui()
            render_scene()

    def delete_bone_cb():
        if state['selected_bone']:
            scene.push_undo()
            scene.delete_bone(state['selected_bone'])
            state['selected_bone'] = None
            update_positions()
            update_ui()
            render_scene()

    def add_frame_cb():
        scene.push_undo()
        idx = scene.add_frame()
        state['current_frame'] = idx
        update_positions()
        update_ui()
        render_scene()

    def undo_cb():
        if scene.undo():
            update_positions()
            update_ui()
            render_scene()

    def redo_cb():
        if scene.redo():
            update_positions()
            update_ui()
            render_scene()

    def load_example_cb():
        name = dpg.get_value("examples_combo")
        if name and storage.load_example(name, scene):
            state['current_frame'] = 0
            update_positions()
            update_ui()
            render_scene()

    def save_scene_cb():
        name = dpg.get_value("save_name")
        if name:
            storage.save_scene(name, scene)
            dpg.configure_item("load_combo", items=storage.list_saved())

    def load_scene_cb():
        name = dpg.get_value("load_combo")
        if name and storage.load_saved(name, scene):
            state['current_frame'] = 0
            update_positions()
            update_ui()
            render_scene()

    def start_render_cb():
        def update_status(status):
            state['job_status'] = status
            update_ui()

        state['job_status'] = "starting"
        update_ui()
        asyncio.create_task(render.export_animation(scene, state['fps'], update_status))

    def set_tool(sender, data):
        state['tool_mode'] = data
        update_ui()

    def set_onion_prev(sender, data):
        state['onion_prev'] = data
        render_scene()

    def set_onion_next(sender, data):
        state['onion_next'] = data
        render_scene()

    def set_onion_alpha(sender, data):
        state['onion_alpha'] = data
        render_scene()

    def set_fps(sender, data):
        state['fps'] = data

    # Настройка окна
    dpg.create_context()
    dpg.create_viewport(title='Bone Animator', width=1200, height=800)

    with dpg.window(label="Bone Animator", no_close=True, no_title_bar=True, width=1200, height=800):
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_combo(label="Examples", tag="examples_combo", items=storage.list_examples(),
                              callback=load_example_cb)
                dpg.add_input_text(label="Save as", tag="save_name")
                dpg.add_button(label="Save", callback=save_scene_cb)
                dpg.add_combo(label="Load", tag="load_combo", items=storage.list_saved(), callback=load_scene_cb)
                dpg.add_button(label="Export GIF/MP4", callback=start_render_cb)
                dpg.add_text(tag="job_status_text", default_value="")

        with dpg.group(horizontal=True):
            with dpg.child_window(width=200):
                dpg.add_text("Tools")
                dpg.add_button(label="Select", callback=set_tool, user_data="select")
                dpg.add_button(label="Move", callback=set_tool, user_data="move")
                dpg.add_button(label="Rotate", callback=set_tool, user_data="rotate")
                dpg.add_button(label="Scale", callback=set_tool, user_data="scale")
                dpg.add_separator()
                dpg.add_text("Add Bone")
                dpg.add_input_text(tag="new_bone_id", label="ID")
                dpg.add_input_text(tag="new_bone_parent", label="Parent")
                dpg.add_button(label="Add", callback=add_bone_cb)
                dpg.add_button(label="Delete Selected", callback=delete_bone_cb)
                dpg.add_separator()
                dpg.add_button(label="Undo (Ctrl+Z)", callback=undo_cb)
                dpg.add_button(label="Redo (Ctrl+Y)", callback=redo_cb)
                dpg.add_separator()
                dpg.add_checkbox(label="Onion Prev", default_value=state['onion_prev'], callback=set_onion_prev)
                dpg.add_checkbox(label="Onion Next", default_value=state['onion_next'], callback=set_onion_next)
                dpg.add_slider_float(label="Onion Alpha", default_value=state['onion_alpha'], min_value=0.0,
                                     max_value=1.0, callback=set_onion_alpha)

            with dpg.child_window(width=600):
                with dpg.drawlist(tag="drawlist", width=500, height=500):
                    pass
                dpg.add_slider_int(tag="frame_slider", label="Frame", default_value=0, min_value=0, max_value=0,
                                   callback=change_frame)
                dpg.add_button(label="Add Frame", callback=add_frame_cb)
                dpg.add_button(label="Play/Pause", callback=toggle_play)
                dpg.add_slider_int(label="FPS", default_value=12, min_value=1, max_value=60, callback=set_fps)

            with dpg.child_window(width=200):
                dpg.add_text("Bones")
                dpg.add_listbox(tag="bone_list", items=[], callback=select_bone, num_items=10)
                dpg.add_separator()
                dpg.add_text("Properties")
                dpg.add_input_float(tag="prop_x", label="X", callback=update_prop, user_data="x")
                dpg.add_input_float(tag="prop_y", label="Y", callback=update_prop, user_data="y")
                dpg.add_input_float(tag="prop_angle", label="Angle", callback=update_prop, user_data="angle")
                dpg.add_input_float(tag="prop_length", label="Length", callback=update_prop, user_data="length")

        dpg.add_text(tag="status_text", default_value="Status")

    # Инициализация
    update_positions()
    update_ui()
    render_scene()

    # Shortcuts (Ctrl+Z для undo, Ctrl+Y для redo)
    def z_pressed(sender, app_data):
        if dpg.is_key_down(dpg.mvKey_ModCtrl):
            undo_cb()

    def y_pressed(sender, app_data):
        if dpg.is_key_down(dpg.mvKey_ModCtrl):
            redo_cb()

    with dpg.handler_registry():
        dpg.add_key_press_handler(key=dpg.mvKey_Z, callback=z_pressed)
        dpg.add_key_press_handler(key=dpg.mvKey_Y, callback=y_pressed)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()