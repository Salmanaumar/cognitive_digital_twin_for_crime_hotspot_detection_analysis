// Chart.js Visualizations for Cognitive Digital Twin

let hourlyChart = null;
let dayChart = null;
let categoryChart = null;
let modelChart = null;
let smoteChart = null;
let areaRankChart = null;
let cachedChartData = null;

const PLUM_MAIN = '#3B103F';
const PLUM_LIGHT = '#54185A';
const PLUM_ACCENT = '#7C3AED';
const ROSE_MAIN = '#D83B6F';
const ROSE_ACCENT = '#E11D48';
const ROSE_LIGHT = '#F4B8CA';

async function loadAndInitCharts(targetKey = null) {
    try {
        const res = await fetch('/api/charts/data', { cache: 'no-store' });
        if (!res.ok) throw new Error("API returned " + res.status);
        const data = await res.json();
        if (data.status === 'SUCCESS') {
            cachedChartData = data;
            // Only build charts whose containers are currently visible, or targetKey
            ['hourly', 'areaRank', 'day', 'category', 'model', 'smote'].forEach(k => {
                const container = document.getElementById(`view-${k}-canvas`);
                if ((container && !container.classList.contains('d-none')) || k === targetKey) {
                    buildSpecificChart(k, data);
                }
            });
        }
    } catch (err) {
        console.warn("Could not load /api/charts/data:", err);
    }
}

function buildSpecificChart(key, data) {
    if (!data) return;
    if (key === 'hourly' && data.hourly) buildHourlyChart(data.hourly);
    if (key === 'areaRank' && data.area_rank) buildAreaRankChart(data.area_rank);
    if (key === 'day' && data.day_of_week) buildDayChart(data.day_of_week);
    if (key === 'category' && data.category) buildCategoryChart(data.category);
    if (key === 'model' && data.model_metrics) renderModelComparisonChart(data.model_metrics);
    if (key === 'smote' && data.smote) renderSmoteChart(data.smote);
}

// 1. Hourly Chart
function buildHourlyChart(hourlyList) {
    const ctxH = document.getElementById('hourlyChart');
    if (!ctxH || typeof Chart === 'undefined') return;
    if (hourlyChart) {
        hourlyChart.destroy();
        hourlyChart = null;
    }

    const labels = hourlyList.map(h => h.hour);
    const counts = hourlyList.map(h => h.count);
    const bgColors = hourlyList.map(h => h.is_peak ? ROSE_ACCENT : PLUM_LIGHT);

    hourlyChart = new Chart(ctxH.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Incidents Count',
                data: counts,
                backgroundColor: bgColors,
                borderRadius: 4,
                maxBarThickness: 28
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => (ctx.dataIndex >= 20 || ctx.dataIndex <= 2)
                            ? 'High-Risk Night Window (Surge)'
                            : 'Normal Daytime Activity'
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F1F5F9' }, title: { display: true, text: 'Incidents' } },
                x: { grid: { display: false } }
            }
        }
    });
}

// 2. Day of Week Chart
function buildDayChart(dayList) {
    const ctxD = document.getElementById('dayChart');
    if (!ctxD || typeof Chart === 'undefined') return;
    if (dayChart) {
        dayChart.destroy();
        dayChart = null;
    }

    const labels = dayList.map(d => d.day);
    const counts = dayList.map(d => d.count);
    const bgColors = dayList.map(d => d.is_weekend ? ROSE_MAIN : PLUM_MAIN);

    dayChart = new Chart(ctxD.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Incidents Count',
                data: counts,
                backgroundColor: bgColors,
                borderRadius: 5,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => (ctx.label === 'Saturday' || ctx.label === 'Sunday' || ctx.label === 'Friday')
                            ? 'Weekend Patrol Surge'
                            : 'Standard Cadence'
                    }
                }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F1F5F9' }, title: { display: true, text: 'Incidents' } },
                x: { grid: { display: false } }
            }
        }
    });
}

// 3. Category Doughnut Chart
function buildCategoryChart(categoryList) {
    const ctxC = document.getElementById('categoryChart');
    if (!ctxC || typeof Chart === 'undefined') return;
    if (categoryChart) {
        categoryChart.destroy();
        categoryChart = null;
    }

    const labels = categoryList.map(c => c.category);
    const counts = categoryList.map(c => c.count);
    const palette = ['#3B103F', '#D83B6F', '#54185A', '#E11D48', '#F59E0B', '#10B981', '#7C3AED', '#64748B'];

    categoryChart = new Chart(ctxC.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: palette.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#FFFFFF'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            cutout: '55%',
            plugins: {
                legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
            }
        }
    });
}

// 4. Area Ranking Horizontal Bar Chart
function buildAreaRankChart(areaList) {
    const ctxA = document.getElementById('areaRankChart');
    if (!ctxA || typeof Chart === 'undefined') return;
    if (areaRankChart) {
        areaRankChart.destroy();
        areaRankChart = null;
    }

    const labels = areaList.map(a => a.area_name);
    const scores = areaList.map(a => a.risk_score);
    const bgColors = areaList.map(a => a.risk_level === 'High' ? '#E11D48' : (a.risk_level === 'Medium' ? '#F59E0B' : '#10B981'));

    areaRankChart = new Chart(ctxA.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Score (0 - 100)',
                data: scores,
                backgroundColor: bgColors,
                borderRadius: 4,
                maxBarThickness: 24
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 400 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: (ctx) => {
                            const item = areaList[ctx.dataIndex];
                            return item ? `Risk Level: ${item.risk_level} | Incidents: ${item.incident_count}` : '';
                        }
                    }
                }
            },
            scales: {
                x: { min: 0, max: 100, grid: { color: '#F1F5F9' }, title: { display: true, text: 'Risk Score (0 - 100)' } },
                y: { grid: { display: false } }
            }
        }
    });
}

// 5. Model Comparison Chart
function renderModelComparisonChart(metricsList) {
    const ctxM = document.getElementById('modelComparisonChart');
    if (!ctxM || !metricsList || metricsList.length === 0 || typeof Chart === 'undefined') return;

    const labels = metricsList.map(m => m.model_name.replace('Proposed ', '').replace(' Ensemble', ''));
    const accuracies = metricsList.map(m => m.accuracy);
    const precisions = metricsList.map(m => m.precision);
    const recalls = metricsList.map(m => m.recall);
    const f1s = metricsList.map(m => m.f1_score);
    const aucs = metricsList.map(m => m.roc_auc);

    if (modelChart) {
        modelChart.destroy();
        modelChart = null;
    }
    modelChart = new Chart(ctxM.getContext('2d'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Accuracy', data: accuracies, backgroundColor: '#3B103F' },
                { label: 'Precision', data: precisions, backgroundColor: '#54185A' },
                { label: 'Recall', data: recalls, backgroundColor: '#7C3AED' },
                { label: 'F1-Score', data: f1s, backgroundColor: '#D83B6F' },
                { label: 'ROC-AUC', data: aucs, backgroundColor: '#E11D48' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 60, max: 100, grid: { color: '#F1F5F9' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
            }
        }
    });
}

// 6. SMOTE Balancing Chart
function renderSmoteChart(smoteData) {
    const ctxS = document.getElementById('smoteChart');
    if (!ctxS || !smoteData || typeof Chart === 'undefined') return;

    const classes = ['Low', 'Medium', 'High'];
    const beforeCounts = classes.map(c => smoteData.before ? (smoteData.before[c] || 0) : 0);
    const afterCounts = classes.map(c => smoteData.after ? (smoteData.after[c] || 0) : 0);

    if (smoteChart) {
        smoteChart.destroy();
        smoteChart = null;
    }
    smoteChart = new Chart(ctxS.getContext('2d'), {
        type: 'bar',
        data: {
            labels: classes,
            datasets: [
                { label: 'Before Balancing (Raw Imbalance)', data: beforeCounts, backgroundColor: '#64748B', borderRadius: 4 },
                { label: 'After SMOTE Balancing (Equalized)', data: afterCounts, backgroundColor: ROSE_MAIN, borderRadius: 4 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: '#F1F5F9' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12 } }
            }
        }
    });
}

// Fallback compatibility wrapper
function initDashboardCharts(records, zones) {
    if (!cachedChartData) {
        loadAndInitCharts();
    }
}

// Interactive View Toggle Handler — Always rebuilds cleanly on visible canvas
window.ensureChartRendered = function(chartKey) {
    setTimeout(() => {
        if (cachedChartData) {
            buildSpecificChart(chartKey, cachedChartData);
        } else {
            loadAndInitCharts(chartKey);
        }
    }, 30);
};
