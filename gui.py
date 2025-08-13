import asyncio
import dearpygui.dearpygui as dpg
import numpy as np
import os
import json


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
        'job_status': "",
        'language': 'ru',  # По умолчанию русский
        'translations': {}  # Словарь переводов
    }

    # Загрузка переводов
    def load_translations(lang):
        lang_path = os.path.join(os.path.dirname(__file__), 'lang', f"{lang}.json")
        if os.path.exists(lang_path):
            with open(lang_path, 'r', encoding='utf-8') as f:
                state['translations'] = json.load(f)
            print(f"Отладка: Загружены переводы для {lang}")
        else:
            print(f"Отладка: Файл переводов {lang}.json не найден")
            state['translations'] = {}  # Пустой словарь, если не найден

    # Функция для получения перевода
    def t(key):
        return state['translations'].get(key, key)  # Если нет перевода, возвращаем ключ

    # Перезагрузка UI при смене языка
    def reload_ui():
        dpg.set_viewport_title(t('title'))
        dpg.set_item_label("file_menu", t('file_menu'))
        dpg.set_item_label("examples_json_text", t('examples_json'))
        dpg.set_item_label("examples_combo", t('examples'))
        dpg.set_item_label("examples_xml_text", t('examples_xml'))
        dpg.set_item_label("save_name", t('save_as_json'))
        dpg.set_item_label("save_json_btn", t('save_json'))
        dpg.set_item_label("load_combo", t('load_json'))
        dpg.set_item_label("save_name_xml", t('save_as_xml'))
        dpg.set_item_label("save_xml_btn", t('save_xml'))
        dpg.set_item_label("load_xml_combo", t('load_xml'))
        dpg.set_item_label("export_btn", t('export_gif_mp4'))
        dpg.set_item_label("tools_text", t('tools'))
        dpg.set_item_label("select_btn", t('select'))
        dpg.set_item_label("move_btn", t('move'))
        dpg.set_item_label("rotate_btn", t('rotate'))
        dpg.set_item_label("scale_btn", t('scale'))
        dpg.set_item_label("add_bone_text", t('add_bone'))
        dpg.set_item_label("new_bone_id", t('id'))
        dpg.set_item_label("new_bone_parent", t('parent'))
        dpg.set_item_label("add_btn", t('add'))
        dpg.set_item_label("delete_btn", t('delete_selected'))
        dpg.set_item_label("undo_btn", t('undo'))
        dpg.set_item_label("redo_btn", t('redo'))
        dpg.set_item_label("onion_prev_cb", t('onion_prev'))
        dpg.set_item_label("onion_next_cb", t('onion_next'))
        dpg.set_item_label("onion_alpha_slider", t('onion_alpha'))
        dpg.set_item_label("frame_slider", t('frame'))
        dpg.set_item_label("add_frame_btn", t('add_frame'))
        dpg.set_item_label("play_pause_btn", t('play_pause'))
        dpg.set_item_label("fps_slider", t('fps'))
        dpg.set_item_label("bones_text", t('bones'))
        dpg.set_item_label("properties_text", t('properties'))
        dpg.set_item_label("prop_x", t('x'))
        dpg.set_item_label("prop_y", t('y'))
        dpg.set_item_label("prop_angle", t('angle'))
        dpg.set_item_label("prop_length", t('length'))
        update_ui()  # Обновляем статус
        print(f"Отладка: Интерфейс обновлён для языка {state['language']}")

    # Инициализация переводов
    load_translations(state['language'])

    def update_positions():
        state['positions'] = {
            k: {"x": v[0], "y": v[1], "angle": v[2], "length": v[3]}
            for k, v in scene.compute_abs_positions(state['current_frame']).items()
        }
        print(f"Отладка: Обновлены позиции для кадра {state['current_frame']}")

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
                      f"{t('frame')}: {state['current_frame']} | {t('bones')}: {state['selected_bone']} | {t('tool_mode')}: {state['tool_mode']}")
        dpg.set_value("job_status_text", state['job_status'])
        print(f"Отладка: Обновлён UI, выбранная кость: {state['selected_bone']}")

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
        print("Отладка: Сцена отрисована")

    async def play_animation():
        while state['playing']:
            state['current_frame'] = (state['current_frame'] + 1) % (max(scene.frames.keys()) + 1)
            update_positions()
            update_ui()
            render_scene()
            await asyncio.sleep(1 / state['fps'])
        print("Отладка: Анимация остановлена")

    def toggle_play():
        state['playing'] = not state['playing']
        if state['playing']:
            asyncio.create_task(play_animation())
            print("Отладка: Анимация запущена")
        else:
            print("Отладка: Анимация на паузе")

    def change_frame(sender, data):
        state['current_frame'] = data
        update_positions()
        update_ui()
        render_scene()
        print(f"Отладка: Сменён кадр на {data}")

    def select_bone(sender, data):
        state['selected_bone'] = data
        update_ui()
        print(f"Отладка: Выбрана кость {data}")

    def update_prop(sender, data):
        if state['selected_bone']:
            key = dpg.get_item_user_data(sender)
            updates = {key: data}
            scene.push_undo()
            scene.update_frame_bone(state['current_frame'], state['selected_bone'], updates)
            update_positions()
            update_ui()
            render_scene()
            print(f"Отладка: Обновлено свойство {key} = {data} для кости {state['selected_bone']}")

    def add_bone_cb():
        bid = dpg.get_value("new_bone_id")
        parent = dpg.get_value("new_bone_parent")
        if bid:
            scene.push_undo()
            scene.bones[bid] = scene.Bone(id=bid, x=0, y=0, angle=0, length=50, parent=parent)
            update_ui()
            render_scene()
            print(f"Отладка: Добавлена кость {bid} с родителем {parent}")

    def delete_bone_cb():
        if state['selected_bone']:
            scene.push_undo()
            scene.delete_bone(state['selected_bone'])
            state['selected_bone'] = None
            update_positions()
            update_ui()
            render_scene()
            print(f"Отладка: Удалена кость {state['selected_bone']}")

    def add_frame_cb():
        scene.push_undo()
        idx = scene.add_frame()
        state['current_frame'] = idx
        update_positions()
        update_ui()
        render_scene()
        print(f"Отладка: Добавлен кадр {idx}")

    def undo_cb():
        if scene.undo():
            update_positions()
            update_ui()
            render_scene()
            print("Отладка: Отмена действия")

    def redo_cb():
        if scene.redo():
            update_positions()
            update_ui()
            render_scene()
            print("Отладка: Повтор действия")

    def load_example_cb():
        name = dpg.get_value("examples_combo")
        if name and storage.load_example(name, scene):
            state['current_frame'] = 0
            update_positions()
            update_ui()
            render_scene()
            print(f"Отладка: Загружен JSON-пример {name}")

    def load_example_xml_cb():
        name = dpg.get_value("examples_xml_combo")
        if name and storage.load_example(name, scene, is_xml=True):
            state['current_frame'] = 0
            update_positions()
            update_ui()
            render_scene()
            print(f"Отладка: Загружен XML-пример {name}")

    def save_scene_cb():
        name = dpg.get_value("save_name")
        if name:
            path = storage.save_scene(name, scene)
            dpg.configure_item("load_combo", items=storage.list_saved('.json'))
            print(f"Отладка: Сохранён JSON в {path}")

    def save_scene_xml_cb():
        name = dpg.get_value("save_name_xml")
        if name:
            path = storage.save_scene(name, scene, is_xml=True)
            dpg.configure_item("load_xml_combo", items=storage.list_saved('.xml'))
            print(f"Отладка: Сохранён XML в {path}")

    def load_scene_cb():
        name = dpg.get_value("load_combo")
        if name and storage.load_saved(name, scene):
            state['current_frame'] = 0
            update_positions()
            update_ui()
            render_scene()
            print(f"Отладка: Загружен сохранённый JSON {name}")

    def load_scene_xml_cb():
        name = dpg.get_value("load_xml_combo")
        if name and storage.load_saved(name, scene, is_xml=True):
            state['current_frame'] = 0
            update_positions()
            update_ui()
            render_scene()
            print(f"Отладка: Загружен сохранённый XML {name}")

    def start_render_cb():
        def update_status(status):
            state['job_status'] = status
            update_ui()
            print(f"Отладка: Статус экспорта: {status}")

        state['job_status'] = "starting"
        update_ui()
        asyncio.create_task(render.export_animation(scene, state['fps'], update_status))
        print("Отладка: Запущен экспорт")

    def set_tool(sender, data):
        state['tool_mode'] = data
        update_ui()
        print(f"Отладка: Сменён инструмент на {data}")

    def set_onion_prev(sender, data):
        state['onion_prev'] = data
        render_scene()
        print(f"Отладка: Onion предыдущий: {data}")

    def set_onion_next(sender, data):
        state['onion_next'] = data
        render_scene()
        print(f"Отладка: Onion следующий: {data}")

    def set_onion_alpha(sender, data):
        state['onion_alpha'] = data
        render_scene()
        print(f"Отладка: Onion прозрачность: {data}")

    def set_fps(sender, data):
        state['fps'] = data
        print(f"Отладка: FPS изменён на {data}")

    # Настройка шрифта для поддержки русского
    font_path = "default_font.ttf"  # Замени на путь к твоему TTF-шрифту (например, arial.ttf)
    if os.path.exists(font_path):
        with dpg.font_registry():
            with dpg.font(font_path, 16) as font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        dpg.bind_font(font)
        print(f"Отладка: Шрифт загружен: {font_path}")
    else:
        print(f"Отладка: Шрифт {font_path} не найден! Русский текст может не отображаться.")

    # Настройка окна
    dpg.create_context()
    dpg.create_viewport(title=t('title'), width=1200, height=800)

    with dpg.window(label=t('title'), no_close=True, no_title_bar=True, width=1200, height=800):
        with dpg.menu_bar():
            with dpg.menu(label=t('file_menu'), tag="file_menu"):
                dpg.add_text(t('examples_json'), tag="examples_json_text")
                dpg.add_combo(label=t('examples'), tag="examples_combo", items=storage.list_examples('.json'),
                              callback=load_example_cb)
                dpg.add_text(t('examples_xml'), tag="examples_xml_text")
                dpg.add_combo(label=t('examples'), tag="examples_xml_combo", items=storage.list_examples('.xml'),
                              callback=load_example_xml_cb)
                dpg.add_separator()
                dpg.add_input_text(label=t('save_as_json'), tag="save_name")
                dpg.add_button(label=t('save_json'), tag="save_json_btn", callback=save_scene_cb)
                dpg.add_combo(label=t('load_json'), tag="load_combo", items=storage.list_saved('.json'),
                              callback=load_scene_cb)
                dpg.add_separator()
                dpg.add_input_text(label=t('save_as_xml'), tag="save_name_xml")
                dpg.add_button(label=t('save_xml'), tag="save_xml_btn", callback=save_scene_xml_cb)
                dpg.add_combo(label=t('load_xml'), tag="load_xml_combo", items=storage.list_saved('.xml'),
                              callback=load_scene_xml_cb)
                dpg.add_separator()
                dpg.add_button(label=t('export_gif_mp4'), tag="export_btn", callback=start_render_cb)
                dpg.add_text(tag="job_status_text", default_value="")

            # Выбор языка
            with dpg.menu(label=t('language')):
                dpg.add_combo(label=t('language'), items=['ru', 'en'], default_value=state['language'],
                              callback=lambda s, d: (state.update({'language': d}), load_translations(d), reload_ui()))

        with dpg.group(horizontal=True):
            with dpg.child_window(width=200):
                dpg.add_text(t('tools'), tag="tools_text")
                dpg.add_button(label=t('select'), tag="select_btn", callback=set_tool, user_data="select")
                dpg.add_button(label=t('move'), tag="move_btn", callback=set_tool, user_data="move")
                dpg.add_button(label=t('rotate'), tag="rotate_btn", callback=set_tool, user_data="rotate")
                dpg.add_button(label=t('scale'), tag="scale_btn", callback=set_tool, user_data="scale")
                dpg.add_separator()
                dpg.add_text(t('add_bone'), tag="add_bone_text")
                dpg.add_input_text(tag="new_bone_id", label=t('id'))
                dpg.add_input_text(tag="new_bone_parent", label=t('parent'))
                dpg.add_button(label=t('add'), tag="add_btn", callback=add_bone_cb)
                dpg.add_button(label=t('delete_selected'), tag="delete_btn", callback=delete_bone_cb)
                dpg.add_separator()
                dpg.add_button(label=t('undo'), tag="undo_btn", callback=undo_cb)
                dpg.add_button(label=t('redo'), tag="redo_btn", callback=redo_cb)
                dpg.add_separator()
                dpg.add_checkbox(label=t('onion_prev'), tag="onion_prev_cb", default_value=state['onion_prev'],
                                 callback=set_onion_prev)
                dpg.add_checkbox(label=t('onion_next'), tag="onion_next_cb", default_value=state['onion_next'],
                                 callback=set_onion_next)
                dpg.add_slider_float(label=t('onion_alpha'), tag="onion_alpha_slider",
                                     default_value=state['onion_alpha'], min_value=0.0, max_value=1.0,
                                     callback=set_onion_alpha)

            with dpg.child_window(width=600):
                with dpg.drawlist(tag="drawlist", width=500, height=500):
                    pass
                dpg.add_slider_int(tag="frame_slider", label=t('frame'), default_value=0, min_value=0, max_value=0,
                                   callback=change_frame)
                dpg.add_button(label=t('add_frame'), tag="add_frame_btn", callback=add_frame_cb)
                dpg.add_button(label=t('play_pause'), tag="play_pause_btn", callback=toggle_play)
                dpg.add_slider_int(label=t('fps'), tag="fps_slider", default_value=12, min_value=1, max_value=60,
                                   callback=set_fps)

            with dpg.child_window(width=200):
                dpg.add_text(t('bones'), tag="bones_text")
                dpg.add_listbox(tag="bone_list", items=[], callback=select_bone, num_items=10)
                dpg.add_separator()
                dpg.add_text(t('properties'), tag="properties_text")
                dpg.add_input_float(tag="prop_x", label=t('x'), callback=update_prop, user_data="x")
                dpg.add_input_float(tag="prop_y", label=t('y'), callback=update_prop, user_data="y")
                dpg.add_input_float(tag="prop_angle", label=t('angle'), callback=update_prop, user_data="angle")
                dpg.add_input_float(tag="prop_length", label=t('length'), callback=update_prop, user_data="length")

        dpg.add_text(tag="status_text", default_value=t('status'))

    # Инициализация
    update_positions()
    update_ui()
    render_scene()
    print("Отладка: GUI инициализирован")

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
    print("Отладка: GUI закрыт")