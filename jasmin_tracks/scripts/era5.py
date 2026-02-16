from datetime import datetime

import huracanpy
import numpy as np

from jasmin_tracks import datasets, combine


end_time=datetime(2025, 1, 1)

for subset, filename in [("nolat-nwc-tcident", "all"), ("nolat-tcident", "nolat-tcident")]:
    tracks_nh = combine.get_tracks(
        "ERA5",
        alternative=subset,
        drop=["hemisphere", "year", "sign"],
        reduce_precision=True,
        end_time=end_time,
    )

    # Southern Hemisphere files are only there without ".new" timestamps
    datasets["ERA5"].alternatives[subset]["filename"] = (
        datasets["ERA5"].alternatives[subset]["filename"].split(".new")[0]
    )
    tracks_sh = combine.get_tracks(
        "ERA5",
        alternative=subset,
        drop=["sign"],
        reduce_precision=True,
        hemisphere="SH",
    )
    # SH tracks have the year variable as {year}{year+1} for the range
    # year-07-01 to year+1-07-01. e.g 19401941
    # The time variable is an integer number of timesteps where the timestep here is 6 hours
    # So extract year for the start time and add time * 6hrs to get the actual time
    tracks_sh["time"] = np.array(
        tracks_sh.year.str.slice(0, 4) + "-07-01", dtype="datetime64"
    ) + (tracks_sh.time - 1) * np.timedelta64(6, "h")
    tracks_sh = tracks_sh.drop_vars(["year"])

    lysis = tracks_sh.hrcn.get_apex_vals("time")
    track_ids = lysis.track_id[lysis.time < end_time]
    tracks_sh = tracks_sh.hrcn.sel_id(track_ids)

    # Original track ID already saved as "track_id_original". Setting keep_track_id=True
    # would overwrite track_id_original with the intermediate track IDs created when
    # creating the separate NH and SH subsets
    tracks = huracanpy.concat_tracks([tracks_nh, tracks_sh], keep_track_id=False)

    huracanpy.save(tracks, f"ERA5_{filename}.nc")

for subset in ["tcident"]:
    tracks = combine.get_tracks(
        "ERA5",
        alternative=subset,
        drop=["hemisphere", "year", "sign"],
        reduce_precision=True,
        end_time=end_time
    )
    tracks.hrcn.save(f"ERA5_{subset}.nc")
