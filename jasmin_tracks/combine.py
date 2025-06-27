import warnings

from parse import parse
import numpy as np
from tqdm import tqdm
import xarray as xr

import huracanpy
from . import datasets


def get_tracks(dataset_name, alternative=None, **kwargs):
    dataset = datasets[dataset_name]
    if alternative is not None:
        dataset = dataset.select_alternative(alternative)

    all_files = list(dataset.find_files(**kwargs))

    all_tracks = []
    current_track_id = 1
    for n, fname in tqdm(enumerate(all_files), total=len(all_files)):
        tracks = huracanpy.load(str(fname), source="TRACK", variable_names=dataset.variable_names)

        # Reindex track_ids
        track_ids, new_track_ids = np.unique(tracks.track_id, return_inverse=True)
        tracks["track_id_original"] = ("record", tracks.track_id.values)
        tracks["track_id"] = ("record", new_track_ids + current_track_id)
        tracks["track_id"].attrs["cf_role"] = "trajectory_id"

        current_track_id = tracks.track_id.values.max() + 1

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

    all_tracks = xr.concat(all_tracks, dim="record")
    all_tracks = gather_vorticity_profile(all_tracks)

    return all_tracks


def gather_vorticity_profile(tracks):
    """Replace variables named vorticity_{n}hPa with a single variable and a pressure
    coordinate
    """
    plevs = [
        float(result.named["n"]) for result in
        [parse("vorticity{n}hPa", var) for var in tracks.variable_names]
        if result is not None
    ]

    tracks["pressure"] = ("pressure", plevs)
    tracks = tracks.set_coords("pressure")

    vorticity = np.zeros([tracks.sizes["record"], tracks.sizes["pressure"]])
    vorticity_lon = np.zeros_like(vorticity)
    vorticity_lat = np.zeros_like(vorticity)
    for n, plev in enumerate(tracks.pressure.values):
        name = f"vorticity{int(plev)}hPa"
        vorticity[:, n] = tracks[name].values
        vorticity_lon[:, n] = tracks[name + "_lon"].values
        vorticity_lat[:, n] = tracks[name + "_lat"].values

        tracks = tracks.drop_vars([name, name + "_lon", name + "_lat"])

    tracks["relative_vorticity"] = (["record", "pressure"], vorticity)
    tracks["relative_vorticity_lon"] = (["record", "pressure"], vorticity_lon)
    tracks["relative_vorticity_lat"] = (["record", "pressure"], vorticity_lat)

    return tracks
