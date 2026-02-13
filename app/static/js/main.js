document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle
    const btnToggle = document.querySelector('.btn-toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const main = document.querySelector('.main');

    if (btnToggle && sidebar && main) {
        btnToggle.addEventListener('click', () => {
            sidebar.classList.toggle('minified');
            main.classList.toggle('expanded');
        });
    }

    // Global variable to store latest results
    let latestAnalysis = null;
    let batchResults = null;

    // --- Single HDBSCAN Form ---
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const btn = e.target.querySelector('button');

            // UI State
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            try {
                const res = await fetch('/upload', { method: 'POST', body: formData });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Unknown error');

                // Render Single Result
                renderSingleResult(data.results);

            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Run HDBSCAN';
            }
        };
    }

    // --- Batch Processing Form ---
    const batchForm = document.getElementById('batch-form');
    if (batchForm) {
        batchForm.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const btn = e.target.querySelector('button');

            // UI State
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running Batch...';

            try {
                const res = await fetch('/batch', { method: 'POST', body: formData });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Unknown error');

                // Store Data
                latestAnalysis = data.analysis;
                batchResults = data.results;

                // 1. Show Batch Panels
                document.getElementById('batch-results').classList.remove('d-none');
                document.getElementById('meta-cluster-panel').classList.remove('d-none');

                // 2. Render HAI Heatmap
                renderHAIMatrix(latestAnalysis.hai_matrix, latestAnalysis.ordered_mpts);

                // 3. Render Meta-Dendrogram
                if (latestAnalysis.meta_dendrogram_json) {
                    const figure = JSON.parse(latestAnalysis.meta_dendrogram_json);
                    Plotly.newPlot('meta-dendrogram', figure.data, figure.layout, { responsive: true });
                }

                // 4. Render Meta-Cluster List
                renderMetaClusters(latestAnalysis.meta_labels, latestAnalysis.medoids);

            } catch (err) {
                alert('Batch Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = 'Run Batch & HAI';
            }
        };
    }

    // --- Helper Functions (Closure Scope) ---

    function renderSingleResult(results) {
        // 1. Label
        const label = document.getElementById('current-view-label');
        if (label) {
            label.className = 'badge badge-success';
            label.innerText = `Result: ${results.n_clusters} clusters`;
        }

        // 2. Plots
        const plots = {
            'dendrogram': results.dendrogram_json,
            'reachability': results.reachability_json,
            'map': results.map_json
        };

        // Helper to render Plotly JSON
        for (const [id, jsonStr] of Object.entries(plots)) {
            if (jsonStr) {
                const figure = JSON.parse(jsonStr);
                Plotly.newPlot(id === 'dendrogram' ? 'dendro-plot' : (id === 'reachability' ? 'reach-plot' : 'map-plot'),
                    figure.data, figure.layout, { responsive: true });
            }
        }
    }

    function renderHAIMatrix(matrix, mpts_labels) {
        const data = [{
            z: matrix,
            x: mpts_labels,
            y: mpts_labels,
            type: 'heatmap',
            colorscale: 'Blues',
            reversescale: true // 1 is match (blue), lower is mismatch
        }];

        const layout = {
            title: 'HAI Similarity Matrix',
            xaxis: { title: 'mpts' },
            yaxis: { title: 'mpts' },
            margin: { t: 30, r: 10, l: 40, b: 40 }
        };

        Plotly.newPlot('hai-heatmap', data, layout, { responsive: true });
    }

    function renderMetaClusters(labels, medoids_mpts) {
        const list = document.getElementById('meta-cluster-list');
        list.innerHTML = '';

        const uniqueLabels = [...new Set(labels)].sort((a, b) => a - b);

        uniqueLabels.forEach(label => {
            if (label === -1) return;

            const mptsValue = medoids_mpts[label];
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">Group ${label}</h6>
                    <small>Medoid: mpts=${mptsValue}</small>
                </div>
            `;

            item.onclick = (e) => {
                e.preventDefault();
                list.querySelectorAll('a').forEach(a => a.classList.remove('active'));
                item.classList.add('active');

                // Load Medoid
                loadMedoidResult(mptsValue);
            };

            list.appendChild(item);
        });
    }

    function loadMedoidResult(mpts) {
        if (batchResults && batchResults[mpts]) {
            renderSingleResult(batchResults[mpts]);

            const label = document.getElementById('current-view-label');
            if (label) {
                label.innerText = `Medoid (mpts=${mpts})`;
                label.className = 'badge badge-info';
            }
        } else {
            console.error('Result not found for mpts', mpts);
        }
    }

});
