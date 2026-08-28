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
        const text = styles.getPropertyValue("--color-text").trim() || "#29332d";
        const muted = styles.getPropertyValue("--color-text-muted").trim() || "#66736b";
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        new window.Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Promedio",
                    data: scores,
                    backgroundColor: "rgba(145, 170, 67, 0.30)",
                    borderColor: primary,
                    borderWidth: 1.5,
                    borderRadius: 7,
                    borderSkipped: false,
                    maxBarThickness: 34,
                }],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                animation: reduceMotion ? false : { duration: 500 },
                layout: {
                    padding: {
                        right: 12,
                    },
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.formattedValue} / 10`,
                        },
                    },
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        min: 0,
                        max: 10,
                        ticks: {
                            stepSize: 2,
                            color: muted,
                        },
                        grid: {
                            color: "rgba(102, 115, 107, 0.12)",
                        },
                    },
                    y: {
                        ticks: {
                            color: text,
                            autoSkip: false,
                            font: {
                                size: 11,
                                weight: "600",
                            },
                        },
                        grid: {
                            display: false,
                        },
                    },
                },
            },
        });
    } catch (error) {
        console.error("No fue posible renderizar la analítica ALPES.", error);
    }
})();
