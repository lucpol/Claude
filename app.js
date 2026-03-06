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
    const applyFiltersBtn = document.getElementById('apply-filters-btn');
    const diffMetricSelect = document.getElementById('diff-metric');

    // --- Metric labels ---
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
        temperature: '°C',
    };

    // --- File loading ---
    file1Input.addEventListener('change', (e) => loadFile(e, 1));
    file2Input.addEventListener('change', (e) => loadFile(e, 2));
    compareBtn.addEventListener('click', runComparison);
    applyFiltersBtn.addEventListener('click', runComparison);
    diffMetricSelect.addEventListener('change', updateDiffChart);

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeInterval = parseInt(tab.dataset.interval, 10);
            renderAveragedTable();
        });
    });

    function loadFile(event, num) {
        const file = event.target.files[0];
        if (!file) return;

        const infoEl = num === 1 ? file1Info : file2Info;
        infoEl.textContent = 'Loading...';
        infoEl.classList.remove('loaded');

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
                infoEl.textContent = `${file.name} | ${result.records.length} points | ${startStr} - ${endStr} (${dur})`;
                infoEl.classList.add('loaded');
            } catch (err) {
                infoEl.textContent = `Error: ${err.message}`;
                infoEl.classList.remove('loaded');
            }

            compareBtn.disabled = !(file1Data && file2Data);
        };
        reader.readAsArrayBuffer(file);
    }

    // --- Time sync and merge ---
    function timeKey(date) {
        // Returns "HH:MM:SS" string for time-of-day alignment
        const h = String(date.getHours()).padStart(2, '0');
        const m = String(date.getMinutes()).padStart(2, '0');
        const s = String(date.getSeconds()).padStart(2, '0');
        return `${h}:${m}:${s}`;
    }

    function buildTimeMap(records) {
        const map = new Map();
        for (const rec of records) {
            const key = timeKey(rec.timestamp);
            // If multiple records share same second, keep last
            map.set(key, rec);
        }
        return map;
    }

    function mergeByTimeOfDay(data1, data2, startFilter, endFilter) {
        const map1 = buildTimeMap(data1.records);
        const map2 = buildTimeMap(data2.records);

        // Collect all time keys that appear in either file
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

    // --- Main comparison ---
    function runComparison() {
        if (!file1Data || !file2Data) return;

        const startFilter = document.getElementById('time-start').value || null;
        const endFilter = document.getElementById('time-end').value || null;
        const smoothingVal = parseInt(document.getElementById('smoothing').value, 10) || 1;
        const selectedMetrics = Array.from(document.getElementById('metric-select').selectedOptions)
            .map(o => o.value);

        mergedData = mergeByTimeOfDay(file1Data, file2Data, startFilter, endFilter);

        // Show sections
        filtersSection.classList.remove('hidden');
        summarySection.classList.remove('hidden');
        chartsSection.classList.remove('hidden');
        tablesSection.classList.remove('hidden');
        diffSection.classList.remove('hidden');

        // Set time filter defaults if empty
        if (!startFilter && mergedData.length > 0) {
            document.getElementById('time-start').value = mergedData[0].time;
        }
        if (!endFilter && mergedData.length > 0) {
            document.getElementById('time-end').value = mergedData[mergedData.length - 1].time;
        }

        renderSummary(selectedMetrics);
        renderCharts(selectedMetrics, smoothingVal);
        renderAveragedTable();
        updateDiffChart();
    }

    // --- Summary table ---
    function renderSummary(metrics) {
        const container = document.getElementById('summary-table-container');

        let html = `<table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>File 1 Avg</th>
                    <th>File 2 Avg</th>
                    <th>Diff</th>
                    <th>File 1 Max</th>
                    <th>File 2 Max</th>
                    <th>File 1 Min</th>
                    <th>File 2 Min</th>
                </tr>
            </thead>
            <tbody>`;

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

        // Duration comparison
        const dur1 = file1Data.summary.duration_seconds;
        const dur2 = file2Data.summary.duration_seconds;
        html += `<div style="margin-top:12px; color: var(--text-muted); font-size:0.85rem;">
            Duration: <span class="file1-val">${formatDuration(dur1)}</span> vs
            <span class="file2-val">${formatDuration(dur2)}</span> |
            Synchronized points: ${mergedData.length} |
            Overlap: File 1 has ${mergedData.filter(m => m.file1).length} points,
            File 2 has ${mergedData.filter(m => m.file2).length} points
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

            // Downsample labels for readability
            const step = Math.max(1, Math.floor(labels.length / 80));
            const displayLabels = labels.map((l, i) => i % step === 0 ? l : '');

            if (charts[metric]) charts[metric].destroy();

            const ctx = document.getElementById(`chart-${metric}`).getContext('2d');
            charts[metric] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: displayLabels,
                    datasets: [
                        {
                            label: 'File 1',
                            data: vals1,
                            borderColor: 'rgba(59, 130, 246, 0.9)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 1.5,
                            pointRadius: 0,
                            fill: false,
                            tension: 0.1,
                            spanGaps: true,
                        },
                        {
                            label: 'File 2',
                            data: vals2,
                            borderColor: 'rgba(249, 115, 22, 0.9)',
                            backgroundColor: 'rgba(249, 115, 22, 0.1)',
                            borderWidth: 1.5,
                            pointRadius: 0,
                            fill: false,
                            tension: 0.1,
                            spanGaps: true,
                        },
                    ],
                },
                options: chartOptions(METRIC_LABELS[metric], METRIC_UNITS[metric]),
            });
        }
    }

    function chartOptions(label, unit) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { labels: { color: '#9ca3af', font: { size: 12 } } },
                tooltip: {
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
                    ticks: { color: '#6b7280', maxRotation: 45, font: { size: 10 } },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                },
                y: {
                    ticks: { color: '#6b7280', font: { size: 11 } },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    title: { display: true, text: unit, color: '#9ca3af' },
                },
            },
        };
    }

    // --- Averaged Data Tables ---
    function renderAveragedTable() {
        if (!mergedData) return;

        const container = document.getElementById('avg-table-container');
        const interval = activeInterval;
        const metrics = Array.from(document.getElementById('metric-select').selectedOptions)
            .map(o => o.value);

        // Group merged data into buckets of `interval` seconds
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

        // Build header
        let html = '<table><thead><tr><th>Time Window</th>';
        for (const metric of metrics) {
            html += `<th>F1 ${METRIC_LABELS[metric]}</th><th>F2 ${METRIC_LABELS[metric]}</th><th>Diff</th>`;
        }
        html += '</tr></thead><tbody>';

        for (const bucket of buckets) {
            const endTime = bucket.entries[bucket.entries.length - 1].time;
            html += `<tr><td>${bucket.startTime} - ${endTime}</td>`;

            for (const metric of metrics) {
                const vals1 = bucket.entries
                    .filter(e => e.file1 && e.file1[metric] != null)
                    .map(e => e.file1[metric]);
                const vals2 = bucket.entries
                    .filter(e => e.file2 && e.file2[metric] != null)
                    .map(e => e.file2[metric]);

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
                    label: `Δ ${METRIC_LABELS[metric]} (File2 - File1)`,
                    data: diffVals,
                    backgroundColor: diffVals.map(v =>
                        v == null ? 'transparent' : v >= 0 ? 'rgba(34, 197, 94, 0.6)' : 'rgba(239, 68, 68, 0.6)'
                    ),
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: '#9ca3af' } },
                    tooltip: {
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
                        ticks: { color: '#6b7280', maxRotation: 45, font: { size: 10 } },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                    y: {
                        ticks: { color: '#6b7280' },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: `Δ ${METRIC_UNITS[metric]}`, color: '#9ca3af' },
                    },
                },
            },
        });
    }

    // --- Helpers ---
    function fmtVal(v) {
        if (v == null) return '-';
        return v.toFixed(1);
    }

    function formatDuration(seconds) {
        if (seconds == null) return '-';
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
