import re
from pathlib import Path

import pytest
import yaml


CONFIG_DIRECTORY = Path(__file__).parents[1] / "jasmin_tracks" / "datasets"
DATASET_FIELDS = {
    "fixed_path",
    "extra_path",
    "filename",
    "variable_names",
    "alternatives",
}
PATH_FIELDS = ("fixed_path", "extra_path", "filename")
TEMPLATE_REFERENCE = re.compile(r"\{([A-Z][A-Za-z0-9_]*)\}")


@pytest.fixture(scope="module")
def common_config():
    with (CONFIG_DIRECTORY / "common.yaml").open() as config_file:
        return yaml.safe_load(config_file)


@pytest.fixture(scope="module")
def grouped_datasets():
    groups = []
    group_paths = sorted(
        path
        for path in CONFIG_DIRECTORY.glob("*.yaml")
        if path.name != "common.yaml"
    )
    for group_path in group_paths:
        with group_path.open() as config_file:
            groups.append((group_path.name, yaml.safe_load(config_file)["datasets"]))
    return groups


def _assert_acyclic(graph):
    complete = set()

    def visit(node, active):
        assert node not in active, f"Circular reference: {' -> '.join((*active, node))}"
        if node in complete:
            return
        for dependency in graph[node]:
            visit(dependency, (*active, node))
        complete.add(node)

    for node in graph:
        visit(node, ())


def _expand_variable_names(names, variable_sets):
    expanded = []
    for name in names:
        if name in variable_sets:
            expanded.extend(_expand_variable_names(variable_sets[name], variable_sets))
        else:
            expanded.append(name)
    return expanded


def _expand_path(value, path_templates):
    for name, template in path_templates.items():
        token = "{" + name + "}"
        if token not in value:
            continue
        value = value.replace(
            token, _expand_path(template, path_templates)
        )
    return value


def test_configuration_files_exist(grouped_datasets):
    assert (CONFIG_DIRECTORY / "common.yaml").is_file()
    assert grouped_datasets


def test_common_configuration(common_config):
    assert set(common_config) == {"path_templates", "variable_sets"}

    path_templates = common_config["path_templates"]
    assert isinstance(path_templates, dict)
    assert all(
        isinstance(name, str) and isinstance(template, str)
        for name, template in path_templates.items()
    )
    template_graph = {
        name: set(TEMPLATE_REFERENCE.findall(template)) & path_templates.keys()
        for name, template in path_templates.items()
    }
    _assert_acyclic(template_graph)

    variable_sets = common_config["variable_sets"]
    assert isinstance(variable_sets, dict)
    assert all(
        isinstance(names, list) and all(isinstance(name, str) for name in names)
        for names in variable_sets.values()
    )
    variable_graph = {
        name: set(names) & variable_sets.keys()
        for name, names in variable_sets.items()
    }
    _assert_acyclic(variable_graph)


def test_dataset_definitions(grouped_datasets, common_config):
    seen = set()
    path_templates = common_config["path_templates"]

    def check_entry(entry, *, alternative=False):
        assert isinstance(entry, dict)
        assert set(entry) <= DATASET_FIELDS
        if not alternative:
            assert {"fixed_path", "extra_path", "filename"} <= entry.keys()
            assert not Path(entry["fixed_path"]).is_absolute()
        for field in PATH_FIELDS:
            if field in entry:
                assert isinstance(entry[field], str)
                assert set(TEMPLATE_REFERENCE.findall(entry[field])) <= path_templates.keys()
        if "variable_names" in entry:
            assert isinstance(entry["variable_names"], list)
            assert all(isinstance(name, str) for name in entry["variable_names"])
        for nested in (entry.get("alternatives") or {}).values():
            check_entry(nested, alternative=True)

    for filename, datasets in grouped_datasets:
        assert isinstance(datasets, dict), filename
        for name, entry in datasets.items():
            assert name not in seen, f"Duplicate dataset definition: {name}"
            seen.add(name)
            if entry is not None:
                check_entry(entry)


def test_loaded_datasets_match_configuration(grouped_datasets, common_config):
    import jasmin_tracks

    raw_datasets = {
        name: entry
        for _, datasets in grouped_datasets
        for name, entry in datasets.items()
    }
    assert list(jasmin_tracks.datasets) == list(raw_datasets)

    variable_sets = common_config["variable_sets"]
    path_templates = common_config["path_templates"]
    for name, entry in raw_datasets.items():
        loaded = jasmin_tracks.datasets[name]
        if entry is None:
            assert loaded == (None,)
            continue

        assert loaded.fixed_path == (
            jasmin_tracks.huracan_project_path
            / _expand_path(entry["fixed_path"], path_templates)
        )
        assert loaded.extra_path == _expand_path(entry["extra_path"], path_templates)
        assert loaded.filename == _expand_path(entry["filename"], path_templates)
        expected_names = _expand_variable_names(
            entry.get("variable_names", []), variable_sets
        )
        assert loaded.variable_names == (expected_names or None)

        for alternative_name, alternative in entry.get("alternatives", {}).items():
            loaded_alternative = loaded.alternatives[alternative_name]
            for field in PATH_FIELDS:
                if field not in alternative:
                    continue
                expected = _expand_path(alternative[field], path_templates)
                if field == "fixed_path":
                    expected = jasmin_tracks.huracan_project_path / expected
                assert loaded_alternative[field] == expected
            if "variable_names" in alternative:
                assert loaded_alternative["variable_names"] == _expand_variable_names(
                    alternative["variable_names"], variable_sets
                )
