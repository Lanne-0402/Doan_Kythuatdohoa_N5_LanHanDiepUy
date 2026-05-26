document.addEventListener("DOMContentLoaded", () => {
    const dropdown6 = document.getElementById('shapeDropdown6');
    const dropdown4 = document.getElementById('shapeDropdown4');
    const selectedShapeTitle = document.getElementById('selectedShapeTitle');
    const toFrame5Buttons = document.querySelectorAll('.to-frame5-btn');
    const toFrame6Btn = document.getElementById('toFrame6Btn');

    // 1. Xử lý Đóng/Mở các menu Dropdown độc lập
    dropdown6.querySelector('.dropdown-toggle').addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown6.classList.toggle('open');
        dropdown4.classList.remove('open');
    });

    dropdown4.querySelector('.dropdown-toggle').addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown4.classList.toggle('open');
        dropdown6.classList.remove('open');
    });

    window.addEventListener('click', () => {
        dropdown6.classList.remove('open');
        dropdown4.classList.remove('open');
    });

    // 2. Chức năng ẩn/hiện chuyển đổi Frame
    function switchFrame(frameId) {
        document.querySelectorAll('.frame').forEach(frame => {
            frame.classList.remove('active');
        });
        document.getElementById(frameId).classList.add('active');
    }

    // 3. Lắng nghe sự kiện click chọn hình từ CẢ HAI menu dropdown
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const shapeName = e.target.getAttribute('data-shape');
            changeAndSetupShape(shapeName);
        });
    });

    // Hàm cập nhật tên hình và sinh ô nhập kích thước dạng số
    function changeAndSetupShape(shapeName) {
        selectedShapeTitle.querySelector('span').innerText = shapeName;
        
        const dynamicInputs = document.getElementById('dynamicInputs');
        if (shapeName === 'Hình Hộp Chữ Nhật') {
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" placeholder="Chiều dài" min="0">
                <input type="number" class="input-dimension" placeholder="Chiều rộng" min="0">
                <input type="number" class="input-dimension" placeholder="Chiều cao" min="0">
            `;
        } else if (shapeName === 'Hình Trụ') {
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" placeholder="Bán kính đáy" min="0">
                <input type="number" class="input-dimension" placeholder="Chiều cao" min="0">
            `;
        }
        
        // Kích hoạt bộ chặn ký tự chữ cho các ô nhập liệu mới sinh ra
        dynamicInputs.querySelectorAll('input').forEach(input => {
            preventNonNumericInputs(input);
        });

        switchFrame('frame4');
    }

    // 4. Điều hướng chuyển mạch Hệ tọa độ 3D / 2D
    toFrame5Buttons.forEach(button => {
        button.addEventListener('click', () => {
            switchFrame('frame5');
        });
    });

    toFrame6Btn.addEventListener('click', () => {
        switchFrame('frame6');
    });

    // 5. Hàm lọc dữ liệu, chỉ cho phép nhập số
    function preventNonNumericInputs(inputElement) {
        inputElement.addEventListener('keydown', (e) => {
            if (['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', '.', ','].includes(e.key)) {
                return;
            }
            if (isNaN(Number(e.key)) && e.key !== '-') {
                e.preventDefault();
            }
        });
    }

    document.querySelectorAll('input[type="number"]').forEach(input => {
        preventNonNumericInputs(input);
    });
});