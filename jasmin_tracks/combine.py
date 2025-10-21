import warnings

from parse import parse
import numpy as np
from tqdm import tqdm

import huracanpy
from . import datasets


def get_tracks(dataset_name, alternative=None, **kwargs):
    dataset = datasets[dataset_name]
    if alternative is not None:
        dataset = dataset.select_alternative(alternative)

    all_files = sorted(dataset.find_files(**kwargs))

    all_tracks = []
    for n, fname in tqdm(enumerate(all_files), total=len(all_files)):
        tracks = huracanpy.load(
            str(fname), source="TRACK", variable_names=dataset.variable_names
        )

        # Add specific details from files
        try:
            details = dataset.file_details(fname)
            for key in details:
                if key not in kwargs:
                    if key in tracks:
                        raise ValueError(
                            f"Need to add {key} to tracks but it already exists"
                        )

                    tracks[key] = ("record", [details[key]] * len(tracks.time))

            all_tracks.append(tracks)
        except AttributeError as e:
            warnings.warn(f"Failed to get details from file {fname}\n" + str(e) + "\n")

    all_tracks = huracanpy.concat_tracks(all_tracks, keep_track_id=True)
    all_tracks = gather_vorticity_profile(all_tracks)

    return all_tracks


def gather_vorticity_profile(tracks):
    """Replace variables named vorticity_{n}hPa with a single variable and a pressure
    coordinate
    """
    plevs = [
        float(result.named["n"]) for result in
        [parse("vorticity{n}hpa", var) for var in tracks]
        if result is not None
    ]

    tracks["pressure"] = ("pressure", plevs)
    tracks = tracks.set_coords("pressure")

    vorticity = np.zeros([tracks.sizes["record"], tracks.sizes["pressure"]])
    vorticity_lon = np.zeros_like(vorticity)
    vorticity_lat = np.zeros_like(vorticity)
    for n, plev in enumerate(tracks.pressure.values):
        name = f"vorticity{int(plev)}hpa"
        vorticity[:, n] = tracks[name].values
        vorticity_lon[:, n] = tracks[name + "_lon"].values
        vorticity_lat[:, n] = tracks[name + "_lat"].values

        tracks = tracks.drop_vars([name, name + "_lon", name + "_lat"])

    tracks["relative_vorticity"] = (["record", "pressure"], vorticity)
    tracks["relative_vorticity_lon"] = (["record", "pressure"], vorticity_lon)
    tracks["relative_vorticity_lat"] = (["record", "pressure"], vorticity_lat)

    return tracks
