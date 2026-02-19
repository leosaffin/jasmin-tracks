from jasmin_tracks import combine
import numpy as np
import pandas as pd

from huracan.interesting_tracks import generate_summary


for scenario in ["hist", "rcp26", "rcp60", "rcp85"]:
    for ensemble_member in range(2, 10 + 1):
        try:
            tracks = combine.get_tracks(
                "MESACLIP",
                drop=["hemisphere", "sign"],
                reduce_precision=True,
                scenario=scenario,
                ensemble_member=ensemble_member
            )

            # Fix time column
            # The filenames are sorted, so it is all "pos" followed by all "neg"
            year = tracks.period[tracks.sign == "pos"].astype(int)
            year_sh = tracks.period[tracks.sign == "neg"].str.slice(0, 4).astype(int)
            start = pd.to_datetime(pd.DataFrame(dict(year=year, month=1, day=1)))
            start_sh = pd.to_datetime(pd.DataFrame(dict(year=year_sh, month=7, day=1)))
            start = np.concat([start, start_sh])
            time = start + (tracks.time - 1) * np.timedelta64(6, "h")
            tracks["time"] = time

            # Drop unneeded variables
            tracks = tracks.drop_vars(["period"])

            # Large dataset. Filter for WCSI before saving
            tracks, summary = generate_summary.apply_filters(
                tracks,
                npoints=4,
                basin=None,
                b_threshold=15,
                vtl_threshold=0,
                vtu_threshold=0,
                vort_threshold=6,
                intensification_threshold=0,
                coherent=True,
                ocean=False,
                filter_size=5,
            )

            summary.to_parquet(
                f"MESACLIP_{scenario}_member{ensemble_member:02d}_WCSI.parquet"
            )
            tracks.hrcn.save(f"MESACLIP_{scenario}_member{ensemble_member:02d}_WCSI.nc")
        except UnboundLocalError:
            print(
                f"Scenario {scenario} with"
                f"ensemble member={ensemble_member} does not exist"
            )
