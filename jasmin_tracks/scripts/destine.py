import numpy as np
import wcsi

from jasmin_tracks import combine


def select_tcs(tracks):

    tracks["wcsi"] = (
        "record",
        wcsi(
            tracks.track_id,
            tracks.cps_b,
            tracks.cps_vtl,
            tracks.cps_vtu,
            tracks.relative_vorticity,
            filter_all=~np.isnan(tracks.mslp_lon),
            npoints=4,
            b_threshold=15,
            vtl_threshold=0,
            vtu_threshold=0,
            vort_threshold=None,
            vort_warm_core_threshold=None,
            intensification_threshold=0,
            coherent=False,
            filter_size=5,
            vort_warm_core_filter_size=None,
        ),
    )

    if ~tracks.wcsi.any():
        return

    # Subset to TCs
    tracks = tracks.hrcn.sel_id(np.unique(tracks.track_id[tracks.wcsi]))

    tracks["nature"] = (
        "record",
        wcsi.nature(
            track_id=tracks.track_id.values,
            b=tracks.cps_b,
            vtl=tracks.cps_vtl,
            vtu=tracks.cps_vtu,
            vortex=np.isnan(tracks.mslp_lon),
            wcsi=tracks.wcsi,
            b_threshold=15,
            vtl_threshold=0,
            vtu_threshold=0,
            filter_size=5,
            min_count=4,
        ),
    )

    return tracks


exp_model_scenario = []
for scenario in ["hist", "ssp", "story-cont", "story-hist", "story-Tplus2.0K"]:
    exp_model_scenario.append(("IFS-FESOM", "IFS-FESOM", scenario))

for scenario in ["cont", "hist", "ssp3-7"]:
    exp_model_scenario.append(("IFS-FESOM2", "IFS-FESOM", scenario))
    exp_model_scenario.append(("IFS-NEMO2", "IFS-NEMO", scenario))

for n in range(1, 3 + 1):
    exp_model_scenario.append(("IFS-FESOM2", "IFS-FESOM", f"story-cont{n}"))
for n in range(1, 5 + 1):
    exp_model_scenario.append(("IFS-FESOM2", "IFS-FESOM", f"story-hist{n}"))

for experiment, model, scenario in exp_model_scenario:
    tracks = combine.get_tracks(
        "DESTINe",
        drop=["hemisphere"],
        experiment=experiment,
        model=model,
        scenario=scenario,
        track_filter_func=select_tcs,
        reduce_precision=True,
        mask_value=1e25,
        fix_times=True,
    )

    tracks.hrcn.save(f"DESTINe_{experiment}_{scenario}_TCs.nc")
