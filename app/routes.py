from flask import Blueprint, render_template, request, jsonify
import pandas as pd
from .core import run_clustering
from .core.batch import run_batch_clustering

import io
import numpy as np

main = Blueprint('main', __name__)

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
        
        return jsonify({
            'message': 'Batch clustering successful',
            'range': {'min': min_mpts, 'max': max_mpts, 'step': step},
            'results': results,
            'analysis': analysis
        })

        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

