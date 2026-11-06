"""The single pinned private HDBSCAN 0.8.44 boundary for CORE-SG trees."""

from importlib.metadata import version


def label_core_sg_linkage(data, linkage, minimum_size):
    """Select flat clusters and retain the *same call's* condensed tree.

    HDBSCAN's public ``HDBSCAN.fit`` increases ``min_cluster_size`` by one
    before calling ``_tree_to_labels`` when ``match_reference_implementation``
    is true. This adapter receives an already fitted CORE-SG linkage, so the
    increment is made here; it is not a second clustering fit.
    """
    if version('hdbscan') != '0.8.44':
        raise RuntimeError('CORE-SG hierarchy adapter requires hdbscan==0.8.44.')
    from hdbscan.hdbscan_ import _tree_to_labels

    output = _tree_to_labels(
        data, linkage, min_cluster_size=int(minimum_size) + 1,
        match_reference_implementation=True,
    )
    if len(output) != 5 or output[3].dtype.names != (
            'parent', 'child', 'lambda_val', 'child_size'):
        raise RuntimeError('HDBSCAN private tree API changed; cannot inspect this hierarchy.')
    return output[0], output[1], output[3]
