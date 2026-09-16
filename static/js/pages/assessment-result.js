(() => {
    const canvas = document.getElementById("alpes-radar-chart");
    const dimensionsNode = document.getElementById("alpes-radar-dimensions");
    const fallback = document.getElementById("radar-fallback");

    const details = Array.from(document.querySelectorAll(".dimension-card"));
    details.forEach((detail) => {
        detail.addEventListener("toggle", () => {
            if (!detail.open) {
                return;
            }
            details.forEach((other) => {
                if (other !== detail) {
                    other.open = false;
                }
            });
        });
    });

    if (!canvas || !dimensionsNode) {
        return;
    }

    const showFallback = () => {
        canvas.hidden = true;
        if (fallback) {
            fallback.hidden = false;
        }
    };

    if (typeof window.Chart === "undefined") {
        showFallback();
        return;
    }

    try {
        const dimensions = JSON.parse(dimensionsNode.textContent);
        const labels = dimensions.map((dimension) => dimension.label);
        const scores = dimensions.map((dimension) => dimension.score);
        const colors = dimensions.map((dimension) => dimension.color);
        const rootStyles = getComputedStyle(document.documentElement);
        const text = rootStyles.getPropertyValue("--color-text").trim() || "#29332d";
        const muted = rootStyles.getPropertyValue("--color-text-muted").trim() || "#66736b";
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        const wrapLabel = (label) => {
            const words = label.split(" ");
            const lines = [];
            let line = "";

            words.forEach((word) => {
                const candidate = line ? `${line} ${word}` : word;
                if (candidate.length > 18 && line) {
                    lines.push(line);
                    line = word;
                } else {
                    line = candidate;
                }
            });

            if (line) {
                lines.push(line);
            }
            return lines;
        };

        const semaphorePolygon = {
            id: "semaphorePolygon",
            afterDatasetsDraw(chart) {
                const meta = chart.getDatasetMeta(0);
                if (!meta?.data?.length) {
                    return;
                }

                const { ctx } = chart;
                ctx.save();
                ctx.lineWidth = 3;
                ctx.lineCap = "round";
                ctx.lineJoin = "round";

                meta.data.forEach((point, index) => {
                    const next = meta.data[(index + 1) % meta.data.length];
                    ctx.beginPath();
                    ctx.moveTo(point.x, point.y);
                    ctx.lineTo(next.x, next.y);
                    ctx.strokeStyle = colors[index];
                    ctx.stroke();
                });

                meta.data.forEach((point, index) => {
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
                    ctx.fillStyle = colors[index];
                    ctx.fill();
                    ctx.lineWidth = 2;
                    ctx.strokeStyle = "#ffffff";
                    ctx.stroke();
                });
                ctx.restore();
            },
        };

        new window.Chart(canvas, {
            type: "radar",
            data: {
                labels: labels.map(wrapLabel),
                datasets: [
                    {
                        label: "Valoración ALPES",
                        data: scores,
                        borderColor: "rgba(0, 0, 0, 0)",
                        backgroundColor: "rgba(88, 104, 47, 0.12)",
                        pointRadius: 0,
                        pointHoverRadius: 7,
                        pointHoverBackgroundColor: colors,
                        pointHoverBorderColor: "#ffffff",
                        borderWidth: 0,
                    },
                ],
            },
            plugins: [semaphorePolygon],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: reduceMotion ? false : { duration: 650 },
                interaction: {
                    mode: "nearest",
                    intersect: false,
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const dimension = dimensions[context.dataIndex];
                                return `${context.formattedValue} / 10 · ${dimension.band}`;
                            },
                        },
                    },
                },
                scales: {
                    r: {
                        min: 0,
                        max: 10,
                        beginAtZero: true,
                        ticks: {
                            stepSize: 2,
                            color: muted,
                            backdropColor: "transparent",
                            showLabelBackdrop: false,
                            font: { size: 10 },
                        },
                        angleLines: { color: "rgba(102, 115, 107, 0.18)" },
                        grid: { color: "rgba(102, 115, 107, 0.18)" },
                        pointLabels: {
                            color: text,
                            padding: 14,
                            font: { size: 11, weight: "600" },
                        },
                    },
                },
            },
        });
    } catch (error) {
        console.error("No fue posible renderizar la Rueda ALPES.", error);
        showFallback();
    }
})();
