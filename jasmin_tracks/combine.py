import warnings

import huracanpy
import numpy as np
import pandas as pd
from parse import parse
from tqdm import tqdm

from . import datasets


def get_tracks(
    dataset,
    alternative=None,
    filename_filters=None,
    track_filter_func=None,
    drop=None,
    reduce_precision=False,
    start_time=None,
    end_time=None,
    mask_value=None,
    fix_times=False,
    **kwargs,
):
    if isinstance(dataset, str):
        dataset = datasets[dataset]
    if alternative is not None:
        dataset = dataset.select_alternative(alternative)

    all_files = sorted(dataset.find_files(**kwargs))

    if filename_filters is not None:
        all_files = [
            f
            for f in all_files
            if np.all([filter_text not in f for filter_text in filename_filters])
        ]

    all_tracks = []
    for fname in tqdm(all_files, total=len(all_files)):
        tracks = huracanpy.load(
            str(fname), source="TRACK", variable_names=dataset.variable_names
        )

        if track_filter_func is not None:
            tracks = track_filter_func(tracks)

            if tracks is None:
                continue

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

    if drop is not None:
        all_tracks = all_tracks.drop_vars(drop)

    if reduce_precision:
        drop_precision(all_tracks)

    if fix_times:
        tracks = add_times(tracks)

    if start_time is not None:
        genesis = all_tracks.hrcn.get_gen_vals()
        track_ids = genesis.track_id[genesis.time >= start_time]
        all_tracks = all_tracks.hrcn.sel_id(track_ids)

    if end_time is not None:
        lysis = all_tracks.hrcn.get_apex_vals("time")
        track_ids = lysis.track_id[lysis.time < end_time]
        all_tracks = all_tracks.hrcn.sel_id(track_ids)

    if mask_value is not None:
        mask_values(all_tracks, mask_value)

    return all_tracks


def gather_vorticity_profile(tracks):
    """Replace variables named vorticity_{n}hPa with a single variable and a pressure
    coordinate
    """
    plevs = [
        float(result.named["n"])
        for result in [parse("vorticity{n}hpa", var) for var in tracks]
        if result is not None
    ]

    if len(plevs) > 0:
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


def drop_precision(tracks):
    for var in tracks:
        if np.issubdtype(tracks[var].dtype, np.floating):
            tracks[var] = tracks[var].astype(np.float32)
        elif np.issubdtype(tracks[var].dtype, np.integer):
            tracks[var] = tracks[var].astype(np.int32)


def mask_values(tracks, mask_value):
    for var in tracks:
        if np.issubdtype(tracks[var].dtype, np.floating):
            try:
                tracks[var][:] = np.where(
                    tracks[var] == mask_value, np.nan, tracks[var]
                )
            except ValueError:
                tracks[var] = tracks[var].copy()
                tracks[var][:] = np.where(
                    tracks[var] == mask_value, np.nan, tracks[var]
                )


def add_times(tracks):
    # Fix time column
    # The filenames are sorted, so it is all "pos" followed by all "neg"
    year = tracks.period[tracks.sign == "pos"].astype(int)
    year_sh = tracks.period[tracks.sign == "neg"].str.slice(0, 4).astype(int)
    start = pd.to_datetime(pd.DataFrame(dict(year=year, month=1, day=1)))
    start_sh = pd.to_datetime(pd.DataFrame(dict(year=year_sh, month=7, day=1)))
    start = np.concatenate([start, start_sh])
    time = start + (tracks.time - 1) * np.timedelta64(6, "h")
    tracks["time"] = time

    # Drop unneeded variables
    return tracks.drop_vars(["period", "sign"])