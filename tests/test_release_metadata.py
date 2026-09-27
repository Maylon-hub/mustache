from importlib.metadata import version


def test_runtime_release_versions_match_distribution_metadata():
    import mustache
    import core_sg
    assert mustache.__version__ == version("mustache-core")
    assert core_sg.__version__ == version("core-sg-mustache")
    assert version("hdbscan") == "0.8.44"
