document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // 1. KHAI BÁO BIẾN VÀ THÀNH PHẦN GIAO DIỆN
    // ==========================================
    const dropdown6 = document.getElementById("shapeDropdown6");
    const dropdown4 = document.getElementById("shapeDropdown4");
    const selectedShapeTitle = document.getElementById("selectedShapeTitle");
    const dynamicInputs = document.getElementById("dynamicInputs");
    const originLabel = document.getElementById("originLabel") || document.createElement("span");
    const projectionMethod = document.getElementById("projectionMethod");
    const projectionMethodAxes = document.getElementById("projectionMethodAxes");
    const questionBox = document.getElementById("questionBox");
    const toast = document.getElementById("toast");
    
    // Màn hình hiển thị
    const drawingCanvas = document.getElementById("drawingCanvas");
    const videoStream = document.getElementById("videoStream");
    const ctx = drawingCanvas.getContext("2d");

    // Các hằng số 3D
    const DEG45 = Math.PI / 4;
    const DEFAULT_UNIT_SIZE = 5;
    const DEFAULT_BOUNDS_UNITS = { x: {min: 0, max: 12}, y: {min: 0, max: 12}, z: {min: 0, max: 12} };
    const MIN_AXIS_SPAN_UNITS = 12;
    const AXIS_PADDING_UNITS = 3;
    const VIEW_DIR = normalize3({x: -0.45, y: -0.65, z: 1.0});
    const shapeNames = { cuboid: "Hình Hộp Chữ Nhật", cube: "Hình Lập Phương", cylinder: "Hình Trụ", sphere: "Hình Cầu" };

    let currentShape = "cuboid";
    let currentScene = { projection: "cabinet", mesh: null, boundsUnits: DEFAULT_BOUNDS_UNITS, unitSize: DEFAULT_UNIT_SIZE };
    let rotationX = -0.15;
    let rotationY = 0.25;
    let zoomScale = 1.0;
    let isDragging = false;
    let lastMouseX = 0;
    let lastMouseY = 0;

    // ==========================================
    // 2. TƯƠNG TÁC CHUỘT VỚI CANVAS 3D
    // ==========================================
    function resizeCanvas() {
        const rect = drawingCanvas.parentElement.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        drawingCanvas.width = Math.floor(rect.width * ratio);
        drawingCanvas.height = Math.floor(rect.height * ratio);
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        renderScene();
    }
    window.addEventListener("resize", resizeCanvas);

    drawingCanvas.addEventListener("mousedown", (e) => { isDragging = true; lastMouseX = e.clientX; lastMouseY = e.clientY; });
    window.addEventListener("mouseup", () => { isDragging = false; });
    window.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        rotationY += (e.clientX - lastMouseX) * 0.01;
        rotationX += (e.clientY - lastMouseY) * 0.01;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
        renderScene();
    });
    drawingCanvas.addEventListener("dblclick", () => { rotationX = -0.15; rotationY = 0.25; zoomScale = 1.0; renderScene(); showToast("Đã đặt lại góc nhìn."); });
    drawingCanvas.addEventListener("wheel", (e) => {
        e.preventDefault();
        zoomScale = Math.max(0.35, Math.min(zoomScale * (e.deltaY < 0 ? 1.1 : 0.9), 4.0));
        renderScene();
    }, { passive: false });
    // --- CHÈN ĐOẠN NÀY ĐỂ KÍCH HOẠT NÚT RESET GÓC ---
    const resetViewBtn = document.getElementById("resetViewBtn");
    if (resetViewBtn) {
        resetViewBtn.addEventListener("click", () => {
            rotationX = -0.15; 
            rotationY = 0.25; 
            zoomScale = 1.0; 
            renderScene();
        });
    }

    // ==========================================
    // 3. UI, CHUYỂN FRAME VÀ MENU THẢ XUỐNG
    // ==========================================
    function switchFrame(frameId) {
        document.querySelectorAll(".frame").forEach(frame => frame.classList.remove("active"));
        document.getElementById(frameId).classList.add("active");
    }

    [dropdown6, dropdown4].forEach(dd => {
        if(!dd) return;
        dd.querySelector(".dropdown-toggle").addEventListener("click", (e) => {
            e.stopPropagation();
            dd.classList.toggle("open");
            if (dd === dropdown6 && dropdown4) dropdown4.classList.remove("open");
            if (dd === dropdown4 && dropdown6) dropdown6.classList.remove("open");
        });
    });

    window.addEventListener("click", () => {
        if(dropdown6) dropdown6.classList.remove("open");
        if(dropdown4) dropdown4.classList.remove("open");
    });

    document.querySelectorAll(".dropdown-item").forEach(item => {
        item.addEventListener("click", (e) => {
            changeAndSetupShape(e.target.getAttribute("data-shape"));
        });
    });

    // Chuyển sang xem 2D
    document.querySelectorAll(".to-frame5-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            switchFrame("frame5");
            drawingCanvas.style.display = 'none';
            videoStream.style.display = 'block';
            forceLoadVideo("/image_grid"); // Hiển thị lưới tĩnh ngay lập tức
        });
    });

    // Quay lại xem 3D
    const toFrame6Btn = document.getElementById("toFrame6Btn");
    if (toFrame6Btn) {
        toFrame6Btn.addEventListener("click", () => {
            switchFrame("frame6");
            videoStream.style.display = 'none';
            drawingCanvas.style.display = 'block';
            videoStream.src = "";
            renderScene();
        });
    }

    // ==========================================
    // 4. LẤY DỮ LIỆU TỪ FORM 3D
    // ==========================================
    function changeAndSetupShape(shape) {
        currentShape = shape;
        const shapeText = shapeNames[shape] || "Hình Hộp Chữ Nhật";
        selectedShapeTitle.querySelector("span").innerText = shapeText;
        if(questionBox) questionBox.innerText = shapeText.replace("Hình ", "");

        // QUAN TRỌNG: Phải có data-param để code tìm được giá trị gửi lên API
        if (shape === "cuboid") {
            originLabel.innerText = "Nhập tọa độ đỉnh dưới - trái - trước";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="length" placeholder="Chiều dài" min="0">
                <input type="number" class="input-dimension" data-param="width" placeholder="Chiều rộng/sâu" min="0">
                <input type="number" class="input-dimension" data-param="height" placeholder="Chiều cao" min="0">`;
        } else if (shape === "cube") {
            originLabel.innerText = "Nhập tọa độ đỉnh dưới - trái - trước";
            dynamicInputs.innerHTML = `<input type="number" class="input-dimension" data-param="size" placeholder="Cạnh lập phương" min="0">`;
        } else if (shape === "cylinder") {
            originLabel.innerText = "Nhập tọa độ tâm đáy dưới";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="radius" placeholder="Bán kính đáy" min="0">
                <input type="number" class="input-dimension" data-param="height" placeholder="Chiều cao" min="0">
                <input type="number" class="input-dimension" data-param="segments" placeholder="Số đoạn chia" min="12">`;
        } else if (shape === "sphere") {
            originLabel.innerText = "Nhập tọa độ tâm hình cầu";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="radius" placeholder="Bán kính" min="0">
                <input type="number" class="input-dimension" data-param="segments" placeholder="Số đoạn chia" min="12">`;
        }

        dynamicInputs.querySelectorAll("input").forEach(input => preventNonNumericInputs(input));
        switchFrame("frame4");
    }

    function collectParams() {
        const params = {};
        dynamicInputs.querySelectorAll("[data-param]").forEach(input => { params[input.dataset.param] = input.value; });
        return params;
    }

    function getNumber(id, fallback = 0) {
        const value = document.getElementById(id)?.value ?? "";
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    // ==========================================
    // 5. ĐIỀU PHỐI NÚT BẤM 2D / 3D
    // ==========================================
    function forceLoadVideo(routePath) {
        videoStream.src = routePath + "?t=" + new Date().getTime();
    }

    const run2DBtn = document.getElementById("drawAxesBtn");
    const drawGridBtn = document.getElementById("drawGridBtn"); // Nút mới
    const clear2DBtn = document.querySelector("#frame5 .clear-btn");
    const animationSelect = document.getElementById("animationSelect");

    const animationDetails = document.getElementById("animationDetails");
async function fetchAnimationCoords() {
    if (!animationDetails) return;

    try {
        const response = await fetch("/api/animation-coords");
        const data = await response.json();

        animationDetails.innerHTML = "";

        if (!data.details || data.details.length === 0) {
            return;
        }

        data.details.forEach(item => {
            const block = document.createElement("div");
            block.className = "coord-object-block";

            const title = document.createElement("div");
            title.className = "coord-object-title";
            title.innerText = item.name;
            block.appendChild(title);

            item.rows.forEach(row => {
                const rowDiv = document.createElement("div");
                rowDiv.className = "duck-coord-row";

                const label = document.createElement("span");
                label.innerText = row.label;

                const value = document.createElement("strong");
                value.innerText = row.value;

                rowDiv.appendChild(label);
                rowDiv.appendChild(value);
                block.appendChild(rowDiv);
            });

            animationDetails.appendChild(block);
        });

    } catch (error) {
        console.error("Không lấy được tọa độ hoạt cảnh:", error);
    }
}

    async function startAnimationCoords(animationName) {
        await fetch("/api/animation-start", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                animation: animationName
            })
        });

        fetchAnimationCoords();
    }


    async function resetAnimationCoords() {
        await fetch("/api/animation-reset", {
            method: "POST"
        });

        fetchAnimationCoords();
    }


    function getSelectedAnimationName() {
        const selectedAnimation = animationSelect?.value || "/video_duck";

        if (selectedAnimation.includes("video_pacman")) {
            return "pacman";
        }

        if (selectedAnimation.includes("video_duck")) {
            return "duck";
        }

        return null;
    }

    // [Nút Chạy 2D]: Bắt đầu phát hoạt cảnh
    if (run2DBtn) {
        run2DBtn.addEventListener("click", async () => {
            drawingCanvas.style.display = "none";
            videoStream.style.display = "block";
            videoStream.style.width = "100%";
            videoStream.style.height = "100%";
            videoStream.style.objectFit = "contain";

            const selectedAnimation = animationSelect?.value || "/video_duck";
            const animationName = getSelectedAnimationName();

            if (animationName) {
                await startAnimationCoords(animationName);
            } else {
                await resetAnimationCoords();
            }

            forceLoadVideo(selectedAnimation);
        });
    }

    // Tự động chuyển đổi hoạt cảnh (Pacman <-> Vịt)
    if (animationSelect) {
        animationSelect.addEventListener("change", async () => {
            if (videoStream.style.display === "block" && videoStream.src.includes("video")) {
                const animationName = getSelectedAnimationName();

                if (animationName) {
                    await startAnimationCoords(animationName);
                } else {
                    await resetAnimationCoords();
                }

                forceLoadVideo(animationSelect.value);
            }
        });
    }
    // [Nút Vẽ hệ tọa độ 2D]: Gọi ảnh lưới tĩnh ra
    if (drawGridBtn) {
        drawGridBtn.addEventListener("click", () => {
            drawingCanvas.style.display = 'none';
            videoStream.style.display = 'block';
            forceLoadVideo("/image_grid"); 
        });
    }

    // [Nút Xóa 2D]: Tắt hẳn màn hình, trả về nền trắng/trống
    if (clear2DBtn) {
        clear2DBtn.addEventListener("click", async () => {
            videoStream.src = "";
            videoStream.style.display = "none";
            drawingCanvas.style.display = "none";

            await resetAnimationCoords();
        });
    }

    // [Nút Vẽ 3D]
    document.querySelectorAll(".draw-btn").forEach(button => {
        // Nút này trong giao diện của bạn trùng class với frame 4/6
        if(button.closest('#frame4') || button.closest('#frame6')) {
            button.addEventListener("click", () => {
                videoStream.style.display = 'none';
                drawingCanvas.style.display = 'block';
                videoStream.src = "";
                if (document.getElementById("frame6").classList.contains("active")) changeAndSetupShape(currentShape);
                drawCurrentShape();
            });
        }
    });

    // [Nút Xóa 3D]
    document.querySelectorAll("#frame4 .clear-btn, #frame6 .clear-btn").forEach(button => {
        button.addEventListener("click", () => {
            currentScene.mesh = null;
            currentScene.boundsUnits = DEFAULT_BOUNDS_UNITS;
            renderScene();
            // showToast("Đã xóa hình vẽ 3D.");
        });
    });

    if (projectionMethod) {
        projectionMethod.addEventListener("change", () => {
            if (currentScene.mesh) { currentScene.projection = projectionMethod.value; renderScene(); }
        });
    }

    // ==========================================
    // 6. LOGIC GỌI API & VẼ 3D
    // ==========================================
    async function drawCurrentShape() {
        const payload = {
            shape: currentShape,
            projection: projectionMethod ? projectionMethod.value : "cabinet",
            origin: { x: getNumber("coordX"), y: getNumber("coordY"), z: getNumber("coordZ") },
            params: collectParams(),
        };

        try {
            const response = await fetch("/api/draw", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
            const data = await response.json();
            if (!response.ok || !data.ok) throw new Error(data.error || "Không thể vẽ hình.");

            currentScene = { projection: data.projection, mesh: data.mesh, boundsUnits: data.bounds_units || DEFAULT_BOUNDS_UNITS, unitSize: data.unit_size || DEFAULT_UNIT_SIZE };
            renderScene();
            // showToast(`Đã vẽ ${shapeNames[currentShape]}.`);
        } catch (error) { showToast(error.message, true); }
    }

    function renderScene() {
        ctx.clearRect(0, 0, drawingCanvas.width, drawingCanvas.height);
        const boundsUnits = currentScene.boundsUnits || DEFAULT_BOUNDS_UNITS;
        const projection = currentScene.projection || "cabinet";
        const unitSize = currentScene.unitSize || DEFAULT_UNIT_SIZE;
        const axisData = createAxisData(boundsUnits, unitSize);

        let rotatedMeshPoints = [];
        let projectedMeshPoints = [];
        if (currentScene.mesh && currentScene.mesh.vertices) {
            rotatedMeshPoints = currentScene.mesh.vertices.map(rotatePoint);
            projectedMeshPoints = rotatedMeshPoints.map(p => projectPoint(p, projection));
        }

        const allPoints = [
            ...axisData.axisReferencePoints.map(p => projectPoint(rotatePoint(p), projection)),
            ...axisData.gridReferencePoints.map(p => projectPoint(rotatePoint(p), projection)),
            ...projectedMeshPoints,
        ];

        const transform = createScreenTransform(allPoints, drawingCanvas.getBoundingClientRect().width, drawingCanvas.getBoundingClientRect().height, zoomScale);

        drawGrid(axisData.gridLines, projection, transform);
        drawAxes(axisData, projection, transform);
        if (currentScene.mesh) drawMeshWithHiddenLines(currentScene.mesh, rotatedMeshPoints, projectedMeshPoints, transform);
    }

    // ==========================================
    // 7. CÁC HÀM TÍNH TOÁN & TOÁN HỌC 3D CỐT LÕI
    // ==========================================
    function projectPoint(point, method) {
        const factor = method === "cavalier" ? 1 : 0.5;
        return { x: point.x + factor * point.z * Math.cos(DEG45), y: point.y + factor * point.z * Math.sin(DEG45) };
    }

    function rotatePoint(point) {
        const cy = Math.cos(rotationY), sy = Math.sin(rotationY);
        const cx = Math.cos(rotationX), sx = Math.sin(rotationX);
        const x1 = point.x * cy + point.z * sy, y1 = point.y, z1 = -point.x * sy + point.z * cy;
        return { x: x1, y: y1 * cx - z1 * sx, z: y1 * sx + z1 * cx };
    }

    function createScreenTransform(points, width, height, zoom = 1.0) {
        const padding = 78;
        if (!points.length) return () => ({x: width / 2, y: height / 2});
        let minX = Math.min(...points.map(p => p.x)), maxX = Math.max(...points.map(p => p.x));
        let minY = Math.min(...points.map(p => p.y)), maxY = Math.max(...points.map(p => p.y));
        if (Math.abs(maxX - minX) < 0.001) { minX -= 1; maxX += 1; }
        if (Math.abs(maxY - minY) < 0.001) { minY -= 1; maxY += 1; }
        const scale = Math.max(8, Math.min((width - padding * 2) / (maxX - minX), (height - padding * 2) / (maxY - minY))) * zoom;
        const centerX = (minX + maxX) / 2, centerY = (minY + maxY) / 2;
        return (p) => ({ x: width / 2 + (p.x - centerX) * scale, y: height / 2 - (p.y - centerY) * scale });
    }

    function createAxisData(bounds, uSize) {
        const normalize = (min, max) => {
            let mn = Math.min(0, Math.floor(min) - AXIS_PADDING_UNITS);
            let mx = Math.max(0, Math.ceil(max) + AXIS_PADDING_UNITS);
            if (mx - mn < MIN_AXIS_SPAN_UNITS) mx = mn + MIN_AXIS_SPAN_UNITS;
            return {min: mn, max: mx};
        };
        const xr = normalize(bounds.x.min, bounds.x.max), yr = normalize(bounds.y.min, bounds.y.max), zr = normalize(bounds.z.min, bounds.z.max);
        const refPoints = [ {x: xr.min*uSize, y:0, z:0}, {x: xr.max*uSize, y:0, z:0}, {x:0, y: yr.min*uSize, z:0}, {x:0, y: yr.max*uSize, z:0}, {x:0, y:0, z: zr.min*uSize}, {x:0, y:0, z: zr.max*uSize}, {x:0, y:0, z:0} ];
        
        const gridLines = []; const gridRef = [];
        const addGL = (a, b) => { gridLines.push({a, b}); gridRef.push(a, b); };
        for (let x = xr.min; x <= xr.max; x++) addGL({x: x*uSize, y: yr.min*uSize, z:0}, {x: x*uSize, y: yr.max*uSize, z:0});
        for (let y = yr.min; y <= yr.max; y++) addGL({x: xr.min*uSize, y: y*uSize, z:0}, {x: xr.max*uSize, y: y*uSize, z:0});
        for (let x = xr.min; x <= xr.max; x++) addGL({x: x*uSize, y: 0, z: zr.min*uSize}, {x: x*uSize, y: 0, z: zr.max*uSize});
        for (let z = zr.min; z <= zr.max; z++) addGL({x: xr.min*uSize, y: 0, z: z*uSize}, {x: xr.max*uSize, y: 0, z: z*uSize});
        for (let y = yr.min; y <= yr.max; y++) addGL({x: 0, y: y*uSize, z: zr.min*uSize}, {x: 0, y: y*uSize, z: zr.max*uSize});
        for (let z = zr.min; z <= zr.max; z++) addGL({x: 0, y: yr.min*uSize, z: z*uSize}, {x: 0, y: yr.max*uSize, z: z*uSize});

        return { xStart: refPoints[0], xEnd: refPoints[1], yStart: refPoints[2], yEnd: refPoints[3], zStart: refPoints[4], zEnd: refPoints[5], xMin: xr.min, xMax: xr.max, yMin: yr.min, yMax: yr.max, zMin: zr.min, zMax: zr.max, gridLines, axisReferencePoints: refPoints, gridReferencePoints: gridRef };
    }

    function drawGrid(lines, proj, transform) {
        ctx.save(); ctx.strokeStyle = "#1e1e1e"; ctx.lineWidth = 1; ctx.globalAlpha = 0.15; ctx.setLineDash([4, 6]);
        lines.forEach(l => {
            const p1 = transform(projectPoint(rotatePoint(l.a), proj));
            const p2 = transform(projectPoint(rotatePoint(l.b), proj));
            ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
        });
        ctx.restore();
    }

    function drawAxes(data, proj, transform) {

    const drawL = (s, e, lbl) => {

        const p1 = transform(
            projectPoint(
                rotatePoint(s),
                proj
            )
        );

        const p2 = transform(
            projectPoint(
                rotatePoint(e),
                proj
            )
        );

        ctx.save();

        ctx.lineWidth = 3;
        ctx.strokeStyle = "#1e1e1e";

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();

        ctx.font = "bold 18px Courier New";
        ctx.fillStyle = "#1e1e1e";
        ctx.fillText(lbl, p2.x + 12, p2.y - 8);

        ctx.restore();

        return { p1, p2 };
    };

    const xAxis = drawL(data.xStart, data.xEnd, "X");
    const yAxis = drawL(data.yStart, data.yEnd, "Y");
    const zAxis = drawL(data.zStart, data.zEnd, "Z");

    const o = transform(
        projectPoint(
            rotatePoint({x:0, y:0, z:0}),
            proj
        )
    );

    ctx.save();
    ctx.font = "bold 16px Courier New";
    ctx.fillStyle = "#1e1e1e";
    ctx.fillText("O", o.x - 18, o.y + 18);
    ctx.restore();

    //----------------------------------
    // VẠCH CHIA OX
    //----------------------------------

    drawAxisTicks(
        data.xMin,
        data.xMax,
        (v) => ({x:v*5, y:0, z:0}),
        xAxis,
        proj,
        transform
    );

    //----------------------------------
    // VẠCH CHIA OY
    //----------------------------------

    drawAxisTicks(
        data.yMin,
        data.yMax,
        (v) => ({x:0, y:v*5, z:0}),
        yAxis,
        proj,
        transform
    );

    //----------------------------------
    // VẠCH CHIA OZ
    //----------------------------------

    drawAxisTicks(
        data.zMin,
        data.zMax,
        (v) => ({x:0, y:0, z:v*5}),
        zAxis,
        proj,
        transform
    );
}

    function drawAxisTicks(minVal, maxVal, pointFn, axis, proj, transform) {

    const dx = axis.p2.x - axis.p1.x;
    const dy = axis.p2.y - axis.p1.y;

    const len = Math.hypot(dx, dy);

    if (len < 1) return;

    const nx = -dy / len;
    const ny = dx / len;

    const tickSize = 4;

    for (let i = minVal; i <= maxVal; i++) {

        if (i === 0) continue;

        const p = transform(
            projectPoint(
                rotatePoint(pointFn(i)),
                proj
            )
        );

        ctx.save();

        ctx.strokeStyle = "#1e1e1e";
        ctx.lineWidth = 1;

        ctx.beginPath();

        ctx.moveTo(
            p.x - nx * tickSize,
            p.y - ny * tickSize
        );

        ctx.lineTo(
            p.x + nx * tickSize,
            p.y + ny * tickSize
        );

        ctx.stroke();

        if (i % 5 === 0) {

            ctx.font = "11px Courier New";
            ctx.fillStyle = "#1e1e1e";

            ctx.fillText(
                i,
                p.x + nx * 10,
                p.y + ny * 10
            );
        }

        ctx.restore();
    }
}

    function drawMeshWithHiddenLines(mesh, rVerts, pVerts, transform) {
        const visibleFaces = (mesh.faces || []).map(f => {
            if (f.length < 3) return false;
            const u = subtract3(rVerts[f[1]], rVerts[f[0]]), v = subtract3(rVerts[f[2]], rVerts[f[0]]);
            const n = cross3(u, v);
            const len = Math.hypot(n.x, n.y, n.z);
            if (len < 0.000001) return false;
            return dot3({x: n.x/len, y: n.y/len, z: n.z/len}, VIEW_DIR) > 0.0001;
        });
        
        const edgeFaces = new Map();
        (mesh.faces || []).forEach((f, fi) => {
            for (let i = 0; i < f.length; i++) {
                const a = f[i], b = f[(i + 1) % f.length], key = a < b ? `${a}-${b}` : `${b}-${a}`;
                if (!edgeFaces.has(key)) edgeFaces.set(key, []);
                edgeFaces.get(key).push(fi);
            }
        });

        (mesh.edges || []).forEach(edge => {
            const key = edge[0] < edge[1] ? `${edge[0]}-${edge[1]}` : `${edge[1]}-${edge[0]}`;
            const isVisible = (edgeFaces.get(key) || []).some(fi => visibleFaces[fi]);
            const p1 = transform(pVerts[edge[0]]), p2 = transform(pVerts[edge[1]]);
            ctx.save(); ctx.beginPath(); ctx.lineWidth = isVisible ? 2.4 : 2; ctx.strokeStyle = "#1e1e1e";
            ctx.globalAlpha = isVisible ? 1 : 0.75; ctx.setLineDash(isVisible ? [] : [8, 6]);
            ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke(); ctx.restore();
        });
    }

    function subtract3(a, b) { return {x: a.x - b.x, y: a.y - b.y, z: a.z - b.z}; }
    function cross3(a, b) { return { x: a.y*b.z - a.z*b.y, y: a.z*b.x - a.x*b.z, z: a.x*b.y - a.y*b.x }; }
    function dot3(a, b) { return a.x*b.x + a.y*b.y + a.z*b.z; }
    function normalize3(v) { const l = Math.hypot(v.x, v.y, v.z) || 1; return {x: v.x/l, y: v.y/l, z: v.z/l}; }

    function preventNonNumericInputs(el) {
        el.addEventListener("keydown", (e) => {
            if (["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab", ".", ",", "-"].includes(e.key)) return;
            if (isNaN(Number(e.key))) e.preventDefault();
        });
    }

    function showToast(msg, isErr = false) {
        if(!toast) return;
        toast.innerText = msg; toast.style.display = "block";
        toast.style.background = isErr ? "rgba(255, 220, 220, 0.97)" : "rgba(255, 255, 255, 0.95)";
        clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.style.display = "none", 3200);
    }

    document.querySelectorAll('input[type="number"]').forEach(input => preventNonNumericInputs(input));
    
    // ==========================================
    // 8. KHỞI TẠO MẶC ĐỊNH KHI MỞ TRANG
    // ==========================================
    setInterval(fetchAnimationCoords, 100);
    fetchAnimationCoords();
    changeAndSetupShape("cuboid");
    switchFrame("frame6");
    resizeCanvas();
});