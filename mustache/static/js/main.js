// Global functions for modals
function openBatchConfigModal() {
    $('#batchConfigModal').modal('show');
}
window.openBatchConfigModal = openBatchConfigModal;

// Open save project modal (available globally so base.html sidebar can call it)
function openSaveProjectModal() {
    const modal = document.getElementById('saveProjectModalMain');
    if (!modal) {
        // Inject modal HTML if not present on this page
        const modalHtml = `
        <div class="modal fade" id="saveProjectModalMain" tabindex="-1" role="dialog" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-bookmark text-success mr-2"></i>Save Analysis to History</h5>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>Project / Dataset Name <span class="text-danger">*</span></label>
                            <input type="text" id="main-save-proj-name" class="form-control" placeholder="e.g., Anuran Frog Exploration">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-success" onclick="confirmSaveProjectMain()">Save Project</button>
                    </div>
                </div>
            </div>
        </div>`;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }
    $('#saveProjectModalMain').modal('show');
}
window.openSaveProjectModal = openSaveProjectModal;

async function confirmSaveProjectMain() {
    const nameInput = document.getElementById('main-save-proj-name');
    const name = nameInput ? nameInput.value.trim() : '';
    if (!name) { alert('Please enter a project name.'); return; }
    try {
        const res = await fetch('/api/projects/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to save');
        $('#saveProjectModalMain').modal('hide');
        // Show brief success toast
        const toast = document.createElement('div');
        toast.className = 'alert alert-success';
        toast.style.cssText = 'position:fixed;top:15px;right:15px;z-index:9999;min-width:280px;';
        toast.innerHTML = '<i class="fas fa-check-circle mr-2"></i> Analysis saved! <a href="/projects" class="alert-link ml-2">View Projects</a>';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    } catch (err) {
        alert('Save Error: ' + err.message);
    }
}
window.confirmSaveProjectMain = confirmSaveProjectMain;

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle
    const btnToggle = document.querySelector('.fa-bars');
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main');

    if (btnToggle && sidebar && main) {
        btnToggle.addEventListener('click', () => {
            if (sidebar.style.display === 'none') {
                sidebar.style.display = 'flex';
            } else {
                sidebar.style.display = 'none';
            }
        });
    }

    // Global state variables
    let latestAnalysis = null;
    let batchResults = null;
    let currentDendroTool = 'select'; // 'select', 'cut', 'pan'
    let selectedBranches = new Set();
    let currentMedoidsSignature = '';
    let debounceRelayoutTimer = null;
    const clientCutCache = new Map();

    // Toolbar Tool Selection
    window.setDendroTool = function(mode) {
        currentDendroTool = mode;
        ['btn-tool-wand', 'btn-tool-cut', 'btn-tool-pan'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.remove('active');
        });

        const activeBtnMap = {
            'select': 'btn-tool-wand',
            'cut': 'btn-tool-cut',
            'pan': 'btn-tool-pan'
        };
        const activeBtn = document.getElementById(activeBtnMap[mode]);
        if (activeBtn) activeBtn.classList.add('active');

        const dendroDiv = document.getElementById('meta-dendrogram');
        if (!dendroDiv || !dendroDiv.data) return;

        if (mode === 'pan') {
            Plotly.relayout('meta-dendrogram', { dragmode: 'pan' });
        } else if (mode === 'cut') {
            Plotly.relayout('meta-dendrogram', { dragmode: false });
        } else {
            // select mode
            Plotly.relayout('meta-dendrogram', { dragmode: 'select' });
        }
    };

    // Zoom Functions
    window.zoomDendrogram = function(factor) {
        const dendroDiv = document.getElementById('meta-dendrogram');
        if (!dendroDiv || !dendroDiv.layout) return;

        const yaxis = dendroDiv.layout.yaxis;
        if (!yaxis || !yaxis.range) return;

        const currentRange = yaxis.range;
        const center = (currentRange[0] + currentRange[1]) / 2;
        const span = (currentRange[1] - currentRange[0]) / factor;
        Plotly.relayout('meta-dendrogram', {
            'yaxis.range': [Math.max(0, center - span / 2), center + span / 2]
        });
    };

    window.resetDendrogramZoom = function() {
        Plotly.relayout('meta-dendrogram', {
            'xaxis.autorange': true,
            'yaxis.autorange': true
        });
    };

    // Branch Selection & Export
    window.exportSelectedBranchesCSV = async function() {
        if (!batchResults) {
            alert('Please run a batch analysis first before exporting.');
            return;
        }

        const exportBtn = document.getElementById('btn-export-csv');
        const origHtml = exportBtn ? exportBtn.innerHTML : '';
        if (exportBtn) {
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
        }

        try {
            // If branches specifically selected, export them; otherwise export active medoids
            const mptsToExport = selectedBranches.size > 0 
                ? Array.from(selectedBranches)
                : Object.values(latestAnalysis.medoids || {});

            const res = await fetch('/export_branches_csv', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mpts_list: mptsToExport })
            });

            if (!res.ok) {
                const errJson = await res.json();
                throw new Error(errJson.error || 'Failed to export CSV');
            }

            const blob = await res.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            // Get filename from header or default
            const disposition = res.headers.get('Content-Disposition');
            let filename = 'mustache_clusters_export.csv';
            if (disposition && disposition.indexOf('filename=') !== -1) {
                filename = disposition.split('filename=')[1].replace(/"/g, '').trim();
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(downloadUrl);
        } catch (err) {
            alert('Export Error: ' + err.message);
        } finally {
            if (exportBtn) {
                exportBtn.disabled = false;
                exportBtn.innerHTML = origHtml;
            }
        }
    };

    function updateSelectedBranchesBadge() {
        const badge = document.getElementById('selected-branches-badge');
        if (!badge) return;
        if (selectedBranches.size > 0) {
            badge.style.display = 'inline-block';
            badge.innerText = `${selectedBranches.size} branch${selectedBranches.size > 1 ? 'es' : ''} selected`;
        } else {
            badge.style.display = 'none';
        }
    }

    // --- Batch Processing Form ---
    const batchForm = document.getElementById('batch-form');
    if (batchForm) {
        batchForm.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const btn = e.target.querySelector('button[type="submit"]');
            // UI State
            const originalBtnHtml = btn.innerHTML;
            btn.disabled = true;
            
            // Clear previous caches
            clientCutCache.clear();
            selectedBranches.clear();
            currentMedoidsSignature = '';
            updateSelectedBranchesBadge();

            // Timer Logic
            const startTime = Date.now();
            const timeDisplay = document.getElementById('proj-time');
            const timerInterval = setInterval(() => {
                const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
                btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing (${elapsed}s)...`;
                if (timeDisplay) timeDisplay.innerText = elapsed + 's';
            }, 100);

            try {
                const res = await fetch('/batch', { method: 'POST', body: formData });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Unknown error');

                // Store Data
                latestAnalysis = data.analysis;
                batchResults = data.results;

                if (latestAnalysis && latestAnalysis.error) {
                    throw new Error(latestAnalysis.error);
                }

                // Update Project Info Sidebar
                const fileName = formData.get('file')?.name || 'Uploaded File';
                document.getElementById('proj-name').innerText = fileName;
                document.getElementById('proj-min-mpts').innerText = formData.get('min_mpts');
                if (timeDisplay && data.execution_time) {
                    timeDisplay.innerText = data.execution_time + 's';
                }

                // Close Modal
                $('#batchConfigModal').modal('hide');

                // Reveal sidebar Save button
                const sidebarSaveBtn = document.getElementById('btn-sidebar-save');
                if (sidebarSaveBtn) sidebarSaveBtn.style.display = 'inline-block';

                // 1. Render Meta-Dendrogram
                if (latestAnalysis.meta_dendrogram_json) {
                    const figure = JSON.parse(latestAnalysis.meta_dendrogram_json);

                    // Adjust margins and spacing
                    figure.layout.margin = { t: 20, r: 20, l: 40, b: 30 };

                    // Add Threshold draggable line
                    let maxY = 0;
                    if (figure.data) {
                        figure.data.forEach(trace => {
                            if (Array.isArray(trace.y) && trace.y.length > 0) {
                                const max_val = Math.max(...trace.y);
                                if (max_val > maxY) maxY = max_val;
                            }
                        });
                    }

                    let threshold = maxY / 2; // initial
                    figure.layout.shapes = [{
                        type: 'line',
                        x0: 0,
                        x1: 1,
                        xref: 'paper',
                        y0: threshold,
                        y1: threshold,
                        yref: 'y',
                        line: { color: '#e53935', width: 2, dash: 'dot' },
                        editable: true
                    }];

                    Plotly.react('meta-dendrogram', figure.data, figure.layout, {
                        responsive: true, displayModeBar: false,
                        edits: { shapePosition: true }
                    });

                    const dendroDiv = document.getElementById('meta-dendrogram');

                    // Support branch selection click
                    dendroDiv.on('plotly_click', (data) => {
                        if (currentDendroTool !== 'select') return;
                        if (!data || !data.points || data.points.length === 0) return;
                        
                        const pt = data.points[0];
                        // If leaf point or label clicked, toggle selection
                        let clickedMpts = null;
                        if (pt.text && !isNaN(parseInt(pt.text))) {
                            clickedMpts = parseInt(pt.text);
                        } else if (pt.x !== undefined && pt.data && pt.data.text && pt.data.text[pt.pointIndex]) {
                            const txt = pt.data.text[pt.pointIndex];
                            if (!isNaN(parseInt(txt))) clickedMpts = parseInt(txt);
                        }

                        if (clickedMpts !== null) {
                            if (selectedBranches.has(clickedMpts)) {
                                selectedBranches.delete(clickedMpts);
                            } else {
                                selectedBranches.add(clickedMpts);
                            }
                            updateSelectedBranchesBadge();
                        }
                    });

                    // Relayout with Debounce & Quantized Height Interval Caching
                    dendroDiv.on('plotly_relayout', (eventData) => {
                        let newY = null;
                        if (eventData['shapes[0].y0'] !== undefined) {
                            newY = eventData['shapes[0].y0'];
                        } else if (eventData['shapes[0].y1'] !== undefined) {
                            newY = eventData['shapes[0].y1'];
                        } else if (eventData.shapes && eventData.shapes[0]) {
                            newY = eventData.shapes[0].y0;
                        }

                        if (newY === null) return;

                        // Debounce slider updates to avoid firing dozens of calls during dragging
                        clearTimeout(debounceRelayoutTimer);
                        debounceRelayoutTimer = setTimeout(async () => {
                            const cacheKey = newY.toFixed(4);

                            // Check Client Cache First
                            if (clientCutCache.has(cacheKey)) {
                                const cached = clientCutCache.get(cacheKey);
                                latestAnalysis.meta_labels = cached.meta_labels;
                                latestAnalysis.medoids = cached.medoids;
                                renderReachabilityPlots(cached.meta_labels, cached.medoids, true);
                                return;
                            }

                            try {
                                const res = await fetch('/cut_dendrogram', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ y_threshold: newY })
                                });
                                const cutData = await res.json();
                                if (!res.ok) throw new Error(cutData.error);

                                // Cache client response
                                clientCutCache.set(cacheKey, cutData);

                                latestAnalysis.meta_labels = cutData.meta_labels;
                                latestAnalysis.medoids = cutData.medoids;
                                renderReachabilityPlots(cutData.meta_labels, cutData.medoids, cutData.from_cache);
                            } catch (err) {
                                console.error('Dendrogram cut failed:', err);
                            }
                        }, 120); // 120ms debounce
                    });
                }

                // 2. Render HAI Heatmap
                renderHAIMatrix(latestAnalysis.hai_matrix, latestAnalysis.ordered_mpts);

                // 3. Render Reachability Plots side by side
                renderReachabilityPlots(latestAnalysis.meta_labels, latestAnalysis.medoids, false);

            } catch (err) {
                alert('Batch Error: ' + err.message);
            } finally {
                clearInterval(timerInterval);
                btn.disabled = false;
                btn.innerHTML = originalBtnHtml;
            }
        };
    }

    // --- Helper Functions ---

    function renderHAIMatrix(matrix, mpts_labels) {
        const data = [{
            z: matrix,
            x: mpts_labels,
            y: mpts_labels,
            type: 'heatmap',
            colorscale: 'Purples',
            reversescale: true,
            showscale: true,
            colorbar: {
                orientation: 'h',
                yanchor: 'top',
                y: -0.15,
                thickness: 15,
                tickfont: { size: 10 }
            }
        }];

        const layout = {
            margin: { t: 30, r: 20, l: 40, b: 60 },
            xaxis: {
                side: 'top',
                tickfont: { size: 10 },
                tickmode: 'array',
                tickvals: mpts_labels
            },
            yaxis: {
                autorange: 'reversed',
                tickfont: { size: 10 },
                tickmode: 'array',
                tickvals: mpts_labels
            }
        };

        Plotly.react('hai-heatmap', data, layout, { responsive: true, displayModeBar: false });
    }

    function renderReachabilityPlots(labels, medoids_mpts, isCached = false) {
        const container = document.getElementById('reachability-container');
        if (!container) return;

        // Check if medoids partition changed
        const newSig = Object.values(medoids_mpts || {}).sort((a, b) => a - b).join('-');
        const cacheIndicator = document.getElementById('cache-indicator');
        if (cacheIndicator) {
            const count = Object.keys(medoids_mpts || {}).length;
            cacheIndicator.innerHTML = isCached || (currentMedoidsSignature === newSig && currentMedoidsSignature !== '')
                ? `<i class="fas fa-bolt text-warning mr-1"></i> Instant Cache (${count} groups)`
                : `<i class="fas fa-check-circle text-success mr-1"></i> Active (${count} groups)`;
        }

        // If medoids are identical to already rendered, avoid re-rendering DOM
        if (currentMedoidsSignature === newSig && currentMedoidsSignature !== '') {
            return;
        }
        currentMedoidsSignature = newSig;

        container.innerHTML = ''; // Clear previous plots

        const uniqueLabels = [...new Set(labels)].sort((a, b) => a - b);
        const colors = ['#00bcd4', '#2196f3', '#4caf50', '#673ab7', '#ff9800', '#e91e63'];

        let i = 0;
        uniqueLabels.forEach(label => {
            if (label === -1) return; // Ignore noise

            const mptsValue = medoids_mpts[label];
            const result = batchResults ? batchResults[mptsValue] : null;

            if (!result || !result.reachability_json) return;

            const color = colors[i % colors.length];

            // Create wrapper div
            const wrapperId = 'reach-plot-' + mptsValue;
            const rDiv = document.createElement('div');
            rDiv.className = 'reachability-plot-wrapper mr-3 flex-shrink-0';
            rDiv.style.width = '280px';
            rDiv.style.height = '380px';
            rDiv.id = wrapperId;
            container.appendChild(rDiv);

            // Parse Plotly JSON
            const figure = JSON.parse(result.reachability_json);

            // Override colors and layout for small multiples
            if (figure.data && figure.data[0]) {
                figure.data[0].marker = { color: color };
            }
            figure.layout.title = '';
            figure.layout.margin = { t: 15, r: 10, l: 30, b: 35 };

            figure.layout.annotations = [{
                text: 'Medoid mpts: ' + mptsValue,
                xref: 'paper', yref: 'paper',
                x: 0.5, y: -0.1,
                showarrow: false,
                font: { color: '#fff', size: 11, weight: 'bold' },
                bgcolor: color,
                borderpad: 4
            }];

            Plotly.newPlot(wrapperId, figure.data, figure.layout, { responsive: true, displayModeBar: false });
            i++;
        });

        if (i === 0) {
            container.innerHTML = '<div class="text-muted p-3">No valid clusters found for current threshold cut.</div>';
        }
    }

    // Listen for project loaded from ?project_id= URL param (fired by index.html inline script)
    document.addEventListener('mustache:project-loaded', (event) => {
        const { analysis, results, metadata } = event.detail;

        latestAnalysis = analysis;
        batchResults = results;
        clientCutCache.clear();
        selectedBranches.clear();
        currentMedoidsSignature = '';
        updateSelectedBranchesBadge();

        // Render Meta-Dendrogram from saved JSON
        if (analysis.meta_dendrogram_json) {
            const figure = JSON.parse(analysis.meta_dendrogram_json);
            figure.layout.margin = { t: 20, r: 20, l: 40, b: 30 };

            let maxY = 0;
            if (figure.data) {
                figure.data.forEach(trace => {
                    if (Array.isArray(trace.y)) {
                        const m = Math.max(...trace.y);
                        if (m > maxY) maxY = m;
                    }
                });
            }
            const threshold = maxY / 2;
            figure.layout.shapes = [{
                type: 'line', x0: 0, x1: 1, xref: 'paper',
                y0: threshold, y1: threshold, yref: 'y',
                line: { color: '#e53935', width: 2, dash: 'dot' },
                editable: true
            }];

            Plotly.react('meta-dendrogram', figure.data, figure.layout, {
                responsive: true, displayModeBar: false,
                edits: { shapePosition: true }
            });

            // Re-attach relayout handler so threshold dragging still works
            const dendroDiv2 = document.getElementById('meta-dendrogram');
            if (dendroDiv2) {
                dendroDiv2.on('plotly_relayout', (evData) => {
                    let newY = null;
                    if (evData['shapes[0].y0'] !== undefined) newY = evData['shapes[0].y0'];
                    else if (evData['shapes[0].y1'] !== undefined) newY = evData['shapes[0].y1'];
                    else if (evData.shapes && evData.shapes[0]) newY = evData.shapes[0].y0;
                    if (newY === null) return;
                    clearTimeout(debounceRelayoutTimer);
                    debounceRelayoutTimer = setTimeout(async () => {
                        const cacheKey = newY.toFixed(4);
                        if (clientCutCache.has(cacheKey)) {
                            const cached = clientCutCache.get(cacheKey);
                            latestAnalysis.meta_labels = cached.meta_labels;
                            latestAnalysis.medoids = cached.medoids;
                            renderReachabilityPlots(cached.meta_labels, cached.medoids, true);
                            return;
                        }
                        try {
                            const res = await fetch('/cut_dendrogram', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ y_threshold: newY })
                            });
                            const cutData = await res.json();
                            if (!res.ok) throw new Error(cutData.error);
                            clientCutCache.set(cacheKey, cutData);
                            latestAnalysis.meta_labels = cutData.meta_labels;
                            latestAnalysis.medoids = cutData.medoids;
                            renderReachabilityPlots(cutData.meta_labels, cutData.medoids, cutData.from_cache);
                        } catch (err) { console.error('Dendrogram cut (project) failed:', err); }
                    }, 120);
                });
            }
        }

        // Render HAI Matrix
        if (analysis.hai_matrix && analysis.ordered_mpts) {
            renderHAIMatrix(analysis.hai_matrix, analysis.ordered_mpts);
        }

        // Render Reachability Plots with current medoids
        if (analysis.meta_labels && analysis.medoids) {
            renderReachabilityPlots(analysis.meta_labels, analysis.medoids, false);
        }
    });

});
