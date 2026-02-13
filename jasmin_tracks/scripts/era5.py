from datetime import datetime

import huracanpy
import numpy as np

from jasmin_tracks import datasets, combine


end_time=datetime(2025, 1, 1)

tracks_nh = combine.get_tracks(
    "ERA5",
    alternative="nolat-nwc-tcident",
    drop=["hemisphere", "year", "sign"],
    reduce_precision=True,
    end_time=end_time,
)

# Southern Hemisphere files are only there without ".new" timestamps
datasets["ERA5"].alternatives["nolat-nwc-tcident"]["filename"] = (
    datasets["ERA5"].alternatives["nolat-nwc-tcident"]["filename"].split(".new")[0]
)
tracks_sh = combine.get_tracks(
    "ERA5",
    alternative="nolat-nwc-tcident",
    drop=["sign"],
    reduce_precision=True,
    end_time=end_time,
    hemisphere="SH",
)
# SH tracks have the year variable as {year}{year+1} for the range
# year-07-01 to year+1-07-01. e.g 19401941
# The time variable is an integer number of timesteps where the timestep here is 6 hours
# So extract year for the start time and add time * 6hrs to get the actual time
tracks_sh["time"] = np.array(
    tracks_sh.year.str.slice(0, 4) + "-07-01", dtype="datetime64"
) + tracks_sh.time * np.timedelta64(6, "h")
tracks_sh = tracks_sh.drop_vars(["year"])

# Original track ID already saved as "track_id_original". Setting keep_track_id=True
# would overwrite track_id_original with the intermediate track IDs created when
# creating the separate NH and SH subsets
tracks = huracanpy.concat_tracks([tracks_nh, tracks_sh], keep_track_id=False)

huracanpy.save(tracks, "ERA5_all.nc")

for subset in ["tcident", "nolat-tcident"]:
    tracks = combine.get_tracks(
        "ERA5",
        alternative=subset,
        drop=["hemisphere", "year", "sign"],
        reduce_precision=True,
        end_time=end_time
    )
    tracks.hrcn.save(f"ERA5_{subset}.nc")
