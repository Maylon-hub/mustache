"""Real-Chrome local E2E of the individual hierarchy explorer.

Uses physical mouse clicks, never synthesizes Plotly events. Run with the
qualified Python 3.11 environment: ``python scripts/verify_hierarchy_explorer.py
OUTPUT_DIR``. Starts its own local server and isolated project directory.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_server(url):
    for _ in range(100):
        try:
            with urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(.2)
    raise RuntimeError(f'Local MustaCHE did not start: {url}')


def run(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    port = free_port()
    base = f'http://127.0.0.1:{port}'
    report = {'checks': [], 'console_errors': [], 'failed_responses': [], 'server_url': base}
    with tempfile.TemporaryDirectory(prefix='mustache-explorer-e2e-') as temporary:
        env = dict(os.environ, MUSTACHE_PROJECTS_DIR=str(Path(temporary) / 'projects'))
        env.pop('PYTHONPATH', None)
        server = None

        def start():
            nonlocal server
            server = subprocess.Popen(
                [sys.executable, '-m', 'mustache.cli', '--host', '127.0.0.1', '--port', str(port)],
                cwd=Path(__file__).resolve().parents[1], env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            wait_server(base)

        def check(name, condition):
            report['checks'].append({'name': name, 'passed': bool(condition)})
            assert condition, name

        try:
            start()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel='chrome', headless=True)
                page = browser.new_page(viewport={'width': 1600, 'height': 1000}, accept_downloads=True)
                page.on('console', lambda message: report['console_errors'].append(message.text)
                        if message.type == 'error' else None)
                page.on('pageerror', lambda error: report['console_errors'].append(str(error)))
                page.on('response', lambda response: report['failed_responses'].append([response.url, response.status])
                        if response.status >= 400 else None)
                page.on('dialog', lambda dialog: dialog.accept())

                page.goto(base + '/?sample_dataset=iris')
                form = page.locator('#batch-form')
                form.wait_for(state='visible')
                check('CORE-SG is default', form.locator('[name="algorithm"]').input_value() == 'core-sg')
                form.locator('[name="min_mpts"]').fill('2')
                form.locator('[name="max_mpts"]').fill('6')
                form.locator('[name="step"]').fill('2')
                form.locator('[name="metric"]').select_option('manhattan')
                form.locator('[name="min_cluster_size_mode"]').select_option('explicit')
                form.locator('[name="min_cluster_size"]').fill('8')
                with page.expect_response(lambda response: response.url.endswith('/batch'), timeout=120000) as batch_wait:
                    form.locator('[type="submit"]').click()
                batch = batch_wait.value
                check('batch accepted', batch.ok)
                body = batch.json()
                check('three hierarchies', body['analysis']['ordered_mpts'] == [2, 4, 6])
                check('explicit size and min_samples distinct', all(
                    body['results'][str(m)]['min_cluster_size'] == 8 and
                    body['results'][str(m)]['min_samples'] == m for m in (2, 4, 6)))
                page.locator('.modal-backdrop').wait_for(state='detached')
                page.wait_for_function("document.querySelector('#group-tree-plot')?.data?.at(-1)?.meta?.role === 'group-targets'", timeout=30000)
                check('explorer shows effective parameters', 'minimum cluster size: 8 (explicit)'
                      in page.locator('#explorer-params').inner_text())
                check('HAI and meta hierarchy still rendered', bool(page.locator('#hai-heatmap .js-plotly-plot').count()
                      or page.locator('#hai-heatmap').evaluate('(e) => !!e.data'))
                      and page.locator('#meta-dendrogram').evaluate('(e) => !!e.data'))
                page.screenshot(path=str(output / 'explorer-before-group.png'), full_page=True)

                group_plot = page.locator('#group-tree-plot')
                marker_info = group_plot.evaluate('''element => {
                    const trace = element.data.at(-1);
                    return {ids: trace.customdata, role: trace.meta.role,
                        groups: trace.customdata.length, root: Math.min(...trace.customdata)};
                }''')
                check('real group markers available', marker_info['role'] == 'group-targets'
                      and marker_info['groups'] >= 2)
                index = 1
                marker = page.locator('#group-tree-plot .scatterlayer .trace:last-child .points path').nth(index)
                marker.scroll_into_view_if_needed()
                box = marker.bounding_box()
                check('physical target has size', bool(box and box['width'] >= 7 and box['height'] >= 7))
                with page.expect_response(lambda response: '/api/hierarchies/2/groups/' in response.url, timeout=15000) as group_wait:
                    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                group_response = group_wait.value
                check('physical group click reached backend', group_response.ok)
                group_data = group_response.json()
                check('selected group is the clicked group', group_data['group']['id'] == marker_info['ids'][index])
                check('group detail and highlight update', f"Group {group_data['group']['id']}" in
                      page.locator('#group-detail').inner_text() and
                      'points highlighted' in page.locator('#explorer-status').inner_text())
                page.mouse.move(1, 1)
                page.screenshot(path=str(output / 'explorer-group-selected.png'), full_page=True)

                point_id = group_data['sample_indices'][0]
                page.locator('#point-id').fill(str(point_id))
                with page.expect_response(lambda response: f'/api/hierarchies/2/points/{point_id}' in response.url,
                                          timeout=15000) as point_wait:
                    page.locator('#inspect-point').click()
                point_response = point_wait.value
                check('point lookup reached backend', point_response.ok)
                trajectory = point_response.json()['trajectory']
                check('original row has ancestry', trajectory['point_id'] == point_id and
                      len(trajectory['groups']) >= 2 and trajectory['groups'][0]['group_id'] == marker_info['root'])
                check('point shown on reachability', f'Input row {point_id}' in
                      page.locator('#point-trajectory').inner_text() and
                      len(page.locator('#hierarchy-detail-plot').evaluate('(e) => e.layout.shapes || []')) == 1)
                page.screenshot(path=str(output / 'explorer-point-trajectory.png'), full_page=True)

                page.locator('#inspect-mpts').select_option('4')
                page.wait_for_function("document.querySelector('#explorer-status')?.textContent?.includes('mpts = 4')")
                check('hierarchy switch resets group and point', 'Click a group marker' in
                      page.locator('#group-detail').inner_text() and
                      page.locator('#point-id').input_value() == '')
                page.locator('#inspect-mpts').select_option('2')
                page.wait_for_function("document.querySelector('#explorer-status')?.textContent?.includes('mpts = 2')")
                marker = page.locator('#group-tree-plot .scatterlayer .trace:last-child .points path').nth(index)
                box = marker.bounding_box()
                with page.expect_response(lambda response: '/api/hierarchies/2/groups/' in response.url) as group_wait:
                    page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
                check('group reselected', group_wait.value.ok)
                page.locator('#point-id').fill(str(point_id))
                with page.expect_response(lambda response: f'/api/hierarchies/2/points/{point_id}' in response.url) as point_wait:
                    page.locator('#inspect-point').click()
                check('point reselected', point_wait.value.ok)

                page.locator('#btn-save-top').click()
                page.locator('#main-save-proj-name').fill('Hierarchy explorer E2E')
                with page.expect_response(lambda response: response.url.endswith('/api/projects/save')) as save_wait:
                    page.locator('#saveProjectModalMain .btn-success').click()
                check('project saved', save_wait.value.ok)
                project_id = save_wait.value.json()['project']['id']
                report['project_id'] = project_id
                server.terminate(); server.wait(timeout=15)
                start()
                page.goto(base + f'/?project_id={project_id}')
                page.wait_for_function("id => document.querySelector('#group-detail')?.textContent?.includes(`Group ${id}`)",
                                       arg=group_data['group']['id'], timeout=30000)
                check('reopen restores hierarchy/group/point', page.locator('#inspect-mpts').input_value() == '2'
                      and f"Group {group_data['group']['id']}" in page.locator('#group-detail').inner_text()
                      and f'Input row {point_id}' in page.locator('#point-trajectory').inner_text())
                check('reopen restores explicit size', 'minimum cluster size: 8 (explicit)' in
                      page.locator('#explorer-params').inner_text())
                page.screenshot(path=str(output / 'explorer-after-reopen.png'), full_page=True)
                with page.expect_download() as csv_wait:
                    page.locator('#btn-export-csv').click()
                csv_path = csv_wait.value.path()
                check('CSV exports size metadata', 'MinClusterSize_mpts_' in csv_path.read_text(encoding='utf-8'))
                zip_response = page.request.get(base + f'/api/projects/{project_id}/export_zip')
                check('ZIP export available', zip_response.ok and zip_response.body()[:2] == b'PK')

                page.set_viewport_size({'width': 780, 'height': 900})
                page.wait_for_timeout(500)
                check('narrow viewport stacks explorer plots', page.locator('.explorer-plots').evaluate(
                    "element => getComputedStyle(element).gridTemplateColumns.split(' ').length === 1"))
                check('narrow viewport preserves group plot', page.locator('#group-tree-plot').evaluate(
                    'element => element.data?.at(-1)?.meta?.role === "group-targets"'))
                page.screenshot(path=str(output / 'explorer-narrow-viewport.png'), full_page=True)

                page.locator('#point-id').fill('')
                page.locator('#inspect-point').click()
                check('blank point input is rejected', 'Enter an input row index' in
                      page.locator('#explorer-status').inner_text())

                from sklearn.datasets import make_blobs
                import pandas as pd
                points, _ = make_blobs(n_samples=40, centers=[(-6, -6), (6, 6)],
                                       cluster_std=.18, random_state=11)
                csv_bytes = pd.DataFrame(points, columns=['x', 'y']).to_csv(index=False).encode()
                for minimum_size, all_noise in ((2, False), (20, True)):
                    page.goto(base + '/?configure=1')
                    form = page.locator('#batch-form')
                    form.wait_for(state='visible')
                    form.locator('[name="file"]').set_input_files({
                        'name': 'two_blobs.csv', 'mimeType': 'text/csv', 'buffer': csv_bytes,
                    })
                    form.locator('[name="csv_header"]').select_option('present')
                    form.locator('[name="min_mpts"]').fill('2')
                    form.locator('[name="max_mpts"]').fill('6')
                    form.locator('[name="step"]').fill('2')
                    form.locator('[name="min_cluster_size_mode"]').select_option('explicit')
                    form.locator('[name="min_cluster_size"]').fill(str(minimum_size))
                    with page.expect_response(lambda response: response.url.endswith('/batch'), timeout=120000) as noise_wait:
                        form.locator('[type="submit"]').click()
                    noise_result = noise_wait.value.json()['results']['2']
                    page.wait_for_function("document.querySelector('#hierarchy-detail-plot')?.data?.length > 0")
                    check(f'noise counts for size {minimum_size}', noise_result['noise_points'] > 0 and
                          (noise_result['n_clusters'] == 0 if all_noise else noise_result['n_clusters'] >= 2))
                    colors = page.locator('#hierarchy-detail-plot').evaluate('''element =>
                        Object.fromEntries(element.data.map(trace => [trace.name, trace.marker.color]))''')
                    check(f'genuine noise is gray for size {minimum_size}', colors.get('Noise') == '#8D969B')
                    if all_noise:
                        check('all-noise message is explicit', 'no valid flat clusters' in
                              page.locator('#explorer-status').inner_text())
                    else:
                        check('cluster zero remains a cluster', 'Cluster 0' in colors and
                              colors['Cluster 0'] != colors['Noise'])
                    page.screenshot(path=str(output / f'explorer-noise-size-{minimum_size}.png'), full_page=True)
                check('no browser script errors', not report['console_errors'])
                check('no HTTP errors', not report['failed_responses'])
                browser.close()
        finally:
            if server and server.poll() is None:
                server.terminate(); server.wait(timeout=15)
            (output / 'hierarchy-e2e.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = run(args.output.resolve())
    print(f"{sum(item['passed'] for item in result['checks'])}/{len(result['checks'])} browser checks passed; "
          f"report: {args.output.resolve() / 'hierarchy-e2e.json'}", flush=True)
