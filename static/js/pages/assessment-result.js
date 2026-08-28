(() => {
    const canvas = document.getElementById("alpes-radar-chart");
    const labelsNode = document.getElementById("alpes-radar-labels");
    const scoresNode = document.getElementById("alpes-radar-scores");
    const fallback = document.getElementById("radar-fallback");

    if (!canvas || !labelsNode || !scoresNode) {
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
        const labels = JSON.parse(labelsNode.textContent);
        const scores = JSON.parse(scoresNode.textContent);
        const rootStyles = getComputedStyle(document.documentElement);
        const primary = rootStyles.getPropertyValue("--color-primary-700").trim() || "#58682f";
        const primarySoft = rootStyles.getPropertyValue("--color-primary-300").trim() || "#c8d690";
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

        new window.Chart(canvas, {
            type: "radar",
            data: {
                labels: labels.map(wrapLabel),
                datasets: [
                    {
                        label: "Valoración ALPES",
                        data: scores,
                        borderColor: primary,
                        backgroundColor: "rgba(145, 170, 67, 0.18)",
                        pointBackgroundColor: primary,
                        pointBorderColor: "#ffffff",
                        pointHoverBackgroundColor: primarySoft,
                        pointHoverBorderColor: primary,
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: reduceMotion ? false : { duration: 650 },
                interaction: {
                    mode: "nearest",
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.formattedValue} / 10`,
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
                        angleLines: {
                            color: "rgba(102, 115, 107, 0.18)",
                        },
                        grid: {
                            color: "rgba(102, 115, 107, 0.18)",
                        },
                        pointLabels: {
                            color: text,
                            padding: 14,
                            font: {
                                size: 11,
                                weight: "600",
                            },
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
