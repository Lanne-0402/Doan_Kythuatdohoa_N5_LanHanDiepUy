from engine import GraphicsEngine, Group, Polygon

# Mau sac
BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
BLUE   = (110, 170, 255)
LBLUE  = (200, 240, 255)
ORANGE = (255, 165, 0)
YELLOW = (255, 220, 0)

# Tam goc cua cum tia nuoc / wake.
# Animation se dung diem nay lam pivot de scale/rotate bang ma tran.
WATER_PIVOT_X = -26
WATER_PIVOT_Y = 8


def create_water_group(engine, main_color=WHITE, soft_color=LBLUE):
    """
    Khoi tia nuoc / wake goc.

    Ham nay chi ve hinh goc. File duck_animation.py se dung ma tran bien doi
    de scale / rotate / translate cum nuoc nay.

    main_color, soft_color giup animation lam tia nuoc nhat dan theo thoi gian.
    Khi chay rieng duck_scene.py, co the goi nhu cu:
        create_water_group(engine)
    """
    water_group = Group()

    # 2 cung nho o phia sau con vit, khong ve ca vong lon bao quanh phao nua.
    water1 = engine.create_ellipse_arc(
        WATER_PIVOT_X, WATER_PIVOT_Y,
        45, 32,
        120, 200,
        is_closed=False
    )

    water2 = engine.create_ellipse_arc(
        WATER_PIVOT_X, WATER_PIVOT_Y,
        52, 38,
        135, 190,
        is_closed=False
    )

    water_group.add(water1, border_color=main_color)
    water_group.add(water2, border_color=soft_color)

    return water_group


def polygon_to_points(poly):
    """
    Lấy danh sách điểm từ Polygon.
    Nếu engine của bạn lưu dưới tên matrix thì dùng matrix.
    """
    M = poly.matrix if hasattr(poly, "matrix") else poly.vertices
    pts = []
    for i in range(M.shape[1]):
        pts.append((M[0, i], M[1, i]))
    return pts


def create_ring_groups(engine):
    """
    Tách phao thành 2 group:
    - ring_back_group: phần phao phía sau
    - ring_front_group: phần phao phía trước để đè lên vịt
    """
    ring_back_group = Group()
    ring_front_group = Group()

    # =========================
    # 1. Phao nền phía sau
    # =========================
    ring_outer = engine.create_ellipse_arc(
        -20, 4, 46, 32,
        1, 359,
        is_closed=True,
        seed_point=(-20, 4),
        fill_color=ORANGE
    )

    ring_inner = engine.create_ellipse_arc(
        -22, 8, 21, 11,
        1, 359,
        is_closed=True,
        seed_point=(-22, 8),
        fill_color=BLUE
    )

    ring_back_group.add(ring_outer, border_color=BLACK)
    ring_back_group.add(ring_inner, border_color=BLACK)

    # =========================
    # 2. Stripe phía sau
    # =========================
    stripe1 = Polygon(
        [(-37, 16), (-41, 14), (-54, 25), (-50, 27)],
        fill_seed=(-43, 20),
        fill_color=YELLOW,
        is_closed=True
    )
    ring_back_group.add(stripe1, border_color=YELLOW)

    # =========================
    # 3. Tạo miếng phao phía trước (1 Polygon kín)
    #    = chỉ là mảng cam để che vịt
    # =========================
    outer_front_arc = engine.create_ellipse_arc(
        -20, 4, 46, 32,
        205, 340,
        is_closed=False
    )

    inner_front_arc = engine.create_ellipse_arc(
        -22, 8, 21, 11,
        210, 335,
        is_closed=False
    )

    outer_pts = polygon_to_points(outer_front_arc)
    inner_pts = polygon_to_points(inner_front_arc)

    # ghép cung ngoài + cung trong theo chiều ngược lại để thành biên kín
    front_vertices = outer_pts + inner_pts[::-1]

    # Dùng màu biên tạm không trùng màu nào trong hình
    # để boundary_fill có thể tô đè qua cả thân trắng và viền đen của vịt
    TEMP_BOUNDARY = (1, 2, 3)
    ORANGE_TMP = (255, 166, 1)

    # Lớp tạm: ép vùng ring_front được fill lại
    front_piece_tmp = Polygon(
        front_vertices,
        fill_seed=(-20, -15),
        fill_color=ORANGE_TMP,
        is_closed=True
    )
    ring_front_group.add(front_piece_tmp, border_color=TEMP_BOUNDARY)

    # Lớp chính: tô lại đúng màu cam
    front_piece = Polygon(
        front_vertices,
        fill_seed=(-20, -15),
        fill_color=ORANGE,
        is_closed=True
    )
    ring_front_group.add(front_piece, border_color=TEMP_BOUNDARY)

    # Che màu biên tạm và che 2 cạnh nối phụ của polygon
    front_seam_cover = Polygon(
        front_vertices,
        is_closed=True
    )
    ring_front_group.add(front_seam_cover, border_color=ORANGE)
    # =========================
    # Stripe phía trước
    # =========================
    stripe_front = Polygon(
        [(8, -20), (2, -24), (-16, -3), (-10, -2)],
        fill_seed=(-10, -7),
        fill_color=YELLOW,
        is_closed=True
    )

    # Chỉ tô vàng, không cần viền đen
    ring_front_group.add(stripe_front, border_color=YELLOW)

    # =========================
    # 4. Vẽ lại 2 viền đen của phao phía trước
    # =========================
    outer_front_outline = engine.create_ellipse_arc(
        -20, 4, 46, 32,
        205, 340,
        is_closed=False
    )

    inner_front_outline = engine.create_ellipse_arc(
        -22, 8, 21, 11,
        210, 335,
        is_closed=False
    )

    ring_front_group.add(outer_front_outline, border_color=BLACK)
    ring_front_group.add(inner_front_outline, border_color=BLACK)

    return ring_back_group, ring_front_group


def create_duck_group(engine):
    """Khoi con vit."""
    duck_group = Group()

    # Than vit
    body = engine.create_ellipse_arc(
        -23, 2, 18, 10,
        1, 359,
        is_closed=True,
        seed_point=(-21, 6),
        fill_color=WHITE
    )
    duck_group.add(body, border_color=WHITE)
    body_outline = engine.create_ellipse_arc(
        -23, 2, 18, 10,
        1, 359,
        is_closed=True
    )
    duck_group.add(body_outline, border_color=BLACK)
    T=engine.rotation_matrix(-13)
    duck_group.transform(T)

    # Dau vit: hinh tron trang kin de che phao phia duoi
    head_fill = engine.create_circle_arc(
        -10, 15, 8,
        1, 359,
        is_closed=True,
        seed_point=(-10, 15),
        fill_color=WHITE
    )
    duck_group.add(head_fill, border_color=WHITE)

    # Vien dau vit khuyet
    head_outline = engine.create_circle_arc(
        -10, 15, 8,
        305, 545,
        is_closed=False
    )
    duck_group.add(head_outline, border_color=BLACK)

    # Mat
    eye_fill = engine.create_circle_arc(
        -13, 16, 1,
        1, 359,
        is_closed=True,
        seed_point=(-13, 16),
        fill_color=BLACK
    )
    duck_group.add(eye_fill, border_color=BLACK)

    #duck_group.add(eye, border_color=BLACK)

    # Mo: fill vang truoc, vien den sau
    beak_fill = engine.create_ellipse_arc(
        -3, 14, 6, 3,
        1, 359,
        is_closed=True,
        seed_point=(-3, 14),
        fill_color=YELLOW
    )
    duck_group.add(beak_fill, border_color=YELLOW)

    beak_outline = engine.create_ellipse_arc(
        -3, 14, 6, 3,
        1, 359,
        is_closed=True
    )
    duck_group.add(beak_outline, border_color=BLACK)

    # Canh nho
    wing = engine.create_ellipse_arc(-24, 6, 8, 5, 210, 330, is_closed=False)
    duck_group.add(wing, border_color=BLACK)

    return duck_group


def main():
    engine = GraphicsEngine(900, 700)

    # Nen nuoc
    engine.draw_rectangle(-90, -70, 180, 140, BLUE)
    engine.boundary_fill(0, 0, BLUE, BLUE)

    # Tao tung khoi rieng
    water_group = create_water_group(engine)
    ring_back_group, ring_front_group = create_ring_groups(engine)
    duck_group = create_duck_group(engine)

    # Dich chuyen ca cum
    T = engine.translation_matrix(18, 8)

    water_group.transform(T)
    ring_back_group.transform(T)
    duck_group.transform(T)
    ring_front_group.transform(T)
    T = engine.translation_matrix(1, 0)
    duck_group.transform(T)
    # Thu tu ve = thu tu layer
    water_group.draw(engine)       # duoi cung
    ring_back_group.draw(engine)   # phao phia sau
    duck_group.draw(engine)        # con vit
    ring_front_group.draw(engine)  # phao phia truoc de len vit

    engine.save("2D_project/duck.png")


if __name__ == "__main__":
    main()
