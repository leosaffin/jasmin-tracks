from datetime import datetime

from jasmin_tracks import combine


end_time=datetime(2025, 1, 1)

kws = dict(
    dataset="JRA3Q",
    drop=["hemisphere", "period", "sign"],
    reduce_precision=True,
    end_time=end_time,
    mask_value=1e25,
)
combine.get_tracks(**kws).hrcn.save("JRA3Q_all.nc")

for subset in ["tcident", "nolat-tcident", "nolat-nwc-tcident"]:
    tracks = combine.get_tracks(alternative=subset, **kws).hrcn.save(
        f"JRA3Q_{subset}.nc"
    )
