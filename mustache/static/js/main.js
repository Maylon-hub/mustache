/* Coordinated analysis views. Server responses are the partition source of truth. */
window.openBatchConfigModal = () => $('#batchConfigModal').modal('show');
window.openSaveProjectModal = () => {
    if (!document.getElementById('saveProjectModalMain')) document.body.insertAdjacentHTML('beforeend', `
        <div class="modal fade" id="saveProjectModalMain" tabindex="-1" role="dialog" aria-label="Save project">
          <div class="modal-dialog"><div class="modal-content">
            <div class="modal-header"><h5>Save analysis</h5><button class="close" data-dismiss="modal" aria-label="Close">&times;</button></div>
            <div class="modal-body"><label for="main-save-proj-name">Project name</label><input id="main-save-proj-name" class="form-control" maxlength="200"></div>
            <div class="modal-footer"><button class="btn btn-secondary" data-dismiss="modal">Cancel</button><button class="btn btn-success" onclick="confirmSaveProjectMain()">Save project</button></div>
          </div></div>
        </div>`);
    $('#saveProjectModalMain').modal('show');
};

document.addEventListener('DOMContentLoaded', () => {
    let analysis = null, results = null, params = {}, metadata = {};
    let selected = new Set(), tool = 'select', timer = null;
    let manualGroups = [];
    let cutSequence = 0, analysisGeneration = 0;
    let pendingCut = Promise.resolve();
    let representativeSignature = '';
    const form = document.getElementById('batch-form');
    const hierarchyExplorer = new window.HierarchyExplorer();
    hierarchyExplorer.onHierarchyChange = () => refreshSelection();
    const modeSelect = document.getElementById('meta-selection-mode');
    const scaleSelect = document.getElementById('hai-scale-mode');
    const settingsKey = 'mustache.settings.v1';
    let settings = {};
    try { settings = JSON.parse(localStorage.getItem(settingsKey) || '{}'); } catch (_) {}
    document.querySelectorAll('[data-mustache-setting]').forEach(field => {
        if (settings[field.dataset.mustacheSetting] !== undefined) field.value = settings[field.dataset.mustacheSetting];
    });
    if (form) {
        const updateMetrics = () => {
            const metric = form.elements.metric;
            const choices = window.mustacheSupportedMetrics?.[form.elements.algorithm.value] || [];
            [...metric.options].forEach(option => { option.disabled = !choices.includes(option.value); });
            if (!choices.includes(metric.value)) metric.value = choices[0] || 'euclidean';
        };
        form.elements.algorithm.addEventListener('change', updateMetrics);
        updateMetrics();
        const updateSizeMode = () => {
            const explicit = form.elements.min_cluster_size_mode.value === 'explicit';
            form.elements.min_cluster_size.disabled = !explicit;
            form.elements.min_cluster_size.required = explicit;
        };
        form.elements.min_cluster_size_mode.addEventListener('change', updateSizeMode);
        updateSizeMode();
    }
    const sidebar = document.querySelector('.sidebar');
    document.querySelector('.fa-bars')?.addEventListener('click', () => {
        sidebar.style.display = sidebar.style.display === 'none' ? 'flex' : 'none';
    });

    function updateProjectInfo() {
        const values = {
            'proj-name': metadata.name || params.dataset_name || 'Unsaved analysis',
            'proj-algorithm': params.algorithm === 'core-sg' ? 'CORE-SG' : (params.algorithm === 'hdbscan' ? 'HDBSCAN' : null),
            'proj-min-mpts': params.min_mpts, 'proj-max-mpts': params.max_mpts,
            'proj-step': params.step, 'proj-metric': params.metric,
            'proj-min-cluster-size': params.min_cluster_size_mode === 'explicit'
                ? params.min_cluster_size : 'Automatic (= mpts)',
            'proj-points': params.n_samples ?? metadata.points,
            'proj-time': params.execution_time == null ? null : Number(params.execution_time).toFixed(2) + ' s'
        };
        Object.entries(values).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value ?? '—';
        });
        if (form) Object.entries(params).forEach(([key, value]) => {
            const field = form.elements.namedItem(key);
            if (field && field.type !== 'file') field.value = value ?? '';
        });
        if (form) {
            const explicit = params.min_cluster_size_mode === 'explicit';
            form.elements.min_cluster_size_mode.value = explicit ? 'explicit' : 'automatic';
            form.elements.min_cluster_size.disabled = !explicit;
            form.elements.min_cluster_size.required = explicit;
        }
        ['btn-save-top', 'btn-sidebar-save'].forEach(id => {
            const button = document.getElementById(id);
            if (button) button.style.display = results ? 'inline-block' : 'none';
        });
    }
    window.getSelectedMpts = () => [...selected].sort((a, b) => a - b);

    function refreshSelection() {
        const badge = document.getElementById('selected-branches-badge');
        const clear = document.getElementById('btn-clear-selection');
        const help = document.getElementById('manual-selection-help');
        if (help) help.style.display = modeSelect.value === 'manual' && !manualGroups.length ? 'inline-block' : 'none';
        if (badge) {
            badge.style.display = manualGroups.length && modeSelect.value === 'manual' ? 'inline-block' : 'none';
            badge.textContent = `${manualGroups.length} ${manualGroups.length === 1 ? 'branch' : 'branches'} selected · ${selected.size} hierarchies: mpts ${window.getSelectedMpts().join(', ')}`;
            badge.title = 'Selected branches define non-overlapping manual meta-clusters; their medoids are shown below. Selected hierarchies are also saved/exported.';
        }
        if (clear) clear.style.display = manualGroups.length && modeSelect.value === 'manual' ? 'inline-block' : 'none';
        const div = document.getElementById('meta-dendrogram');
        div?.data?.forEach((trace, i) => {
            if (trace.meta?.role === 'hierarchy-leaves') {
                const current = hierarchyExplorer.selection.mpts;
                const colors = trace.customdata.map(value => Number(value) === current ? '#D27A16' : '#FFFFFF');
                const sizes = trace.customdata.map(value => Number(value) === current ? 16 : 12);
                Plotly.restyle(div, { 'marker.color': [colors], 'marker.size': [sizes] }, [i]);
                return;
            }
            if (trace.meta?.role === 'branch-targets') {
                const groups = trace.meta.branch_members || {};
                const colors = trace.customdata.map(id => manualGroups.some(group => sameGroup(group, groups[id] || [])) ? '#1F6F5F' : '#FFFFFF');
                const sizes = trace.customdata.map((id, index) => colors[index] === '#1F6F5F' ? trace.meta.default_size + 4 : trace.meta.default_size);
                Plotly.restyle(div, { 'marker.color': [colors], 'marker.size': [sizes] }, [i]);
                return;
            }
            const values = trace.meta?.mpts_values || [];
            if (!values.length) return;
            const active = modeSelect.value === 'manual' && manualGroups.some(group => values.every(value => group.includes(Number(value))));
            Plotly.restyle(div, { 'line.color': active ? '#1F6F5F' : '#2196F3', 'line.width': active ? 5 : 3 }, [i]);
        });
    }
    const sameGroup = (left, right) => left.length === right.length && left.every(value => right.includes(value));
    window.clearSelectedBranches = () => {
        selected.clear(); manualGroups = []; refreshSelection();
        if (analysis && modeSelect.value === 'manual') enqueuePartition(null).catch(error => alert(error.message));
    };
    window.setDendroTool = async value => {
        tool = value;
        const ids = { select: 'btn-tool-wand', cut: 'btn-tool-cut', pan: 'btn-tool-pan' };
        Object.entries(ids).forEach(([name, id]) => document.getElementById(id)?.classList.toggle('active', name === value));
        const div = document.getElementById('meta-dendrogram');
        if (!div?.data) return;
        if (value !== 'select') div.classList.remove('over-branch-target');
        if (value === 'cut' && modeSelect?.value !== 'threshold') {
            modeSelect.value = 'threshold';
            await changeMode();
        }
        Plotly.relayout(div, { dragmode: value === 'pan' ? 'pan' : false });
    };
    window.zoomDendrogram = factor => {
        const div = document.getElementById('meta-dendrogram');
        const range = div?._fullLayout?.yaxis?.range;
        if (!range) return;
        const centre = (range[0] + range[1]) / 2, half = (range[1] - range[0]) / (2 * factor);
        Plotly.relayout(div, { 'yaxis.range': [Math.max(0, centre - half), centre + half] });
    };
    window.resetDendrogramZoom = () => {
        if (document.getElementById('meta-dendrogram')?.data) Plotly.relayout('meta-dendrogram', { 'xaxis.autorange': true, 'yaxis.autorange': true });
    };

    async function requestPartition(threshold, mode, groups) {
        const sequence = ++cutSequence, generation = analysisGeneration;
        const response = await fetch('/cut_dendrogram', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(mode === 'automatic' ? { mode } : (mode === 'manual' ? { mode, groups } : { y_threshold: threshold }))
        });
        const partition = await response.json();
        if (!response.ok) throw new Error(partition.error || 'Unable to select meta-clusters.');
        if (sequence !== cutSequence || generation !== analysisGeneration) return;
        Object.assign(analysis, partition);
        renderReachability(partition.from_cache);
    }
    function enqueuePartition(threshold) {
        // Serialize requests so the server's saved partition cannot regress
        // behind the last visible cut when a user drags rapidly.
        const mode = modeSelect.value, groups = manualGroups.map(group => [...group]);
        pendingCut = pendingCut.catch(() => {}).then(() => requestPartition(threshold, mode, groups));
        return pendingCut;
    }
    async function changeMode() {
        if (!analysis) return;
        clearTimeout(timer);
        selected = new Set(modeSelect.value === 'manual' ? manualGroups.flat() : []);
        refreshSelection();
        const div = document.getElementById('meta-dendrogram');
        const max = Math.max(0, ...div.data.flatMap(trace => trace.y || []));
        try {
            await enqueuePartition(analysis.cut_threshold ?? max / 2);
            await renderDendrogram();
        } catch (error) { alert('Meta-cluster selection error: ' + error.message); }
    }
    modeSelect?.addEventListener('change', changeMode);

    async function renderDendrogram() {
        if (!analysis?.meta_dendrogram_json) return;
        const figure = JSON.parse(analysis.meta_dendrogram_json);
        // Projects saved before visible targets used transparent markers inside
        // line traces. Upgrade their figures only in memory; no recomputation.
        if (!figure.data.some(trace => trace.meta?.role === 'branch-targets')) {
            const branches = figure.data.filter(trace => trace.meta?.mpts_values?.length);
            if (branches.length) {
                const branchMembers = {}, markerIds = [], markerX = [], markerY = [], markerText = [];
                branches.forEach((trace, index) => {
                    const id = String(trace.meta.branch_id ?? index);
                    branchMembers[id] = trace.meta.mpts_values.map(Number);
                    markerIds.push(id);
                    markerX.push(trace.x.length === 5 ? trace.x[2] : (trace.x[1] + trace.x[2]) / 2);
                    markerY.push(trace.y[1]);
                    markerText.push(`Select hierarchy group: mpts ${branchMembers[id].join(', ')}`);
                    trace.mode = 'lines'; delete trace.marker;
                    trace.hoverinfo = 'skip';
                });
                const size = branches.length <= 20 ? 14 : (branches.length <= 60 ? 11 : 8);
                figure.data.push({ type: 'scatter', mode: 'markers', x: markerX, y: markerY,
                    customdata: markerIds, text: markerText,
                    marker: { size, color: '#FFFFFF', line: { color: '#1D6F9E', width: 2 } },
                    hovertemplate: '%{text}<br>Merge distance: %{y:.6f}<extra></extra>',
                    meta: { role: 'branch-targets', branch_members: branchMembers, default_size: size },
                    showlegend: false });
            }
        }
        // Leaves identify individual hierarchies; internal nodes continue to
        // select meta-clusters. Insert before branch targets so their existing
        // trace and physical-click tests retain the same last-trace position.
        if (!figure.data.some(trace => trace.meta?.role === 'hierarchy-leaves')) {
            const axis = figure.layout?.xaxis || {};
            let leaves = (axis.tickvals || []).map((x, index) => ({
                x: Number(x), mpts: Number(axis.ticktext?.[index]),
            })).filter(item => Number.isFinite(item.x) && analysis.ordered_mpts.includes(item.mpts));
            if (leaves.length !== analysis.ordered_mpts.length && analysis.ordered_mpts.length === 1)
                leaves = [{ x: 5, mpts: Number(analysis.ordered_mpts[0]) }];
            if (leaves.length === analysis.ordered_mpts.length) {
                const trace = { type: 'scatter', mode: 'markers', x: leaves.map(item => item.x),
                    y: leaves.map(() => 0), customdata: leaves.map(item => item.mpts),
                    marker: { size: 12, color: '#FFFFFF', line: { color: '#2C7896', width: 2 } },
                    hovertemplate: 'Open hierarchy: mpts = %{customdata}<br>Click to inspect its dendrogram and groups<extra></extra>',
                    cliponaxis: false, meta: { role: 'hierarchy-leaves' }, showlegend: false };
                const branchIndex = figure.data.findIndex(item => item.meta?.role === 'branch-targets');
                figure.data.splice(branchIndex < 0 ? figure.data.length : branchIndex, 0, trace);
            }
        }
        figure.layout.hovermode = 'closest';
        figure.layout.hoverdistance = 12;
        figure.layout.margin = { t: 50, r: 20, l: 60, b: 55 };
        figure.layout.font = { size: 12 };
        if (modeSelect) modeSelect.value = analysis.selection_mode || 'automatic';
        figure.layout.shapes = analysis.selection_mode === 'threshold' ? [{
            type: 'line', x0: 0, x1: 1, xref: 'paper', yref: 'y',
            y0: analysis.cut_threshold, y1: analysis.cut_threshold,
            line: { color: '#9A681A', width: 2, dash: 'dot' }, editable: true
        }] : [];
        const div = document.getElementById('meta-dendrogram');
        const hierarchyCount = analysis.ordered_mpts?.length || 0;
        // Dense trees remain readable on narrow screens by scrolling rather
        // than compressing touch targets into overlapping pixels.
        div.style.minWidth = `${Math.max(320, hierarchyCount * (hierarchyCount > 20 ? 24 : 18) + 100)}px`;
        Plotly.purge(div); div.innerHTML = '';
        await Plotly.newPlot(div, figure.data, figure.layout, { responsive: true, displayModeBar: false, edits: { shapePosition: true } });
        refreshSelection();
        // The drag overlay sits above Plotly's SVG. Browser/Plotly versions can
        // differ in hover-event timing, so derive the cursor from the visible
        // marker bounds rather than requiring a plotly_hover event. Capture
        // mousemove before the drag overlay can consume its bubbling phase.
        if (div._branchCursorHandler) div.removeEventListener('mousemove', div._branchCursorHandler, true);
        div._branchCursorHandler = event => {
            const overlay = div.querySelector('.draglayer .nsewdrag');
            if (!overlay) return;
            const branchMarkers = div.querySelectorAll('.scatterlayer .trace:last-child .points path');
            const leaves = div.querySelectorAll('.hierarchy-leaf-targets .points path');
            const hit = markers => Array.from(markers).some(marker => {
                const box = marker.getBoundingClientRect();
                return event.clientX >= box.left && event.clientX <= box.right &&
                    event.clientY >= box.top && event.clientY <= box.bottom;
            });
            div.classList.toggle('over-leaf-target', hit(leaves));
            div.classList.toggle('over-branch-target', tool === 'select' && hit(branchMarkers));
        };
        const leafTraceIndex = div.data.findIndex(trace => trace.meta?.role === 'hierarchy-leaves');
        div.querySelectorAll('.scatterlayer .trace')[leafTraceIndex]?.classList.add('hierarchy-leaf-targets');
        div.addEventListener('mousemove', div._branchCursorHandler, true);
        if (div._branchCursorLeaveHandler) div.removeEventListener('mouseleave', div._branchCursorLeaveHandler);
        div._branchCursorLeaveHandler = () => {
            div.classList.remove('over-branch-target');
            div.classList.remove('over-leaf-target');
        };
        div.addEventListener('mouseleave', div._branchCursorLeaveHandler);
        div.on('plotly_click', event => {
            const point = event.points?.[0];
            if (point?.data?.meta?.role === 'hierarchy-leaves') {
                const mpts = Number(point.customdata ?? point.data.customdata?.[point.pointNumber]);
                if (analysis.ordered_mpts.includes(mpts)) hierarchyExplorer.open(mpts, { scroll: true })
                    .catch(error => alert('Hierarchy inspection error: ' + error.message));
                return;
            }
            if (tool !== 'select') return;
            if (point?.data?.meta?.role !== 'branch-targets') return;
            const nodeId = String(point.customdata ?? point.data.customdata?.[point.pointNumber]);
            const values = (point.data.meta.branch_members?.[nodeId] || []).map(Number);
            if (!values.length) return;
            const remove = manualGroups.some(group => sameGroup(group, values));
            // New ancestor/descendant replaces overlapping previous groups;
            // each hierarchy can belong to at most one manual meta-cluster.
            manualGroups = manualGroups.filter(group => !group.some(value => values.includes(value)));
            if (!remove) manualGroups.push(values);
            selected = new Set(manualGroups.flat());
            modeSelect.value = 'manual';
            Plotly.relayout(div, { shapes: [] });
            refreshSelection();
            enqueuePartition(null).catch(error => alert('Manual selection error: ' + error.message));
        });
        div.on('plotly_relayout', event => {
            if (modeSelect.value !== 'threshold') return;
            const height = event['shapes[0].y0'] ?? event['shapes[0].y1'] ?? event.shapes?.[0]?.y0;
            if (height == null) return;
            clearTimeout(timer);
            timer = setTimeout(() => enqueuePartition(height).catch(error => alert('Cut error: ' + error.message)), 120);
        });
    }

    function renderHAI() {
        if (!analysis?.hai_matrix) return;
        const matrix = analysis.hai_matrix, mpts = analysis.ordered_mpts;
        const values = matrix.flat(), min = Math.min(...values), max = Math.max(...values);
        const mode = scaleSelect?.value || 'adaptive';
        const offDiagonal = matrix.flatMap((row, i) => row.filter((_, j) => i !== j)).sort((a, b) => a - b);
        const robustMin = offDiagonal[Math.floor(offDiagonal.length * 0.1)] ?? min;
        const lower = mode === 'fixed' ? 0 : (mode === 'robust' ? robustMin : min);
        const upper = mode === 'fixed' ? 1 : Math.max(max, lower + 1e-9);
        const method = analysis.hai_computation;
        const note = document.getElementById('hai-method-note');
        if (note) {
            note.textContent = !method ? 'HAI method metadata unavailable in this older project.' : method.approximate
                ? `Approximate HAI · ${method.pair_count.toLocaleString()} sampled pairs · seed ${method.random_state} · 95% per-comparison bound ±${method.absolute_error_bound.toFixed(4)}`
                : 'Exact HAI · all point pairs';
            note.title = method ? JSON.stringify(method) : '';
        }
        const ticks = mpts.filter((_, i) => i % Math.max(1, Math.ceil(mpts.length / 12)) === 0);
        Plotly.react('hai-heatmap', [{
            type: 'heatmap', z: matrix, x: mpts, y: mpts,
            // Preserve the original HAI visual convention: lighter = higher agreement.
            colorscale: [[0, '#1F6F5F'], [1, '#F5F5F2']], zmin: lower, zmax: upper,
            hovertemplate: 'mpts %{y} × %{x}<br>HAI: %{z:.8f}<extra></extra>',
            colorbar: { orientation: 'h', yanchor: 'top', y: -0.18, thickness: 15, tickfont: { size: 12 } }
        }], {
            margin: { t: 55, r: 20, l: 55, b: 85 }, font: { size: 12 },
            annotations: [{ text: `Scale: ${mode} [${lower.toFixed(4)}, ${upper.toFixed(4)}]${mode === 'robust' ? ' · lowest 10% clipped' : ''}`, xref: 'paper', yref: 'paper', x: 0, y: 1.16, xanchor: 'left', showarrow: false, font: { size: 12 } }],
            xaxis: { side: 'top', tickmode: 'array', tickvals: ticks, title: 'mpts' },
            yaxis: { autorange: 'reversed', tickmode: 'array', tickvals: ticks, title: 'mpts' }
        }, { responsive: true, displayModeBar: false });
    }
    if (scaleSelect) {
        scaleSelect.value = settings.hai_scale || 'adaptive';
        scaleSelect.addEventListener('change', renderHAI);
    }

    const reachContainer = document.getElementById('reachability-container');
    const reachPrev = document.getElementById('reachability-prev');
    const reachNext = document.getElementById('reachability-next');
    const reachPosition = document.getElementById('reachability-position');
    function updateReachabilityNavigation() {
        if (!reachContainer) return;
        const total = reachContainer.querySelectorAll('.reachability-plot-wrapper').length;
        const page = total ? Math.min(total - 1, Math.round(reachContainer.scrollLeft /
            Math.max(1, reachContainer.clientWidth))) : 0;
        if (reachPosition) reachPosition.textContent = total ? `${page + 1} of ${total}` : 'No representatives';
        if (reachPrev) reachPrev.disabled = page === 0;
        if (reachNext) reachNext.disabled = page >= total - 1;
    }
    reachPrev?.addEventListener('click', () => reachContainer.scrollBy({ left: -reachContainer.clientWidth, behavior: 'smooth' }));
    reachNext?.addEventListener('click', () => reachContainer.scrollBy({ left: reachContainer.clientWidth, behavior: 'smooth' }));
    reachContainer?.addEventListener('scroll', updateReachabilityNavigation);

    function renderReachability(cached = false) {
        const container = reachContainer;
        if (!container) return;
        const representatives = Object.entries(analysis.medoids || {}).map(([group, mpts]) => ({ group, mpts: Number(mpts), outlier: false }));
        const outliers = (analysis.outliers || []).map(mpts => ({ mpts: Number(mpts), outlier: true }));
        const signature = JSON.stringify([representatives, outliers, analysis.meta_labels]);
        const indicator = document.getElementById('cache-indicator');
        if (indicator) indicator.textContent = `${representatives.length} meta-clusters · ${outliers.length} outliers${analysis.selection_mode === 'manual' ? ` · manual · ${analysis.ordered_mpts.length - manualGroups.flat().length} unselected` : ''}${cached ? ' · cached partition' : ''}`;
        if (signature === representativeSignature) return;
        representativeSignature = signature;
        container.querySelectorAll('.js-plotly-plot').forEach(div => Plotly.purge(div));
        container.innerHTML = '';
        [...representatives, ...outliers].forEach(({ group, mpts, outlier }) => {
            const result = results?.[mpts];
            if (!result?.reachability_data && !result?.reachability_json) return;
            const wrapper = document.createElement('div');
            wrapper.className = 'reachability-plot-wrapper';
            const heading = document.createElement('div'); heading.className = 'small px-3 pt-2';
            heading.textContent = outlier ? `Meta-clustering outlier: mpts = ${mpts}` : `Representative hierarchy (medoid): mpts = ${mpts}`;
            heading.title = outlier ? 'No automatic meta-cluster contains this hierarchy; it is not a medoid.' : `Meta-cluster ${group}: minimizes the sum of 1 − HAI to other hierarchies in this group.`;
            const note = document.createElement('div'); note.className = 'small text-muted px-3';
            const reach = result.reachability_data;
            note.textContent = reach?.method === 'hierarchy-adjacent-cophenetic'
                ? `${outlier ? 'Meta-clustering outlier' : 'Meta-cluster ' + group} · ${result.n_clusters} flat clusters · ${result.noise_points}/${result.n_samples} sample noise · colors distinguish flat clusters; inspect for full legend`
                : 'Older saved layout: geometry may be shared across mpts.';
            if (result.n_clusters === 0) note.textContent += ' · No valid flat clusters at this minimum cluster size.';
            const chart = document.createElement('div'); chart.style.height = '330px';
            wrapper.append(heading, note, chart); container.append(wrapper);
            const inspect = document.createElement('button');
            inspect.className = 'btn btn-sm btn-link px-3'; inspect.textContent = 'Inspect hierarchy';
            inspect.addEventListener('click', () => hierarchyExplorer.open(mpts, { scroll: true }));
            wrapper.insertBefore(inspect, chart);
            const figure = reach ? {
                data: [...new Set(reach.labels.map(Number))].sort((a, b) => a - b).map(label => {
                    const positions = reach.labels.map((value, j) => Number(value) === label ? j : -1).filter(j => j >= 0);
                    return { type: 'bar', name: label === -1 ? 'Noise' : `Cluster ${label}`,
                        x: positions.map(j => reach.x[j]), y: positions.map(j => reach.y[j]),
                        customdata: positions.map(j => [reach.ordering?.[j] ?? j, label]),
                        marker: { color: window.mustacheClusterColor(label) },
                        hovertemplate: 'Input row %{customdata[0]}<br>Hierarchy distance: %{y:.6f}<br>Flat label: %{customdata[1]}<extra></extra>' };
                }),
                layout: { template: 'plotly_white', barmode: 'overlay', bargap: 0,
                    legend: { orientation: 'h' }, xaxis: { title: 'Leaf order' },
                    yaxis: { title: 'Hierarchy reachability distance', rangemode: 'tozero' } }
            } : JSON.parse(result.reachability_json);
            Object.assign(figure.layout, { title: '', annotations: [], showlegend: false,
                font: { size: 12 }, margin: { t: 10, r: 25, l: 75, b: 60 } });
            Plotly.newPlot(chart, figure.data, figure.layout, { responsive: true, displayModeBar: false });
        });
        if (!container.children.length) container.textContent = 'No representative hierarchies are available.';
        container.scrollLeft = 0;
        updateReachabilityNavigation();
    }

    async function renderAnalysis() {
        updateProjectInfo(); refreshSelection();
        await renderDendrogram(); renderHAI(); renderReachability();
        await hierarchyExplorer.setData(analysis, results, params);
    }
    if (form) form.addEventListener('submit', async event => {
        event.preventDefault();
        // Flush any pending cut before replacing the analysis session.
        clearTimeout(timer); await pendingCut.catch(() => {});
        const button = form.querySelector('[type="submit"]'), original = button.innerHTML;
        button.disabled = true;
        const start = Date.now();
        const interval = setInterval(() => { button.textContent = `Processing (${((Date.now() - start) / 1000).toFixed(1)} s)…`; }, 100);
        try {
            const response = await fetch('/batch', { method: 'POST', body: new FormData(form) });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Unable to run batch.');
            analysisGeneration++; cutSequence++; selected.clear(); manualGroups = []; representativeSignature = '';
            analysis = data.analysis; results = data.results; params = data.params; metadata = {};
            $('#batchConfigModal').modal('hide');
            await renderAnalysis();
        } catch (error) { alert('Batch error: ' + error.message); }
        finally { clearInterval(interval); button.disabled = false; button.innerHTML = original; }
    });
    document.addEventListener('mustache:project-loaded', async event => {
        ({ analysis, results, params, metadata } = event.detail);
        analysisGeneration++; cutSequence++; representativeSignature = '';
        selected = new Set((analysis.selected_mpts || []).map(Number));
        manualGroups = (analysis.manual_groups || []).map(group => group.map(Number));
        if (analysis.selection_mode !== 'manual') selected.clear();
        await renderAnalysis();
    });
    window.confirmSaveProjectMain = async () => {
        const name = document.getElementById('main-save-proj-name').value.trim();
        if (!name) return alert('Enter a project name.');
        try {
            clearTimeout(timer);
            // Capture a dragged threshold even if its debounce has not fired.
            if (modeSelect?.value === 'threshold') await enqueuePartition(document.getElementById('meta-dendrogram').layout.shapes[0].y0);
            await pendingCut;
            const response = await fetch('/api/projects/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, selected_mpts: window.getSelectedMpts(), explorer_selection: hierarchyExplorer.selection }) });
            const data = await response.json(); if (!response.ok) throw new Error(data.error);
            metadata = data.project; updateProjectInfo(); $('#saveProjectModalMain').modal('hide');
            alert('Analysis saved. Open Projects & History to reopen or download it.');
        } catch (error) { alert('Save error: ' + error.message); }
    };
    window.exportSelectedBranchesCSV = async () => {
        if (!results) return alert('Run or load an analysis before exporting.');
        if (modeSelect?.value === 'manual' && !manualGroups.length) return alert('Select at least one branch before exporting manual meta-clusters.');
        try {
            clearTimeout(timer);
            if (modeSelect?.value === 'threshold') await enqueuePartition(document.getElementById('meta-dendrogram').layout.shapes[0].y0);
            await pendingCut;
            const mptsList = modeSelect?.value === 'manual' ? window.getSelectedMpts() : Object.values(analysis.medoids || {});
            const response = await fetch('/export_branches_csv', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mpts_list: mptsList }) });
            if (!response.ok) throw new Error((await response.json()).error);
            const url = URL.createObjectURL(await response.blob()), link = document.createElement('a');
            link.href = url; link.download = 'mustache_clusters.csv'; document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
        } catch (error) { alert('Export error: ' + error.message); }
    };
});
