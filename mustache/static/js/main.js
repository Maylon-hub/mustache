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
            'proj-points': params.n_samples ?? metadata.points,
            'proj-time': params.execution_time == null ? null : Number(params.execution_time).toFixed(2) + ' s'
        };
        Object.entries(values).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value ?? '—';
        });
        if (form) Object.entries(params).forEach(([key, value]) => {
            const field = form.elements.namedItem(key);
            if (field && field.type !== 'file') field.value = value;
        });
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
        // Plotly's drag overlay is above the SVG markers, so the cursor must
        // change on that overlay when hit testing reports an interactive node.
        div.on('plotly_hover', event => {
            const overlay = div.querySelector('.draglayer .nsewdrag');
            if (overlay) overlay.style.cursor = event.points?.[0]?.data?.meta?.role === 'branch-targets' ? 'pointer' : '';
        });
        div.on('plotly_unhover', () => {
            const overlay = div.querySelector('.draglayer .nsewdrag');
            if (overlay) overlay.style.cursor = '';
        });
        div.on('plotly_click', event => {
            if (tool !== 'select') return;
            const point = event.points?.[0];
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

    function renderReachability(cached = false) {
        const container = document.getElementById('reachability-container');
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
            wrapper.className = 'reachability-plot-wrapper mr-3 flex-shrink-0'; wrapper.style.width = '360px';
            const heading = document.createElement('div'); heading.className = 'small px-3 pt-2';
            heading.textContent = outlier ? `Meta-clustering outlier: mpts = ${mpts}` : `Representative hierarchy (medoid): mpts = ${mpts}`;
            heading.title = outlier ? 'No automatic meta-cluster contains this hierarchy; it is not a medoid.' : `Meta-cluster ${group}: minimizes the sum of 1 − HAI to other hierarchies in this group.`;
            const note = document.createElement('div'); note.className = 'small text-muted px-3';
            const reach = result.reachability_data;
            note.textContent = reach?.method === 'hierarchy-adjacent-cophenetic' ? `${outlier ? 'Outlier hierarchy' : 'Meta-cluster ' + group} · distances from this hierarchy` : 'Older saved layout: geometry may be shared across mpts.';
            const chart = document.createElement('div'); chart.style.height = '345px';
            wrapper.append(heading, note, chart); container.append(wrapper);
            const inspect = document.createElement('button');
            inspect.className = 'btn btn-sm btn-link px-3'; inspect.textContent = 'Inspect hierarchy';
            inspect.addEventListener('click', () => inspectHierarchy(mpts));
            wrapper.insertBefore(inspect, chart);
            const figure = reach ? {
                data: [{ type: 'bar', x: reach.x, y: reach.y, customdata: reach.x.map((_, j) => [reach.ordering?.[j] ?? j, reach.labels[j]]), hovertemplate: 'Sample %{customdata[0]}<br>Hierarchy distance: %{y:.6f}<br>Cluster: %{customdata[1]}<extra></extra>' }],
                layout: { template: 'plotly_white', xaxis: { title: 'Sample order' }, yaxis: { title: 'Hierarchy reachability distance', rangemode: 'tozero' } }
            } : JSON.parse(result.reachability_json);
            figure.data.forEach(trace => { trace.marker = { color: outlier ? '#8D8D88' : '#1F6F5F' }; });
            Object.assign(figure.layout, { title: '', annotations: [], font: { size: 12 }, margin: { t: 10, r: 15, l: 65, b: 55 } });
            Plotly.newPlot(chart, figure.data, figure.layout, { responsive: true, displayModeBar: false });
        });
        if (!container.children.length) container.textContent = 'No representative hierarchies are available.';
    }

    async function renderAnalysis() {
        const select = document.getElementById('inspect-mpts');
        if (select) select.replaceChildren(...analysis.ordered_mpts.map(mpts => new Option(`mpts = ${mpts}`, mpts)));
        updateProjectInfo(); refreshSelection();
        await renderDendrogram(); renderHAI(); renderReachability();
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
            const response = await fetch('/api/projects/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, selected_mpts: window.getSelectedMpts() }) });
            const data = await response.json(); if (!response.ok) throw new Error(data.error);
            metadata = data.project; updateProjectInfo(); $('#saveProjectModalMain').modal('hide');
            alert('Analysis saved. Open Projects & History to reopen or download it.');
        } catch (error) { alert('Save error: ' + error.message); }
    };
    function inspectHierarchy(mpts) {
        const result = results?.[mpts], reach = result?.reachability_data;
        if (!reach) return alert('This older project did not preserve detailed hierarchy arrays.');
        if (!document.getElementById('hierarchyDetailModal')) document.body.insertAdjacentHTML('beforeend', `
            <div id="hierarchyDetailModal" class="modal fade" tabindex="-1" role="dialog" aria-label="Detailed hierarchy">
            <div class="modal-dialog modal-xl"><div class="modal-content"><div class="modal-header">
            <h5 id="hierarchy-detail-title"></h5><button class="close" data-dismiss="modal" aria-label="Close">&times;</button></div>
            <div class="modal-body"><p class="small">Colors are flat-cluster labels within this hierarchy, not corresponding clusters across mpts. Black indicates noise. Hover shows the original sample index; drag to zoom.</p><div id="hierarchy-detail-plot" style="height:480px;"></div></div></div></div></div>`);
        document.getElementById('hierarchy-detail-title').textContent = `Hierarchy: mpts = ${mpts} · ${result.metric || params.metric || 'metric unavailable'}`;
        const colors = ['#1F6F5F', '#486B8A', '#C9823B', '#847A96', '#879C7D', '#A06F65', '#577F7A', '#8D8D88'];
        const labels = [...new Set(reach.labels)].sort((a, b) => a - b);
        const traces = labels.map((label, i) => {
            const indices = reach.labels.map((value, j) => value === label ? j : -1).filter(j => j >= 0);
            return { type: 'bar', name: label === -1 ? 'Noise' : `Cluster ${label}`,
                x: indices.map(j => reach.x[j]), y: indices.map(j => reach.y[j]),
                customdata: indices.map(j => reach.ordering?.[j] ?? j),
                marker: { color: label === -1 ? '#000000' : colors[i % colors.length] },
                hovertemplate: 'Sample %{customdata}<br>Hierarchy distance: %{y:.6f}<extra>%{fullData.name}</extra>' };
        });
        const description = document.querySelector('#hierarchyDetailModal p');
        description.textContent = 'Colors are flat-cluster labels within this hierarchy, not corresponding clusters across mpts. Black indicates noise. Hover shows the original sample index; drag to zoom.';
        if (labels.filter(label => label >= 0).length > colors.length) description.textContent += ' More than eight clusters: colors repeat; use legend and hover labels.';
        $('#hierarchyDetailModal').one('shown.bs.modal', () => Plotly.react('hierarchy-detail-plot', traces, {
            template: 'plotly_white', barmode: 'overlay', bargap: 0,
            xaxis: { title: 'Sample order' }, yaxis: { title: 'Hierarchy reachability distance' },
            legend: { orientation: 'h' }, margin: { t: 20, l: 65, r: 20, b: 65 }
        }, { responsive: true, displaylogo: false }));
        $('#hierarchyDetailModal').modal('show');
    }
    document.getElementById('inspect-hierarchy')?.addEventListener('click', () => inspectHierarchy(Number(document.getElementById('inspect-mpts').value)));
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
