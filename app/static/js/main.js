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
    let latestResults = null;

    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const btn = e.target.querySelector('button');
            const output = document.getElementById('output');
            const resultsDiv = document.getElementById('results');

            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            resultsDiv.classList.add('hidden');
            document.getElementById('dendrogram').innerHTML = '';

            try {
                const res = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                if (!res.ok) throw new Error(data.error || 'Unknown error');

                // Store results for export
                latestResults = {
                    timestamp: new Date().toISOString(),
                    parameters: {
                        min_cluster_size: formData.get('min_cluster_size'),
                        min_samples: formData.get('min_samples'),
                        metric: formData.get('metric')
                    },
                    results: data.results
                };

                resultsDiv.classList.remove('hidden');
                output.textContent = JSON.stringify({
                    labels: data.results.labels,
                    n_clusters: data.results.n_clusters,
                    noise_points: data.results.noise_points,
                    metric: formData.get('metric')
                }, null, 2);

                // Display Metrics
                const metricsDiv = document.getElementById('metrics');
                if (data.results.metrics && (data.results.metrics.ARI !== undefined)) {
                    metricsDiv.style.display = 'block';
                    document.getElementById('ari-score').textContent = data.results.metrics.ARI.toFixed(4);
                    document.getElementById('ami-score').textContent = data.results.metrics.AMI.toFixed(4);
                } else {
                    metricsDiv.style.display = 'none';
                }

                if (data.results.dendrogram_json) {
                    const figure = JSON.parse(data.results.dendrogram_json);
                    Plotly.newPlot('dendrogram', figure.data, figure.layout, { responsive: true });
                }

                if (data.results.reachability_json) {
                    const figure = JSON.parse(data.results.reachability_json);
                    Plotly.newPlot('reachability', figure.data, figure.layout, { responsive: true });
                }

                if (data.results.map_json) {
                    const figure = JSON.parse(data.results.map_json);
                    Plotly.newPlot('map', figure.data, figure.layout, { responsive: true });
                }

            } catch (err) {
                alert('Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play"></i> Run Clustering';
            }
        };
    }
});

// About Modal Functions
function openAboutModal() {
    document.getElementById('aboutModal').style.display = 'block';
}

function closeAboutModal() {
    document.getElementById('aboutModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('aboutModal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// Export Results Function
function exportResults() {
    if (!latestResults) {
        alert('No results to export. Please run clustering first.');
        return;
    }

    const dataStr = JSON.stringify(latestResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });

    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mustache_results_${new Date().getTime()}.json`;
    link.click();

    URL.revokeObjectURL(url);
}
