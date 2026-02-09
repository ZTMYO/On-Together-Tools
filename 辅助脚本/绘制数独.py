from pynput import mouse
from pynput import keyboard
import threading
import time

mouse_controller = mouse.Controller()

CELL_SIZE = 60

last_grid_top_left = None

# 控制宏执行的停止开关：左键按下时置为 True，各绘制宏在执行过程中定期检查
macro_stop_event = threading.Event()

SUDOKU_PUZZLE =[
    [6, 0, 4, 5, 0, 0, 3, 0, 0],
    [0, 0, 0, 0, 0, 6, 5, 8, 4],
    [0, 3, 0, 7, 9, 0, 0, 0, 2],
    [4, 2, 0, 0, 1, 0, 7, 0, 0],
    [0, 0, 7, 2, 0, 9, 8, 0, 0],
    [0, 0, 1, 0, 4, 0, 0, 5, 3],
    [8, 0, 0, 0, 2, 3, 0, 1, 0],
    [1, 7, 3, 4, 0, 0, 0, 0, 0],
    [0, 0, 9, 0, 0, 1, 6, 0, 5]
]

def draw_line(x1, y1, x2, y2, hold_time=0.02):
    # 若已请求停止宏，则不再继续绘制
    if macro_stop_event.is_set():
        return

    # 移动到起点
    mouse_controller.position = (x1, y1)
    time.sleep(0.02)

    # 按下左键
    mouse_controller.press(mouse.Button.left)
    time.sleep(hold_time)

    # 拖动到终点
    mouse_controller.position = (x2, y2)
    time.sleep(hold_time)

    # 松开左键
    mouse_controller.release(mouse.Button.left)
    time.sleep(0.02)


def draw_grid(top_left_x, top_left_y):
    global last_grid_top_left
    rows = len(SUDOKU_PUZZLE)
    cols = len(SUDOKU_PUZZLE[0]) if SUDOKU_PUZZLE else 9
    width = cols * CELL_SIZE
    height = rows * CELL_SIZE
    print(f"开始绘制 {rows}x{cols} 网格，格子大小 {CELL_SIZE} 像素，左上角=({top_left_x}, {top_left_y})")
    last_grid_top_left = (top_left_x, top_left_y)
    # 先画竖线（列）
    for c in range(cols + 1):
        x = top_left_x + c * CELL_SIZE
        y1 = top_left_y
        y2 = top_left_y + height
        draw_line(x, y1, x, y2)
    # 再画横线（行）
    for r in range(rows + 1):
        y = top_left_y + r * CELL_SIZE
        x1 = top_left_x
        x2 = top_left_x + width
        draw_line(x1, y, x2, y)

    print("网格绘制完成 ✅")


def draw_sudoku_separators():
    if last_grid_top_left is None:
        print("尚未绘制网格，无法绘制数独粗分隔线，请先按 X1 画网格。")
        return

    top_left_x, top_left_y = last_grid_top_left
    rows = len(SUDOKU_PUZZLE)
    cols = len(SUDOKU_PUZZLE[0]) if SUDOKU_PUZZLE else 9
    width = cols * CELL_SIZE
    height = rows * CELL_SIZE

    print(f"开始绘制数独粗分隔线，基于左上角=({top_left_x}, {top_left_y})，格子大小 {CELL_SIZE}")

    # 外框四条边
    x1 = top_left_x
    x2 = top_left_x + width
    y1 = top_left_y
    y2 = top_left_y + height

    draw_line(x1, y1, x2, y1)  # 上边
    draw_line(x1, y2, x2, y2)  # 下边
    draw_line(x1, y1, x1, y2)  # 左边
    draw_line(x2, y1, x2, y2)  # 右边

    # 内部分隔线：每 3 个格子画一条粗线，把 9x9 分成 3x3 宫
    # 竖向分隔线（两条）
    for c in (3, 6):
        x = top_left_x + c * CELL_SIZE
        draw_line(x, y1, x, y2)

    # 水平分隔线（两条）
    for r in (3, 6):
        y = top_left_y + r * CELL_SIZE
        draw_line(x1, y, x2, y)

    print("数独粗分隔线绘制完成 ✅")


def handle_side_button_click():
    """在单独线程中执行网格绘制，避免阻塞监听"""
    # 启动新宏前清除停止标志
    macro_stop_event.clear()
    # 先松开上侧键，避免在移动到起点过程中留下多余笔迹
    try:
        mouse_controller.release(mouse.Button.x2)
    except Exception:
        pass

    # 以当前鼠标位置为左上角
    x, y = mouse_controller.position
    draw_grid(x, y)


def handle_sudoku_button_click():
    """在单独线程中执行数独粗分隔线绘制"""
    # 启动新宏前清除停止标志
    macro_stop_event.clear()
    # 先松开下侧键，避免在移动到起点过程中留下多余笔迹
    try:
        mouse_controller.release(mouse.Button.x1)
    except Exception:
        pass

    draw_sudoku_separators()


def get_current_cell_row_col():
    """根据当前鼠标位置和最近一次网格左上角，计算所在格子的行列索引"""
    if last_grid_top_left is None:
        print("尚未绘制网格，无法确定格子位置，请先按侧键画网格。")
        return None

    grid_x, grid_y = last_grid_top_left
    mouse_x, mouse_y = mouse_controller.position

    col = int((mouse_x - grid_x) // CELL_SIZE)
    row = int((mouse_y - grid_y) // CELL_SIZE)

    max_row = len(SUDOKU_PUZZLE) - 1
    max_col = len(SUDOKU_PUZZLE[0]) - 1 if SUDOKU_PUZZLE else 8

    col = max(0, min(max_col, col))
    row = max(0, min(max_row, row))

    return row, col


def get_current_cell_center():
    """计算当前鼠标所在格子的中心坐标"""
    rc = get_current_cell_row_col()
    if rc is None:
        return None

    row, col = rc
    grid_x, grid_y = last_grid_top_left

    center_x = grid_x + col * CELL_SIZE + CELL_SIZE / 2
    center_y = grid_y + row * CELL_SIZE + CELL_SIZE / 2

    return center_x, center_y


def draw_digit_at_center(digit, cx, cy):
    size = CELL_SIZE * 0.6
    half = size / 2
    left = cx - half
    right = cx + half
    top = cy - half
    bottom = cy + half

    mid_x = cx
    mid_y = cy

    inset = size * 0.15
    left_in = left + inset
    right_in = right - inset
    top_in = top + inset
    bottom_in = bottom - inset

    top_seg = (left_in, top_in, right_in, top_in)
    mid_seg = (left_in, mid_y, right_in, mid_y)
    bot_seg = (left_in, bottom_in, right_in, bottom_in)

    ul_seg = (left_in, top_in, left_in, mid_y)      # 左上竖
    ll_seg = (left_in, mid_y, left_in, bottom_in)   # 左下竖
    ur_seg = (right_in, top_in, right_in, mid_y)    # 右上竖
    lr_seg = (right_in, mid_y, right_in, bottom_in) # 右下竖

    def seg(line):
        x1, y1, x2, y2 = line
        draw_line(x1, y1, x2, y2)

    if digit == 1:
        draw_line(mid_x, top_in, mid_x, bottom_in)
    elif digit == 2:
        for s in (top_seg, mid_seg, bot_seg, ur_seg, ll_seg):
            seg(s)
    elif digit == 3:
        for s in (top_seg, mid_seg, bot_seg, ur_seg, lr_seg):
            seg(s)
    elif digit == 4:
        for s in (mid_seg, ul_seg, ur_seg, lr_seg):
            seg(s)
    elif digit == 5:
        for s in (top_seg, mid_seg, bot_seg, ul_seg, lr_seg):
            seg(s)
    elif digit == 6:
        for s in (top_seg, mid_seg, bot_seg, ul_seg, ll_seg, lr_seg):
            seg(s)
    elif digit == 7:
        for s in (top_seg, ur_seg, lr_seg):
            seg(s)
    elif digit == 8:
        for s in (top_seg, mid_seg, bot_seg, ul_seg, ll_seg, ur_seg, lr_seg):
            seg(s)
    elif digit == 9:
        for s in (top_seg, mid_seg, bot_seg, ul_seg, ur_seg, lr_seg):
            seg(s)
    else:
        pass


def draw_digit_in_current_cell(digit):
    """在当前鼠标所在格子里绘制数字 digit (0-9)。"""
    if macro_stop_event.is_set():
        return
    center = get_current_cell_center()
    if center is None:
        return
    cx, cy = center
    print(f"在当前格子绘制数字 {digit}，中心=({cx:.1f}, {cy:.1f})")
    draw_digit_at_center(digit, cx, cy)


def fill_all_cells_from_puzzle():
    if last_grid_top_left is None:
        print("尚未绘制网格，无法一键填充，请先绘制网格。")
        return

    grid_x, grid_y = last_grid_top_left

    rows = len(SUDOKU_PUZZLE)
    cols = len(SUDOKU_PUZZLE[0]) if SUDOKU_PUZZLE else 9

    for row in range(rows):
        for col in range(cols):
            if macro_stop_event.is_set():
                return
            digit = SUDOKU_PUZZLE[row][col]
            if not digit:
                continue

            cx = grid_x + col * CELL_SIZE + CELL_SIZE / 2
            cy = grid_y + row * CELL_SIZE + CELL_SIZE / 2
            print(f"填充题目：({row + 1}, {col + 1}) = {digit}")
            draw_digit_at_center(digit, cx, cy)


def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.x2:
        print("检测到侧键按下，准备绘制网格...")
        t = threading.Thread(target=handle_side_button_click, daemon=True)
        t.start()
    elif pressed and button == mouse.Button.x1:
        print("检测到侧键（X1，对应下侧键）按下，准备绘制数独粗分隔线...")
        t = threading.Thread(target=handle_sudoku_button_click, daemon=True)
        t.start()


def on_key_press(key):
    try:
        if (hasattr(key, "char") and key.char in ("p", "P")) or (hasattr(key, "vk") and key.vk == 80):
            macro_stop_event.set()
            return

        # '-' 键：替代上侧键(X2)触发绘制网格
        if hasattr(key, "char") and key.char == "-":
            t = threading.Thread(target=handle_side_button_click, daemon=True)
            t.start()
            return

        # '=' 键：替代下侧键(X1)触发绘制数独粗分隔线
        if hasattr(key, "char") and key.char == "=":
            t = threading.Thread(target=handle_sudoku_button_click, daemon=True)
            t.start()
            return

        if (hasattr(key, "char") and key.char == "0") or (hasattr(key, "vk") and key.vk == 96):
            macro_stop_event.clear()
            t = threading.Thread(target=fill_all_cells_from_puzzle, daemon=True)
            t.start()
            return

        digit = None

        # 上排数字键 1-9
        if hasattr(key, "char") and key.char is not None and key.char.isdigit() and key.char != "0":
            digit = int(key.char)
        # 小键盘数字键 1-9（VK_Numpad1-9 = 97-105）
        elif hasattr(key, "vk") and 97 <= key.vk <= 105:
            digit = key.vk - 96

        if digit is not None:
            macro_stop_event.clear()
            t = threading.Thread(target=draw_digit_in_current_cell, args=(digit,), daemon=True)
            t.start()
    except Exception as e:
        print(f"键盘监听异常: {e}")


def main():
    print("侧键绘制网格脚本已启动")
    print("1. 先选择画笔工具")
    print("2. 鼠标移动到网格左上角位置")
    print("3. 按下鼠标上侧键或 '-' 键，自动绘制 9x9 网格")
    print("4. 换成其他颜色笔刷后，按下鼠标下侧键或 '=' 键绘制数独粗分隔线")
    print("5. 按小键盘0将开始填入预设的数字")
    print("6. 鼠标放在格子中按小键盘1-9可以往该格填入相应数字")
    print("按P键暂停绘制")
    print("按 Ctrl+C 退出脚本")

    # 启动鼠标监听和键盘监听
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_key_press)

    mouse_listener.start()
    keyboard_listener.start()

    mouse_listener.join()


if __name__ == "__main__":
    main()
