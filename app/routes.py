from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import time
from .core import run_clustering
from .core.batch import run_batch_clustering
from scipy.cluster.hierarchy import fcluster

import io
import numpy as np

main = Blueprint('main', __name__)

# Global state to store the latest batch session for dynamic dendrogram cuts
# Acceptable for single-user local tool usage.
SESSION_DATA = {
    'meta_linkage': None,
    'hai_matrix': None,
    'ordered_mpts': None
}

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main.route('/settings')
def settings():
    return render_template('settings.html')

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        # Read CSV with header inference
        df = pd.read_csv(file)
        
        # Ensure we only have numeric data for clustering
        df_numeric = df.select_dtypes(include=[np.number])
        if df_numeric.empty:
            # If inference with header failed or file has no header but read_csv took first row as header
            # Try once more without header if the inferred one has no numeric columns
            file.seek(0)
            df = pd.read_csv(file, header=None)
            df_numeric = df.select_dtypes(include=[np.number])
            
        if df_numeric.empty:
            return jsonify({'error': 'The provided file contains no numerical data for clustering.'}), 400
        
        # Read Labels if provided
        true_labels = None
        labels_file = request.files.get('labels_file')
        if labels_file and labels_file.filename != '':
            true_labels_df = pd.read_csv(labels_file, header=None)
            # Assuming labels are in the first column
            true_labels = true_labels_df.iloc[:, 0].values

        # Get parameters
        min_cluster_size = request.form.get('min_cluster_size', 5)
        min_samples = request.form.get('min_samples', None)
        metric = request.form.get('metric', 'euclidean')
        
        # Run clustering
        results = run_clustering(df, min_cluster_size, min_samples, metric=metric, true_labels=true_labels)
        
        return jsonify({
            'message': 'Clustering successful',
            'results': results,
            'preview': df.head().to_dict(orient='records')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/batch', methods=['POST'])
def batch_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    start_time = time.time()
    try:
        # Read CSV with header inference
        df = pd.read_csv(file)
        
        # Validate numeric data
        if df.select_dtypes(include=[np.number]).empty:
            file.seek(0)
            df = pd.read_csv(file, header=None)
            if df.select_dtypes(include=[np.number]).empty:
                return jsonify({'error': 'The provided file contains no numerical data for clustering.'}), 400
        
        # Get parameters for batch
        min_mpts = int(request.form.get('min_mpts', 2))
        max_mpts = int(request.form.get('max_mpts', 10)) # Default small range for testing
        step = int(request.form.get('step', 1))
        metric = request.form.get('metric', 'euclidean')
        
        # Run batch clustering
        results = run_batch_clustering(df, min_mpts, max_mpts, step, metric=metric)
        
        # Run meta-analysis
        from .core.batch import analyze_batch_results
        analysis = analyze_batch_results(results)
        
        # Store for dynamic cuts
        SESSION_DATA['meta_linkage'] = analysis.get('meta_linkage')
        SESSION_DATA['hai_matrix'] = analysis.get('hai_matrix')
        SESSION_DATA['ordered_mpts'] = analysis.get('ordered_mpts')
        
        # Remove meta_linkage from JSON response since we don't need to send the large matrix
        if 'meta_linkage' in analysis:
            del analysis['meta_linkage']
        
        exec_time = round(time.time() - start_time, 2)
        
        return jsonify({
            'message': 'Batch clustering successful',
            'range': {'min': min_mpts, 'max': max_mpts, 'step': step},
            'results': results,
            'analysis': analysis,
            'execution_time': exec_time
        })

        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main.route('/cut_dendrogram', methods=['POST'])
def cut_dendrogram():
    try:
        data = request.get_json()
        y_threshold = float(data.get('y_threshold', 0.0))
        
        Z = SESSION_DATA.get('meta_linkage')
        hai_matrix = SESSION_DATA.get('hai_matrix')
        ordered_mpts = SESSION_DATA.get('ordered_mpts')

        if Z is None or hai_matrix is None:
            return jsonify({'error': 'No active batch session found.'}), 400
        
        # We need to compute cluster labels using fcluster
        # distance criterion cuts the tree at y_threshold
        labels = fcluster(Z, t=y_threshold, criterion='distance')
        
        # Scipy clustering returns 1-indexed labels (1, 2, 3...)
        # We need to map them back to medoids.
        from .core.hai import compute_medoids
        
        medoids_map = compute_medoids(np.array(hai_matrix), labels)
        
        medoids_mpts = {}
        for label, idx in medoids_map.items():
            if idx < len(ordered_mpts):
                medoids_mpts[int(label)] = int(ordered_mpts[idx])
            
        return jsonify({
            'meta_labels': labels.tolist(),
            'medoids': medoids_mpts
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

