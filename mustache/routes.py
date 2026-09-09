from flask import Blueprint, render_template, request, jsonify, send_file
import pandas as pd
import time
from .core import run_clustering
from .core.batch import run_batch_clustering
from .core import storage
from scipy.cluster.hierarchy import fcluster

import io
import numpy as np

main = Blueprint('main', __name__)

# Global state to store the latest batch session for dynamic dendrogram cuts
SESSION_DATA = {
    'meta_linkage': None,
    'hai_matrix': None,
    'ordered_mpts': None
}

@main.route('/')
def index():
    project_id = request.args.get('project_id', '')
    return render_template('index.html', project_id=project_id)

@main.route('/projects')
def projects_page():
    return render_template('home.html')

@main.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main.route('/settings')
def settings():
    return render_template('settings.html')

@main.route('/api/session_status')
def session_status():
    has_batch = SESSION_DATA.get('results') is not None
    return jsonify({
        'has_active_batch': has_batch,
        'dataset_name': SESSION_DATA.get('dataset_name', '')
    })

@main.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify(storage.list_projects())

@main.route('/api/projects/save', methods=['POST'])
def save_project_route():
    data = request.get_json() or {}
    name = data.get('name', 'My Analysis')
    
    results = SESSION_DATA.get('results')
    params = SESSION_DATA.get('params', {})
    raw_df = SESSION_DATA.get('raw_data')
    
    if results is None:
        return jsonify({'error': 'No active analysis to save.'}), 400
        
    analysis = {
        'meta_linkage': SESSION_DATA.get('meta_linkage').tolist() if isinstance(SESSION_DATA.get('meta_linkage'), np.ndarray) else SESSION_DATA.get('meta_linkage'),
        'hai_matrix': SESSION_DATA.get('hai_matrix'),
        'ordered_mpts': SESSION_DATA.get('ordered_mpts'),
        'meta_labels': SESSION_DATA.get('meta_labels'),
        'medoids': SESSION_DATA.get('last_medoids'),
        'meta_dendrogram_json': SESSION_DATA.get('meta_dendrogram_json')
    }
    
    meta = storage.save_project(name, params, analysis, results, raw_df)
    return jsonify({'success': True, 'project': meta})

@main.route('/api/projects/<project_id>/data', methods=['GET'])
def get_project_data(project_id):
    try:
        data = storage.load_project(project_id)
        analysis = data.get('analysis', {})
        results = data.get('results', {})
        params = data.get('params', {})
        raw_df = data.get('raw_df')
        
        SESSION_DATA['meta_linkage'] = analysis.get('meta_linkage')
        SESSION_DATA['hai_matrix'] = analysis.get('hai_matrix')
        SESSION_DATA['ordered_mpts'] = analysis.get('ordered_mpts')
        SESSION_DATA['results'] = results
        SESSION_DATA['raw_data'] = raw_df
        SESSION_DATA['params'] = params
        SESSION_DATA['dataset_name'] = data.get('metadata', {}).get('name', 'dataset')
        SESSION_DATA['cut_cache'] = {}
        SESSION_DATA['last_medoids'] = analysis.get('medoids', {})
        SESSION_DATA['meta_dendrogram_json'] = analysis.get('meta_dendrogram_json')
        
        return jsonify({
            'metadata': data.get('metadata'),
            'params': params,
            'analysis': analysis,
            'results': results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 404

@main.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project_route(project_id):
    success = storage.delete_project(project_id)
    return jsonify({'success': success})

@main.route('/api/projects/<project_id>/export_zip', methods=['GET'])
def export_project_zip_route(project_id):
    try:
        zip_buf = storage.create_project_zip(project_id)
        return send_file(
            zip_buf,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"mustache_project_{project_id}.zip"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

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
        algorithm = request.form.get('algorithm', 'core-sg')
        
        # Run clustering
        results = run_clustering(df, min_cluster_size, min_samples, metric=metric, algorithm=algorithm, true_labels=true_labels)
        
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
        algorithm = request.form.get('algorithm', 'core-sg')
        
        # Run batch clustering
        results = run_batch_clustering(df, min_mpts, max_mpts, step, metric=metric, algorithm=algorithm)
        
        # Run meta-analysis
        from .core.batch import analyze_batch_results
        analysis = analyze_batch_results(results)
        
        # Store for dynamic cuts and export
        SESSION_DATA['meta_linkage'] = analysis.get('meta_linkage')
        SESSION_DATA['hai_matrix'] = analysis.get('hai_matrix')
        SESSION_DATA['ordered_mpts'] = analysis.get('ordered_mpts')
        SESSION_DATA['meta_labels'] = analysis.get('meta_labels')
        SESSION_DATA['last_medoids'] = analysis.get('medoids')
        SESSION_DATA['meta_dendrogram_json'] = analysis.get('meta_dendrogram_json')
        SESSION_DATA['results'] = results
        SESSION_DATA['raw_data'] = df
        SESSION_DATA['cut_cache'] = {}
        SESSION_DATA['dataset_name'] = getattr(file, 'filename', 'dataset.csv')
        SESSION_DATA['params'] = {
            'min_mpts': min_mpts,
            'max_mpts': max_mpts,
            'step': step,
            'metric': metric,
            'algorithm': algorithm
        }
        
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
        
        Z_arr = np.asarray(Z)
        # Discretize height intervals to cache identical partitions
        heights = np.sort(np.unique(Z_arr[:, 2]))
        interval_idx = int(np.searchsorted(heights, y_threshold))
        
        cut_cache = SESSION_DATA.setdefault('cut_cache', {})
        if interval_idx in cut_cache:
            # Instant return from memory cache
            cached = dict(cut_cache[interval_idx])
            cached['from_cache'] = True
            return jsonify(cached)

        # Compute cluster labels using fcluster
        labels = fcluster(Z_arr, t=y_threshold, criterion='distance')
        
        from .core.hai import compute_medoids
        medoids_map = compute_medoids(np.array(hai_matrix), labels)
        
        medoids_mpts = {}
        for label, idx in medoids_map.items():
            if idx < len(ordered_mpts):
                medoids_mpts[int(label)] = int(ordered_mpts[idx])
            
        result_payload = {
            'meta_labels': labels.tolist(),
            'medoids': medoids_mpts,
            'interval_idx': interval_idx,
            'from_cache': False
        }
        cut_cache[interval_idx] = result_payload
        SESSION_DATA['last_medoids'] = medoids_mpts
        return jsonify(result_payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main.route('/export_branches_csv', methods=['POST'])
def export_branches_csv():
    try:
        from flask import Response
        import io

        df = SESSION_DATA.get('raw_data')
        results = SESSION_DATA.get('results')
        if df is None or results is None:
            return jsonify({'error': 'No active clustering data found to export.'}), 400

        data = request.get_json(silent=True) or {}
        selected_mpts = data.get('mpts_list')

        # If no specific list is passed, use current active medoids
        if not selected_mpts:
            last_medoids = SESSION_DATA.get('last_medoids', {})
            selected_mpts = list(last_medoids.values())

        if not selected_mpts:
            # Fallback: all available mpts
            selected_mpts = [int(k) for k in results.keys()]

        # Build exported DataFrame
        export_df = df.copy()

        for mpts in selected_mpts:
            key = str(mpts)
            if key in results:
                res = results[key]
                if 'labels' in res:
                    export_df[f'Cluster_mpts_{mpts}'] = res['labels']
                if 'probabilities' in res:
                    export_df[f'Prob_mpts_{mpts}'] = [round(p, 4) for p in res['probabilities']]

        # Generate CSV string in memory
        output = io.StringIO()
        export_df.to_csv(output, index=True, index_label='Sample_Index')
        csv_content = output.getvalue()

        dataset_base = SESSION_DATA.get('dataset_name', 'dataset')
        if '.' in dataset_base:
            dataset_base = dataset_base.rsplit('.', 1)[0]
        filename = f"{dataset_base}_mustache_clusters.csv"

        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


