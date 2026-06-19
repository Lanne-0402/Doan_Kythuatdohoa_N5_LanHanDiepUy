import sys
from flask import Flask, jsonify, render_template, request, Response
# 1. Chỉ đường cho Python tìm thấy thư mục 2D
sys.path.append('./2D_project')
sys.path.append('./3D_project')
from pacman import generate_pacman_frames, get_static_grid
from duck_animation import generate_duck_frames
from core.geometry import Point3D, make_cuboid, make_cube, make_cylinder, make_sphere

app = Flask(__name__)

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
    return Response(generate_pacman_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.get("/video_duck")
def video_duck():
    return Response(generate_duck_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.get("/image_grid")
def image_grid():
    return Response(get_static_grid(), mimetype='image/jpeg')

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


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
