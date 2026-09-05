// FarmTwin Chart.js Telemetry Controller
let moistureChartInstance = null;

function renderTelemetryChart(dailyResults, fcPct = 28.0, wpPct = 14.0) {
    const ctx = document.getElementById('telemetry-chart');
    if (!ctx) return;

    const labels = dailyResults.map(d => {
        const parts = d.date.split('-');
        return `${parts[1]}/${parts[2]}`;
    });

    const moistureData = dailyResults.map(d => d.soil_moisture_pct);
    const rainData = dailyResults.map(d => d.precipitation_mm);
    const etcData = dailyResults.map(d => d.etc_mm);

    if (moistureChartInstance) {
        moistureChartInstance.destroy();
    }

    moistureChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Soil Moisture (%)',
                    data: moistureData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Crop Water Use ETc (mm)',
                    data: etcData,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.05)',
                    borderDash: [4, 4],
                    borderWidth: 2,
                    pointRadius: 2,
                    yAxisID: 'y1'
                },
                {
                    label: 'Rainfall (mm)',
                    data: rainData,
                    type: 'bar',
                    backgroundColor: 'rgba(59, 130, 246, 0.65)',
                    borderRadius: 4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#94a3b8',
                        font: { size: 11, family: "'Plus Jakarta Sans', sans-serif" },
                        boxWidth: 12,
                        padding: 10
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 27, 0.95)',
                    titleColor: '#34d399',
                    bodyColor: '#f1f5f9',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#64748b', font: { size: 10 } }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Moisture (% vol)',
                        color: '#10b981',
                        font: { size: 10 }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { size: 10 } },
                    min: Math.max(0, Math.floor(wpPct * 0.7)),
                    max: Math.ceil(fcPct * 1.3)
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Water Depth (mm)',
                        color: '#38bdf8',
                        font: { size: 10 }
                    },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#64748b', font: { size: 10 } },
                    min: 0
                }
            }
        }
    });
}
