from datetime import datetime

from jasmin_tracks import combine


end_time=datetime(2025, 1, 1)

for subset in ["nolat-tcident"]:
    tracks = combine.get_tracks(
        "JRA3Q",
        alternative=subset,
        drop=["hemisphere", "year", "sign"],
        reduce_precision=True,
        end_time=end_time
    )
    tracks.hrcn.save(f"JRA3Q_{subset}.nc")
