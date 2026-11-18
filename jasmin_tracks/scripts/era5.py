from datetime import datetime

from jasmin_tracks import combine


end_time=datetime(2025, 1, 1)

kws = dict(
    dataset="ERA5",
    drop=["hemisphere", "period", "sign"],
    reduce_precision=True,
    end_time=end_time,
    mask_value=1e25,
)

combine.get_tracks(**kws).hrcn.save("ERA5_all.nc")
combine.get_tracks(alternative="tcident", **kws).hrcn.save("ERA5_tcident.nc")

kws["drop"] = ["hemisphere"]
kws["fix_times"] = True
for subset in ["nolat-nwc-tcident", "nolat-tcident"]:
    # Southern Hemisphere files are only there without ".new" timestamps
    combine.get_tracks(**kws).save(f"ERA5_{subset}.nc")
