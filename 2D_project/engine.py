from PIL import Image, ImageDraw
import numpy as np
import math
import cv2

class GraphicsEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Tao bang ve
        self.image = Image.new('RGB', (width, height), 'white')
        # Tao but ve
        self.draw = ImageDraw.Draw(self.image)
        self.bg_layer = self.image.copy()

    def clear(self):
        self.image.paste(self.bg_layer, (0, 0))

    def generate_frames(self):
        while True:
            self.clear()
            cv_img = np.array(self.image)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
            success, buffer = cv2.imencode('.jpg', cv_img)
            if success:
                frame_bytes = buffer.tobytes()
                yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


    def to_screen(self, x, y):
        px_x = round(self.width // 2 + x * 5)
        px_y = round(self.height // 2 - y * 5)
        return (px_x, px_y)

#ham putpixel
    def putpixel(self, x, y, color=(0, 0, 0)):
        px_x, px_y = self.to_screen(x, y)
        # DK ve diem nam trong khung hinh
        for i in range(px_x - 2, px_x + 3):
            for j in range(px_y - 2, px_y + 3):
                if 0 <= i < self.width and 0 <= j < self.height:
                    self.draw.point((i, j), fill=color)

    def draw_grid(self):
        grid_color = (220, 220, 220)
        axis_color = (0, 0, 0)
        # //Oy
        for x in range(0, self.width, 5):
            self.draw.line([(x, 0), (x, self.height)], fill = grid_color)
        # //Ox
        for y in range(0, self.height, 5):
            self.draw.line([(0, y), (self.width, y)], fill = grid_color)
        mid_x = self.width // 2
        mid_y = self.height // 2
        # Ox
        self.draw.line([(0, mid_y), (self.width, mid_y)], fill = axis_color, width = 1)
        # Oy
        self.draw.line([(mid_x, 0), (mid_x, self.height)], fill = axis_color, width = 1)
        # Viet Oxy
        if hasattr(self, 'to_screen'):
            cx, cy = self.to_screen(0, 0)
        else:
            cx = self.width // 2
            cy = self.height // 2
        text_color = (0, 0, 0)
        self.draw.text((cx - 15, cy + 5), "O", fill=text_color)
        self.draw.text((self.width - 20, cy + 5), "X", fill=text_color)
        self.draw.text((cx + 10, 10), "Y", fill=text_color)

    # Ve doan thang: nhap vao toa do 2 dinh
    def draw_line(self, x1, y1, x2, y2, color=(0, 0, 0)):
        x1, y1, x2, y2 = round(x1), round(y1), round(x2), round(y2)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self.putpixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = err*2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    #Ve HCN: nhap toa do 1 dinh (dinh duoi ben trai), chieu dai, chieu rong
    def draw_rectangle(self, x1, y1, width, height, color=(0, 0, 0)):
        x1, y1, width, height = round(x1), round(y1), round(width), round(height)
        x2 = x1 + width
        y2 = y1 + height
        self.draw_line(x1, y1, x2, y1, color) #canh duoi
        self.draw_line(x1, y1, x1, y2, color) #canh trai
        self.draw_line(x2, y1, x2, y2, color) #canh phai
        self.draw_line(x2, y2, x1, y2, color) #canh tren

    # Ve tam giac: nhap toa do 3 dinh
    def draw_triangle(self, x1, y1, x2, y2, x3, y3, color=(0, 0, 0)):
        self.draw_line(x1, y1, x2, y2, color)
        self.draw_line(x1, y1, x3, y3, color)
        self.draw_line(x2, y2, x3, y3, color)

    def draw_any_circle(self, xc, yc, r, color=(0, 0, 0)):
        xc, yc, r = round(xc), round(yc), round(r)
        x = 0
        y = r
        p = 1 - r
        while x <= y:
            self.putpixel(x + xc, y + yc, color)
            self.putpixel(-x + xc, y + yc, color)
            self.putpixel(x + xc, -y + yc, color)
            self.putpixel(-x + xc, -y + yc, color)
            self.putpixel(y + xc, x + yc, color)
            self.putpixel(-y + xc, x + yc, color)
            self.putpixel(y + xc, -x + yc, color)
            self.putpixel(-y + xc, -x + yc, color)

            if p < 0:
                x += 1
                p += 2*x + 1
            else:
                x += 1
                y -= 1
                p += 2*x - 2*y +1

    #Ve elip: nhap vao tam (xc, yc) va ban kinh lon a, ban kinh nho b
    def draw_any_ellipse(self, xc, yc, a, b, color=(0, 0, 0)):
        xc, yc, a, b = round(xc), round(yc), round(a), round(b)
        x = 0
        y = b
        a2 = a*a
        b2 = b*b
        two_a2 = 2*a2
        two_b2 = 2*b2
        # Mien I
        p = b2 - a2*b + a2*0.25
        dx = two_b2*x
        dy = two_a2*y
        while dx < dy:
            self.putpixel(x + xc, y + yc, color)
            self.putpixel(-x + xc, y + yc, color)
            self.putpixel(x + xc, -y + yc, color)
            self.putpixel(-x + xc, -y + yc, color)
            if p < 0:
                x += 1
                dx += two_b2
                p += dx + b2
            else:
                x += 1
                y -= 1
                dx += two_b2
                dy -= two_a2
                p += dx - dy + b2

        # Mien II
        q = b2*(x + 0.5)*(x + 0.5) + a2*(y - 1)*(y - 1) - a2*b2
        while y >= 0:
            self.putpixel(x + xc, y + yc, color)
            self.putpixel(-x + xc, y + yc, color)
            self.putpixel(x + xc, -y + yc, color)
            self.putpixel(-x + xc, -y + yc, color)
            if q > 0:
                y -= 1
                dy -= two_a2
                q += a2 - dy
            else:
                y -= 1
                x += 1
                dx += two_b2
                dy -= two_a2
                q += dx - dy + a2

    #Hàm vẽ elip khuyết: nhập vào tâm (xc, yc), bán kính lớn a, bán kính nhỏ b, góc bắt đầu start_angle và góc kết thúc end_angle
    def create_ellipse_arc(self, xc, yc, a, b, start_angle, end_angle, is_closed=False, seed_point=None, fill_color=None, is_connect = False):
        xc, yc, a, b = round(xc), round(yc), round(a), round(b)
        vertices = []
        for angle in range(start_angle, end_angle + 1):
            rad = math.radians(angle)
            x = a * math.cos(rad)
            y = b * math.sin(rad)
            vertices.append((x + xc, y + yc))
        if is_connect:
            vertices.append((xc, yc))
        return Polygon(vertices, is_closed = is_closed, fill_seed=seed_point, fill_color=fill_color)
    #Hàm vẽ cung tròn: nhập vào tâm (xc, yc), bán kính r, góc bắt đầu start_angle và góc kết thúc end_angle
    def create_circle_arc(self, xc, yc, r, start_angle, end_angle, is_closed=False, seed_point=None, fill_color=None, is_connect = False):
        return self.create_ellipse_arc(xc, yc, r, r, start_angle, end_angle, is_closed=is_closed, seed_point=seed_point, fill_color=fill_color, is_connect=is_connect)

    def getpixel(self, x, y):
        return self.image.getpixel((x, y))
    # Ham to mau theo duong bien: nhap vao toa do 1 diem ben trong hinh can fill, mau fill va mau bien
    def boundary_fill(self, x, y, fill_color, boundary_color):
        # Seed sau transform thường là số thực, nên dùng round thay vì int.
        x, y = round(x), round(y)
        stack = [(x, y)]
        while len(stack) > 0:
            current_x, current_y = stack.pop()
            screen_x, screen_y = self.to_screen(current_x, current_y)
            if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                current_color = self.getpixel(screen_x, screen_y)
                if current_color != boundary_color and current_color != fill_color:
                    self.putpixel(current_x, current_y, fill_color)
                    stack.append((current_x + 1, current_y))
                    stack.append((current_x - 1, current_y))
                    stack.append((current_x, current_y + 1))
                    stack.append((current_x, current_y - 1))

    # Ma tran tinh tien
    def translation_matrix(self, tx, ty):
        return np.array([
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ])
    # Ma tran ty le
    def scaling_matrix(self, sx, sy):
        return np.array([
            [sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]
        ])
    # Ma tran xoay
    def rotation_matrix(self, angle):
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        return np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])
    #Ma tran doi xung
    # Ma tran doi xung qua truc X
    def reflection_matrix_x(self):
        return np.array([
            [1,  0, 0],
            [0, -1, 0],
            [0,  0, 1]
        ])

    # Ma tran doi xung qua truc Y
    def reflection_matrix_y(self):
        return np.array([
            [-1, 0, 0],
            [0,  1, 0],
            [0,  0, 1]
        ])

# class Polygon: nhap vao danh sach cac dinh, luu tru duoi dang ma tran 3xN, co ham transform de nhan ma tran chuyen doi va ham draw_changed de ve lai hinh sau khi bi bien doi
class Polygon:
    def __init__(self, vertices, fill_seed=None, fill_color=None, is_closed = True):
        self.matrix = np.array([
            [p[0] for p in vertices],
            [p[1] for p in vertices],
            [1]*len(vertices)
        ])
        self.fill_color = fill_color
        self.is_closed = is_closed
        if fill_seed is not None:
            self.seed_matrix = np.array([
                [fill_seed[0]],
                [fill_seed[1]],
                [1]
            ])
        else: self.seed_matrix = None

    # Ham nhan ma tran chuyen doi vao ma tran dinh va cap nhat lai ma tran dinh
    def transform(self, transform_matrix):
            self.matrix = transform_matrix @ self.matrix
            if self.seed_matrix is not None:
                self.seed_matrix = transform_matrix @ self.seed_matrix

     # Ham ve lai hinh sau khi bi bien doi
    def draw(self, engine, color=(0, 0, 0)):
        num_vertices = self.matrix.shape[1]
        limit = num_vertices if self.is_closed else num_vertices - 1
        for i in range(limit):
            x1, y1 = self.matrix[0, i], self.matrix[1, i]
            next_i = (i + 1) % num_vertices
            x2, y2 = self.matrix[0, next_i], self.matrix[1, next_i]
            engine.draw_line(x1, y1, x2, y2, color)
        if self.seed_matrix is not None and self.fill_color is not None:
            sx = self.seed_matrix[0, 0]
            sy = self.seed_matrix[1, 0]
            engine.boundary_fill(sx, sy, self.fill_color, boundary_color=color)

class Group:
    def __init__(self):
        self.shapes = []
    
    def add(self, polygon, border_color=(0, 0, 0)):
        self.shapes.append({
            "obj": polygon,
            "color": border_color
        })
    
    def transform(self, transform_matrix):
        for item in self.shapes:
            item["obj"].transform(transform_matrix)
    
    def draw(self, engine, override_color=None):
        for item in self.shapes:
            shape = item["obj"]
            shape_color = item["color"]
            final_color = override_color if override_color is not None else shape_color
            shape.draw(engine, color=final_color)

# if __name__ == "__main__":
#     engine = GraphicsEngine(800, 600)
#     engine.draw_grid()
#     engine.bg_layer = engine.image.copy()
#     engine.draw_line(5, 6, 40, 25)
    