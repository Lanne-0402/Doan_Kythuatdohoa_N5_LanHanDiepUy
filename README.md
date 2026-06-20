# ĐỒ ÁN KỸ THUẬT ĐỒ HỌA
Repo chứa mã nguồn đồ án môn Kỹ thuật đồ hoạ về 2D và 3D của nhóm 2 gồm: Lan, Hân, Diệp, Uy

## Cấu trúc hệ thống

DoAn_KyThuatDoHoa/
│
├── dist/                   <-- Đóng gói chương trình
│   └── DoAn_2D3D_N2.exe    
│
├── project.py              <-- Trái tim của Server Web
│
├── 2D_project/             <-- Thư mục 2D
│   ├── engine.py
│   ├── pacman.py
│   └── duck_animation.py
|        └── duck_scene.py
│
├── 3D_project/             <-- Thư mục 3D
│   └── core
|       └── __init__.py
|       └── geometry.py 
|       └── projection.py          
│
├── static/                 <-- Đưa các file tĩnh vào
│   ├── style.css
│   ├── script.js
│
└── templates/              <-- Đưa HTML vào
    └── index.html