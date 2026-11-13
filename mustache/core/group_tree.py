"""Explore the HDBSCAN-condensed view of an already fitted hierarchy.

Point IDs below are zero-based input row positions. Cluster IDs are HDBSCAN
internal IDs (at least ``n_samples``); they are never dataset row IDs.
"""

from collections import defaultdict, deque
import math


def serialize_condensed_tree(tree):
    """Turn the pinned HDBSCAN 0.8.44 record array into portable JSON rows."""
    rows = []
    for row in tree:
        value = float(row['lambda_val'])
        rows.append({
            'parent': int(row['parent']), 'child': int(row['child']),
            'lambda_val': value if math.isfinite(value) else None,
            'lambda_infinite': math.isinf(value),
            'child_size': int(row['child_size']),
        })
    return rows


def _index_tree(rows, n_samples):
    if not rows:
        raise ValueError('This hierarchy has no condensed-tree data.')
    by_parent = defaultdict(list)
    incoming = {}
    for row in rows:
        parent, child = int(row['parent']), int(row['child'])
        if parent < n_samples or child in incoming:
            raise ValueError('Invalid condensed-tree parent or duplicate child.')
        incoming[child] = row
        by_parent[parent].append(row)
    roots = set(by_parent) - set(incoming)
    if len(roots) != 1:
        raise ValueError('Condensed tree must have exactly one root group.')
    root = roots.pop()
    points = {child for child in incoming if child < n_samples}
    if points != set(range(n_samples)):
        raise ValueError('Condensed-tree point IDs do not match input row positions.')
    return root, by_parent, incoming


def _pruned_linkage_subgroups(linkage, incoming, n_samples, threshold):
    """Recover the small children pruned by HDBSCAN's tree condensation.

    This only annotates the fitted linkage. It never changes the condensed
    tree, flat labels, HAI, or the CORE-SG extraction. The replay checks every
    emitted child against the actual condensed tree so a future HDBSCAN
    convention change cannot silently misidentify a discarded subgroup.
    """
    if len(linkage) != n_samples - 1:
        raise ValueError('Linkage and condensed tree have different sample counts.')

    def size(node):
        return 1 if node < n_samples else int(linkage[node - n_samples][3])

    def leaves(node):
        points, stack = [], [node]
        while stack:
            current = stack.pop()
            if current < n_samples:
                points.append(current)
            else:
                left, right = linkage[current - n_samples][:2]
                stack.extend((int(left), int(right)))
        return sorted(points)

    def matches(edge, parent, child_size, value):
        if edge is None or int(edge['parent']) != parent or int(edge['child_size']) != child_size:
            return False
        if math.isinf(value):
            return bool(edge.get('lambda_infinite'))
        return not edge.get('lambda_infinite') and math.isclose(
            float(edge['lambda_val']), value, rel_tol=1e-12, abs_tol=1e-12)

    subgroups = []
    queue = deque([(2 * n_samples - 2, n_samples)])
    next_group = n_samples + 1
    while queue:
        node, group = queue.popleft()
        left, right, distance = linkage[node - n_samples][:3]
        left, right = int(left), int(right)
        value = 1.0 / float(distance) if distance > 0 else math.inf
        small = [child for child in (left, right) if size(child) < threshold]
        large = [child for child in (left, right) if size(child) >= threshold]
        if len(large) == 2:
            for child in (left, right):
                if not matches(incoming.get(next_group), group, size(child), value):
                    raise ValueError('Linkage and condensed group branches disagree.')
                queue.append((child, next_group))
                next_group += 1
        else:
            for child in small:
                points = leaves(child)
                if any(not matches(incoming.get(point), group, 1, value) for point in points):
                    raise ValueError('Linkage and condensed point departures disagree.')
                if len(points) > 1:
                    subgroups.append({
                        'id': child, 'id_namespace': 'full_linkage_node',
                        'parent': group, 'size': len(points),
                        'sample_indices': points,
                        'lambda_val': None if math.isinf(value) else value,
                        'lambda_infinite': math.isinf(value),
                        'status': 'pruned_below_condensation_threshold',
                    })
            if large:
                queue.append((large[0], group))
    return subgroups


def group_tree_summary(rows, n_samples, min_cluster_size, linkage=None):
    """Condensed topology, point departures and checked pruned linkage nodes."""
    root, by_parent, incoming = _index_tree(rows, n_samples)
    groups = []
    for group_id in sorted(by_parent):
        edge = incoming.get(group_id)
        children = by_parent[group_id]
        groups.append({
            'id': group_id,
            'parent': int(edge['parent']) if edge else None,
            'birth_lambda': edge['lambda_val'] if edge else 0.0,
            'birth_lambda_infinite': bool(edge.get('lambda_infinite')) if edge else False,
            'size_at_birth': int(edge['child_size']) if edge else n_samples,
            'child_groups': [int(child['child']) for child in children
                             if int(child['child_size']) > 1],
            'point_departures': sum(int(child['child_size']) == 1 for child in children),
        })
    if linkage is not None and root != n_samples:
        raise ValueError('Condensed-tree root does not match the linkage sample count.')
    pruned = (_pruned_linkage_subgroups(linkage, incoming, n_samples,
                                      int(min_cluster_size) + 1)
              if linkage is not None else [])
    return {
        'root': root, 'groups': groups, 'n_samples': n_samples,
        'min_cluster_size': int(min_cluster_size),
        # HDBSCAN 0.8.44 with match_reference_implementation=True internally
        # increments the public minimum size before condensing this tree.
        'condensation_threshold': int(min_cluster_size) + 1,
        'point_departures': [row for row in rows if int(row['child_size']) == 1],
        'pruned_subgroups': pruned,
        'pruned_subgroups_status': 'reconstructed_and_checked' if linkage is not None else 'not_recorded',
        'method': 'hdbscan-condense-tree-from-fitted-linkage',
        'point_id_convention': 'zero-based input row position, not leaf order',
    }


def group_members(rows, n_samples, group_id):
    """All original input rows descending from a condensed-tree group."""
    root, by_parent, _ = _index_tree(rows, n_samples)
    if group_id not in by_parent:
        raise ValueError(f'Unknown group {group_id}.')
    members, stack, visited = [], [group_id], set()
    while stack:
        node = stack.pop()
        if node in visited:
            raise ValueError('Cycle in condensed tree.')
        visited.add(node)
        for child in by_parent[node]:
            child_id = int(child['child'])
            if int(child['child_size']) == 1:
                members.append(child_id)
            else:
                stack.append(child_id)
    if any(point < 0 or point >= n_samples for point in members):
        raise ValueError('Condensed-tree point ID is outside the dataset.')
    return sorted(members)


def point_trajectory(rows, n_samples, point_id, flat_label):
    """Trace parent groups from root to a point's departure edge.

    The departure from a group occurs at its next edge on this path. Final
    flat-cluster noise is a *separate* EOM-selection outcome, not inferred from
    the mere existence of a singleton departure in the condensed tree.
    """
    root, by_parent, incoming = _index_tree(rows, n_samples)
    if point_id < 0 or point_id >= n_samples:
        raise ValueError('Point index is outside the dataset.')
    path = []
    child = point_id
    visited = set()
    while child != root:
        if child in visited or child not in incoming:
            raise ValueError('Point has no valid route to the root group.')
        visited.add(child)
        edge = incoming[child]
        group_id = int(edge['parent'])
        group_birth = incoming.get(group_id)
        path.append({
            'group_id': group_id,
            'size_at_birth': int(group_birth['child_size']) if group_birth else n_samples,
            'birth_lambda': group_birth['lambda_val'] if group_birth else 0.0,
            'exit_lambda': edge['lambda_val'],
            'exit_lambda_infinite': bool(edge.get('lambda_infinite')),
            'exit_to': 'point' if child == point_id else 'subgroup',
            'next_group_id': child if child != point_id else None,
        })
        child = group_id
    path.reverse()
    return {
        'point_id': point_id, 'flat_label': int(flat_label),
        'flat_status': 'noise' if int(flat_label) == -1 else 'cluster',
        'groups': path, 'point_departure_lambda': path[-1]['exit_lambda'],
        'point_departure_lambda_infinite': path[-1]['exit_lambda_infinite'],
        # Hierarchical noise begins when the point leaves its last condensed
        # group. EOM's final flat noise label is a separate global selection.
        'hierarchical_noise_onset_lambda': path[-1]['exit_lambda'],
        'hierarchical_noise_onset_infinite': path[-1]['exit_lambda_infinite'],
        'flat_noise_transition_lambda': None,
        'root': root,
        'note': ('The singleton departure is the hierarchical noise-onset '
                 'lambda for this condensed tree. The final flat noise label '
                 'comes from EOM cluster selection and has no separate '
                 'universal transition lambda.'),
    }
