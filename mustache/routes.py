from flask import Blueprint, render_template, request, jsonify, send_file, Response
import pandas as pd
import time
from .core import run_clustering
from .core.batch import run_batch_clustering
from .core import storage
from .core.validation import SUPPORTED_METRICS
from scipy.cluster.hierarchy import fcluster

import io
import numpy as np

main = Blueprint('main', __name__)

# In-memory session store for local interactive GUI sessions (single-worker server).
# Note: For multi-worker production deployments (e.g. gunicorn -w 4), session state
# should be backed by a persistent key-value store like Redis or file-based caching.
SESSION_DATA = {
    'meta_linkage': None,
    'hai_matrix': None,
    'ordered_mpts': None
}

@main.route('/')
def index():
    if request.args.get('new') == '1':
        SESSION_DATA.clear()
        SESSION_DATA.update({
            'meta_linkage': None,
            'hai_matrix': None,
            'ordered_mpts': None
        })
    project_id = request.args.get('project_id', '')
    sample_dataset = request.args.get('sample_dataset', '')
    return render_template('index.html', project_id=project_id, sample_dataset=sample_dataset, supported_metrics=SUPPORTED_METRICS)

@main.route('/datasets')
def datasets_page():
    from .core.sample_datasets import list_datasets
    query = request.args.get('q', '').strip().lower()
    datasets = [item for item in list_datasets() if query in (item['name'] + ' ' + item['description']).lower()]
    return render_template('datasets.html', datasets=datasets)

@main.route('/api/datasets/<dataset_key>/csv')
def sample_dataset_csv(dataset_key):
    from .core.sample_datasets import load_dataset
    try:
        frame, info = load_dataset(dataset_key)
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 404
    return Response(
        frame.to_csv(index=False),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={dataset_key}.csv'}
    )

@main.route('/projects')
def projects_page():
    return render_template('home.html')

@main.route('/dashboard')
def dashboard():
    # Historical alternate page had disconnected single/batch handlers.
    # Keep its URL working through the canonical explorer.
    from flask import redirect, url_for
    return redirect(url_for('main.index'))

@main.route('/settings')
def settings():
    return render_template('settings.html', supported_metrics=SUPPORTED_METRICS)


def read_csv_upload(file, header_mode='auto'):
    """Infer a numeric headerless CSV without dropping its first sample."""
    if header_mode not in ('auto', 'present', 'absent'):
        raise ValueError('CSV header must be auto, present or absent.')
    if header_mode == 'present':
        return pd.read_csv(file)
    frame = pd.read_csv(file, header=None)
    if header_mode == 'absent':
        return frame
    first = pd.to_numeric(frame.iloc[0], errors='coerce')
    if first.notna().all():
        return frame.apply(pd.to_numeric, errors='raise')
    file.seek(0)
    return pd.read_csv(file)

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
    try:
        selected_mpts = [int(value) for value in data.get('selected_mpts', SESSION_DATA.get('selected_mpts', []))]
    except (TypeError, ValueError):
        return jsonify({'error': 'Selected mpts values must be integers.'}), 400
    
    results = SESSION_DATA.get('results')
    params = SESSION_DATA.get('params', {})
    raw_df = SESSION_DATA.get('raw_data')
    
    if results is None:
        return jsonify({'error': 'No active analysis to save.'}), 400
    if any(str(value) not in results for value in selected_mpts):
        return jsonify({'error': 'Selected mpts values do not belong to this analysis.'}), 400
        
    analysis = {
        'meta_linkage': SESSION_DATA.get('meta_linkage').tolist() if isinstance(SESSION_DATA.get('meta_linkage'), np.ndarray) else SESSION_DATA.get('meta_linkage'),
        'hai_matrix': SESSION_DATA.get('hai_matrix'),
        'ordered_mpts': SESSION_DATA.get('ordered_mpts'),
        'meta_labels': SESSION_DATA.get('meta_labels'),
        'medoids': SESSION_DATA.get('last_medoids'),
        'outliers': SESSION_DATA.get('outliers', []),
        'meta_dendrogram_json': SESSION_DATA.get('meta_dendrogram_json'),
        'hai_computation': SESSION_DATA.get('hai_computation'),
        'selected_mpts': selected_mpts
    }
    analysis['selection_mode'] = SESSION_DATA.get('selection_mode', 'automatic')
    analysis['cut_threshold'] = SESSION_DATA.get('cut_threshold')
    analysis['times'] = SESSION_DATA.get('times', {})
    analysis['automatic_partition'] = SESSION_DATA.get('automatic_partition')
    analysis['manual_groups'] = SESSION_DATA.get('manual_groups', [])
    
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
        SESSION_DATA['dataset_name'] = params.get('dataset_name') or data.get('metadata', {}).get('name', 'dataset')
        SESSION_DATA['cut_cache'] = {}
        SESSION_DATA['last_medoids'] = analysis.get('medoids', {})
        SESSION_DATA['meta_labels'] = analysis.get('meta_labels')
        SESSION_DATA['selection_mode'] = analysis.get('selection_mode', 'automatic')
        SESSION_DATA['cut_threshold'] = analysis.get('cut_threshold')
        SESSION_DATA['times'] = analysis.get('times', {})
        SESSION_DATA['automatic_partition'] = analysis.get('automatic_partition') or ({
            'meta_labels': analysis.get('meta_labels'), 'medoids': analysis.get('medoids'),
            'outliers': analysis.get('outliers', []),
        } if analysis.get('selection_mode', 'automatic') == 'automatic' else None)
        SESSION_DATA['outliers'] = analysis.get('outliers', [])
        SESSION_DATA['meta_dendrogram_json'] = analysis.get('meta_dendrogram_json')
        SESSION_DATA['hai_computation'] = analysis.get('hai_computation')
        SESSION_DATA['selected_mpts'] = analysis.get('selected_mpts', [])
        SESSION_DATA['manual_groups'] = analysis.get('manual_groups', [])
        
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
        df = read_csv_upload(file, request.form.get('csv_header', 'auto'))
        
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
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/batch', methods=['POST'])
def batch_process():
    sample_dataset = request.form.get('sample_dataset', '').strip()
    file = request.files.get('file')
    if not sample_dataset and (file is None or file.filename == ''):
        return jsonify({'error': 'Select a CSV file or a sample dataset.'}), 400
    if sample_dataset and file is not None and file.filename:
        return jsonify({'error': 'Select either a sample dataset or a CSV file, not both.'}), 400
        
    start_time = time.time()
    try:
        if sample_dataset:
            from .core.sample_datasets import load_dataset
            df, dataset_info = load_dataset(sample_dataset)
            dataset_name = dataset_info.name
        else:
            # Read CSV with header inference
            df = read_csv_upload(file, request.form.get('csv_header', 'auto'))
            dataset_name = file.filename
        
        # Validate numeric data
        if df.select_dtypes(include=[np.number]).empty:
            if file is None:
                return jsonify({'error': 'The sample dataset contains no numerical data.'}), 400
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
        exec_time = round(time.time() - start_time, 4)
        analysis['selection_mode'] = 'automatic'
        analysis['cut_threshold'] = None
        
        # Store for dynamic cuts and export
        SESSION_DATA['meta_linkage'] = analysis.get('meta_linkage')
        SESSION_DATA['hai_matrix'] = analysis.get('hai_matrix')
        SESSION_DATA['ordered_mpts'] = analysis.get('ordered_mpts')
        SESSION_DATA['meta_labels'] = analysis.get('meta_labels')
        SESSION_DATA['last_medoids'] = analysis.get('medoids')
        SESSION_DATA['outliers'] = analysis.get('outliers', [])
        SESSION_DATA['meta_dendrogram_json'] = analysis.get('meta_dendrogram_json')
        SESSION_DATA['hai_computation'] = analysis.get('hai_computation')
        SESSION_DATA['selected_mpts'] = []
        SESSION_DATA['manual_groups'] = []
        SESSION_DATA['selection_mode'] = 'automatic'
        SESSION_DATA['cut_threshold'] = None
        SESSION_DATA['times'] = analysis.get('times', {})
        SESSION_DATA['automatic_partition'] = {key: analysis[key] for key in ('meta_labels', 'medoids', 'outliers')}
        SESSION_DATA['results'] = results
        SESSION_DATA['raw_data'] = df
        SESSION_DATA['cut_cache'] = {}
        SESSION_DATA['dataset_name'] = dataset_name
        SESSION_DATA['params'] = {
            'min_mpts': min_mpts,
            'max_mpts': max_mpts,
            'step': step,
            'metric': metric,
            'algorithm': algorithm
        }
        SESSION_DATA['params'].update(dataset_name=dataset_name, n_samples=len(df), execution_time=exec_time)
        SESSION_DATA['params']['csv_header'] = request.form.get('csv_header', 'auto') if not sample_dataset else 'present'
        
        # Remove meta_linkage from JSON response since we don't need to send the large matrix
        if 'meta_linkage' in analysis:
            del analysis['meta_linkage']
        
        
        return jsonify({
            'message': 'Batch clustering successful',
            'range': {'min': min_mpts, 'max': max_mpts, 'step': step},
            'results': results,
            'analysis': analysis,
            'execution_time': exec_time,
            'params': SESSION_DATA['params']
        })

        
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main.route('/cut_dendrogram', methods=['POST'])
def cut_dendrogram():
    try:
        data = request.get_json() or {}
        if data.get('mode') == 'manual':
            ordered = SESSION_DATA.get('ordered_mpts')
            hai = SESSION_DATA.get('hai_matrix')
            if ordered is None or hai is None:
                return jsonify({'error': 'No active batch session found.'}), 400
            groups = data.get('groups', [])
            if not isinstance(groups, list) or any(not isinstance(group, list) or not group for group in groups):
                return jsonify({'error': 'Manual meta-clusters must be a list of non-empty mpts groups.'}), 400
            flattened = [value for group in groups for value in group]
            if any(not isinstance(value, int) or isinstance(value, bool) or value not in ordered for value in flattened) or len(set(flattened)) != len(flattened):
                return jsonify({'error': 'Manual groups must contain valid, non-overlapping mpts values.'}), 400
            labels = np.full(len(ordered), -1, dtype=int)
            for group_id, group in enumerate(groups):
                labels[[ordered.index(value) for value in group]] = group_id
            from .core.hai import compute_medoids
            medoids = {group: ordered[index] for group, index in compute_medoids(np.array(hai), labels).items()}
            payload = {'meta_labels': labels.tolist(), 'medoids': medoids, 'outliers': [],
                       'selection_mode': 'manual', 'cut_threshold': None, 'manual_groups': groups,
                       'unselected_count': len(ordered) - len(flattened), 'from_cache': False}
            SESSION_DATA.update(meta_labels=labels.tolist(), last_medoids=medoids, outliers=[],
                selection_mode='manual', cut_threshold=None, manual_groups=groups)
            return jsonify(payload)
        if data.get('mode') == 'automatic':
            partition = SESSION_DATA.get('automatic_partition')
            if not partition:
                return jsonify({'error': 'This older project did not preserve its automatic meta-clustering partition.'}), 400
            SESSION_DATA.update(meta_labels=partition['meta_labels'], last_medoids=partition['medoids'], outliers=partition['outliers'], selection_mode='automatic', cut_threshold=None)
            return jsonify({**partition, 'selection_mode': 'automatic', 'cut_threshold': None, 'from_cache': False})
        y_threshold = float(data.get('y_threshold', 0.0))
        if not np.isfinite(y_threshold) or y_threshold < 0:
            return jsonify({'error': 'Cut threshold must be a finite non-negative distance.'}), 400
        
        Z = SESSION_DATA.get('meta_linkage')
        hai_matrix = SESSION_DATA.get('hai_matrix')
        ordered_mpts = SESSION_DATA.get('ordered_mpts')

        if Z is None or hai_matrix is None:
            return jsonify({'error': 'No active batch session found.'}), 400
        
        Z_arr = np.asarray(Z)
        # Discretize height intervals to cache identical partitions
        heights = np.sort(np.unique(Z_arr[:, 2])) if Z_arr.size else np.array([])
        interval_idx = int(np.searchsorted(heights, y_threshold, side='right'))
        
        cut_cache = SESSION_DATA.setdefault('cut_cache', {})
        if interval_idx in cut_cache:
            # Instant return from memory cache
            cached = dict(cut_cache[interval_idx])
            cached['from_cache'] = True
            cached['cut_threshold'] = y_threshold
            SESSION_DATA.update(meta_labels=cached['meta_labels'], last_medoids=cached['medoids'], outliers=[], selection_mode='threshold', cut_threshold=y_threshold)
            return jsonify(cached)

        # Compute cluster labels using fcluster
        labels = fcluster(Z_arr, t=y_threshold, criterion='distance') if Z_arr.size else np.array([1])
        
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
            'from_cache': False,
            'outliers': [], 'selection_mode': 'threshold', 'cut_threshold': y_threshold
        }
        cut_cache[interval_idx] = result_payload
        SESSION_DATA.update(last_medoids=medoids_mpts, meta_labels=labels.tolist(), outliers=[], selection_mode='threshold', cut_threshold=y_threshold)
        return jsonify(result_payload)
    except (TypeError, ValueError) as e:
        return jsonify({'error': str(e)}), 400
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


