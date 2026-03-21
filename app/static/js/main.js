// Global functions for modals
function openBatchConfigModal() {
    $('#batchConfigModal').modal('show');
}

// Ensure the function is accessible globally
window.openBatchConfigModal = openBatchConfigModal;

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

    // Global variable to store latest results
    let latestAnalysis = null;
    let batchResults = null;

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
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            try {
                const res = await fetch('/batch', { method: 'POST', body: formData });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Unknown error');

                // Store Data
                latestAnalysis = data.analysis;
                batchResults = data.results;

                // Update Project Info Sidebar
                const fileName = formData.get('file').name;
                document.getElementById('proj-name').innerText = fileName;
                document.getElementById('proj-min-mpts').innerText = formData.get('min_mpts');

                // Close Modal
                $('#batchConfigModal').modal('hide');

                // 1. Render Meta-Dendrogram
                if (latestAnalysis.meta_dendrogram_json) {
                    const figure = JSON.parse(latestAnalysis.meta_dendrogram_json);

                    // Adjust margins and spacing
                    figure.layout.margin = { t: 20, r: 20, l: 40, b: 20 };

                    // Add Threshold draggable line
                    let maxY = 0;
                    if (figure.data) {
                        figure.data.forEach(trace => {
                            if (trace.y) {
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
                        line: { color: 'red', width: 2, dash: 'dot' },
                        editable: true
                    }];

                    Plotly.react('meta-dendrogram', figure.data, figure.layout, {
                        responsive: true, displayModeBar: false,
                        edits: { shapePosition: true }
                    });

                    const dendroDiv = document.getElementById('meta-dendrogram');
                    dendroDiv.on('plotly_relayout', async (eventData) => {
                        let newY = null;
                        if (eventData['shapes[0].y0'] !== undefined) {
                            newY = eventData['shapes[0].y0'];
                        } else if (eventData['shapes[0].y1'] !== undefined) {
                            newY = eventData['shapes[0].y1'];
                        } else if (eventData.shapes && eventData.shapes[0]) {
                            newY = eventData.shapes[0].y0;
                        }

                        // Force threshold line to be horizontal by ensuring y0 == y1
                        if (newY !== null) {
                            // Enforce horizontal line if the user dragged just one end
                            const isHorizontal = eventData['shapes[0].y0'] !== undefined && eventData['shapes[0].y1'] !== undefined;

                            try {
                                const res = await fetch('/cut_dendrogram', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ y_threshold: newY })
                                });
                                const cutData = await res.json();
                                if (!res.ok) throw new Error(cutData.error);

                                // Store new labels and medoids to ensure redrawing happens smoothly
                                latestAnalysis.meta_labels = cutData.meta_labels;
                                latestAnalysis.medoids = cutData.medoids;
                                renderReachabilityPlots(cutData.meta_labels, cutData.medoids);
                            } catch (err) {
                                console.error('Dendrogram cut failed:', err);
                            }
                        }
                    });
                }

                // 2. Render HAI Heatmap
                renderHAIMatrix(latestAnalysis.hai_matrix, latestAnalysis.ordered_mpts);

                // 3. Render Reachability Plots side by side
                renderReachabilityPlots(latestAnalysis.meta_labels, latestAnalysis.medoids);

            } catch (err) {
                alert('Batch Error: ' + err.message);
            } finally {
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
            colorscale: 'Purples', // As seen in screenshot
            reversescale: true,
            showscale: true,
            colorbar: {
                orientation: 'h',
                yanchor: 'top',
                y: -0.15, // push below the x-axis
                thickness: 15,
                tickfont: { size: 10 }
            }
        }];

        const layout = {
            margin: { t: 30, r: 20, l: 40, b: 60 }, // increased bottom margin for colorbar
            xaxis: {
                side: 'top',
                tickfont: { size: 10 },
                tickmode: 'array',
                tickvals: mpts_labels
            },
            yaxis: {
                autorange: 'reversed', // to make it visually match traditional heatmaps with 0,0 top-left or match legacy
                tickfont: { size: 10 },
                tickmode: 'array',
                tickvals: mpts_labels
            }
        };

        Plotly.react('hai-heatmap', data, layout, { responsive: true, displayModeBar: false });
    }

    function renderReachabilityPlots(labels, medoids_mpts) {
        const container = document.getElementById('reachability-container');
        container.innerHTML = ''; // Clear previous

        const uniqueLabels = [...new Set(labels)].sort((a, b) => a - b);

        // Define a qualitative palette for the meta-clusters as in the paper
        const colors = ['#00bcd4', '#2196f3', '#4caf50', '#673ab7', '#ff9800', '#e91e63'];

        let i = 0;
        uniqueLabels.forEach(label => {
            if (label === -1) return; // Ignore noise in meta-clusters if any

            const mptsValue = medoids_mpts[label];
            const result = batchResults[mptsValue];

            if (!result || !result.reachability_json) return;

            const color = colors[i % colors.length];

            // Create wrapper div
            const wrapperId = 'reach-plot-' + mptsValue;
            const rDiv = document.createElement('div');
            rDiv.className = 'reachability-plot-wrapper';
            rDiv.id = wrapperId;
            container.appendChild(rDiv);

            // Parse Plotly JSON
            const figure = JSON.parse(result.reachability_json);

            // Override colors and layout for small multiples
            if (figure.data && figure.data[0]) {
                figure.data[0].marker = { color: color };
                // figure.data[0].fillcolor = color; // If it's filled
            }
            // Remove full title, keep it minimal
            figure.layout.title = '';
            figure.layout.margin = { t: 10, r: 10, l: 30, b: 30 };

            // Add custom annotation for 'mpts: X' at bottom center
            figure.layout.annotations = [{
                text: 'mpts: ' + mptsValue,
                xref: 'paper', yref: 'paper',
                x: 0.5, y: -0.05,
                showarrow: false,
                font: { color: '#fff', size: 12 },
                bgcolor: color,
                borderpad: 4
            }];

            Plotly.newPlot(wrapperId, figure.data, figure.layout, { responsive: true, displayModeBar: false });

            i++;
        });
    }

});
