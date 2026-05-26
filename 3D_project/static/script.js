document.addEventListener("DOMContentLoaded", () => {
    const dropdown6 = document.getElementById("shapeDropdown6");
    const dropdown4 = document.getElementById("shapeDropdown4");
    const selectedShapeTitle = document.getElementById("selectedShapeTitle");
    const dynamicInputs = document.getElementById("dynamicInputs");
    const originLabel = document.getElementById("originLabel");
    const projectionMethod = document.getElementById("projectionMethod");
    const projectionMethodAxes = document.getElementById("projectionMethodAxes");
    const questionBox = document.getElementById("questionBox");
    const toast = document.getElementById("toast");
    const rightPanel = document.getElementById("displayCanvas");

    const toFrame5Buttons = document.querySelectorAll(".to-frame5-btn");
    const toFrame6Btn = document.getElementById("toFrame6Btn");
    const drawAxesBtn = document.getElementById("drawAxesBtn");
    const resetViewBtn = document.getElementById("resetViewBtn");

    const canvas = document.getElementById("drawingCanvas");
    const ctx = canvas.getContext("2d");

    const DEG45 = Math.PI / 4;

    // Hướng nhìn cố định trong không gian sau khi xoay.
    // Dấu y âm giúp thấy mặt trên; dấu z dương giúp thấy mặt trước theo quy ước z đi vào sâu.
    const VIEW_DIR = normalize3({x: -0.45, y: -0.65, z: 1.0});

    const shapeNames = {
        cuboid: "Hình Hộp Chữ Nhật",
        cube: "Hình Lập Phương",
        cylinder: "Hình Trụ",
        sphere: "Hình Cầu",
    };

    let currentShape = "cuboid";
    let currentScene = {
        projection: "cabinet",
        mesh: null,
        dimensions: {x: 6, y: 6, z: 6},
    };

    // Góc xoay toàn bộ không gian Oxyz.
    let rotationX = -0.15;
    let rotationY = 0.25;

    // Tỉ lệ phóng to / thu nhỏ bằng con lăn chuột.
    let zoomScale = 1.0;

    let isDragging = false;
    let lastMouseX = 0;
    let lastMouseY = 0;

    function resizeCanvas() {
        const rect = canvas.parentElement.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        canvas.width = Math.floor(rect.width * ratio);
        canvas.height = Math.floor(rect.height * ratio);
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        renderScene();
    }

    window.addEventListener("resize", resizeCanvas);

    canvas.addEventListener("mousedown", (event) => {
        isDragging = true;
        lastMouseX = event.clientX;
        lastMouseY = event.clientY;
        rightPanel.classList.add("dragging");
    });

    window.addEventListener("mouseup", () => {
        isDragging = false;
        rightPanel.classList.remove("dragging");
    });

    window.addEventListener("mousemove", (event) => {
        if (!isDragging) return;

        const dx = event.clientX - lastMouseX;
        const dy = event.clientY - lastMouseY;

        rotationY += dx * 0.01;
        rotationX += dy * 0.01;

        lastMouseX = event.clientX;
        lastMouseY = event.clientY;

        renderScene();
    });

    canvas.addEventListener("dblclick", () => {
        resetRotation();
        showToast("Đã đặt lại góc nhìn và mức zoom.");
    });

    canvas.addEventListener("wheel", (event) => {
        event.preventDefault();

        const zoomStep = event.deltaY < 0 ? 1.1 : 0.9;
        zoomScale *= zoomStep;

        // Giới hạn zoom để tránh hình quá nhỏ hoặc quá lớn.
        zoomScale = Math.max(0.35, Math.min(zoomScale, 4.0));

        renderScene();
    }, { passive: false });

    if (resetViewBtn) {
        resetViewBtn.addEventListener("click", () => {
            resetRotation();
            showToast("Đã đặt lại góc nhìn.");
        });
    }

    function resetRotation() {
        rotationX = -0.15;
        rotationY = 0.25;
        zoomScale = 1.0;
        renderScene();
    }

    function switchFrame(frameId) {
        document.querySelectorAll(".frame").forEach(frame => frame.classList.remove("active"));
        document.getElementById(frameId).classList.add("active");
    }

    function setupDropdown(dropdown) {
        dropdown.querySelector(".dropdown-toggle").addEventListener("click", (event) => {
            event.stopPropagation();
            dropdown.classList.toggle("open");

            if (dropdown === dropdown6) dropdown4.classList.remove("open");
            if (dropdown === dropdown4) dropdown6.classList.remove("open");
        });
    }

    setupDropdown(dropdown6);
    setupDropdown(dropdown4);

    window.addEventListener("click", () => {
        dropdown6.classList.remove("open");
        dropdown4.classList.remove("open");
    });

    document.querySelectorAll(".dropdown-item").forEach(item => {
        item.addEventListener("click", (event) => {
            const shape = event.target.getAttribute("data-shape");
            changeAndSetupShape(shape);
        });
    });

    toFrame5Buttons.forEach(button => {
        button.addEventListener("click", () => {
            switchFrame("frame5");
            currentScene.projection = projectionMethodAxes.value;
            currentScene.mesh = null;
            currentScene.dimensions = {x: 6, y: 6, z: 6};
            renderScene();
            showToast("Kéo chuột để xoay hệ trục Oxyz, lăn chuột để zoom.");
        });
    });

    toFrame6Btn.addEventListener("click", () => {
        switchFrame("frame6");
    });

    drawAxesBtn.addEventListener("click", () => {
        currentScene.projection = projectionMethodAxes.value;
        currentScene.mesh = null;
        currentScene.dimensions = {x: 6, y: 6, z: 6};
        renderScene();
    });

    projectionMethodAxes.addEventListener("change", () => {
        currentScene.projection = projectionMethodAxes.value;
        renderScene();
    });

    projectionMethod.addEventListener("change", () => {
        if (currentScene.mesh) {
            currentScene.projection = projectionMethod.value;
            renderScene();
        }
    });

    document.querySelectorAll(".draw-btn").forEach(button => {
        button.addEventListener("click", () => {
            if (document.getElementById("frame6").classList.contains("active")) {
                changeAndSetupShape(currentShape);
            }
            drawCurrentShape();
        });
    });

    document.querySelectorAll(".clear-btn").forEach(button => {
        button.addEventListener("click", () => {
            currentScene.mesh = null;
            currentScene.dimensions = {x: 6, y: 6, z: 6};
            renderScene();
            showToast("Đã xóa hình vẽ.");
        });
    });

    function changeAndSetupShape(shape) {
        currentShape = shape;

        const shapeText = shapeNames[shape] || "Hình Hộp Chữ Nhật";
        selectedShapeTitle.querySelector("span").innerText = shapeText;
        questionBox.innerText = shapeText.replace("Hình ", "");

        if (shape === "cuboid") {
            originLabel.innerText = "Nhập tọa độ đỉnh dưới - trái - trước";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="length" placeholder="Chiều dài" min="0" value="4">
                <input type="number" class="input-dimension" data-param="width" placeholder="Chiều rộng / chiều sâu" min="0" value="3">
                <input type="number" class="input-dimension" data-param="height" placeholder="Chiều cao" min="0" value="3">
            `;
        } else if (shape === "cube") {
            originLabel.innerText = "Nhập tọa độ đỉnh dưới - trái - trước";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="size" placeholder="Cạnh lập phương" min="0" value="3">
            `;
        } else if (shape === "cylinder") {
            originLabel.innerText = "Nhập tọa độ tâm đáy dưới";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="radius" placeholder="Bán kính đáy" min="0" value="2">
                <input type="number" class="input-dimension" data-param="height" placeholder="Chiều cao" min="0" value="4">
                <input type="number" class="input-dimension" data-param="segments" placeholder="Số đoạn chia" min="12" value="36">
            `;
        } else if (shape === "sphere") {
            originLabel.innerText = "Nhập tọa độ tâm hình cầu";
            dynamicInputs.innerHTML = `
                <input type="number" class="input-dimension" data-param="radius" placeholder="Bán kính" min="0" value="2">
                <input type="number" class="input-dimension" data-param="segments" placeholder="Số đoạn chia" min="12" value="24">
            `;
        }

        dynamicInputs.querySelectorAll("input").forEach(input => preventNonNumericInputs(input));
        switchFrame("frame4");
    }

    function getNumber(id, fallback = 0) {
        const value = document.getElementById(id).value;
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : fallback;
    }

    function collectParams() {
        const params = {};

        dynamicInputs.querySelectorAll("[data-param]").forEach(input => {
            params[input.dataset.param] = input.value;
        });

        return params;
    }

    async function drawCurrentShape() {
        const payload = {
            shape: currentShape,
            projection: projectionMethod.value,
            origin: {
                x: getNumber("coordX"),
                y: getNumber("coordY"),
                z: getNumber("coordZ"),
            },
            params: collectParams(),
        };

        try {
            const response = await fetch("/api/draw", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload),
            });

            const data = await response.json();

            if (!response.ok || !data.ok) {
                throw new Error(data.error || "Không thể vẽ hình.");
            }

            currentScene = {
                projection: data.projection,
                mesh: data.mesh,
                dimensions: data.dimensions,
            };

            renderScene();
            showToast(`Đã vẽ ${shapeNames[currentShape]}. Kéo chuột để xoay, lăn chuột để zoom.`);
        } catch (error) {
            showToast(error.message, true);
        }
    }

    function renderScene() {
        clearCanvas();

        const rect = canvas.getBoundingClientRect();
        const dimensions = currentScene.dimensions || {x: 6, y: 6, z: 6};
        const projection = currentScene.projection || "cabinet";

        const axisData = createAxisData(dimensions);
        const rotatedAxisPoints = axisData.points.map(rotatePoint);
        const projectedAxisPoints = rotatedAxisPoints.map(p => projectPoint(p, projection));

        let projectedMeshPoints = [];
        let rotatedMeshPoints = [];

        if (currentScene.mesh && currentScene.mesh.vertices) {
            rotatedMeshPoints = currentScene.mesh.vertices.map(rotatePoint);
            projectedMeshPoints = rotatedMeshPoints.map(p => projectPoint(p, projection));
        }

        const allProjectedPoints = [
            ...projectedAxisPoints,
            ...projectedMeshPoints,
            ...axisData.tickPoints.map(point => projectPoint(rotatePoint(point), projection)),
        ];

        const transform = createScreenTransform(allProjectedPoints, rect.width, rect.height, zoomScale);

        drawAxes(axisData, projection, transform);

        if (currentScene.mesh) {
            drawMeshWithHiddenLines(currentScene.mesh, rotatedMeshPoints, projectedMeshPoints, transform);
        }
    }

    function createAxisData(dimensions) {
        const maxDim = Math.max(
            Number(dimensions.x) || 0,
            Number(dimensions.y) || 0,
            Number(dimensions.z) || 0,
            6
        );

        const axisLength = maxDim + 1;

        const points = [
            {x: 0, y: 0, z: 0},
            {x: axisLength, y: 0, z: 0},
            {x: 0, y: axisLength, z: 0},
            {x: 0, y: 0, z: axisLength},
        ];

        const xTicks = tickValues(Number(dimensions.x) || 6).map(value => ({axis: "x", value, point: {x: value, y: 0, z: 0}}));
        const yTicks = tickValues(Number(dimensions.y) || 6).map(value => ({axis: "y", value, point: {x: 0, y: value, z: 0}}));
        const zTicks = tickValues(Number(dimensions.z) || 6).map(value => ({axis: "z", value, point: {x: 0, y: 0, z: value}}));

        const ticks = [...xTicks, ...yTicks, ...zTicks];

        return {
            points,
            ticks,
            tickPoints: ticks.map(tick => tick.point),
        };
    }

    function tickValues(maxValue) {
        if (!Number.isFinite(maxValue) || maxValue <= 0) return [];

        const values = [];
        const maxTicks = 12;
        let step = 1;

        if (maxValue > maxTicks) {
            step = Math.ceil(maxValue / maxTicks);
        }

        for (let value = step; value <= Math.floor(maxValue); value += step) {
            values.push(value);
        }

        const rounded = Number(maxValue.toFixed(2));
        const last = values.length ? values[values.length - 1] : 0;

        if (Math.abs(rounded - last) > 0.001) {
            values.push(rounded);
        }

        return values;
    }

    function drawAxes(axisData, projection, transform) {
        const projected = axisData.points.map(point => projectPoint(rotatePoint(point), projection));

        drawArrow(projected[0], projected[1], transform, "X");
        drawArrow(projected[0], projected[2], transform, "Y");
        drawArrow(projected[0], projected[3], transform, "Z");

        const origin = transform(projected[0]);
        ctx.font = "bold 16px Courier New";
        ctx.fillStyle = "#1e1e1e";
        ctx.fillText("O", origin.x - 18, origin.y + 18);

        axisData.ticks.forEach(tick => {
            drawAxisTick(tick, projection, transform);
        });
    }

    function drawAxisTick(tick, projection, transform) {
        const originProjected = projectPoint(rotatePoint({x: 0, y: 0, z: 0}), projection);
        const tickProjected = projectPoint(rotatePoint(tick.point), projection);

        const originScreen = transform(originProjected);
        const tickScreen = transform(tickProjected);

        const vx = tickScreen.x - originScreen.x;
        const vy = tickScreen.y - originScreen.y;
        const length = Math.hypot(vx, vy);

        if (length < 1) return;

        const nx = -vy / length;
        const ny = vx / length;
        const tickSize = 6;

        ctx.setLineDash([]);
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#1e1e1e";
        ctx.beginPath();
        ctx.moveTo(tickScreen.x - nx * tickSize, tickScreen.y - ny * tickSize);
        ctx.lineTo(tickScreen.x + nx * tickSize, tickScreen.y + ny * tickSize);
        ctx.stroke();

        ctx.font = "bold 12px Courier New";
        ctx.fillStyle = "#1e1e1e";

        const label = Number.isInteger(tick.value) ? String(tick.value) : tick.value.toFixed(2);
        ctx.fillText(label, tickScreen.x + nx * 10 + 2, tickScreen.y + ny * 10 - 2);
    }

    function drawMeshWithHiddenLines(mesh, rotatedVertices, projectedVertices, transform) {
        const edgeFaces = buildEdgeFaces(mesh.faces || []);
        const visibleFaces = (mesh.faces || []).map(face => isFaceVisible(face, rotatedVertices));

        const hiddenEdges = [];
        const visibleEdges = [];

        (mesh.edges || []).forEach(edge => {
            const key = edgeKey(edge[0], edge[1]);
            const faces = edgeFaces.get(key) || [];

            let isVisible = true;

            if (faces.length > 0) {
                isVisible = faces.some(faceIndex => visibleFaces[faceIndex]);
            }

            if (isVisible) {
                visibleEdges.push(edge);
            } else {
                hiddenEdges.push(edge);
            }
        });

        // Vẽ nét khuất trước, sau đó vẽ nét thấy đè lên trên.
        hiddenEdges.forEach(edge => {
            drawLine(projectedVertices[edge[0]], projectedVertices[edge[1]], transform, {
                width: 2,
                dashed: true,
                alpha: 0.75,
            });
        });

        visibleEdges.forEach(edge => {
            drawLine(projectedVertices[edge[0]], projectedVertices[edge[1]], transform, {
                width: 2.4,
                dashed: false,
                alpha: 1,
            });
        });
    }

    function buildEdgeFaces(faces) {
        const map = new Map();

        faces.forEach((face, faceIndex) => {
            for (let i = 0; i < face.length; i++) {
                const a = face[i];
                const b = face[(i + 1) % face.length];
                const key = edgeKey(a, b);

                if (!map.has(key)) {
                    map.set(key, []);
                }

                map.get(key).push(faceIndex);
            }
        });

        return map;
    }

    function isFaceVisible(face, vertices) {
        const normal = faceNormal(face, vertices);
        if (!normal) return false;

        // Mặt có pháp tuyến cùng hướng nhìn được xem là mặt trước.
        // Bản trước dùng dấu ngược nên một số cạnh mặt trước bị vẽ nét đứt.
        return dot3(normal, VIEW_DIR) > 0.0001;
    }

    function faceNormal(face, vertices) {
        if (!face || face.length < 3) return null;

        const p0 = vertices[face[0]];

        for (let i = 1; i < face.length - 1; i++) {
            const p1 = vertices[face[i]];
            const p2 = vertices[face[i + 1]];

            const u = subtract3(p1, p0);
            const v = subtract3(p2, p0);
            const n = cross3(u, v);
            const length = Math.hypot(n.x, n.y, n.z);

            if (length > 0.000001) {
                return {
                    x: n.x / length,
                    y: n.y / length,
                    z: n.z / length,
                };
            }
        }

        return null;
    }

    function drawLine(a, b, transform, options = {}) {
        const p1 = transform(a);
        const p2 = transform(b);

        ctx.save();
        ctx.globalAlpha = options.alpha ?? 1;
        ctx.beginPath();
        ctx.lineWidth = options.width || 2;
        ctx.strokeStyle = "#1e1e1e";

        if (options.dashed) {
            ctx.setLineDash([8, 6]);
        } else {
            ctx.setLineDash([]);
        }

        ctx.moveTo(Math.round(p1.x), Math.round(p1.y));
        ctx.lineTo(Math.round(p2.x), Math.round(p2.y));
        ctx.stroke();
        ctx.restore();
    }

    function drawArrow(a, b, transform, label) {
        const p1 = transform(a);
        const p2 = transform(b);

        ctx.setLineDash([]);
        ctx.lineWidth = 3;
        ctx.strokeStyle = "#1e1e1e";
        ctx.beginPath();
        ctx.moveTo(Math.round(p1.x), Math.round(p1.y));
        ctx.lineTo(Math.round(p2.x), Math.round(p2.y));
        ctx.stroke();

        const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
        const headLength = 13;

        ctx.beginPath();
        ctx.moveTo(p2.x, p2.y);
        ctx.lineTo(
            p2.x - headLength * Math.cos(angle - Math.PI / 6),
            p2.y - headLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            p2.x - headLength * Math.cos(angle + Math.PI / 6),
            p2.y - headLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = "#1e1e1e";
        ctx.fill();

        ctx.font = "bold 18px Courier New";
        ctx.fillText(label, p2.x + 12, p2.y - 8);
    }

    function clearCanvas() {
        const rect = canvas.getBoundingClientRect();
        ctx.clearRect(0, 0, rect.width, rect.height);
    }

    function createScreenTransform(points, width, height, zoom = 1.0) {
        const padding = 78;

        if (!points.length) {
            return () => ({x: width / 2, y: height / 2});
        }

        let minX = Math.min(...points.map(p => p.x));
        let maxX = Math.max(...points.map(p => p.x));
        let minY = Math.min(...points.map(p => p.y));
        let maxY = Math.max(...points.map(p => p.y));

        if (Math.abs(maxX - minX) < 0.001) {
            minX -= 1;
            maxX += 1;
        }

        if (Math.abs(maxY - minY) < 0.001) {
            minY -= 1;
            maxY += 1;
        }

        const sceneWidth = maxX - minX;
        const sceneHeight = maxY - minY;
        const scaleX = (width - padding * 2) / sceneWidth;
        const scaleY = (height - padding * 2) / sceneHeight;
        const scale = Math.max(8, Math.min(scaleX, scaleY)) * zoom;

        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        return function transform(point) {
            return {
                x: width / 2 + (point.x - centerX) * scale,
                y: height / 2 - (point.y - centerY) * scale,
            };
        };
    }

    function projectPoint(point, method) {
        const factor = method === "cavalier" ? 1 : 0.5;

        return {
            x: point.x + factor * point.z * Math.cos(DEG45),
            y: point.y + factor * point.z * Math.sin(DEG45),
        };
    }

    function rotatePoint(point) {
        // Xoay quanh trục Y.
        const cy = Math.cos(rotationY);
        const sy = Math.sin(rotationY);

        const x1 = point.x * cy + point.z * sy;
        const y1 = point.y;
        const z1 = -point.x * sy + point.z * cy;

        // Xoay quanh trục X.
        const cx = Math.cos(rotationX);
        const sx = Math.sin(rotationX);

        return {
            x: x1,
            y: y1 * cx - z1 * sx,
            z: y1 * sx + z1 * cx,
        };
    }

    function edgeKey(a, b) {
        return a < b ? `${a}-${b}` : `${b}-${a}`;
    }

    function subtract3(a, b) {
        return {
            x: a.x - b.x,
            y: a.y - b.y,
            z: a.z - b.z,
        };
    }

    function cross3(a, b) {
        return {
            x: a.y * b.z - a.z * b.y,
            y: a.z * b.x - a.x * b.z,
            z: a.x * b.y - a.y * b.x,
        };
    }

    function dot3(a, b) {
        return a.x * b.x + a.y * b.y + a.z * b.z;
    }

    function normalize3(v) {
        const length = Math.hypot(v.x, v.y, v.z) || 1;
        return {
            x: v.x / length,
            y: v.y / length,
            z: v.z / length,
        };
    }

    function preventNonNumericInputs(inputElement) {
        inputElement.addEventListener("keydown", (event) => {
            if (["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab", ".", ",", "-"].includes(event.key)) {
                return;
            }

            if (isNaN(Number(event.key))) {
                event.preventDefault();
            }
        });
    }

    function showToast(message, isError = false) {
        toast.innerText = message;
        toast.style.display = "block";
        toast.style.background = isError ? "rgba(255, 220, 220, 0.97)" : "rgba(255, 255, 255, 0.95)";

        clearTimeout(showToast.timer);
        showToast.timer = setTimeout(() => {
            toast.style.display = "none";
        }, 3000);
    }

    document.querySelectorAll('input[type="number"]').forEach(input => preventNonNumericInputs(input));

    changeAndSetupShape("cuboid");
    switchFrame("frame6");
    resizeCanvas();
    showToast("Kéo chuột để xoay, lăn chuột để phóng to / thu nhỏ.");
});
