from string import Formatter
import re
import pathlib

from parse import parse

# Paths to data on JASMIN
# From https://research.reading.ac.uk/huracan/science/data/
huracan_project_path = pathlib.Path(
    "/gws/nopw/j04/huracan/data/tracks/tropical_cyclones/TRACK/"
)

# Shorthands for defining paths for each dataset
_YYYYMMDDHH = "{year:04d}{month:02d}{day:02d}{hour:02d}"
_YYYYMMDDHH_model = _YYYYMMDDHH.replace("year", "model_year")


def summary():
    for dataset in datasets:
        print(dataset)
        print(datasets[dataset], "\n")


def _get_keyword_from_string(format_string):
    # A tuple of (keyword, keyword_format) for all unique pairings in format_string
    keywords = [(x[1], x[2]) for x in Formatter().parse(format_string) if x[1]]

    # Preserve ordering for readability when converting to set
    return sorted(set(keywords), key=keywords.index)


def _format_string_by_keyword_subset(format_string, keywords):
    kw_in_string = _get_keyword_from_string(format_string)

    # Get a dictionary subset of the keywords that are present in format_string
    # For any keywords in format_string but not keywords, replace with an asterisk
    kw_matching = dict()
    for kw in kw_in_string:
        if kw[0] in keywords:
            kw_matching[kw[0]] = keywords[kw[0]]
        else:
            if kw[1] == "":
                format_string = format_string.replace(
                    "{" + f"{kw[0]}" + "}", "*"
                )
            else:
                format_string = format_string.replace(
                    "{" + f"{kw[0]}:{kw[1]}" + "}", "*"
                )

    # Replace any parts with multiple asterisks with a single asterisk
    format_string = re.sub("\*+", "*", format_string)

    return format_string.format(**kw_matching)


class TrackDataset:
    def __init__(
        self, fixed_path, extra_path, filename, variable_names=None, alternatives=None
    ):
        self.fixed_path = pathlib.Path(fixed_path)
        self.extra_path = extra_path
        self.filename = filename
        self.variable_names = variable_names
        self.alternatives = alternatives

    @property
    def full_path(self):
        return str(self.fixed_path / self.extra_path / self.filename)

    @property
    def keys(self):
        return [kw[0] for kw in _get_keyword_from_string(self.full_path)]

    def find_files(self, **kwargs):
        extra_path = _format_string_by_keyword_subset(self.extra_path, kwargs)
        filename = _format_string_by_keyword_subset(self.filename, kwargs)

        return [str(f) for f in self.fixed_path.glob(extra_path + filename)]

    def file_details(self, filename):
        return parse(self.full_path, filename).named

    def select_alternative(self, alternative):
        alternative = self.alternatives[alternative].copy()

        for key in ["fixed_path", "extra_path", "filename", "variable_names"]:
            if key not in alternative:
                alternative[key] = getattr(self, key)

        return TrackDataset(**alternative)

    def __str__(self):
        return (
            f"{self.full_path}\n"
            f"{self.keys}"
        )


# If .new is in the filename, then the track indices have been converted to timestamps
datasets = dict()
# Modern era reanalyses
_filename = "tr_trs_{sign}.2day_addT63vor_addmslp_add925wind_add10mwind"
_variable_names = [
    f"vorticity{plev}hPa" for plev in [850, 700, 600, 500, 400, 300, 200]
] + ["mslp", "vmax925hPa", "vmax10m"]
datasets["ERA5"] = TrackDataset(
    fixed_path=huracan_project_path / "ERA5",
    extra_path="{hemisphere}/ERA5_{year}_VOR_VERTAVG_T63/",
    filename=_filename + "_addmslpavg_mslpdiff.new",
    variable_names=_variable_names + ["mslpavg", "mslpdiff"],
    alternatives={
        "nolat-tcident": dict(
            filename=_filename + ".nolat.tcident.hart",
            variable_names=_variable_names + ["cps_vtl", "cps_vtu", "cps_b"],
        ),
        "nolat-tcident-dwcore": dict(
            filename=_filename + ".nolat.tcident.hart.dwcore.new",
            variable_names=_variable_names + ["cps_vtl", "cps_vtu", "cps_b"],
        ),
        "tcident": dict(
            filename=_filename + ".tcident.new",
            variable_names=_variable_names,
        ),
        "matches": dict(
            extra_path="MATCH-{hemisphere}/",
            filename="ERA5_{year}_match_yes.dat",
            variable_names=_variable_names,
        )
    },
)

_filename = "tr_trs_{sign}.2day_addT63vor_addmslp_addw925_addw10m"
datasets["JRA3Q"] = TrackDataset(
    fixed_path=huracan_project_path / "JRA3Q/TC/",
    extra_path="{hemisphere}/JRA3Q_{year}_VOR_VERTAVG_T63/",
    filename=_filename + ".new",
    variable_names=_variable_names,
    alternatives={
        "nolat-tcident": dict(
            filename=_filename + ".nolat.tcident.hart.new",
            variable_names=_variable_names + ["cps_vtl", "cps_vtu", "cps_b"],
        ),
        "tcident": dict(
            filename=_filename + ".tcident.new",
            variable_names=_variable_names,
        ),
    },
)

# Longer reanalyses
_filename = "tr_trs_{sign}.2day_addT63vor7lev_addmslp_addwind925_addwind10m"
datasets["ERA20C"] = TrackDataset(
    fixed_path=huracan_project_path / "ERA20C/{hemisphere}/",
    extra_path="ERA20C_VOR_{year:04d}_vertavg_T63/",
    filename=_filename + "_addmslpavg_mslpdiff.new",
    variable_names=_variable_names + ["mslpavg", "mslpdiff"],
    alternatives={
        "tcident": dict(
            filename=_filename + ".tcident.new",
            variable_names=_variable_names,
        ),
    },

)
datasets["CERA20C"] = TrackDataset(
    fixed_path=huracan_project_path / "CERA20C/",
    extra_path="{hemisphere}/CERA20C_VOR_{year}_{ensemble_member}_vertavg_T63/",
    filename=_filename + "_addmslpavg_mslpdiff.new",
    variable_names=_variable_names + ["mslpavg", "mslpdiff"],
    alternatives={
        "tcident": dict(
            filename=_filename + ".tcident.new",
            variable_names=_variable_names,
        ),
    }
)

_filename = "tr_trs_pos.2day_addT63vor_addw925_addw10m_addmslp_addprecip"
_variable_names = [
    f"vorticity{plev}hPa" for plev in [850, 700, 600, 500, 400, 300, 200]
] + ["vmax925hPa", "vmax10m", "mslp", "precip"]
datasets["20CRv3"] = TrackDataset(
    fixed_path=huracan_project_path / "NOAA-20CRv3/TC/NOAA-20CRv3",
    extra_path="NOAA-20CRv3_VOR_VERTAVG_{month_range}{year}_{ensemble_member:03d}_T63/",
    filename=_filename,
    variable_names=_variable_names,
    alternatives={
        "tcident": dict(
            filename=_filename + ".tcident.new",
            variable_names=_variable_names,
        ),
    }
)

# Climate model simulations
datasets["CMIP6"] = TrackDataset(
    fixed_path=huracan_project_path / "CMIP6/TC/CMIP6",
    extra_path="{model_parent}/{model_variant}/{experiment}/TC/{hemisphere}"
               "{model_variant}_{experiment}_{variant}_{grid}_VOR850_jan-dec{year}_T42/",
    filename="tr_trs_pos.2day_addvorT63_addwind.tcident.new.nc",
)
datasets["HighResMip"] = TrackDataset(
    fixed_path=huracan_project_path / "HiResMIP/HiResMIP",
    extra_path="{model_parent}/{model_variant}/{experiment}/TC/{hemisphere}/"
               "{model_variant}_{experiment}_{variant}_gn_VOR_vertavg_jan-dec{year}_T63",
    filename="tr_trs_pos.2day_addvorT63_addwind_addmslp.tcident.new.nc",
)
datasets["SPHINX"] = TrackDataset(
    fixed_path=huracan_project_path / "SPHINX/TC/SPHINX/",
    # Physics = "BASE" or "STOC"
    # Experiment = "PRESENT" or "FUTURE"
    # Hemisphere = "-SH" or "" for NH
    extra_path="T{spectral_resolution}-ATMOS-{physics}-{experiment}{hemisphere}/"
               "{runid}_{year}_VOR_VERTAVG_T63/",
    filename="{tr_or_ff}_trs_pos.addT63vor_add925w_add10w_addmslp_addprecip.tcident.hart",
    variable_names=[f"vorticity_{n+1}" for n in range(6)] + ["v925hPa", "v10m", "mslp", "precip", "TL", "TU", "B"],
)
# "d4PDF": TrackDataset(
#     fixed_path=huracan_project_path / "d4pdf/TC",
#     extra_path="{experiment}/HPB_VOR_VERTAVG_jan-dec{year:04d}_{ensemble_member:03d}_T63"
#                "{HFB_VOR_VERTAVG_jan-dec{year}_{:03d}_T63/ or "
#                "HFB_VOR_VERTAVG_jan-dec{year}_HFB_4k_{??}_{:03d}_T63/}",
#     # "HPB_VOR_VERTAVG_jul-jun20092010_100_T63"
#     filename="tr_trs_pos.2day_addT63vor_add925w_add10w_addmslp_addprecip.tcident.new.nc"
# ),
datasets["d4PDF"] = None,
datasets["HighResMip2"] = None,
datasets["nextGEMS"] = None,
datasets["N1280-UM"] = None,

# Seasonal prediction ensembles
datasets["GloSea5"] = TrackDataset(
    fixed_path=huracan_project_path / "GLOSEA5/TC/GLOSEA5",
    extra_path="",
    filename="",
)
datasets["GloSea6"] = TrackDataset(
    fixed_path=huracan_project_path / "GLOSEA6/TC",
    # Broken links beyond here
    extra_path="GLOSEA6-{experiment}/",
    filename=""
)

datasets["ASF-20C"] = TrackDataset(
    fixed_path=huracan_project_path / "ANTJE",
    extra_path="{experiment_id}/" + _YYYYMMDDHH + "/S2S_VOR_VERTAVG_" + _YYYYMMDDHH + "_{ensemble_member}_T63/",
    filename="tr_trs_pos.2day_addvorT63_addwinds925_addwinds10m_addmslp.new",
    variable_names=[
        f"vorticity{plev}hPa" for plev in [850, 700, 600, 500, 300, 200]
    ] + ["vmax925hPa", "vmax10m", "mslp"],
)

_extra_path = _YYYYMMDDHH + "/S2S_VOR850_" + _YYYYMMDDHH + "_{ensemble_member}_T42_hilat/"
_filename = "tr_trs_{sign}.2day_addvorT63_addwind850_addmslp.new"
_variable_names = [
    f"vorticity{plev}hPa" for plev in [850, 500, 200]
] + ["vmax850hPa", "mslp"]
datasets["CSF-20C"] = TrackDataset(
    fixed_path=huracan_project_path / "ANTJE/guh4",
    extra_path=_extra_path,
    filename=_filename + ".gz",
    variable_names=_variable_names,
)

datasets["SEAS5-20C"] = TrackDataset(
    fixed_path=huracan_project_path / "ANTJE/guxf",
    extra_path=_extra_path,
    filename=_filename,
    variable_names=_variable_names,
    alternatives={
        "nolat-tcident": dict(
            filename=_filename.replace(".new", ".nolat.tcident.hart.new"),
            variable_names=_variable_names + ["cps_vtl", "cps_vtu", "cps_b"],
        ),
    }
)

datasets["C3S"] = None,

# NWP
# Year/Month/Day/Hour refer to initialisation time
datasets["TIGGE"] = TrackDataset(
    fixed_path=huracan_project_path / "TIGGE/TC/TIGGE",
    extra_path="{model}/Y{year:04d}/" + f"{_YYYYMMDDHH}/" +
               "{model}_VOR_" + f"{_YYYYMMDDHH}" + "_{ensemble_member}",
    filename="tr_trs_pos.2day.addfullvor_addavgvor_addmslp_addw10m.new.gz",
)

_filename = "tr_trs_{sign}.2day_addvorT63_addwinds_addmslp.highres.hart.new"
_variable_names = [
    f"vorticity{plev}hPa" for plev in [850, 700, 500, 400, 300, 200]
] + ["vmax925hPa", "vmax10m", "mslp"]
# For matched tracks, track ID in file ranges from 0-11.
# 0 is analysis. 1 is control. 2-11 are ensemble members
datasets["ECMWF_hindcasts"] = TrackDataset(
    fixed_path=huracan_project_path / "ECMWF-HINDCASTS/TC/",
    extra_path=f"{_YYYYMMDDHH_model}/{_YYYYMMDDHH}/"
               f"HIND_VOR_VERTAVG_{_YYYYMMDDHH_model}_{_YYYYMMDDHH}" +
               "_{ensemble_member}/",
    filename="tr_trs_{sign}.2day_addvorT63_addwinds_addmslp.highres.hart.new",
    variable_names=_variable_names + ["cps_vtl", "cps_vtu", "cps_b"],
    alternatives={
        "matches": dict(
            extra_path=f"{_YYYYMMDDHH_model}/{_YYYYMMDDHH}/" +
                       "MATCH_{hemisphere}_ERA5_highres/",
            variable_names=["vmax925hPa", "vmax10m", "mslp"],
            filename="trmatch_cntl_tr{ibtracs_id:04d}"
        ),
    }
)

_filename = "tr_trs_{sign}.2day_addvorT63_addwinds_addmslp.hart.new"
_variable_names = [
    f"vorticity{plev}hPa" for plev in [850, 700, 600, 500, 400, 300, 200]
] + ["vmax925hPa", "vmax10m", "mslp"]
_extra_path = "Y{model_year:04d}/" + f"{_YYYYMMDDHH}/"
datasets["ECMWF_Extended_Ensemble"] = TrackDataset(
    fixed_path=huracan_project_path / "EPSEXT100/TC/",
    extra_path=_extra_path + f"EPSEXT_VOR_VERTAVG_{_YYYYMMDDHH}_" + "{ensemble_member}/",
    filename=_filename,
    variable_names=_variable_names + ["cps_vtl", "cps_vtu", "cps_b"],
    alternatives={
        "matches": dict(
            extra_path=_extra_path + "MATCH_{hemisphere}/",
            filename="trmatch_cntl_tr{storm_number:04d}",
            variable_names=["vmax925hPa", "vmax10m", "mslp"],
        ),
    }
)

# Decadal Prediction Systems
datasets["DePreSys4"] = TrackDataset(
    fixed_path=huracan_project_path / "DePreSys4/TC/DePreSys4",
    extra_path="DePreSys4_{run_id}_{year:04d}_{ensemble_member:d}",
    filename="tr_trs_pos.2day_addT63vor_addw10m_addmslp_addprecip.tcident.new",
)


# To add
# CANARI
# ECMWF-OP-AN
# ERA20CM
# HINDCAST15
