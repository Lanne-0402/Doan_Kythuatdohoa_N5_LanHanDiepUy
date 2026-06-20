import os
import sys
from flask import Flask, jsonify, render_template, request, Response

# Khi chạy Python bình thường: BASE_DIR là thư mục project.
# Khi chạy file .exe: BASE_DIR là thư mục tạm PyInstaller giải nén.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, "2D_project"))
sys.path.insert(0, os.path.join(BASE_DIR, "3D_project"))
import pacman as pacman_anim
import duck_animation as duck_anim
from core.geometry import Point3D, make_cuboid, make_cube, make_cylinder, make_sphere
import time
import math

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

UNIT_SIZE = 5.0  # 1 đơn vị = 5 pixel nội bộ


def to_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} phải là số hợp lệ.")


def to_int(value, field_name, default=24):
    if value in (None, ""):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} phải là số nguyên hợp lệ.")


def require_positive(value, field_name):
    if value <= 0:
        raise ValueError(f"{field_name} phải lớn hơn 0.")
    return value


def scale_units(value):
    return value * UNIT_SIZE


def mesh_to_json(mesh):
    return {
        "vertices": [{"x": p.x, "y": p.y, "z": p.z} for p in mesh.vertices],
        "edges": [[a, b] for a, b in mesh.edges],
        "faces": mesh.faces,
    }


def build_bounds_units(xmin, xmax, ymin, ymax, zmin, zmax):
    return {
        "x": {"min": float(xmin), "max": float(xmax)},
        "y": {"min": float(ymin), "max": float(ymax)},
        "z": {"min": float(zmin), "max": float(zmax)},
    }


@app.get("/")
def index():
    return render_template("index.html")

@app.get("/video_pacman")
def video_pacman():
    return Response(
        pacman_anim.generate_pacman_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.get("/video_duck")
def video_duck():
    return Response(
        duck_anim.generate_duck_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.get("/image_grid")
def image_grid():
    return Response(pacman_anim.get_static_grid(), mimetype='image/jpeg')

@app.post("/api/draw")
def draw():
    try:
        data = request.get_json(force=True)

        shape = data.get("shape", "cuboid")
        projection = data.get("projection", "cabinet")
        origin_data = data.get("origin", {})
        params = data.get("params", {})

        x_units = to_float(origin_data.get("x", 0), "X")
        y_units = to_float(origin_data.get("y", 0), "Y")
        z_units = to_float(origin_data.get("z", 0), "Z")

        origin = Point3D(scale_units(x_units), scale_units(y_units), scale_units(z_units))

        if shape == "cuboid":
            length_units = require_positive(to_float(params.get("length"), "Chiều dài"), "Chiều dài")
            width_units = require_positive(to_float(params.get("width"), "Chiều rộng/sâu"), "Chiều rộng/sâu")
            height_units = require_positive(to_float(params.get("height"), "Chiều cao"), "Chiều cao")

            mesh = make_cuboid(
                origin,
                scale_units(length_units),
                scale_units(width_units),
                scale_units(height_units),
            )
            bounds_units = build_bounds_units(
                x_units, x_units + length_units,
                y_units, y_units + height_units,
                z_units, z_units + width_units,
            )

        elif shape == "cube":
            size_units = require_positive(to_float(params.get("size"), "Cạnh lập phương"), "Cạnh lập phương")

            mesh = make_cube(origin, scale_units(size_units))
            bounds_units = build_bounds_units(
                x_units, x_units + size_units,
                y_units, y_units + size_units,
                z_units, z_units + size_units,
            )

        elif shape == "cylinder":
            radius_units = require_positive(to_float(params.get("radius"), "Bán kính đáy"), "Bán kính đáy")
            height_units = require_positive(to_float(params.get("height"), "Chiều cao"), "Chiều cao")
            segments = max(12, to_int(params.get("segments"), "Số đoạn chia", default=36))

            mesh = make_cylinder(origin, scale_units(radius_units), scale_units(height_units), segments)
            bounds_units = build_bounds_units(
                x_units - radius_units, x_units + radius_units,
                y_units, y_units + height_units,
                z_units - radius_units, z_units + radius_units,
            )

        elif shape == "sphere":
            radius_units = require_positive(to_float(params.get("radius"), "Bán kính"), "Bán kính")
            segments = max(12, to_int(params.get("segments"), "Số đoạn chia", default=24))

            mesh = make_sphere(origin, scale_units(radius_units), 12, segments)
            bounds_units = build_bounds_units(
                x_units - radius_units, x_units + radius_units,
                y_units - radius_units, y_units + radius_units,
                z_units - radius_units, z_units + radius_units,
            )

        else:
            raise ValueError("Loại hình không hợp lệ.")

        return jsonify({
            "ok": True,
            "shape": shape,
            "projection": projection,
            "mesh": mesh_to_json(mesh),
            "bounds_units": bounds_units,
            "unit_size": UNIT_SIZE,
            "hint": "Lưới và trục Oxyz tự mở rộng theo vị trí + kích thước vật thể.",
        })

    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Lỗi hệ thống: {exc}"}), 500

animation_state = {
    "current": None,      # "duck" hoặc "pacman"
    "running": False,
    "start_time": None,
    "elapsed": 0.0
}


def start_animation_state(animation_name):
    animation_state["current"] = animation_name
    animation_state["running"] = True
    animation_state["start_time"] = time.time()
    animation_state["elapsed"] = 0.0


def reset_animation_state():
    animation_state["current"] = None
    animation_state["running"] = False
    animation_state["start_time"] = None
    animation_state["elapsed"] = 0.0


def get_animation_elapsed():
    if animation_state["running"] and animation_state["start_time"] is not None:
        return time.time() - animation_state["start_time"]
    return animation_state["elapsed"]

    """
    Tọa độ đại diện của Pacman.

    Nếu trong pacman.py sau này bạn có hàm get_pacman_position(time_sec),
    đoạn này sẽ dùng hàm đó để khớp chính xác với animation Pacman.
    Nếu chưa có, code dùng đường chạy mặc định từ trái sang phải.
    """

    fps = getattr(pacman_anim, "FPS", 30)
    total_duration = getattr(pacman_anim, "TOTAL_DURATION", 8)
    time_sec = elapsed % total_duration

    if hasattr(pacman_anim, "get_pacman_position"):
        x, y = pacman_anim.get_pacman_position(time_sec)
    else:
        # Fallback: Pacman chạy ngang từ trái sang phải.
        # Nếu pacman.py của bạn dùng tọa độ khác, sửa START/END ở đây cho khớp.
        start_x, start_y = -70, 0
        end_x, end_y = 70, 0

        t = time_sec / total_duration
        x = start_x + (end_x - start_x) * t
        y = start_y + (end_y - start_y) * t

    return {
        "type": "pacman",
        "object": "Pacman",
        "x": round(x, 2),
        "y": round(y, 2),
        "z": 0,
        "frame": int(time_sec * fps),
        "time": round(time_sec, 2),
        "status": "Đang chạy",

        "duck": None,
        "pacman": None
    }

def calculate_animation_coords():
    if not animation_state["running"]:
        return {
            "type": "none",
            "object": "",
            "x": "",
            "y": "",
            "z": "",
            "frame": "",
            "time": "",
            "status": "",
            "duck": None,
            "pacman": None,
            "details": []
        }
        return {
            "type": "none",
            "object": "",
            "x": "",
            "y": "",
            "z": "",
            "frame": "",
            "time": "",
            "status": "",
            "duck": None,
            "pacman": None,
            "details": []
        }

    if animation_state["current"] == "duck":
        return duck_anim.get_current_state()

    if animation_state["current"] == "pacman":
        return pacman_anim.get_current_state()

    return {
        "type": "none",
        "object": "---",
        "x": 0.00,
        "y": 0.00,
        "z": 0,
        "frame": 0,
        "time": 0.00,
        "status": "Đang dừng",
        "duck": None,
        "pacman": None
    }

@app.get("/api/animation-coords")
def api_animation_coords():
    return jsonify(calculate_animation_coords())


@app.post("/api/animation-start")
def api_animation_start():
    data = request.get_json(silent=True) or {}
    animation_name = data.get("animation", "duck")

    if animation_name not in ["duck", "pacman"]:
        return jsonify({"ok": False, "error": "Hoạt cảnh không hợp lệ."}), 400

    start_animation_state(animation_name)
    return jsonify({"ok": True, "animation": animation_name})


@app.post("/api/animation-reset")
def api_animation_reset():
    reset_animation_state()
    return jsonify({"ok": True})


if __name__ == "__main__":
    import webbrowser
    from threading import Timer

    # Tự mở giao diện khi chạy file .exe
    Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        threaded=True,
        use_reloader=False
    )