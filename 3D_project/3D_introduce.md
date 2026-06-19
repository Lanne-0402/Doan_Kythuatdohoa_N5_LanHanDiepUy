# Đồ án vẽ 3D bằng Python + HTML UI

Project này tích hợp UI HTML/CSS pixel với phần xử lý Python.

## Chức năng

- Chọn hình cần vẽ:
  - Hình hộp chữ nhật
  - Hình lập phương
  - Hình trụ
  - Hình cầu
- Nhập tọa độ và kích thước.
- Chọn phép chiếu:
  - Cabinet
  - Cavalier
- Python tạo mesh 3D dạng wireframe.
- Python chiếu 3D xuống 2D.
- HTML Canvas vẽ kết quả.

## Cấu trúc

```text
project.py
core/
  geometry.py
  projection.py
templates/
  index.html
static/
  style.css
  script.js
  bg_pixel.jpg
requirements.txt
```
## Các thao tác

- Kéo thả chuột: xoay không gian 3 chiều
- Đúp chuột: đặt lại góc nhìn
- Lăn chuột: phóng to và thu nhỏ

## Cách chạy

### 1. Cài thư viện

```bash
pip install Flask>=3.0.0
```

### 2. Chạy server

```bash
python project.py
```

### 3. Mở trình duyệt

Vào địa chỉ:

```text
http://127.0.0.1:5000
```

## Luồng xử lý

```text
Người dùng nhập thông số trên HTML
        ↓
JavaScript gửi dữ liệu sang Flask API
        ↓
Python tạo đối tượng 3D
        ↓
Python dùng Cavalier/Cabinet để chiếu sang 2D
        ↓
JavaScript nhận points + edges và vẽ lên canvas
```

## Công thức chiếu

```text
x' = x + f * z * cos(45°)
y' = y + f * z * sin(45°)
```

Trong đó:

```text
Cavalier: f = 1
Cabinet : f = 1/2
```