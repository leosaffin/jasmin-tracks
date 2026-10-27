from jasmin_tracks import combine


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
        filter_tcs=True,
        reduce_precision=True,
        mask_value=1e25,
        fix_times=True,
    )

    tracks.hrcn.save(f"DESTINe_{experiment}_{scenario}_TCs.nc")
