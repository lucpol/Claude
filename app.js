(() => {
    'use strict';

    // --- State ---
    let file1Data = null;
    let file2Data = null;
    let mergedData = null;
    let charts = {};
    let activeInterval = 60;

    // --- DOM refs ---
    const file1Input = document.getElementById('file1');
    const file2Input = document.getElementById('file2');
    const file1Info = document.getElementById('file1-info');
    const file2Info = document.getElementById('file2-info');
    const compareBtn = document.getElementById('compare-btn');
    const filtersSection = document.getElementById('filters-section');
    const summarySection = document.getElementById('summary-section');
    const chartsSection = document.getElementById('charts-section');
    const tablesSection = document.getElementById('tables-section');
    const diffSection = document.getElementById('diff-section');
    const statsSection = document.getElementById('stats-section');
    const applyFiltersBtn = document.getElementById('apply-filters-btn');
    const diffMetricSelect = document.getElementById('diff-metric');
    const smoothingInput = document.getElementById('smoothing');
    const smoothingValue = document.getElementById('smoothing-value');

    const METRIC_LABELS = {
        heart_rate: 'Heart Rate',
        power: 'Power',
        speed: 'Speed',
        cadence: 'Cadence',
        altitude: 'Altitude',
        temperature: 'Temperature',
    };
    const METRIC_UNITS = {
        heart_rate: 'bpm',
        power: 'W',
        speed: 'km/h',
        cadence: 'rpm',
        altitude: 'm',
        temperature: '\u00b0C',
    };
    const METRIC_COLORS = {
        heart_rate: '#f87171',
        power: '#fbbf24',
        speed: '#34d399',
        cadence: '#22d3ee',
        altitude: '#2dd4bf',
        temperature: '#fb923c',
    };

    // --- Events ---
    file1Input.addEventListener('change', (e) => loadFile(e, 1));
    file2Input.addEventListener('change', (e) => loadFile(e, 2));
    compareBtn.addEventListener('click', runComparison);
    applyFiltersBtn.addEventListener('click', runComparison);
    diffMetricSelect.addEventListener('change', updateDiffChart);

    smoothingInput.addEventListener('input', () => {
        smoothingValue.textContent = smoothingInput.value + 's';
    });

    // Metric chips toggle
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => chip.classList.toggle('active'));
    });

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeInterval = parseInt(tab.dataset.interval, 10);
            renderAveragedTable();
        });
    });

    // Drag-and-drop
    ['upload-box-1', 'upload-box-2'].forEach(id => {
        const box = document.getElementById(id);
        const fileNum = parseInt(box.dataset.file, 10);

        box.addEventListener('dragover', (e) => {
            e.preventDefault();
            box.classList.add('dragover');
        });
        box.addEventListener('dragleave', () => box.classList.remove('dragover'));
        box.addEventListener('drop', (e) => {
            e.preventDefault();
            box.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file, fileNum);
        });
    });

    // --- File loading ---
    function loadFile(event, num) {
        const file = event.target.files[0];
        if (file) handleFile(file, num);
    }

    function handleFile(file, num) {
        const infoEl = num === 1 ? file1Info : file2Info;
        const box = document.getElementById(`upload-box-${num}`);
        infoEl.innerHTML = '<span class="file-meta">Parsing...</span>';
        box.classList.remove('loaded');

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const result = FitParser.parse(e.target.result);
                if (num === 1) file1Data = result;
                else file2Data = result;

                const s = result.summary;
                const startStr = s.start_time ? s.start_time.toLocaleTimeString() : '?';
                const endStr = s.end_time ? s.end_time.toLocaleTimeString() : '?';
                const dur = s.duration_seconds ? formatDuration(s.duration_seconds) : '?';
                infoEl.innerHTML = `<span class="file-name">${file.name}</span><br><span class="file-meta">${result.records.length} pts &middot; ${startStr}\u2013${endStr} &middot; ${dur}</span>`;
                box.classList.add('loaded');
            } catch (err) {
                infoEl.innerHTML = `<span style="color:var(--red)">Error: ${err.message}</span>`;
                box.classList.remove('loaded');
            }
            compareBtn.disabled = !(file1Data && file2Data);
        };
        reader.readAsArrayBuffer(file);
    }

    // --- Time sync ---
    function timeKey(date) {
        const h = String(date.getHours()).padStart(2, '0');
        const m = String(date.getMinutes()).padStart(2, '0');
        const s = String(date.getSeconds()).padStart(2, '0');
        return `${h}:${m}:${s}`;
    }

    function buildTimeMap(records) {
        const map = new Map();
        for (const rec of records) {
            map.set(timeKey(rec.timestamp), rec);
        }
        return map;
    }

    function mergeByTimeOfDay(data1, data2, startFilter, endFilter) {
        const map1 = buildTimeMap(data1.records);
        const map2 = buildTimeMap(data2.records);
        const allKeys = new Set([...map1.keys(), ...map2.keys()]);
        const sortedKeys = [...allKeys].sort();

        const merged = [];
        for (const key of sortedKeys) {
            if (startFilter && key < startFilter) continue;
            if (endFilter && key > endFilter) continue;
            merged.push({
                time: key,
                file1: map1.get(key) || null,
                file2: map2.get(key) || null,
            });
        }
        return merged;
    }

    // --- Smoothing ---
    function smooth(values, windowSize) {
        if (windowSize <= 1) return values;
        const result = new Array(values.length);
        const half = Math.floor(windowSize / 2);
        for (let i = 0; i < values.length; i++) {
            let sum = 0, count = 0;
            for (let j = Math.max(0, i - half); j <= Math.min(values.length - 1, i + half); j++) {
                if (values[j] !== null && values[j] !== undefined) {
                    sum += values[j];
                    count++;
                }
            }
            result[i] = count > 0 ? sum / count : null;
        }
        return result;
    }

    // --- Get selected metrics ---
    function getSelectedMetrics() {
        return Array.from(document.querySelectorAll('.chip.active')).map(c => c.dataset.metric);
    }

    // --- Main comparison ---
    function runComparison() {
        if (!file1Data || !file2Data) return;

        const startFilter = document.getElementById('time-start').value || null;
        const endFilter = document.getElementById('time-end').value || null;
        const smoothingVal = parseInt(smoothingInput.value, 10) || 1;
        const selectedMetrics = getSelectedMetrics();

        mergedData = mergeByTimeOfDay(file1Data, file2Data, startFilter, endFilter);

        filtersSection.classList.remove('hidden');
        statsSection.classList.remove('hidden');
        summarySection.classList.remove('hidden');
        chartsSection.classList.remove('hidden');
        tablesSection.classList.remove('hidden');
        diffSection.classList.remove('hidden');

        if (!startFilter && mergedData.length > 0) {
            document.getElementById('time-start').value = mergedData[0].time;
        }
        if (!endFilter && mergedData.length > 0) {
            document.getElementById('time-end').value = mergedData[mergedData.length - 1].time;
        }

        renderStats(selectedMetrics);
        renderSummary(selectedMetrics);
        renderCharts(selectedMetrics, smoothingVal);
        renderAveragedTable();
        updateDiffChart();
    }

    // --- Stats cards ---
    function renderStats(metrics) {
        const grid = document.getElementById('stats-grid');
        let html = '';

        // Duration card
        const dur1 = file1Data.summary.duration_seconds;
        const dur2 = file2Data.summary.duration_seconds;
        html += statCard('Duration', formatDuration(dur1), formatDuration(dur2), dur2 - dur1, 's');

        // Points card
        html += statCard('Sync Points', mergedData.filter(m => m.file1).length.toString(), mergedData.filter(m => m.file2).length.toString(), null, '');

        for (const metric of metrics) {
            const s1 = file1Data.summary;
            const s2 = file2Data.summary;
            const avg1 = s1[`avg_${metric}`];
            const avg2 = s2[`avg_${metric}`];
            if (avg1 == null && avg2 == null) continue;
            const diff = (avg1 != null && avg2 != null) ? avg2 - avg1 : null;
            html += statCard(
                `Avg ${METRIC_LABELS[metric]}`,
                fmtVal(avg1),
                fmtVal(avg2),
                diff,
                METRIC_UNITS[metric]
            );
        }

        grid.innerHTML = html;
    }

    function statCard(label, val1, val2, diff, unit) {
        let diffHtml = '';
        if (diff != null) {
            const cls = diff >= 0 ? 'positive' : 'negative';
            const arrow = diff >= 0 ? '\u25B2' : '\u25BC';
            diffHtml = `<div class="stat-diff ${cls}">${arrow} ${diff >= 0 ? '+' : ''}${typeof diff === 'number' ? diff.toFixed(1) : diff} ${unit}</div>`;
        }
        return `<div class="stat-card">
            <div class="stat-label">${label}</div>
            <div class="stat-values">
                <span class="stat-val v1">${val1}</span>
                <span class="stat-vs">vs</span>
                <span class="stat-val v2">${val2}</span>
            </div>
            ${diffHtml}
        </div>`;
    }

    // --- Summary table ---
    function renderSummary(metrics) {
        const container = document.getElementById('summary-table-container');

        let html = `<table>
            <thead><tr>
                <th>Metric</th>
                <th>File 1 Avg</th>
                <th>File 2 Avg</th>
                <th>Diff</th>
                <th>File 1 Max</th>
                <th>File 2 Max</th>
                <th>File 1 Min</th>
                <th>File 2 Min</th>
            </tr></thead><tbody>`;

        for (const metric of metrics) {
            const s1 = file1Data.summary;
            const s2 = file2Data.summary;
            const avg1 = s1[`avg_${metric}`];
            const avg2 = s2[`avg_${metric}`];
            const max1 = s1[`max_${metric}`];
            const max2 = s2[`max_${metric}`];
            const min1 = s1[`min_${metric}`];
            const min2 = s2[`min_${metric}`];
            const diff = (avg1 != null && avg2 != null) ? avg2 - avg1 : null;
            const diffClass = diff != null ? (diff >= 0 ? 'diff-positive' : 'diff-negative') : '';
            const diffStr = diff != null ? `${diff >= 0 ? '+' : ''}${diff.toFixed(1)} ${METRIC_UNITS[metric]}` : '-';

            html += `<tr>
                <td>${METRIC_LABELS[metric]} (${METRIC_UNITS[metric]})</td>
                <td class="file1-val">${fmtVal(avg1)}</td>
                <td class="file2-val">${fmtVal(avg2)}</td>
                <td class="${diffClass}">${diffStr}</td>
                <td class="file1-val">${fmtVal(max1)}</td>
                <td class="file2-val">${fmtVal(max2)}</td>
                <td class="file1-val">${fmtVal(min1)}</td>
                <td class="file2-val">${fmtVal(min2)}</td>
            </tr>`;
        }

        html += '</tbody></table>';

        const dur1 = file1Data.summary.duration_seconds;
        const dur2 = file2Data.summary.duration_seconds;
        html += `<div class="summary-footer">
            <span>Duration: <strong class="file1-val">${formatDuration(dur1)}</strong> vs <strong class="file2-val">${formatDuration(dur2)}</strong></span>
            <span>Synchronized: <strong>${mergedData.length}</strong> time points</span>
            <span>File 1: <strong class="file1-val">${mergedData.filter(m => m.file1).length}</strong> pts</span>
            <span>File 2: <strong class="file2-val">${mergedData.filter(m => m.file2).length}</strong> pts</span>
        </div>`;

        container.innerHTML = html;
    }

    // --- Charts ---
    function renderCharts(metrics, smoothingVal) {
        const allMetrics = ['heart_rate', 'power', 'speed', 'cadence', 'altitude', 'temperature'];

        for (const metric of allMetrics) {
            const card = document.getElementById(`chart-${metric}-card`);
            if (!metrics.includes(metric)) {
                card.classList.add('hidden');
                if (charts[metric]) { charts[metric].destroy(); delete charts[metric]; }
                continue;
            }
            card.classList.remove('hidden');

            const labels = mergedData.map(m => m.time);
            let vals1 = mergedData.map(m => m.file1 ? (m.file1[metric] ?? null) : null);
            let vals2 = mergedData.map(m => m.file2 ? (m.file2[metric] ?? null) : null);
            vals1 = smooth(vals1, smoothingVal);
            vals2 = smooth(vals2, smoothingVal);

            const step = Math.max(1, Math.floor(labels.length / 80));
            const displayLabels = labels.map((l, i) => i % step === 0 ? l : '');

            if (charts[metric]) charts[metric].destroy();

            const ctx = document.getElementById(`chart-${metric}`).getContext('2d');

            // Gradient fill for file 1
            const grad1 = ctx.createLinearGradient(0, 0, 0, 280);
            grad1.addColorStop(0, 'rgba(129, 140, 248, 0.15)');
            grad1.addColorStop(1, 'rgba(129, 140, 248, 0)');

            const grad2 = ctx.createLinearGradient(0, 0, 0, 280);
            grad2.addColorStop(0, 'rgba(245, 158, 11, 0.1)');
            grad2.addColorStop(1, 'rgba(245, 158, 11, 0)');

            charts[metric] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: displayLabels,
                    datasets: [
                        {
                            label: 'File 1',
                            data: vals1,
                            borderColor: 'rgba(129, 140, 248, 0.9)',
                            backgroundColor: grad1,
                            borderWidth: 1.5,
                            pointRadius: 0,
                            fill: true,
                            tension: 0.2,
                            spanGaps: true,
                        },
                        {
                            label: 'File 2',
                            data: vals2,
                            borderColor: 'rgba(245, 158, 11, 0.9)',
                            backgroundColor: grad2,
                            borderWidth: 1.5,
                            pointRadius: 0,
                            fill: true,
                            tension: 0.2,
                            spanGaps: true,
                        },
                    ],
                },
                options: chartOptions(METRIC_UNITS[metric]),
            });
        }
    }

    function chartOptions(unit) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: {
                        color: '#555d72',
                        font: { size: 11, family: 'Inter' },
                        usePointStyle: true,
                        pointStyleWidth: 8,
                        padding: 20,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(16, 18, 27, 0.95)',
                    borderColor: 'rgba(255,255,255,0.08)',
                    borderWidth: 1,
                    titleFont: { family: 'Inter', size: 12 },
                    bodyFont: { family: 'Inter', size: 12 },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y != null ? ctx.parsed.y.toFixed(1) : '-'} ${unit}`,
                    },
                },
                zoom: {
                    pan: { enabled: true, mode: 'x' },
                    zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x',
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#3a3f50', maxRotation: 0, font: { size: 10, family: 'Inter' }, maxTicksLimit: 12 },
                    grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                    border: { display: false },
                },
                y: {
                    ticks: { color: '#3a3f50', font: { size: 10, family: 'Inter' }, padding: 8 },
                    grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                    border: { display: false },
                    title: { display: true, text: unit, color: '#555d72', font: { size: 11, family: 'Inter' } },
                },
            },
        };
    }

    // --- Averaged Data Tables ---
    function renderAveragedTable() {
        if (!mergedData) return;

        const container = document.getElementById('avg-table-container');
        const interval = activeInterval;
        const metrics = getSelectedMetrics();

        const buckets = [];
        let currentBucket = null;
        let bucketStart = null;

        for (let i = 0; i < mergedData.length; i++) {
            const m = mergedData[i];
            const secs = timeToSeconds(m.time);
            if (bucketStart === null || secs - bucketStart >= interval) {
                if (currentBucket) buckets.push(currentBucket);
                bucketStart = secs;
                currentBucket = { startTime: m.time, entries: [] };
            }
            currentBucket.entries.push(m);
        }
        if (currentBucket && currentBucket.entries.length > 0) buckets.push(currentBucket);

        let html = '<table><thead><tr><th>Time Window</th>';
        for (const metric of metrics) {
            html += `<th>F1 ${METRIC_LABELS[metric]}</th><th>F2 ${METRIC_LABELS[metric]}</th><th>\u0394</th>`;
        }
        html += '</tr></thead><tbody>';

        for (const bucket of buckets) {
            const endTime = bucket.entries[bucket.entries.length - 1].time;
            html += `<tr><td>${bucket.startTime}\u2013${endTime}</td>`;

            for (const metric of metrics) {
                const vals1 = bucket.entries.filter(e => e.file1 && e.file1[metric] != null).map(e => e.file1[metric]);
                const vals2 = bucket.entries.filter(e => e.file2 && e.file2[metric] != null).map(e => e.file2[metric]);
                const avg1 = vals1.length > 0 ? vals1.reduce((a, b) => a + b, 0) / vals1.length : null;
                const avg2 = vals2.length > 0 ? vals2.reduce((a, b) => a + b, 0) / vals2.length : null;
                const diff = (avg1 != null && avg2 != null) ? avg2 - avg1 : null;
                const diffClass = diff != null ? (diff >= 0 ? 'diff-positive' : 'diff-negative') : '';

                html += `<td class="file1-val">${fmtVal(avg1)}</td>`;
                html += `<td class="file2-val">${fmtVal(avg2)}</td>`;
                html += `<td class="${diffClass}">${diff != null ? (diff >= 0 ? '+' : '') + diff.toFixed(1) : '-'}</td>`;
            }
            html += '</tr>';
        }

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // --- Difference chart ---
    function updateDiffChart() {
        if (!mergedData) return;
        const metric = diffMetricSelect.value;

        const labels = [];
        const diffVals = [];

        for (const m of mergedData) {
            labels.push(m.time);
            const v1 = m.file1 ? (m.file1[metric] ?? null) : null;
            const v2 = m.file2 ? (m.file2[metric] ?? null) : null;
            diffVals.push(v1 != null && v2 != null ? v2 - v1 : null);
        }

        const step = Math.max(1, Math.floor(labels.length / 80));
        const displayLabels = labels.map((l, i) => i % step === 0 ? l : '');

        if (charts.diff) charts.diff.destroy();

        const ctx = document.getElementById('chart-diff').getContext('2d');
        charts.diff = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [{
                    label: `\u0394 ${METRIC_LABELS[metric]} (File2 \u2212 File1)`,
                    data: diffVals,
                    backgroundColor: diffVals.map(v =>
                        v == null ? 'transparent' : v >= 0 ? 'rgba(52, 211, 153, 0.5)' : 'rgba(248, 113, 113, 0.5)'
                    ),
                    borderColor: diffVals.map(v =>
                        v == null ? 'transparent' : v >= 0 ? 'rgba(52, 211, 153, 0.8)' : 'rgba(248, 113, 113, 0.8)'
                    ),
                    borderWidth: 1,
                    borderRadius: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        labels: {
                            color: '#555d72',
                            font: { size: 11, family: 'Inter' },
                            usePointStyle: true,
                            padding: 20,
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(16, 18, 27, 0.95)',
                        borderColor: 'rgba(255,255,255,0.08)',
                        borderWidth: 1,
                        titleFont: { family: 'Inter', size: 12 },
                        bodyFont: { family: 'Inter', size: 12 },
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y != null ? ctx.parsed.y.toFixed(1) : '-'} ${METRIC_UNITS[metric]}`,
                        },
                    },
                    zoom: {
                        pan: { enabled: true, mode: 'x' },
                        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' },
                    },
                },
                scales: {
                    x: {
                        ticks: { color: '#3a3f50', maxRotation: 0, font: { size: 10, family: 'Inter' }, maxTicksLimit: 12 },
                        grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                        border: { display: false },
                    },
                    y: {
                        ticks: { color: '#3a3f50', font: { size: 10, family: 'Inter' } },
                        grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                        border: { display: false },
                        title: { display: true, text: `\u0394 ${METRIC_UNITS[metric]}`, color: '#555d72', font: { size: 11, family: 'Inter' } },
                    },
                },
            },
        });
    }

    // --- Helpers ---
    function fmtVal(v) {
        if (v == null) return '\u2014';
        return v.toFixed(1);
    }

    function formatDuration(seconds) {
        if (seconds == null) return '\u2014';
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        if (h > 0) return `${h}h ${m}m ${s}s`;
        return `${m}m ${s}s`;
    }

    function timeToSeconds(timeStr) {
        const parts = timeStr.split(':').map(Number);
        return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
})();
