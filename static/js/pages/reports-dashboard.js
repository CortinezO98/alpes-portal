(() => {
    const canvas = document.getElementById("reports-dimension-chart");
    const labelsNode = document.getElementById("reports-chart-labels");
    const scoresNode = document.getElementById("reports-chart-scores");

    if (!canvas || !labelsNode || !scoresNode || typeof window.Chart === "undefined") {
        return;
    }

    try {
        const labels = JSON.parse(labelsNode.textContent);
        const scores = JSON.parse(scoresNode.textContent);
        const styles = getComputedStyle(document.documentElement);
        const primary = styles.getPropertyValue("--color-primary-700").trim() || "#58682f";
        const muted = styles.getPropertyValue("--color-text-muted").trim() || "#66736b";
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        new window.Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Promedio",
                    data: scores,
                    backgroundColor: "rgba(145, 170, 67, 0.34)",
                    borderColor: primary,
                    borderWidth: 1.5,
                    borderRadius: 6,
                    maxBarThickness: 46,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: reduceMotion ? false : { duration: 550 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.formattedValue} / 10`,
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 10,
                        ticks: { stepSize: 2, color: muted },
                        grid: { color: "rgba(102, 115, 107, 0.14)" },
                    },
                    x: {
                        ticks: {
                            color: muted,
                            maxRotation: 0,
                            autoSkip: false,
                            callback(value) {
                                const label = this.getLabelForValue(value);
                                return label.length > 18 ? `${label.slice(0, 18)}…` : label;
                            },
                        },
                        grid: { display: false },
                    },
                },
            },
        });
    } catch (error) {
        console.error("No fue posible renderizar la analítica ALPES.", error);
    }
})();
