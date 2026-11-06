/* Individual hierarchy inspection; the meta-hierarchy remains in main.js. */
(() => {
    const NOISE = '#8D969B';
    const clusterColor = label => Number(label) === -1 ? NOISE : `hsl(${(Number(label) * 137.508 + 155) % 360}, 55%, 37%)`;
    const lambdaText = (value, infinite = false) => infinite ? '∞' : value == null ? 'unavailable' : Number(value).toPrecision(5);

    class HierarchyExplorer {
        constructor() {
            this.selection = { mpts: null, group_id: null, point_id: null };
            this.members = null;
            this.results = null;
            this.params = {};
            this.sequence = 0;
            this.select = document.getElementById('inspect-mpts');
            document.getElementById('inspect-hierarchy')?.addEventListener('click', () =>
                this.open(Number(this.select.value), { scroll: true }));
            this.select?.addEventListener('change', () => this.open(Number(this.select.value)));
            document.getElementById('inspect-point')?.addEventListener('click', () =>
                this.selectPointFromInput());
            document.getElementById('point-id')?.addEventListener('keydown', event => {
                if (event.key === 'Enter') { event.preventDefault(); this.selectPointFromInput(); }
            });
        }

        selectPointFromInput() {
            const value = document.getElementById('point-id').value.trim();
            if (value === '') { this.status('Enter an input row index before tracing a point.', true); return; }
            this.selectPoint(Number(value));
        }

        status(message, error = false) {
            const element = document.getElementById('explorer-status');
            element.textContent = message;
            element.classList.toggle('text-danger', error);
        }

        async setData(analysis, results, params) {
            this.results = results;
            this.params = params || {};
            const ordered = (analysis?.ordered_mpts || []).map(Number);
            this.select.replaceChildren(...ordered.map(value => new Option(`mpts = ${value}`, value)));
            const saved = analysis?.explorer_selection || {};
            const mpts = ordered.includes(Number(saved.mpts)) ? Number(saved.mpts) : ordered[0];
            if (mpts == null) { this.status('No individual hierarchies are available.'); return; }
            await this.open(mpts);
            if (saved.group_id != null) await this.selectGroup(Number(saved.group_id));
            if (saved.point_id != null) await this.selectPoint(Number(saved.point_id));
        }

        async open(mpts, { scroll = false } = {}) {
            const result = this.results?.[mpts];
            if (!result) { this.status('Select a hierarchy from this analysis.', true); return; }
            ++this.sequence;
            if (this.selection.mpts !== mpts) {
                this.selection = { mpts, group_id: null, point_id: null };
                this.members = null;
                document.getElementById('group-detail').textContent = 'Click a group marker in the tree.';
                document.getElementById('point-trajectory').textContent = 'Enter an input row index or click a reachability bar.';
                document.getElementById('point-id').value = '';
            }
            this.select.value = String(mpts);
            document.getElementById('point-id').max = String(result.n_samples - 1);
            const mode = this.params.min_cluster_size_mode === 'explicit' ? 'explicit' : 'automatic (previous behavior)';
            document.getElementById('explorer-params').textContent =
                `Algorithm: ${result.algorithm || this.params.algorithm} · mpts: ${mpts} · min_samples: ${result.min_samples ?? mpts} · minimum cluster size: ${result.min_cluster_size ?? mpts} (${mode}) · metric: ${result.metric || this.params.metric}`;
            this.status(`Inspecting mpts = ${mpts} · ${result.n_clusters} flat clusters · ${result.noise_points} noise points`);
            if (result.n_clusters === 0) this.status(`mpts = ${mpts}: no valid flat clusters; all ${result.n_samples} points are noise under this selection.`);
            await this.drawReachability(result);
            await this.drawGroupTree(result);
            if (scroll) document.getElementById('hierarchy-explorer').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        async drawReachability(result) {
            const div = document.getElementById('hierarchy-detail-plot');
            const reach = result.reachability_data;
            if (!reach?.ordering || !reach?.labels || !reach?.y) {
                Plotly.purge(div); div.textContent = 'This older project has no per-hierarchy reachability arrays.';
                return;
            }
            const labels = [...new Set(reach.labels.map(Number))].sort((a, b) => a - b);
            const traces = labels.map(label => {
                const positions = reach.labels.map((value, index) => Number(value) === label ? index : -1).filter(index => index >= 0);
                return {
                    type: 'bar', name: label === -1 ? 'Noise' : `Cluster ${label}`,
                    x: positions.map(index => reach.x[index]), y: positions.map(index => reach.y[index]),
                    customdata: positions.map(index => [Number(reach.ordering[index]), label]),
                    marker: { color: clusterColor(label), opacity: positions.map(index =>
                        this.members === null || this.members.has(Number(reach.ordering[index])) ? 1 : 0.18) },
                    hovertemplate: 'Input row %{customdata[0]}<br>Flat label %{customdata[1]}<br>Hierarchy distance %{y:.6f}<extra></extra>',
                };
            });
            const point = this.selection.point_id;
            const position = point == null ? -1 : reach.ordering.indexOf(point);
            await Plotly.react(div, traces, {
                template: 'plotly_white', barmode: 'overlay', bargap: 0,
                xaxis: { title: 'Leaf order (not input row index)' },
                yaxis: { title: 'Adjacent hierarchy merge distance', rangemode: 'tozero' },
                legend: { orientation: 'h', x: 0, y: -0.34, yanchor: 'top' },
                margin: { t: 25, l: 75, r: 20, b: 130 },
                shapes: position < 0 ? [] : [{ type: 'line', x0: position, x1: position,
                    y0: 0, y1: 1, yref: 'paper', line: { color: '#D27A16', width: 3 } }],
            }, { responsive: true, displaylogo: false });
            div.removeAllListeners?.('plotly_click');
            div.on('plotly_click', event => {
                const pointId = event.points?.[0]?.customdata?.[0];
                if (Number.isInteger(pointId)) this.selectPoint(pointId);
            });
            document.getElementById('explorer-reach-stats').textContent =
                `· ${result.n_clusters} clusters · ${result.noise_points}/${result.n_samples} noise · first leaf has no predecessor`;
        }

        async drawGroupTree(result) {
            const div = document.getElementById('group-tree-plot');
            const tree = result.group_tree;
            if (!tree?.groups?.length) {
                Plotly.purge(div);
                div.textContent = 'This older project has no condensed tree. Rerun the analysis to explore groups.';
                return;
            }
            const groups = new Map(tree.groups.map(group => [Number(group.id), group]));
            const y = new Map(); let nextY = 0;
            const place = id => {
                if (y.has(id)) return y.get(id);
                const children = groups.get(id).child_groups.filter(child => groups.has(child));
                const value = children.length ? children.map(place).reduce((a, b) => a + b, 0) / children.length : nextY++;
                y.set(id, value); return value;
            };
            place(tree.root);
            const finite = [...tree.groups.map(group => group.birth_lambda),
                ...tree.point_departures.map(row => row.lambda_val)].filter(value => Number.isFinite(value));
            const ceiling = Math.max(1, ...finite);
            const x = value => value == null ? ceiling * 1.05 : Number(value);
            const traces = [];
            for (const group of tree.groups) {
                if (group.parent == null || !groups.has(group.parent)) continue;
                const parent = groups.get(group.parent);
                traces.push({ type: 'scatter', mode: 'lines', x: [x(parent.birth_lambda), x(group.birth_lambda), x(group.birth_lambda)],
                    y: [y.get(parent.id), y.get(parent.id), y.get(group.id)],
                    line: { color: '#4B7183', width: Math.min(8, 1 + Math.sqrt(group.size_at_birth) / 2) },
                    hoverinfo: 'skip', showlegend: false });
            }
            const departures = new Map();
            for (const row of tree.point_departures) {
                const key = `${row.parent}|${row.lambda_val}|${row.lambda_infinite}`;
                if (!departures.has(key)) departures.set(key, { parent: row.parent, value: row.lambda_val,
                    infinite: row.lambda_infinite, points: [] });
                departures.get(key).points.push(row.child);
            }
            traces.push({ type: 'scatter', mode: 'markers', name: 'Points leaving groups',
                x: [...departures.values()].map(item => x(item.value)),
                y: [...departures.values()].map(item => y.get(item.parent) ?? 0),
                text: [...departures.values()].map(item => `${item.points.length} point(s) leave group ${item.parent} at λ = ${lambdaText(item.value, item.infinite)}; input rows: ${item.points.slice(0, 20).join(', ')}${item.points.length > 20 ? '…' : ''}`),
                marker: { color: '#AAB0B4', size: [...departures.values()].map(item => Math.min(15, 4 + Math.sqrt(item.points.length) * 2)), symbol: 'diamond', opacity: 0.65 },
                hovertemplate: '%{text}<extra></extra>' });
            traces.push({ type: 'scatter', mode: 'markers', name: 'Groups (click to select)',
                x: tree.groups.map(group => x(group.birth_lambda)), y: tree.groups.map(group => y.get(group.id)),
                customdata: tree.groups.map(group => group.id),
                text: tree.groups.map(group => `Group ${group.id} · ${group.size_at_birth} points at birth · λ = ${lambdaText(group.birth_lambda, group.birth_lambda_infinite)}`),
                marker: { color: tree.groups.map(group => group.id === this.selection.group_id ? '#D27A16' : '#1F6F5F'),
                    size: tree.groups.map(group => group.id === this.selection.group_id ? 18 : 13), line: { color: '#FFFFFF', width: 1.5 } },
                hovertemplate: '%{text}<br>Click to inspect descendants<extra></extra>',
                meta: { role: 'group-targets' } });
            await Plotly.react(div, traces, {
                template: 'plotly_white', xaxis: { title: 'λ = 1 / separation distance (not distance)', rangemode: 'tozero' },
                yaxis: { title: 'Group-tree layout (no numeric meaning)', showticklabels: false },
                legend: { orientation: 'h', x: 0, y: -0.34, yanchor: 'top' },
                margin: { t: 25, l: 65, r: 20, b: 130 }, hovermode: 'closest',
                annotations: tree.point_departures.some(row => row.lambda_infinite) ? [{
                    text: '∞ lambda is plotted at the finite-axis edge', xref: 'paper', yref: 'paper', x: 1, y: 1,
                    xanchor: 'right', showarrow: false, font: { size: 10 } }] : [],
            }, { responsive: true, displaylogo: false });
            div.removeAllListeners?.('plotly_click');
            div.on('plotly_click', event => {
                const point = event.points?.[0];
                if (point?.data?.meta?.role === 'group-targets') this.selectGroup(Number(point.customdata));
            });
        }

        async selectGroup(groupId) {
            const mpts = this.selection.mpts, sequence = this.sequence;
            this.status(`Loading group ${groupId} in mpts = ${mpts}…`);
            try {
                const response = await fetch(`/api/hierarchies/${mpts}/groups/${groupId}`);
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to load group.');
                if (sequence !== this.sequence) return;
                this.selection.group_id = groupId;
                this.members = new Set(data.sample_indices);
                const group = data.group;
                document.getElementById('group-detail').textContent =
                    `Group ${groupId} · ${data.count} input rows · born at λ = ${lambdaText(group.birth_lambda, group.birth_lambda_infinite)} · size at birth ${group.size_at_birth} · ${group.point_departures} direct point departures · final flat labels: ${JSON.stringify(data.flat_label_counts)} · rows: ${data.sample_indices.slice(0, 80).join(', ')}${data.count > 80 ? '…' : ''}`;
                await this.drawReachability(this.results[mpts]);
                await this.drawGroupTree(this.results[mpts]);
                this.status(`Group ${groupId} selected · ${data.count} points highlighted`);
            } catch (error) { this.status(error.message, true); }
        }

        async selectPoint(pointId) {
            const mpts = this.selection.mpts, result = this.results?.[mpts], sequence = this.sequence;
            if (!Number.isInteger(pointId) || pointId < 0 || pointId >= result?.n_samples) {
                this.status(`Enter an input row index from 0 to ${(result?.n_samples ?? 1) - 1}.`, true);
                return;
            }
            this.status(`Tracing input row ${pointId}…`);
            try {
                const response = await fetch(`/api/hierarchies/${mpts}/points/${pointId}`);
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || 'Unable to trace point.');
                if (sequence !== this.sequence) return;
                this.selection.point_id = pointId;
                document.getElementById('point-id').value = String(pointId);
                const trajectory = data.trajectory;
                const target = document.getElementById('point-trajectory');
                target.replaceChildren();
                const heading = document.createElement('p');
                heading.textContent = `Input row ${pointId} · final flat label: ${trajectory.flat_label === -1 ? 'noise (−1)' : `cluster ${trajectory.flat_label}`} · singleton departure λ = ${lambdaText(trajectory.point_departure_lambda, trajectory.point_departure_lambda_infinite)}.`;
                target.append(heading);
                const list = document.createElement('ol');
                trajectory.groups.forEach(group => {
                    const item = document.createElement('li');
                    item.textContent = `Group ${group.group_id} (${group.size_at_birth} at birth): λ ${lambdaText(group.birth_lambda)} → ${lambdaText(group.exit_lambda, group.exit_lambda_infinite)}; exits to ${group.exit_to === 'subgroup' ? `subgroup ${group.next_group_id}` : 'singleton point'}.`;
                    list.append(item);
                });
                target.append(list);
                const note = document.createElement('p'); note.textContent = trajectory.note; target.append(note);
                await this.drawReachability(result);
                this.status(`Input row ${pointId} traced in mpts = ${mpts}`);
            } catch (error) { this.status(error.message, true); }
        }
    }
    window.HierarchyExplorer = HierarchyExplorer;
    window.mustacheClusterColor = clusterColor;
})();
