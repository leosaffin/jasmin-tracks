from string import Formatter
import re
import pathlib

import yaml

from parse import parse

# Paths to data on JASMIN
# From https://research.reading.ac.uk/huracan/science/data/
huracan_project_path = pathlib.Path(
    "/gws/ssde/j25b/huracan/data/tracks/tropical_cyclones/TRACK/"
)

# Shorthands for defining paths for each dataset
_YYYYMMDDHH = "{year:04d}{month:02d}{day:02d}{hour:02d}"
_YYYYMMDDHH_model = _YYYYMMDDHH.replace("year", "model_year")
_YYYYMMDDHH_model_leap = _YYYYMMDDHH.replace("year", "model_year").replace(
    "day", "model_day"
)


def summary():
    for dataset in datasets:
        print(dataset)
        print(datasets[dataset], "\n")


def _get_keyword_from_string(format_string):
    # A tuple of (keyword, keyword_format) for all unique pairings in format_string
    keywords = [(x[1], x[2]) for x in Formatter().parse(format_string) if x[1]]

    # Preserve ordering for readability when converting to set
    return sorted(set(keywords), key=keywords.index)


def _format_string_by_keyword_subset(format_string, keywords):
    kw_in_string = _get_keyword_from_string(format_string)

    # Get a dictionary subset of the keywords that are present in format_string
    # For any keywords in format_string but not keywords, replace with an asterisk
    kw_matching = dict()
    for kw in kw_in_string:
        if kw[0] in keywords:
            kw_matching[kw[0]] = keywords[kw[0]]
        else:
            if kw[1] == "":
                format_string = format_string.replace("{" + f"{kw[0]}" + "}", "*")
            else:
                format_string = format_string.replace(
                    "{" + f"{kw[0]}:{kw[1]}" + "}", "*"
                )

    # Replace any parts with multiple asterisks with a single asterisk
    format_string = re.sub(r"\*+", "*", format_string)

    return format_string.format(**kw_matching)


class TrackDataset:
    def __init__(
        self, fixed_path, extra_path, filename, variable_names=None, alternatives=None
    ):
        self.fixed_path = pathlib.Path(fixed_path)
        self.extra_path = extra_path
        self.filename = filename
        self.variable_names = variable_names
        self.alternatives = alternatives

    @property
    def full_path(self):
        return str(self.fixed_path / self.extra_path / self.filename)

    @property
    def keys(self):
        return [kw[0] for kw in _get_keyword_from_string(self.full_path)]

    def find_files(self, **kwargs):
        extra_path = _format_string_by_keyword_subset(self.extra_path, kwargs)
        filename = _format_string_by_keyword_subset(self.filename, kwargs)

        return [str(f) for f in self.fixed_path.glob(extra_path + filename)]

    def file_details(self, filename):
        try:
            return parse(self.full_path, filename).named
        except AttributeError:
            # Hindcasts on leap years 29th Feb the days don't match
            details = parse(
                self.full_path.replace(_YYYYMMDDHH_model, _YYYYMMDDHH_model_leap),
                filename,
            ).named
            del details["model_day"]

            return details

    def select_alternative(self, alternative):
        alternative = self.alternatives[alternative].copy()

        for key in ["fixed_path", "extra_path", "filename", "variable_names"]:
            if key not in alternative:
                alternative[key] = getattr(self, key)

        return TrackDataset(**alternative)

    def __str__(self):
        return f"{self.full_path}\n{self.keys}"


def _expand_variable_name(variable_name, variable_sets):
    """Expand a variable-set name in place, or return a regular variable."""
    if variable_name not in variable_sets:
        return [variable_name]

    variable_names = []
    for nested_name in variable_sets[variable_name]:
        variable_names.extend(_expand_variable_name(nested_name, variable_sets))
    return variable_names


def _resolve_variable_names(entry, variable_sets):
    """Expand variable-set names wherever they occur in an entry's list."""
    configured_names = entry.get("variable_names")
    if not configured_names:
        return

    variable_names = []
    for variable_name in configured_names:
        variable_names.extend(_expand_variable_name(variable_name, variable_sets))
    entry["variable_names"] = variable_names


def _expand_path_templates(value, path_templates):
    """Recursively expand named templates embedded in a path string."""
    for name, template in path_templates.items():
        token = "{" + name + "}"
        if token in value:
            replacement = _expand_path_templates(template, path_templates)
            value = value.replace(token, replacement)
    return value


def _resolve_path_templates(entry, path_templates):
    """Expand templates in all path-bearing fields of a dataset entry."""
    for field in ("fixed_path", "extra_path", "filename"):
        if field in entry:
            entry[field] = _expand_path_templates(entry[field], path_templates)


def _load_datasets():
    """Build the dataset registry from the packaged YAML files."""
    config_directory = pathlib.Path(__file__).with_name("datasets")
    with (config_directory / "common.yaml").open() as config_file:
        common = yaml.safe_load(config_file)

    variable_sets = common["variable_sets"]
    path_templates = common["path_templates"]
    configured_datasets = {}
    group_paths = sorted(
        path for path in config_directory.glob("*.yaml") if path.name != "common.yaml"
    )
    for group_path in group_paths:
        with group_path.open() as config_file:
            configured_datasets.update(yaml.safe_load(config_file)["datasets"])

    loaded_datasets = {}

    for name, entry in configured_datasets.items():
        # Preserve the existing placeholder value for unconfigured datasets.
        if entry is None:
            loaded_datasets[name] = (None,)
        else:
            _resolve_path_templates(entry, path_templates)
            entry["fixed_path"] = huracan_project_path / entry["fixed_path"]
            _resolve_variable_names(entry, variable_sets)

            for alternative in (entry.get("alternatives") or {}).values():
                _resolve_path_templates(alternative, path_templates)
                if "fixed_path" in alternative:
                    alternative["fixed_path"] = (
                        huracan_project_path / alternative["fixed_path"]
                    )
                _resolve_variable_names(alternative, variable_sets)

            loaded_datasets[name] = TrackDataset(**entry)

    return loaded_datasets


datasets = _load_datasets()
