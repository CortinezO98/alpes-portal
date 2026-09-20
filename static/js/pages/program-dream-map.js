document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.querySelector("[data-dream-map-visual]");
    const dataElement = document.getElementById("dream-map-graph-data");
    const detail = document.querySelector("[data-dream-map-detail]");
    if (!canvas || !dataElement || !detail) return;

    let nodes = [];
    try {
        nodes = JSON.parse(dataElement.textContent || "[]");
    } catch {
        return;
    }
    if (!nodes.length) return;

    const stage = canvas.querySelector(".dream-mental-stage");
    const svg = canvas.querySelector(".dream-mental-links");
    const nodeLayer = canvas.querySelector(".dream-mental-nodes");
    if (!stage || !svg || !nodeLayer) return;

    const byId = new Map(nodes.map(node => [String(node.id), node]));
    const depthMemo = new Map();
    const depthOf = node => {
        const key = String(node.id);
        if (depthMemo.has(key)) return depthMemo.get(key);
        if (!node.parent_id || !byId.has(String(node.parent_id))) {
            depthMemo.set(key, 1);
            return 1;
        }
        const depth = Math.min(depthOf(byId.get(String(node.parent_id))) + 1, 6);
        depthMemo.set(key, depth);
        return depth;
    };

    const groups = new Map();
    nodes.forEach(node => {
        const depth = depthOf(node);
        if (!groups.has(depth)) groups.set(depth, []);
        groups.get(depth).push(node);
    });

    const maxDepth = Math.max(...groups.keys());
    const maxRows = Math.max(...Array.from(groups.values(), group => group.length));
    const columnWidth = 260;
    const rowHeight = 132;
    const stageWidth = Math.max(900, 170 + maxDepth * columnWidth + 220);
    const stageHeight = Math.max(520, 100 + maxRows * rowHeight);
    stage.style.width = `${stageWidth}px`;
    stage.style.height = `${stageHeight}px`;
    svg.setAttribute("viewBox", `0 0 ${stageWidth} ${stageHeight}`);
    svg.setAttribute("width", stageWidth);
    svg.setAttribute("height", stageHeight);

    const positions = new Map();
    positions.set("root", {x: 32, y: stageHeight / 2 - 35, w: 150, h: 70});

    groups.forEach((group, depth) => {
        const totalHeight = (group.length - 1) * rowHeight;
        const startY = stageHeight / 2 - totalHeight / 2 - 35;
        group.forEach((node, index) => {
            positions.set(String(node.id), {
                x: 205 + (depth - 1) * columnWidth,
                y: startY + index * rowHeight,
                w: 210,
                h: 78,
            });
        });
    });

    const svgNS = "http://www.w3.org/2000/svg";
    const makePath = (source, target) => {
        const path = document.createElementNS(svgNS, "path");
        const x1 = source.x + source.w;
        const y1 = source.y + source.h / 2;
        const x2 = target.x;
        const y2 = target.y + target.h / 2;
        const mid = (x1 + x2) / 2;
        path.setAttribute("d", `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`);
        path.setAttribute("class", "dream-mental-link");
        svg.appendChild(path);
    };

    nodes.forEach(node => {
        const target = positions.get(String(node.id));
        const source = node.parent_id
            ? positions.get(String(node.parent_id))
            : positions.get("root");
        if (source && target) makePath(source, target);
    });

    const root = document.createElement("div");
    root.className = "dream-mental-root";
    root.style.left = `${positions.get("root").x}px`;
    root.style.top = `${positions.get("root").y}px`;
    root.innerHTML = '<i class="bi bi-compass"></i><strong>Mi nueva etapa</strong>';
    nodeLayer.appendChild(root);

    const clearSelection = () => {
        nodeLayer.querySelectorAll(".dream-mental-node.is-selected").forEach(el => {
            el.classList.remove("is-selected");
        });
    };

    const addTextRow = (container, label, value) => {
        if (!value) return;
        const row = document.createElement("div");
        row.className = "dream-detail-row";
        const term = document.createElement("span");
        term.textContent = label;
        const val = document.createElement("strong");
        val.textContent = value;
        row.append(term, val);
        container.appendChild(row);
    };

    const renderDetail = node => {
        detail.innerHTML = "";

        const header = document.createElement("div");
        header.className = "dream-detail-header";
        const badge = document.createElement("span");
        badge.className = `dream-detail-type dream-detail-type-${String(node.type).toLowerCase()}`;
        badge.textContent = node.type_label;
        const title = document.createElement("h3");
        title.textContent = node.title;
        header.append(badge, title);
        detail.appendChild(header);

        if (node.description) {
            const description = document.createElement("p");
            description.className = "dream-detail-description";
            description.textContent = node.description;
            detail.appendChild(description);
        }

        const meta = document.createElement("div");
        meta.className = "dream-detail-meta";
        addTextRow(meta, "Prioridad", node.priority_label);
        addTextRow(meta, "Fecha objetivo", node.target_date || "Sin fecha");
        const parent = node.parent_id ? byId.get(String(node.parent_id)) : null;
        addTextRow(meta, "Relacionado con", parent ? parent.title : "Mi nueva etapa");
        detail.appendChild(meta);

        const actionsTitle = document.createElement("div");
        actionsTitle.className = "dream-detail-section-title";
        actionsTitle.innerHTML = '<i class="bi bi-list-check"></i><strong>Plan de acción relacionado</strong>';
        detail.appendChild(actionsTitle);

        const goals = node.goals || [];
        if (!goals.length) {
            const empty = document.createElement("div");
            empty.className = "dream-detail-empty-actions";
            empty.innerHTML = '<i class="bi bi-arrow-right-circle"></i><span>Este elemento aún no tiene acciones vinculadas en el Plan de acción.</span>';
            detail.appendChild(empty);
            return;
        }

        goals.forEach(goal => {
            const goalCard = document.createElement("article");
            goalCard.className = "dream-detail-goal";
            const goalTitle = document.createElement("h4");
            goalTitle.textContent = goal.title;
            goalCard.appendChild(goalTitle);
            if (goal.description) {
                const p = document.createElement("p");
                p.textContent = goal.description;
                goalCard.appendChild(p);
            }
            if (goal.target_date) addTextRow(goalCard, "Fecha meta", goal.target_date);

            const items = goal.items || [];
            if (!items.length) {
                const empty = document.createElement("small");
                empty.textContent = "Meta creada, todavía sin acciones.";
                goalCard.appendChild(empty);
            } else {
                items.forEach(item => {
                    const itemEl = document.createElement("div");
                    itemEl.className = "dream-detail-action";
                    const top = document.createElement("div");
                    const action = document.createElement("strong");
                    action.textContent = item.action;
                    const status = document.createElement("span");
                    status.className = `action-status action-status-${String(item.status).toLowerCase()}`;
                    status.textContent = item.status_label;
                    top.append(action, status);
                    itemEl.appendChild(top);
                    addTextRow(itemEl, "Indicador", item.indicator);
                    addTextRow(itemEl, "Responsable", item.responsible);
                    addTextRow(itemEl, "Fecha", item.due_date);
                    if (item.consultant_appreciation) {
                        addTextRow(itemEl, "Apreciación", item.consultant_appreciation);
                    }
                    goalCard.appendChild(itemEl);
                });
            }
            detail.appendChild(goalCard);
        });
    };

    nodes.forEach(node => {
        const position = positions.get(String(node.id));
        const button = document.createElement("button");
        button.type = "button";
        button.className = `dream-mental-node dream-mental-node-${String(node.type).toLowerCase()}`;
        button.style.left = `${position.x}px`;
        button.style.top = `${position.y}px`;
        button.dataset.nodeId = node.id;

        const type = document.createElement("span");
        type.className = "dream-mental-node-type";
        type.textContent = node.type_label;
        const title = document.createElement("strong");
        title.textContent = node.title;
        const meta = document.createElement("small");
        meta.textContent = node.goals && node.goals.length
            ? `${node.goals.length} meta(s) vinculada(s)`
            : node.priority_label;
        button.append(type, title, meta);

        button.addEventListener("click", () => {
            clearSelection();
            button.classList.add("is-selected");
            renderDetail(node);
        });
        nodeLayer.appendChild(button);
    });
});
