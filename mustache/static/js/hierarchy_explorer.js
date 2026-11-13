/* Individual hierarchy inspection; the meta-hierarchy remains in main.js. */
(() => {
    const NOISE = '#8D969B';
    const clusterColor = label => Number(label) === -1 ? NOISE : `hsl(${(Number(label) * 137.508 + 155) % 360}, 55%, 37%)`;
    const lambdaText = (value, infinite = false) => infinite ? '∞' : value == null ? 'unavailable' : Number(value).toPrecision(5);

    // Plot the fitted full single-linkage tree, not the size-condensed group tree.
    // SciPy's default dendrogram traverses each linkage row's left child first;
    // its leaves occupy positions 5, 15, ... . Divide those positions by 10
    // and subtract 0.5 so x also indexes the reachability leaf order.
    function individualDendrogramGeometry(linkage) {
        if (!Array.isArray(linkage) || !linkage.length) throw new Error('This hierarchy has no linkage tree.');
        const n = linkage.length + 1;
        const order = [], stack = [2 * n - 2];
        while (stack.length) {
            const id = stack.pop();
            if (id < n) { order.push(id); continue; }
            const row = linkage[id - n];
            if (!row) throw new Error('Invalid linkage node.');
            stack.push(Number(row[1]), Number(row[0]));
        }
        if (order.length !== n || new Set(order).size !== n) throw new Error('Invalid linkage leaf order.');
        const centre = Array(2 * n - 1), height = Array(2 * n - 1).fill(0);
        order.forEach((id, position) => { centre[id] = position; });
        const x = [], y = [], mergeX = [], mergeY = [], mergeSize = [];
        linkage.forEach((row, index) => {
            const left = Number(row[0]), right = Number(row[1]);
            const value = Number(row[2]);
            if (left >= n + index || right >= n + index || !Number.isFinite(value) || value < 0)
                throw new Error('Invalid linkage merge.');
            x.push(centre[left], centre[left], centre[right], centre[right], null);
            y.push(height[left], value, value, height[right], null);
            centre[n + index] = (centre[left] + centre[right]) / 2;
            height[n + index] = value;
            mergeX.push(centre[n + index]); mergeY.push(value); mergeSize.push(Number(row[3]));
        });
        return { order, x, y, mergeX, mergeY, mergeSize };
    }

    class HierarchyExplorer {
        constructor() {
            this.selection = { mpts: null, group_id: null, pruned_id: null, point_id: null };
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
            this.selection = { mpts: null, group_id: null, pruned_id: null, point_id: null };
            this.members = null;
            const ordered = (analysis?.ordered_mpts || []).map(Number);
            this.select.replaceChildren(...ordered.map(value => new Option(`mpts = ${value}`, value)));
            const saved = analysis?.explorer_selection || {};
            const mpts = ordered.includes(Number(saved.mpts)) ? Number(saved.mpts) : ordered[0];
            if (mpts == null) { this.status('No individual hierarchies are available.'); return; }
            await this.open(mpts);
            if (saved.group_id != null) await this.selectGroup(Number(saved.group_id));
            if (saved.pruned_id != null) await this.selectPruned(Number(saved.pruned_id));
            if (saved.point_id != null) await this.selectPoint(Number(saved.point_id));
        }

        async open(mpts, { scroll = false } = {}) {
            const result = this.results?.[mpts];
            if (!result) { this.status('Select a hierarchy from this analysis.', true); return; }
            ++this.sequence;
            if (this.selection.mpts !== mpts) {
                this.selection = { mpts, group_id: null, pruned_id: null, point_id: null };
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
            await this.drawIndividualDendrogram(result);
            await this.drawReachability(result);
            await this.drawGroupTree(result);
            this.onHierarchyChange?.(mpts);
            if (scroll) document.getElementById('hierarchy-explorer').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        async drawIndividualDendrogram(result) {
            const div = document.getElementById('individual-dendrogram');
            if (!result.linkage_z?.length) {
                Plotly.purge(div);
                div.textContent = 'This saved project has no individual linkage tree.';
                return;
            }
            const geometry = individualDendrogramGeometry(result.linkage_z);
            const n = geometry.order.length;
            const expectedOrder = result.reachability_data?.method === 'hierarchy-adjacent-cophenetic'
                ? result.reachability_data.ordering : null;
            if (expectedOrder && expectedOrder.some((id, index) => Number(id) !== geometry.order[index]))
                throw new Error('The dendrogram and reachability leaf orders disagree.');
            div.style.setProperty('--dendrogram-min-width', `${Math.min(4800, n * 7)}px`);
            const point = this.selection.point_id;
            const markers = geometry.order.map(id => point === id ? '#D27A16'
                : this.members === null || this.members.has(id) ? '#2C7896' : '#B9C2C8');
            await Plotly.react(div, [
                { type: 'scatter', mode: 'lines', x: geometry.x, y: geometry.y,
                    line: { color: '#2F7EBA', width: 1.5 }, hoverinfo: 'skip', showlegend: false },
                { type: 'scatter', mode: 'markers', x: geometry.mergeX, y: geometry.mergeY,
                    customdata: geometry.mergeSize, marker: { color: '#2F7EBA', size: 4, opacity: 0.55 },
                    hovertemplate: 'Merge of %{customdata} points<br>Distance %{y:.6f}<extra></extra>', showlegend: false },
                { type: 'scatter', mode: 'markers', x: geometry.order.map((_, index) => index),
                    y: geometry.order.map(() => 0), customdata: geometry.order,
                    marker: { color: markers, size: geometry.order.map(id => id === point ? 12 : n > 500 ? 5 : 8),
                        line: { color: '#FFFFFF', width: 0.5 } },
                    hovertemplate: 'Input row %{customdata}<br>Click to trace this point<extra></extra>',
                    cliponaxis: false, meta: { role: 'individual-leaves' }, showlegend: false },
            ], {
                template: 'plotly_white', showlegend: false, hovermode: 'closest',
                xaxis: { title: 'Leaf order (input row on hover)', range: [-1, n],
                    dtick: Math.max(1, Math.ceil(n / 15)) },
                yaxis: { title: 'Linkage merge distance', rangemode: 'tozero' },
                margin: { t: 20, l: 75, r: 20, b: 70 }, uirevision: `hierarchy-${result.mpts}`,
            }, { responsive: true, displaylogo: false });
            div.removeAllListeners?.('plotly_click');
            div.on('plotly_click', event => {
                const clicked = event.points?.[0];
                if (clicked?.data?.meta?.role !== 'individual-leaves') return;
                const id = Number(clicked.customdata);
                if (Number.isInteger(id)) this.selectPoint(id);
            });
            document.getElementById('individual-dendrogram-stats').textContent =
                `· mpts = ${result.mpts} · ${n} input points · ${n - 1} merges`;
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
            if (!tree?.groups?.length || !result.condensed_tree?.length) {
                Plotly.purge(div);
                div.textContent = 'This older project has no condensed tree. Rerun the analysis to explore groups.';
                return;
            }
            const groups = new Map(tree.groups.map(group => [Number(group.id), group]));
            const rowsByParent = new Map();
            for (const row of result.condensed_tree) {
                const parent = Number(row.parent);
                if (!rowsByParent.has(parent)) rowsByParent.set(parent, []);
                rowsByParent.get(parent).push(row);
            }
            const order = result.reachability_data?.ordering ||
                Array.from({ length: tree.n_samples }, (_, index) => index);
            const leafPosition = new Map(order.map((point, index) => [Number(point), index]));
            const members = new Map();
            for (const group of [...tree.groups].sort((a, b) => b.id - a.id)) {
                const descendants = [];
                for (const row of rowsByParent.get(group.id) || []) {
                    const child = Number(row.child);
                    descendants.push(...(Number(row.child_size) === 1 ? [child] : members.get(child) || []));
                }
                if (descendants.length !== Number(group.size_at_birth))
                    throw new Error(`Condensed group ${group.id} has inconsistent membership.`);
                members.set(group.id, descendants);
            }
            const center = points => points.reduce((total, point) => total + leafPosition.get(point), 0) / points.length;
            const finite = result.condensed_tree.map(row => row.lambda_val).filter(value => Number.isFinite(value));
            const ceiling = finite.reduce((highest, value) => Math.max(highest, value), 1);
            const lambda = row => row.lambda_infinite || row.birth_lambda_infinite
                ? ceiling * 1.05 : Number(row.lambda_val ?? row.birth_lambda ?? 0);
            const traces = [];
            // Each filled ribbon spans the exact leaf-order interval of the
            // points still in this condensed group. Its width decreases when
            // points depart. This is the HDBSCAN condensed-tree representation,
            // derived from the already fitted CORE-SG linkage, not a new fit.
            for (const group of tree.groups) {
                const remaining = new Set(members.get(group.id));
                const events = new Map();
                for (const row of rowsByParent.get(group.id) || []) {
                    const value = lambda(row);
                    if (!events.has(value)) events.set(value, { departing: [], split: false });
                    if (Number(row.child_size) === 1) events.get(value).departing.push(Number(row.child));
                    else events.get(value).split = true;
                }
                const bandX = [], bandY = [], bandText = [];
                let previous = lambda(group);
                for (const [value, event] of [...events].sort((a, b) => a[0] - b[0])) {
                    if (value > previous && remaining.size) {
                        const positions = [...remaining].map(point => leafPosition.get(point)).sort((a, b) => a - b);
                        if (positions.at(-1) - positions[0] + 1 !== positions.length)
                            throw new Error(`Condensed group ${group.id} is not contiguous in the linkage leaf order.`);
                        const left = positions[0] - 0.48, right = positions.at(-1) + 0.48;
                        bandX.push(left, right, right, left, left, null);
                        bandY.push(previous, previous, value, value, previous, null);
                        bandText.push(...Array(6).fill(`Group ${group.id}<br>${remaining.size} points remain<br>λ ${lambdaText(previous)} → ${lambdaText(value)}`));
                    }
                    for (const point of event.departing) remaining.delete(point);
                    previous = value;
                    if (event.split) break;
                }
                if (bandX.length) traces.push({ type: 'scatter', mode: 'lines',
                    x: bandX, y: bandY, text: bandText, fill: 'toself',
                    fillcolor: group.id === this.selection.group_id ? 'rgba(210,122,22,0.55)' : 'rgba(31,111,95,0.46)',
                    line: { color: group.id === this.selection.group_id ? '#D27A16' : '#1F6F5F', width: 1 },
                    hovertemplate: '%{text}<extra></extra>', showlegend: false });
            }
            const pruned = tree.pruned_subgroups || [];
            const prunedPoints = new Set(pruned.flatMap(item => item.sample_indices));
            const departures = tree.point_departures.filter(row => !prunedPoints.has(Number(row.child)));
            traces.push({ type: 'scatter', mode: 'markers', name: 'Points leaving groups',
                x: departures.map(row => leafPosition.get(Number(row.child))),
                y: departures.map(lambda),
                text: departures.map(row => `Input row ${row.child} leaves group ${row.parent} at λ = ${lambdaText(row.lambda_val, row.lambda_infinite)}`),
                marker: { color: '#AAB0B4', size: 6, symbol: 'diamond', opacity: 0.7 },
                hovertemplate: '%{text}<extra></extra>' });
            traces.push({ type: 'scatter', mode: 'markers', name: 'Small linkage subgroups pruned during condensation',
                x: pruned.map(item => center(item.sample_indices)),
                y: pruned.map(lambda),
                customdata: pruned.map(item => item.id),
                text: pruned.map(item => `Full-linkage subgroup ${item.id}: ${item.size} input points; pruned at λ = ${lambdaText(item.lambda_val, item.lambda_infinite)} because it is below the effective condensation threshold. Click to highlight rows ${item.sample_indices.slice(0, 20).join(', ')}${item.size > 20 ? '…' : ''}.`),
                marker: { color: pruned.map(item => item.id === this.selection.pruned_id ? '#D27A16' : '#B77929'),
                    size: pruned.map(item => item.id === this.selection.pruned_id ? 16 : 11),
                    symbol: 'triangle-down', line: { color: '#FFFFFF', width: 1 } },
                hovertemplate: '%{text}<extra></extra>',
                meta: { role: 'pruned-subgroup-targets' } });
            traces.push({ type: 'scatter', mode: 'markers', name: 'Groups (click to select)',
                x: tree.groups.map(group => center(members.get(group.id))),
                y: tree.groups.map(lambda),
                customdata: tree.groups.map(group => group.id),
                text: tree.groups.map(group => `Group ${group.id} · ${group.size_at_birth} points at birth · λ = ${lambdaText(group.birth_lambda, group.birth_lambda_infinite)}`),
                marker: { color: tree.groups.map(group => group.id === this.selection.group_id ? '#D27A16' : '#1F6F5F'),
                    size: tree.groups.map(group => group.id === this.selection.group_id ? 18 : 13), line: { color: '#FFFFFF', width: 1.5 } },
                hovertemplate: '%{text}<br>Click to inspect descendants<extra></extra>',
                meta: { role: 'group-targets' } });
            await Plotly.react(div, traces, {
                template: 'plotly_white', xaxis: { title: 'Leaf order · band width = points remaining',
                    range: [-1, order.length] },
                yaxis: { title: 'λ = 1 / separation distance', autorange: 'reversed' },
                legend: { orientation: 'h', x: 0, y: -0.32, yanchor: 'top' },
                margin: { t: 30, l: 70, r: 20, b: 125 }, hovermode: 'closest',
                annotations: tree.point_departures.some(row => row.lambda_infinite) ? [{
                    text: '∞ lambda is plotted at the finite-axis edge', xref: 'paper', yref: 'paper', x: 1, y: 0,
                    xanchor: 'right', showarrow: false, font: { size: 10 } }] : [],
            }, { responsive: true, displaylogo: false });
            div.removeAllListeners?.('plotly_click');
            div.on('plotly_click', event => {
                const point = event.points?.[0];
                if (point?.data?.meta?.role === 'group-targets') this.selectGroup(Number(point.customdata));
                if (point?.data?.meta?.role === 'pruned-subgroup-targets') this.selectPruned(Number(point.customdata));
            });
        }

        async selectPruned(subgroupId) {
            const mpts = this.selection.mpts;
            const item = this.results?.[mpts]?.group_tree?.pruned_subgroups?.find(
                candidate => Number(candidate.id) === subgroupId);
            if (!item) { this.status('This pruned linkage subgroup is unavailable.', true); return; }
            this.selection.group_id = null;
            this.selection.pruned_id = subgroupId;
            this.members = new Set(item.sample_indices);
            document.getElementById('group-detail').textContent =
                `Full-linkage subgroup ${subgroupId} · ${item.size} input rows · pruned from condensed group ${item.parent} at λ = ${lambdaText(item.lambda_val, item.lambda_infinite)} because its size is below the effective condensation threshold. It is not a valid condensed group or a selected flat cluster. Rows: ${item.sample_indices.join(', ')}`;
            await this.drawReachability(this.results[mpts]);
            await this.drawIndividualDendrogram(this.results[mpts]);
            await this.drawGroupTree(this.results[mpts]);
            this.status(`Pruned linkage subgroup ${subgroupId} selected · ${item.size} points highlighted`);
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
                this.selection.pruned_id = null;
                this.members = new Set(data.sample_indices);
                const group = data.group;
                document.getElementById('group-detail').textContent =
                    `Group ${groupId} · ${data.count} input rows · born at λ = ${lambdaText(group.birth_lambda, group.birth_lambda_infinite)} · size at birth ${group.size_at_birth} · ${group.point_departures} direct point departures · final flat labels: ${JSON.stringify(data.flat_label_counts)} · rows: ${data.sample_indices.slice(0, 80).join(', ')}${data.count > 80 ? '…' : ''}`;
                await this.drawReachability(this.results[mpts]);
                await this.drawIndividualDendrogram(this.results[mpts]);
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
                heading.textContent = `Input row ${pointId} · final EOM flat label: ${trajectory.flat_label === -1 ? 'noise (−1)' : `cluster ${trajectory.flat_label}`} · hierarchical noise onset (singleton departure) λ = ${lambdaText(trajectory.hierarchical_noise_onset_lambda ?? trajectory.point_departure_lambda, trajectory.hierarchical_noise_onset_infinite ?? trajectory.point_departure_lambda_infinite)}.`;
                target.append(heading);
                const list = document.createElement('ol');
                trajectory.groups.forEach(group => {
                    const item = document.createElement('li');
                    item.textContent = `Group ${group.group_id} (${group.size_at_birth} at birth): λ ${lambdaText(group.birth_lambda)} → λₚ ${lambdaText(group.exit_lambda, group.exit_lambda_infinite)} (leaves this group); exits to ${group.exit_to === 'subgroup' ? `subgroup ${group.next_group_id}` : 'singleton point'}.`;
                    list.append(item);
                });
                target.append(list);
                const note = document.createElement('p'); note.textContent = trajectory.note; target.append(note);
                await this.drawReachability(result);
                await this.drawIndividualDendrogram(result);
                this.status(`Input row ${pointId} traced in mpts = ${mpts}`);
            } catch (error) { this.status(error.message, true); }
        }
    }
    window.HierarchyExplorer = HierarchyExplorer;
    window.mustacheIndividualDendrogramGeometry = individualDendrogramGeometry;
    window.mustacheClusterColor = clusterColor;
})();
