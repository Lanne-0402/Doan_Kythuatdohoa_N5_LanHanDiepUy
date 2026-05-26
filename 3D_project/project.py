from flask import Flask, jsonify, render_template, request

from core.geometry import Point3D, make_cuboid, make_cube, make_cylinder, make_sphere

app = Flask(__name__)


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


def mesh_to_json(mesh):
    return {
        "vertices": [
            {"x": point.x, "y": point.y, "z": point.z}
            for point in mesh.vertices
        ],
        "edges": [
            [a, b]
            for a, b in mesh.edges
        ],
        "faces": mesh.faces,
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/draw")
def draw():
    try:
        data = request.get_json(force=True)

        shape = data.get("shape", "cuboid")
        projection = data.get("projection", "cabinet")

        origin_data = data.get("origin", {})
        params = data.get("params", {})

        x = to_float(origin_data.get("x", 0), "X")
        y = to_float(origin_data.get("y", 0), "Y")
        z = to_float(origin_data.get("z", 0), "Z")
        origin = Point3D(x, y, z)

        dimensions = {"x": 6, "y": 6, "z": 6}

        if shape == "cuboid":
            length = require_positive(to_float(params.get("length"), "Chiều dài"), "Chiều dài")
            width = require_positive(to_float(params.get("width"), "Chiều rộng/sâu"), "Chiều rộng/sâu")
            height = require_positive(to_float(params.get("height"), "Chiều cao"), "Chiều cao")
            mesh = make_cuboid(origin, length=length, width=width, height=height)
            dimensions = {"x": length, "y": height, "z": width}

        elif shape == "cube":
            size = require_positive(to_float(params.get("size"), "Cạnh lập phương"), "Cạnh lập phương")
            mesh = make_cube(origin, size=size)
            dimensions = {"x": size, "y": size, "z": size}

        elif shape == "cylinder":
            radius = require_positive(to_float(params.get("radius"), "Bán kính đáy"), "Bán kính đáy")
            height = require_positive(to_float(params.get("height"), "Chiều cao"), "Chiều cao")
            segments = max(12, to_int(params.get("segments"), "Số đoạn chia", default=36))
            mesh = make_cylinder(origin, radius=radius, height=height, segments=segments)
            dimensions = {"x": radius, "y": height, "z": radius}

        elif shape == "sphere":
            radius = require_positive(to_float(params.get("radius"), "Bán kính"), "Bán kính")
            segments = max(12, to_int(params.get("segments"), "Số đoạn chia", default=24))
            mesh = make_sphere(origin, radius=radius, lat_steps=12, lon_steps=segments)
            dimensions = {"x": radius, "y": radius, "z": radius}

        else:
            raise ValueError("Loại hình không hợp lệ.")

        return jsonify({
            "ok": True,
            "shape": shape,
            "projection": projection,
            "mesh": mesh_to_json(mesh),
            "dimensions": dimensions,
            "hint": "Kéo chuột trên khung vẽ để xoay toàn bộ hệ tọa độ Oxyz và vật thể.",
        })

    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": f"Lỗi hệ thống: {exc}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
