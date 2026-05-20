import datetime

from huracan.interesting_tracks import generate_summary
import pandas as pd
from jasmin_tracks import combine


dataset = "ECMWF_Extended_Ensemble"
start = datetime.datetime(2023, 7, 1)
end = datetime.datetime(2025, 1, 1)
step = datetime.timedelta(days=1)

time = start
while time < end:
    print(time)
    tracks = combine.get_tracks(
        dataset,
        drop=["sign"],
        reduce_precision=True,
        year=time.year,
        month=time.month,
        day=time.day
    )

    tracks["forecast_start"] = (
        "record",
        pd.to_datetime(
            dict(
                year=time.year,
                month=time.month,
                day=time.day,
                hour=tracks.hour,
            )
        ),
    )

    tracks["ensemble_member"][tracks.ensemble_member == "CNTRL"] = "0"
    tracks["ensemble_member"] = tracks.ensemble_member.astype(int)

    tracks = tracks.drop_vars(["hour"])

    # Match initialised tracks to operational analyses

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

    summary.to_parquet(f"EPSEXT_{time.strftime('%Y%m%d')}_WCSI.parquet")
    tracks.hrcn.save(f"EPSEXT_{time.strftime('%Y%m%d')}_WCSI.nc")

    time += step
