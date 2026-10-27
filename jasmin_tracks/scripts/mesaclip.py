import sys

from jasmin_tracks import combine


scenario = sys.argv[1]
ensemble_member = int(sys.argv[2])
try:
    tracks = combine.get_tracks(
        "MESACLIP",
        drop=["hemisphere"],
        reduce_precision=True,
        scenario=scenario,
        ensemble_member=ensemble_member,
        filter_tcs=True,
        mask_value=1e25,
        fix_times=True,
    )

    tracks.hrcn.save(f"MESACLIP_{scenario}_member{ensemble_member:02d}_WCSI.nc")
except UnboundLocalError:
    print(
        f"Scenario {scenario} with "
        f"ensemble member={ensemble_member} does not exist"
    )
