from flask import Blueprint, render_template, request, jsonify
import pandas as pd
from .core import run_clustering
import io

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
        # Read CSV (assume no header for numerical data)
        df = pd.read_csv(file, header=None)
        
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
