"""
projection.py
Cài đặt phép chiếu xiên Cavalier / Cabinet.

Công thức chiếu lên mặt phẳng Oxy:
    x' = x + f * z * cos(alpha)
    y' = y + f * z * sin(alpha)

Trong đó:
- Cavalier: f = 1
- Cabinet : f = 1/2
- alpha thường dùng là 45 độ.
"""

from dataclasses import dataclass
from math import cos, sin, radians
from typing import List, Tuple
from .geometry import Point3D, Mesh


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


def project_point(point: Point3D, method: str = "cabinet", angle_deg: float = 45.0) -> Point2D:
    method = method.lower().strip()

    if method == "cavalier":
        factor = 1.0
    elif method == "cabinet":
        factor = 0.5
    else:
        raise ValueError("method phải là 'cavalier' hoặc 'cabinet'.")

    angle = radians(angle_deg)

    xp = point.x + factor * point.z * cos(angle)
    yp = point.y + factor * point.z * sin(angle)

    return Point2D(xp, yp)


def project_mesh(mesh: Mesh, method: str = "cabinet", angle_deg: float = 45.0) -> Tuple[List[Point2D], List[Tuple[int, int]]]:
    projected_vertices = [
        project_point(vertex, method=method, angle_deg=angle_deg)
        for vertex in mesh.vertices
    ]

    return projected_vertices, mesh.edges
