# 2D Graphics Engine - Tài liệu hướng dẫn sử dụng

Đây là lõi đồ họa `engine.py` của nhóm mình, được xây dựng hoàn toàn từ đầu (không dùng thư viện vẽ có sẵn). File này cung cấp mọi công cụ cần thiết để bạn thực hiện nhiệm vụ **Vẽ hình & Chuyển động 2D**. 

## 1. Cài đặt môi trường
Động cơ sử dụng tọa độ đồng nhất và ma trận để tính toán siêu tốc, nên bạn cần cài đặt thư viện `numpy` và 'pillow'trước khi chạy:
```bash
pip install numpy
pip install PIL
```

## 2. Các thành phần chính trong engine.py
GraphicsEngine: Chứa các thuật toán lõi (Bresenham, Midpoint), thuật toán tô màu (Boundary Fill với nét cọ đã được làm đậm 3x3) và các hàm tạo ma trận (Tịnh tiến, Thu phóng, Quay).

Polygon: Class dùng để đóng gói các hình vẽ. Nó tự động chuyển danh sách tọa độ đỉnh thành Ma trận 3xN và xử lý phép nhân ma trận tối ưu.

## 3. Hướng dẫn vẽ hình cơ bản
Để vẽ một hình, chỉ cần nạp tọa độ các đỉnh theo thứ tự (để engine tự nối khép kín). Gốc tọa độ (0, 0) nằm ở chính giữa màn hình
```python
    from engine import GraphicsEngine, Polygon
    # Khởi tạo Engine (ví dụ màn hình 800x600)
    engine = GraphicsEngine(800, 600)
    # Tạo một hình chữ nhật (Tâm ở 0,0)
    rect_vertices = [(-50, -50), (50, -50), (50, 50), (-50, 50)]
    my_rect = Polygon(rect_vertices)
    # Vẽ hình lên màn hình
    my_rect.draw(engine, color=(255, 0, 0)) # Vẽ viền đỏ
```
## 4. Hướng dẫn làm Chuyển động (Animation)
Để tạo chuyển động mượt mà, nguyên tắc là: Xóa màn hình -> Tính ma trận biến đổi -> Cập nhật hình -> Vẽ lại -> Tạm dừng (FPS).

Dưới đây là khung code mẫu để làm cho hình chữ nhật tự động xoay và di chuyển:
```python
import time

# Tạo vòng lặp hoạt hình (Animation Loop)
while True:
    # Bước 1: Xóa màn hình cũ (code tùy thuộc vào thư viện hiển thị như pygame/tkinter/pillow)
    # engine.clear_screen() 
    
    # Bước 2: Tạo ma trận biến đổi (VD: Xoay 5 độ, dịch sang phải 2 pixel mỗi khung hình)
    # LƯU Ý: Nhân ma trận theo thứ tự từ PHẢI qua TRÁI!
    T = engine.get_translation_matrix(2, 0)
    R = engine.get_rotation_matrix(5)
    ma_tran_tong = T @ R 
    
    # Bước 3: Áp dụng biến đổi vào hình
    my_rect.transform(ma_tran_tong)
    
    # Bước 4: Vẽ lại và cập nhật màn hình
    my_rect.draw(engine, color=(0, 0, 255))
    # engine.update_display()
    
    # Bước 5: Tạm dừng để kiểm soát tốc độ khung hình (VD: ~30 FPS)
    time.sleep(0.03)
```
## 5. Note
Phép quay mặc định quanh gốc (0,0): Nếu muốn một vật thể tự xoay quanh chính tâm của nó khi nó đang ở vị trí khác, phải dùng chuỗi 3 ma trận: T_xuôi @ R @ T_ngược.

Nét cọ đã được nâng cấp: Nét vẽ hiện tại là 4x4 pixel (hiển thị rất rõ nét),  có thể yên tâm sử dụng putpixel hoặc draw_line mà không sợ nét bị mờ.

Có hàm draw_any_circle và draw_any_ellipse là hàm vẽ đường tròn và elip với tâm bất kì, chỉ cần nhập toạ độ tâm và bán kính.

## 6. Các tính năng Nâng cao: Vẽ cung khuyết & Gom nhóm vật thể (MỚI)

Để hỗ trợ việc vẽ các hình khối phức tạp và làm animation dễ dàng hơn, Engine đã được nâng cấp thêm cơ chế sinh Ma trận đỉnh (Vertex Matrix) bằng Lượng giác cho đường cong, và class `Group` để gom nhóm.

### 6.1. Hàm tạo hình tròn và elip khuyết
Thay vì dùng thuật toán Midpoint vẽ từng pixel, các hàm này dùng `sin` và `cos` để sinh ra một danh sách đỉnh và tự động đóng gói thành đối tượng `Polygon`. Nhờ vậy, cung khuyết có thể nhận ma trận xoay, thu phóng bình thường mà không bị méo.

**Quy ước góc:** Góc 0 độ nằm ở vị trí 3 giờ (nằm ngang bên phải).

* **Tạo cung tròn:**
  ```python
  # Cú pháp: create_circle_arc(tâm_x, tâm_y, bán_kính, góc_bắt_đầu, góc_kết_thúc)
  # Ví dụ: Tạo nửa vòng tròn trên
  half_circle = engine.create_circle_arc(0, 0, 50, 0, 180)
  ```
* **Tạo cung elip:**
  ```python
  # Cú pháp: create_ellipse_arc(tâm_x, tâm_y, bán_kính_ngang_a, bán_kính_dọc_b, góc_bắt_đầu, góc_kết_thúc)
  # Ví dụ: Tạo cung elip khuyết phần tư cuối
  ellipse_arc = engine.create_ellipse_arc(0, 0, 60, 30, 0, 270)
  ```
### 6.2. Class `Group`: Gom khối vật thể
Dùng để nhóm nhiều hình (Polygon, Cung tròn...) thành một cỗ máy thống nhất. Khi bạn áp dụng ma trận biến đổi lên Group, toàn bộ các hình con bên trong sẽ di chuyển theo cùng một tỷ lệ và góc độ.

Các bước sử dụng:
  Khởi tạo: `my_group = Group()`
  Thêm hình: `my_group.add(shape_1), my_group.add(shape_2)`
  Biến đổi & Vẽ: `my_group.transform(matrix) và my_group.draw(engine, color)`