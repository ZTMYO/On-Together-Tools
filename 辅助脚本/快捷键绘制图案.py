from pynput import mouse
from pynput import keyboard
import threading
import time
import math

# 核心配置
mouse_controller = mouse.Controller()
RADIUS = 80  # 默认圆半径（像素），两点模式下仅作备用
SEGMENTS = 50  # 分段数（越大越圆滑）
LINE_SEGMENTS = 100

# 控制宏执行的停止开关：各绘制宏在执行过程中定期检查
macro_stop_event = threading.Event()

def draw_circle(center_x, center_y, radius=None):
    """以指定坐标为圆心绘制圆形，半径可由参数指定"""
    if radius is None:
        radius = RADIUS
    # 计算圆周离散点
    points = [(int(center_x + radius * math.cos(2 * math.pi * i / SEGMENTS)),
               int(center_y + radius * math.sin(2 * math.pi * i / SEGMENTS))) 
              for i in range(SEGMENTS + 1)]
    
    # 移动到起点并开始绘制
    mouse_controller.position = points[0]
    time.sleep(0.01)
    mouse_controller.press(mouse.Button.left)
    time.sleep(0.02)
    
    # 拖动绘制圆周
    for x, y in points[1:]:
        if macro_stop_event.is_set():
            break
        mouse_controller.position = (x, y)
        time.sleep(0.02)
    
    # 结束绘制
    mouse_controller.release(mouse.Button.left)
    print("圆形绘制完成 ")

def draw_rectangle(x1, y1, x2, y2):
    # 规范化为左上和右下
    left = min(x1, x2)
    right = max(x1, x2)
    top = min(y1, y2)
    bottom = max(y1, y2)
    points = [
        (left, top),
        (right, top),
        (right, bottom),
        (left, bottom),
        (left, top),
    ]
    mouse_controller.position = points[0]
    time.sleep(0.01)
    mouse_controller.press(mouse.Button.left)
    time.sleep(0.02)
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        for s in range(1, SEGMENTS + 1):
            if macro_stop_event.is_set():
                break
            t = s / SEGMENTS
            x = int(x1 + (x2 - x1) * t)
            y = int(y1 + (y2 - y1) * t)
            mouse_controller.position = (x, y)
            time.sleep(0.01)
    mouse_controller.release(mouse.Button.left)
    print("矩形绘制完成")

def draw_line(x1, y1, x2, y2):
    mouse_controller.position = (x1, y1)
    time.sleep(0.01)
    mouse_controller.press(mouse.Button.left)
    time.sleep(0.02)
    for i in range(1, LINE_SEGMENTS + 1):
        if macro_stop_event.is_set():
            break
        t = i / LINE_SEGMENTS
        x = int(x1 + (x2 - x1) * t)
        y = int(y1 + (y2 - y1) * t)
        mouse_controller.position = (x, y)
        time.sleep(0.01)
    mouse_controller.release(mouse.Button.left)
    print("直线绘制完成")

def draw_triangle(p1, p2, p3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    points = [(x1, y1), (x2, y2), (x3, y3), (x1, y1)]
    mouse_controller.position = points[0]
    time.sleep(0.01)
    mouse_controller.press(mouse.Button.left)
    time.sleep(0.02)
    for i in range(len(points) - 1):
        sx, sy = points[i]
        ex, ey = points[i + 1]
        for s in range(1, SEGMENTS + 1):
            if macro_stop_event.is_set():
                break
            t = s / SEGMENTS
            x = int(sx + (ex - sx) * t)
            y = int(sy + (ey - sy) * t)
            mouse_controller.position = (x, y)
            time.sleep(0.01)
    mouse_controller.release(mouse.Button.left)
    print("三角形绘制完成")

def handle_draw_line(start_pos, end_pos):
    macro_stop_event.clear()
    x1, y1 = start_pos
    x2, y2 = end_pos
    draw_line(x1, y1, x2, y2)

def handle_draw_circle_two_points(start_pos, end_pos):
    macro_stop_event.clear()
    cx, cy = start_pos
    ex, ey = end_pos
    radius = int(math.hypot(ex - cx, ey - cy))
    if radius <= 0:
        print("半径过小，未绘制圆形")
        return
    draw_circle(cx, cy, radius)

def handle_draw_rectangle_two_points(start_pos, end_pos):
    macro_stop_event.clear()
    x1, y1 = start_pos
    x2, y2 = end_pos
    draw_rectangle(x1, y1, x2, y2)

def handle_draw_triangle(points):
    macro_stop_event.clear()
    if len(points) != 3:
        return
    draw_triangle(points[0], points[1], points[2])

circle_start_point = None
rect_start_point = None
line_start_point = None
triangle_points = []

def on_key_press(key):
    try:
        # P 键：暂停当前宏（不再继续后续绘制）
        if (hasattr(key, "char") and key.char in ("p", "P")) or (hasattr(key, "vk") and key.vk == 80):
            macro_stop_event.set()
            return

        # C 键：两次按下，以两点距离作为半径绘制圆形
        global circle_start_point, rect_start_point, line_start_point, triangle_points
        if hasattr(key, "char") and key.char in ("c", "C"):
            if circle_start_point is None:
                circle_start_point = mouse_controller.position
                print("已记录圆心位置，移动鼠标后再次按 C 结束并绘制圆形")
            else:
                end_pos = mouse_controller.position
                start_pos = circle_start_point
                circle_start_point = None
                threading.Thread(target=handle_draw_circle_two_points, args=(start_pos, end_pos), daemon=True).start()
            return

        # R 键：两次按下，以两点为对角绘制矩形（左上和右下）
        if hasattr(key, "char") and key.char in ("r", "R"):
            if rect_start_point is None:
                rect_start_point = mouse_controller.position
                print("已记录矩形第一个点，移动鼠标后再次按 R 结束并绘制矩形")
            else:
                end_pos = mouse_controller.position
                start_pos = rect_start_point
                rect_start_point = None
                threading.Thread(target=handle_draw_rectangle_two_points, args=(start_pos, end_pos), daemon=True).start()
            return

        # L 键：两次按下，连成一条直线
        if hasattr(key, "char") and key.char in ("l", "L"):
            if line_start_point is None:
                line_start_point = mouse_controller.position
                print("已记录直线起点，移动鼠标后再次按 L 结束并绘制")
            else:
                end_pos = mouse_controller.position
                start_pos = line_start_point
                line_start_point = None
                threading.Thread(target=handle_draw_line, args=(start_pos, end_pos), daemon=True).start()
            return

        # T 键：三次按下，依次记录三角形三个顶点
        if hasattr(key, "char") and key.char in ("t", "T"):
            pos = mouse_controller.position
            triangle_points.append(pos)
            if len(triangle_points) < 3:
                print(f"已记录三角形第{len(triangle_points)}个点，继续移动鼠标按 T 记录下一个点")
            else:
                points = triangle_points[:3]
                triangle_points.clear()
                threading.Thread(target=handle_draw_triangle, args=(points,), daemon=True).start()
            return

    except Exception as e:
        print(f"键盘监听异常: {e}")

# 主程序
print("绘图脚本启动 | C键两次定圆心和半径 | R键两次定矩形对角 | L键两次连线 | T键三次定三角形顶点 | P键暂停当前绘制 | Ctrl+C退出")

keyboard_listener = keyboard.Listener(on_press=on_key_press)

keyboard_listener.start()

keyboard_listener.join()