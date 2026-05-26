"""
geometry.py
Tạo dữ liệu hình học 3D dạng wireframe + faces.

Bản v3 bổ sung:
- faces: danh sách các mặt của vật thể.
- Từ faces có thể xác định cạnh nào thuộc mặt thấy được / bị khuất.
"""

from dataclasses import dataclass, field
from math import cos, sin, pi
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float


@dataclass
class Mesh:
    vertices: List[Point3D] = field(default_factory=list)
    edges: List[Tuple[int, int]] = field(default_factory=list)
    faces: List[List[int]] = field(default_factory=list)

    def rebuild_edges_from_faces(self) -> None:
        """Tạo danh sách cạnh duy nhất từ danh sách mặt."""
        edge_set = set()

        for face in self.faces:
            count = len(face)
            for i in range(count):
                a = face[i]
                b = face[(i + 1) % count]
                key = tuple(sorted((a, b)))
                edge_set.add(key)

        self.edges = sorted(edge_set)


def make_cuboid(origin: Point3D, length: float, width: float, height: float) -> Mesh:
    """
    Tạo hình hộp chữ nhật.

    Quy ước:
    - origin: đỉnh dưới - trái - trước.
    - length: chiều dài theo trục x.
    - width : chiều sâu theo trục z.
    - height: chiều cao theo trục y.

    Mỗi face được sắp xếp theo chiều sao cho pháp tuyến hướng ra ngoài.
    """
    x, y, z = origin.x, origin.y, origin.z
    l, w, h = length, width, height

    vertices = [
        Point3D(x,     y,     z),      # 0
        Point3D(x + l, y,     z),      # 1
        Point3D(x + l, y + h, z),      # 2
        Point3D(x,     y + h, z),      # 3

        Point3D(x,     y,     z + w),  # 4
        Point3D(x + l, y,     z + w),  # 5
        Point3D(x + l, y + h, z + w),  # 6
        Point3D(x,     y + h, z + w),  # 7
    ]

    faces = [
        [0, 3, 2, 1],  # mặt trước, normal -Z
        [4, 5, 6, 7],  # mặt sau, normal +Z
        [0, 4, 7, 3],  # mặt trái, normal -X
        [1, 2, 6, 5],  # mặt phải, normal +X
        [0, 1, 5, 4],  # mặt dưới, normal -Y
        [3, 7, 6, 2],  # mặt trên, normal +Y
    ]

    mesh = Mesh(vertices=vertices, faces=faces)
    mesh.rebuild_edges_from_faces()
    return mesh


def make_cube(origin: Point3D, size: float) -> Mesh:
    """Tạo hình lập phương."""
    return make_cuboid(origin, length=size, width=size, height=size)


def make_cylinder(base_center: Point3D, radius: float, height: float, segments: int = 36) -> Mesh:
    """
    Tạo hình trụ dạng wireframe + faces.

    base_center: tâm đáy dưới.
    radius     : bán kính đáy.
    height     : chiều cao theo trục y.
    segments   : số đoạn chia đường tròn đáy.

    Mặt trên được khai báo là một face riêng, nên khi nhìn thấy mặt trên,
    toàn bộ đường ellipse trên sẽ là nét liền, không bị chia nửa nét đứt.
    """
    segments = max(8, int(segments))

    vertices: List[Point3D] = []
    bottom_indices: List[int] = []
    top_indices: List[int] = []

    cx, cy, cz = base_center.x, base_center.y, base_center.z

    for i in range(segments):
        angle = 2 * pi * i / segments
        x = cx + radius * cos(angle)
        z = cz + radius * sin(angle)

        bottom_indices.append(len(vertices))
        vertices.append(Point3D(x, cy, z))

        top_indices.append(len(vertices))
        vertices.append(Point3D(x, cy + height, z))

    faces: List[List[int]] = []

    # Đáy dưới: normal -Y.
    faces.append(bottom_indices[:])

    # Đáy trên: đảo thứ tự để normal +Y.
    faces.append(list(reversed(top_indices)))

    # Các mặt bên: normal hướng ra ngoài.
    for i in range(segments):
        j = (i + 1) % segments
        faces.append([
            bottom_indices[i],
            top_indices[i],
            top_indices[j],
            bottom_indices[j],
        ])

    mesh = Mesh(vertices=vertices, faces=faces)
    mesh.rebuild_edges_from_faces()
    return mesh


def make_sphere(center: Point3D, radius: float, lat_steps: int = 12, lon_steps: int = 24) -> Mesh:
    """
    Tạo hình cầu dạng lưới kinh tuyến - vĩ tuyến.

    Bản v3 tạo thêm faces nhỏ trên bề mặt cầu để xác định phần trước/sau
    khi vẽ nét liền/nét đứt.
    """
    lat_steps = max(6, int(lat_steps))
    lon_steps = max(12, int(lon_steps))

    vertices: List[Point3D] = []
    grid: List[List[int]] = []

    for i in range(lat_steps + 1):
        lat = -pi / 2 + pi * i / lat_steps
        row: List[int] = []

        for j in range(lon_steps):
            lon = 2 * pi * j / lon_steps

            x = center.x + radius * cos(lat) * cos(lon)
            y = center.y + radius * sin(lat)
            z = center.z + radius * cos(lat) * sin(lon)

            row.append(len(vertices))
            vertices.append(Point3D(x, y, z))

        grid.append(row)

    faces: List[List[int]] = []

    # Thứ tự lat rồi lon tạo pháp tuyến hướng ra ngoài.
    for i in range(lat_steps):
        for j in range(lon_steps):
            a = grid[i][j]
            b = grid[i + 1][j]
            c = grid[i + 1][(j + 1) % lon_steps]
            d = grid[i][(j + 1) % lon_steps]
            faces.append([a, b, c, d])

    mesh = Mesh(vertices=vertices, faces=faces)
    mesh.rebuild_edges_from_faces()
    return mesh
