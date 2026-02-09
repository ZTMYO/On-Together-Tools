from pynput import mouse
from pynput import keyboard
import threading
import time

mouse_controller = mouse.Controller()

PIXEL_SIZE = 6  # 每个像素的大小，根据图案调整

last_grid_top_left = None

# 控制宏执行的停止开关：左键按下时置为 True，各绘制宏在执行过程中定期检查
macro_stop_event = threading.Event()

# 从dots.txt读取点阵图案
def load_pattern_from_file(file_path):
    pattern = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 找到最大行长度
            max_cols = max(len(line.rstrip('\n')) for line in lines) if lines else 0
            for line in lines:
                row = []
                for char in line.rstrip('\n'):
                    if char == '.':
                        row.append(True)
                    else:
                        row.append(False)
                # 补齐到最大长度
                while len(row) < max_cols:
                    row.append(False)
                pattern.append(row)
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到")
        return []
    return pattern

PATTERN = load_pattern_from_file('dots.txt')
GRID_ROWS = len(PATTERN)
GRID_COLS = max(len(row) for row in PATTERN) if PATTERN else 0

def draw_line(x1, y1, x2, y2, hold_time=0.02):
    # 若已请求停止宏，则不再继续绘制
    if macro_stop_event.is_set():
        return

    # 移动到起点
    mouse_controller.position = (x1, y1)
    time.sleep(0.01)

    # 按下左键
    mouse_controller.press(mouse.Button.left)
    time.sleep(hold_time)

    # 拖动到终点
    mouse_controller.position = (x2, y2)
    time.sleep(hold_time)

    # 松开左键
    mouse_controller.release(mouse.Button.left)
    time.sleep(0.02)

def draw_pixel(cx, cy, size):
    """绘制一个像素点：移动到中心，点击一下"""
    # 移动到像素中心
    mouse_controller.position = (cx, cy)
    time.sleep(0.02)

    # 按下左键
    mouse_controller.press(mouse.Button.left)
    time.sleep(0.02)

    # 松开左键
    mouse_controller.release(mouse.Button.left)
    time.sleep(0.02)

def draw_pattern():
    if last_grid_top_left is None:
        print("尚未设置起点，无法绘制图案。")
        return

    mouse_controller.release(mouse.Button.left)
    time.sleep(0.01)

    grid_x, grid_y = last_grid_top_left

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if macro_stop_event.is_set():
                return
            if PATTERN[row][col]:
                cx = grid_x + col * PIXEL_SIZE + PIXEL_SIZE / 2
                cy = grid_y + row * PIXEL_SIZE + PIXEL_SIZE / 2
                print(f"绘制图案像素 ({row}, {col})")
                draw_pixel(cx, cy, PIXEL_SIZE)

def handle_side_button_click():
    macro_stop_event.clear()
    try:
        mouse_controller.release(mouse.Button.x2)
    except Exception:
        pass

    # 以当前鼠标位置为左上角
    x, y = mouse_controller.position
    global last_grid_top_left
    last_grid_top_left = (x, y)
    draw_pattern()

def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.x2:
        print("检测到侧键按下，准备绘制点阵网格...")
        t = threading.Thread(target=handle_side_button_click, daemon=True)
        t.start()

def on_key_press(key):
    try:
        if (hasattr(key, "char") and key.char in ("p", "P")) or (hasattr(key, "vk") and key.vk == 80):
            macro_stop_event.set()
            return

        # '-' 键作为上侧键(X2)的替代触发
        if hasattr(key, "char") and key.char == "-":
            t = threading.Thread(target=handle_side_button_click, daemon=True)
            t.start()
            return
    except Exception as e:
        print(f"键盘监听异常: {e}")

def main():
    print("脚本启动 🚀 | 侧键(X2)或 '-' 键开始绘制 | P键暂停 | Ctrl+C退出")
    # 启动鼠标监听和键盘监听
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_key_press)

    mouse_listener.start()
    keyboard_listener.start()

    mouse_listener.join()

if __name__ == "__main__":
    main()
