import math
import os
import time
import cv2
import numpy as np
import importlib
import importlib.util
import sys
from PIL import Image, ImageDraw

CURRENT_DUCK_STATE = {
    "type": "duck",
    "object": "Vịt + Phao",
    "x": 0,
    "y": 0,
    "z": 0,
    "frame": 0,
    "time": 0,
    "status": "Đang dừng",
    "duck": {
        "angle": 0,
        "bob_y": 0
    },
    "pacman": None
}


def get_current_state():
    return CURRENT_DUCK_STATE.copy()
# ============================================================
# Load engine.py / duck_scene.py an toàn
# ============================================================
def load_module_safely(module_name, filename_candidates):
    """Load module by normal import first, then fall back to candidate file paths."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        for path in filename_candidates:
            if os.path.exists(path):
                spec = importlib.util.spec_from_file_location(f"{module_name}_fallback", path)
                module = importlib.util.module_from_spec(spec)
                # Đăng ký vào sys.modules để duck_scene.py có thể `from engine import ...`
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
        raise


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
engine_module = load_module_safely(
    "engine",
    [
        os.path.join(BASE_DIR, "engine.py"),
        os.path.join(BASE_DIR, "engine(2).py"),
        "/mnt/data/engine(2).py",
    ],
)

duck_scene_module = load_module_safely(
    "duck_scene",
    [
        os.path.join(BASE_DIR, "duck_scene.py"),
        os.path.join(BASE_DIR, "duck_scene(2).py"),
        "/mnt/data/duck_scene(2).py",
    ],
)

GraphicsEngine = engine_module.GraphicsEngine
create_water_group = duck_scene_module.create_water_group
create_ring_groups = duck_scene_module.create_ring_groups
create_duck_group = duck_scene_module.create_duck_group

BLUE = duck_scene_module.BLUE
WHITE = getattr(duck_scene_module, "WHITE", (255, 255, 255))
LBLUE = getattr(duck_scene_module, "LBLUE", (200, 240, 255))


# =========================
# Kích thước cửa sổ hiển thị
# =========================
VIEW_WIDTH = 800
VIEW_HEIGHT = 600


# =========================
# Cài đặt thời gian chung
# =========================
FPS = 30

# Thời gian đi từ đầu đến cuối nếu không có đoạn dừng.
TRAVEL_DURATION = 30

# Dừng tại chính giữa để hoạt họa tại chỗ.
HOLD_DURATION = 1.5

# Tổng thời gian thật của animation = thời gian di chuyển + thời gian dừng.
TOTAL_DURATION = TRAVEL_DURATION + HOLD_DURATION
TOTAL_FRAMES = int(FPS * TOTAL_DURATION)


# =========================
# 1. Chuyển động chung của cả cụm
# =========================
START_POS = (-105, 45)
END_POS = (175, -65)


# =========================
# 2. Phao nhấp nhô
# =========================
RING_BOB_AMPLITUDE = 0.8
RING_BOB_FREQ = 0.95


# =========================
# 3. Vịt lắc lư
# =========================
DUCK_SWAY_AMPLITUDE = 3.5
DUCK_SWAY_FREQ = 0.9
DUCK_BASE_OFFSET = (2, 0)
DUCK_CACHE_ANGLES = list(range(-4, 5))


# =========================
# 4. Sprite cache settings
# =========================
# Canvas tạm để dựng sprite. Chỉ dùng 1 lần lúc khởi tạo cache.
SPRITE_CANVAS_W = 700
SPRITE_CANVAS_H = 500

# Canvas rieng cho ripple vi ripple luc phong to co the rong hon sprite phao/vit.
# Neu dung chung SPRITE_CANVAS_W/H thi cac cung nuoc lon de bi cat mat.
RIPPLE_CANVAS_W = 1500
RIPPLE_CANVAS_H = 900

# Màu nền chroma không trùng với màu của hình.
CHROMA_KEY = (17, 241, 193)


# =========================
# 5. Ripple / vòng nước động
# =========================
# False = không vẽ vòng nước tĩnh vào background nữa, để thấy rõ vòng nước động.
DRAW_STATIC_WATER_IN_BACKGROUND = False

# Số sprite dựng sẵn cho 1 lần gợn nước phóng to rồi mất.
RIPPLE_CACHE_STEPS = 32

# Khi phao xuống thấp nhất thì bắt đầu tạo vòng nước mới.
# sin phase thấp nhất ở 0.75 chu kỳ.
RIPPLE_START_BOB_PHASE = 0.75

# Vòng nước nhỏ lúc mới sinh ra, lớn dần đến RIPPLE_END_SCALE.
RIPPLE_START_SCALE = 0.90
RIPPLE_END_SCALE = 1.25

# Dời tâm ripple xuống một chút nếu muốn vòng nước nằm dưới phao hơn.
RIPPLE_OFFSET_X = 0
RIPPLE_OFFSET_Y = 0

# Wake/gợn nước chỉ nằm ở phía sau hướng di chuyển.
# Vì hình wake gốc trong duck_scene đã nằm về phía sau rồi,
# WAKE_DISTANCE chỉ cần nhỏ để tránh bị tách quá xa khỏi phao.
WAKE_DISTANCE = 5

# Pivot của cụm nước, lấy từ duck_scene.py nếu có.
WATER_PIVOT_X = getattr(duck_scene_module, "WATER_PIVOT_X", -26)
WATER_PIVOT_Y = getattr(duck_scene_module, "WATER_PIVOT_Y", 8)


# ============================================================
# Hàm toán học / transform
# ============================================================
def rotate_about(engine, angle, cx, cy):
    """Xoay quanh điểm (cx, cy)."""
    return (
        engine.translation_matrix(cx, cy)
        @ engine.rotation_matrix(angle)
        @ engine.translation_matrix(-cx, -cy)
    )


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    """Bắt đầu chậm, giữa nhanh hơn, cuối chậm lại."""
    return t * t * (3 - 2 * t)


def transform_point(M, x=0, y=0):
    """
    Nhan 1 diem voi ma tran bien doi 3x3.
    Dung de tinh vi tri paste sprite bang ma tran tinh tien cua engine.
    """
    p = M @ np.array([[x], [y], [1]])
    return p[0, 0], p[1, 0]


def get_paused_path_position(time_sec):
    """
    Tính vị trí của cả cụm khi có dừng ở chính giữa.

    - Chạy từ START -> MID trong TRAVEL_DURATION / 2 giây đầu
    - Dừng ở MID trong HOLD_DURATION giây
    - Chạy từ MID -> END trong TRAVEL_DURATION / 2 giây cuối

    Mục tiêu là giữ tốc độ di chuyển trước và sau đoạn dừng gần giống nhau.
    """
    half_travel = TRAVEL_DURATION / 2.0
    mid_x = (START_POS[0] + END_POS[0]) / 2.0
    mid_y = (START_POS[1] + END_POS[1]) / 2.0

    if time_sec <= half_travel:
        t = smoothstep(time_sec / half_travel)
        x = lerp(START_POS[0], mid_x, t)
        y = lerp(START_POS[1], mid_y, t)
        return x, y

    if time_sec <= half_travel + HOLD_DURATION:
        return mid_x, mid_y

    t2 = (time_sec - half_travel - HOLD_DURATION) / half_travel
    t2 = max(0.0, min(1.0, t2))
    t2 = smoothstep(t2)
    x = lerp(mid_x, END_POS[0], t2)
    y = lerp(mid_y, END_POS[1], t2)
    return x, y


def blend_color(color_a, color_b, t):
    """
    Trộn màu A sang màu B.
    Dùng để làm vòng nước càng lớn càng nhạt dần về màu nền BLUE.
    """
    t = max(0.0, min(1.0, t))
    return tuple(
        int(round(color_a[i] * (1 - t) + color_b[i] * t))
        for i in range(3)
    )


def get_group_bounds(group):
    xs = []
    ys = []
    for item in group.shapes:
        M = item["obj"].matrix
        xs.extend(M[0, :].tolist())
        ys.extend(M[1, :].tolist())
    return min(xs), max(xs), min(ys), max(ys)


def get_group_bottom_center(group):
    """Lấy tâm đáy của group để vịt lắc quanh đáy."""
    min_x, max_x, min_y, max_y = get_group_bounds(group)
    cx = (min_x + max_x) / 2
    cy = min_y
    return cx, cy


# ============================================================
# Sprite helpers
# ============================================================
def make_chroma_engine(width, height):
    """Tạo engine nền chroma để dựng sprite trong suốt."""
    engine = GraphicsEngine(width, height)
    engine.image = Image.new("RGB", (width, height), CHROMA_KEY)
    engine.draw = ImageDraw.Draw(engine.image)
    engine.bg_layer = engine.image.copy()
    return engine


def rgb_to_rgba_with_transparent_chroma(rgb_image):
    """Đổi nền chroma thành alpha=0, giữ nguyên phần hình đã vẽ."""
    rgba = rgb_image.convert("RGBA")
    arr = np.array(rgba)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    mask = (r == CHROMA_KEY[0]) & (g == CHROMA_KEY[1]) & (b == CHROMA_KEY[2])
    a[mask] = 0
    arr[:, :, 3] = a
    return Image.fromarray(arr, mode="RGBA")


def render_group_to_sprite(group, canvas_w=SPRITE_CANVAS_W, canvas_h=SPRITE_CANVAS_H):
    """
    Dựng group thành 1 sprite RGBA đã crop, đồng thời lưu anchor
    để khi paste có thể canh đúng gốc tọa độ local (0,0).
    """
    engine = make_chroma_engine(canvas_w, canvas_h)
    group.draw(engine)

    rgba = rgb_to_rgba_with_transparent_chroma(engine.image)
    bbox = rgba.getbbox()

    if bbox is None:
        empty = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        return {
            "image": empty,
            "anchor": (0, 0),
        }

    cropped = rgba.crop(bbox)
    center_x = canvas_w // 2
    center_y = canvas_h // 2
    anchor_x = center_x - bbox[0]
    anchor_y = center_y - bbox[1]

    return {
        "image": cropped,
        "anchor": (anchor_x, anchor_y),
    }


def paste_sprite(engine, sprite_info, world_x, world_y):
    """Paste sprite RGBA lên canvas chính theo tọa độ Oxy."""
    sprite = sprite_info["image"]
    anchor_x, anchor_y = sprite_info["anchor"]

    screen_x, screen_y = engine.to_screen(world_x, world_y)
    left = int(round(screen_x - anchor_x))
    top = int(round(screen_y - anchor_y))

    engine.image.paste(sprite, (left, top), sprite)


# ============================================================
# Background / Ripple
# ============================================================
def build_background(engine):
    """Vẽ nền nước 1 lần rồi lưu vào bg_layer."""
    half_w_coord = engine.width / 10
    half_h_coord = engine.height / 10

    engine.draw_rectangle(
        -half_w_coord,
        -half_h_coord,
        half_w_coord * 2,
        half_h_coord * 2,
        BLUE,
    )
    engine.boundary_fill(0, 0, BLUE, BLUE)

    # Bản này dùng vòng nước động, nên mặc định không vẽ vòng nước tĩnh nữa.
    if DRAW_STATIC_WATER_IN_BACKGROUND:
        water_group = create_water_group(engine)
        water_group.draw(engine)

    engine.bg_layer = engine.image.copy()


def create_ripple_group(engine, age):
    """
    Tao ripple/wake dong bang ma tran bien doi.

    Quy trinh:
    1. Tao hinh wake goc bang create_water_group() trong duck_scene.py.
    2. Dung scaling_matrix() de phong to quanh WATER_PIVOT.
    3. Dung translation_matrix() de day wake ve phia sau huong di chuyen.
    4. Render group da bien doi thanh sprite cache de animation khong bi lag.
    """
    age = max(0.0, min(1.0, age))

    # Ease-out: luc dau phong nhanh, cang ve sau cham lai.
    grow_t = 1 - (1 - age) * (1 - age)
    scale = lerp(RIPPLE_START_SCALE, RIPPLE_END_SCALE, grow_t)

    # Fade: cang lon cang nhat ve mau nen nuoc.
    fade_t = age ** 1.25
    main_color = blend_color(WHITE, BLUE, fade_t)
    soft_color = blend_color(LBLUE, BLUE, min(1.0, fade_t + 0.22))

    # Tao hinh wake goc. Khong truyen scale vao day nua.
    # Phong to se duoc lam bang ma tran scaling_matrix.
    ripple_group = create_water_group(
        engine,
        main_color=main_color,
        soft_color=soft_color,
    )

    # Tinh huong di chuyen cua ca cum.
    move_dx = END_POS[0] - START_POS[0]
    move_dy = END_POS[1] - START_POS[1]
    length = math.sqrt(move_dx * move_dx + move_dy * move_dy)

    if length == 0:
        back_ux, back_uy = -1, 0
    else:
        # Phia sau = nguoc huong di chuyen.
        back_ux = -move_dx / length
        back_uy = -move_dy / length

    # 1. Dua pivot ve goc O
    T_to_origin = engine.translation_matrix(-WATER_PIVOT_X, -WATER_PIVOT_Y)

    # 2. Scale bang ma tran
    S = engine.scaling_matrix(scale, scale)

    # 3. Dua pivot ve lai vi tri cu
    T_back = engine.translation_matrix(WATER_PIVOT_X, WATER_PIVOT_Y)

    # 4. Day wake ve phia sau huong di chuyen
    T_wake_offset = engine.translation_matrix(
        back_ux * WAKE_DISTANCE * scale,
        back_uy * WAKE_DISTANCE * scale,
    )

    # Thu tu ap dung: ve goc -> scale quanh pivot -> tinh tien ra phia sau
    ripple_group.transform(T_wake_offset @ T_back @ S @ T_to_origin)

    return ripple_group


# ============================================================
# Sprite Cache
# ============================================================
class SpriteCache:
    def __init__(self):
        self.ring_back = None
        self.ring_front = None
        self.duck_frames = {}
        self.ripple_frames = []

    def build(self):
        print("Dang tao sprite cache...")

        # 1. Cache vòng nước động theo nhiều phase.
        for i in range(RIPPLE_CACHE_STEPS):
            age = i / (RIPPLE_CACHE_STEPS - 1)
            tmp_engine = make_chroma_engine(RIPPLE_CANVAS_W, RIPPLE_CANVAS_H)
            ripple_group = create_ripple_group(tmp_engine, age)
            self.ripple_frames.append(
                render_group_to_sprite(
                    ripple_group,
                    canvas_w=RIPPLE_CANVAS_W,
                    canvas_h=RIPPLE_CANVAS_H,
                )
            )

        # 2. Phao sau / trước: chỉ dựng 1 lần.
        tmp_engine = make_chroma_engine(SPRITE_CANVAS_W, SPRITE_CANVAS_H)
        ring_back_group, ring_front_group = create_ring_groups(tmp_engine)
        self.ring_back = render_group_to_sprite(ring_back_group)
        self.ring_front = render_group_to_sprite(ring_front_group)

        # 3. Vịt: dựng sẵn nhiều góc để lúc chạy chỉ paste sprite.
        for angle in DUCK_CACHE_ANGLES:
            tmp_engine = make_chroma_engine(SPRITE_CANVAS_W, SPRITE_CANVAS_H)
            duck_group = create_duck_group(tmp_engine)

            # Đẩy vịt vào vị trí đẹp trong phao trước khi cache.
            T_duck_base = tmp_engine.translation_matrix(
                DUCK_BASE_OFFSET[0],
                DUCK_BASE_OFFSET[1],
            )
            duck_group.transform(T_duck_base)

            pivot_x, pivot_y = get_group_bottom_center(duck_group)
            T_duck_sway = rotate_about(tmp_engine, angle, pivot_x, pivot_y)
            duck_group.transform(T_duck_sway)

            self.duck_frames[angle] = render_group_to_sprite(duck_group)

        print("Da tao xong sprite cache.")

    def get_duck_sprite(self, angle):
        angle_key = int(round(angle))
        angle_key = max(min(angle_key, max(DUCK_CACHE_ANGLES)), min(DUCK_CACHE_ANGLES))
        return self.duck_frames[angle_key]

    def get_ripple_sprite(self, age):
        age = max(0.0, min(1.0, age))
        index = int(round(age * (RIPPLE_CACHE_STEPS - 1)))
        return self.ripple_frames[index]


# ============================================================
# Animation loop
# ============================================================
def draw_one_frame(engine, cache, frame):
    engine.clear()

    time_sec = frame / FPS

    # A. Cả cụm đi từ trên trái -> giữa, dừng, rồi đi tiếp.
    common_x, common_y = get_paused_path_position(time_sec)

    # B. Phao nhấp nhô riêng.
    bob_phase = (time_sec * RING_BOB_FREQ) % 1.0
    ring_bob_y = RING_BOB_AMPLITUDE * math.sin(2 * math.pi * bob_phase)

    # C. Ripple bắt đầu khi phao xuống thấp nhất.
    ripple_age = (bob_phase - RIPPLE_START_BOB_PHASE) % 1.0
    ripple_sprite = cache.get_ripple_sprite(ripple_age)

    # D. Vịt lắc lư: chọn sprite đã được tạo bằng rotation_matrix trong lúc cache.
    duck_angle = DUCK_SWAY_AMPLITUDE * math.sin(
        2 * math.pi * DUCK_SWAY_FREQ * time_sec
    )
    duck_sprite = cache.get_duck_sprite(duck_angle)

    # E. Tính vị trí paste bằng ma trận tịnh tiến của engine.
    # Sprite đã cache sẵn hình dạng; còn vị trí di chuyển vẫn lấy từ translation_matrix.
    T_common = engine.translation_matrix(common_x, common_y)
    T_bob = engine.translation_matrix(0, ring_bob_y)
    T_final = T_common @ T_bob

    base_x, base_y = transform_point(T_final, 0, 0)

    # F. Vẽ layer.
    paste_sprite(engine, ripple_sprite, base_x, base_y)
    paste_sprite(engine, cache.ring_back, base_x, base_y)
    paste_sprite(engine, duck_sprite, base_x, base_y)
    paste_sprite(engine, cache.ring_front, base_x, base_y)

    # G. Tính tọa độ đại diện cho từng đối tượng để hiển thị lên web.

    # Vịt đã được cache với DUCK_BASE_OFFSET, nên tọa độ đại diện của vịt
    # lấy theo base_x/base_y cộng thêm offset này.
    duck_x = base_x + DUCK_BASE_OFFSET[0]
    duck_y = base_y + DUCK_BASE_OFFSET[1]

    # Phao dùng đúng vị trí base của cả cụm.
    ring_x = base_x
    ring_y = base_y

    # Tia nước trong duck_scene.py có 2 cung nhưng dùng chung pivot,
    # nên chỉ cần hiển thị 1 tọa độ đại diện cho cụm tia nước.
    move_dx = END_POS[0] - START_POS[0]
    move_dy = END_POS[1] - START_POS[1]
    move_len = math.sqrt(move_dx * move_dx + move_dy * move_dy)

    if move_len == 0:
        back_ux, back_uy = -1, 0
    else:
        back_ux = -move_dx / move_len
        back_uy = -move_dy / move_len

    grow_t = 1 - (1 - ripple_age) * (1 - ripple_age)
    ripple_scale = lerp(RIPPLE_START_SCALE, RIPPLE_END_SCALE, grow_t)

    water_x = base_x + WATER_PIVOT_X + back_ux * WAKE_DISTANCE * ripple_scale
    water_y = base_y + WATER_PIVOT_Y + back_uy * WAKE_DISTANCE * ripple_scale

    return {
        "type": "duck",
        "object": "",
        "x": round(base_x, 2),
        "y": round(base_y, 2),
        "z": 0,
        "frame": frame,
        "time": round(time_sec, 2),
        "status": "Đang chạy",

        # Giữ lại phần cũ để code hiện tại không bị lỗi
        "duck": {
            "angle": round(duck_angle, 2),
            "bob_y": round(ring_bob_y, 2)
        },
        "pacman": None,

        # Phần mới để script.js render danh sách đối tượng
        "details": [
            {
                "name": "Vịt",
                "rows": [
                    {
                        "label": "Tọa độ",
                        "value": f"({round(duck_x, 2)}, {round(duck_y, 2)})"
                    },
                    {
                        "label": "Góc lắc",
                        "value": f"{round(duck_angle, 2)}°"
                    }
                ]
            },
            {
                "name": "Phao",
                "rows": [
                    {
                        "label": "Tọa độ",
                        "value": f"({round(ring_x, 2)}, {round(ring_y, 2)})"
                    },
                    {
                        "label": "Độ nhấp nhô",
                        "value": round(ring_bob_y, 2)
                    }
                ]
            },
            {
                "name": "Tia nước",
                "rows": [
                    {
                        "label": "Tọa độ",
                        "value": f"({round(water_x, 2)}, {round(water_y, 2)})"
                    },
                    {
                        "label": "Độ phóng to",
                        "value": round(ripple_scale, 2)
                    }
                ]
            }
        ]
    }
def generate_duck_frames():
    engine = GraphicsEngine(VIEW_WIDTH, VIEW_HEIGHT)
    build_background(engine)

    cache = SpriteCache()
    cache.build()

    print("Đang chạy luồng Video Vịt trên Web...")

    while True:
        for frame in range(TOTAL_FRAMES):
            global CURRENT_DUCK_STATE
            CURRENT_DUCK_STATE = draw_one_frame(engine, cache, frame)

            cv_image = np.array(engine.image)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)
            
            ret, buffer = cv2.imencode('.jpg', cv_image)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(1.0 / FPS)


def save_gif(filename="2D_project/duck_animation_final.gif"):
    """Xuất GIF từ phiên bản sprite cache có ripple."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    engine = GraphicsEngine(VIEW_WIDTH, VIEW_HEIGHT)
    build_background(engine)

    cache = SpriteCache()
    cache.build()

    frames = []
    for frame in range(TOTAL_FRAMES):
        draw_one_frame(engine, cache, frame)
        frames.append(engine.image.copy())

    frame_duration_ms = int(1000 / FPS)

    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=0,
    )

    print("Da luu GIF:", filename)


# if __name__ == "__main__":
#     run_animation()
#     # Nếu muốn xuất GIF, comment dòng run_animation() phía trên
#     # rồi mở dòng dưới:
#     # save_gif()
