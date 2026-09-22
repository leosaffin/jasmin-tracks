"""
Usage:
    find_tracks.py
        [--basin=<str>]
        [--model_year=<model_year>]
        [--year=<year>]
        [--month=<month>]
        [--day=<day>]
    find_tracks.py  (-h | --help)

Arguments:
    --basin=<str>
    --model_year=<model_year>
    --year=<year>
    --month=<month>
    --day=<day>

Options:
    -h --help        Show help

"""

import huracanpy
import numpy as np

from jasmin_tracks import combine
from parse_docopt import parse_docopt
from wcsi import nature


def main(**kwargs):
    keys = kwargs.keys()
    for key in keys:
        kwargs[key] = int(kwargs[key])

    if "basin" in kwargs:
        basin = kwargs["basin"]
        del kwargs["basin"]

        def _select_tcs(tracks):
            return select_tcs(tracks, basin=basin)

    else:
        _select_tcs = select_tcs

    tracks = combine.get_tracks(
        "ECMWF_hindcasts",
        filename_filters=["HIND_VOR_VERTAVG_2016060900_2011060900_10", ".old"],
        track_filter_func=_select_tcs,
        drop=kwargs.keys(),
        reduce_precision=True,
        mask_value=1e25,
    )

    fname = "ecmwf-hindcasts_{basin}_TCs"
    for key in ["model_year", "year", "month", "day"]:
        if key in kwargs:
            fname += f"_{kwargs['key']}"

    huracanpy.save(
        tracks,
        f"hindcast_tracks_{basin}_TC_{kwargs['model_year']}_{kwargs['month']}.nc",
    )


def select_tcs(tracks, basin=None):
    tracks_12hr = tracks.isel(record=np.where(tracks.time.dt.hour % 12 == 0)[0])

    try:
        tracks_tc, summary = nature.wcsi(
            tracks_12hr,
            npoints=3,
            basin=basin,
            b_threshold=15,
            vtl_threshold=0,
            vtu_threshold=0,
            vort_threshold=6,
            intensification_threshold=0,
            coherent=False,
            ocean=False,
            filter_size=3,
        )
    except ValueError:
        # No TC tracks found in basin
        return

    # Add the "is_TC" info back to the full tracks
    tracks = tracks.hrcn.sel_id(summary.loc[summary.is_tc, "track_id"])
    tracks["is_tc"] = ("record", np.zeros(len(tracks.time), dtype=bool))
    tracks.is_tc[tracks.time.dt.hour % 12 == 0] = tracks_tc.is_tc.values

    return tracks


if __name__ == "__main__":
    main(**parse_docopt(__doc__))
