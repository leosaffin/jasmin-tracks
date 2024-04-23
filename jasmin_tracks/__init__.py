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
    def __init__(self, fixed_path, extra_path, filename, variable_names=None):
        self.fixed_path = pathlib.Path(fixed_path)
        self.extra_path = extra_path
        self.filename = filename
        self.variable_names = variable_names

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

    def __str__(self):
        return (
            f"{self.full_path}\n"
            f"{self.keys}"
        )


# If .new is in the filename, then the track indices have been converted to timestamps
datasets = {
    # Modern era reanalyses
    "ERA5": TrackDataset(
        fixed_path=huracan_project_path / "ERA5",
        extra_path="{hemisphere}/",
        filename="tr_trs_pos.{year}.2day_addT63vor_addmslp_add925wind_add10mwind.tcident.hart.nc",
    ),
    "ERA-Interim": None,
    "JRA-25": None,
    "JRA-55": None,
    "MERRA2": None,

    # Longer reanalyses
    "ERA-20C": TrackDataset(
        fixed_path=huracan_project_path / "ERA20C/NH/",
        extra_path="ERA20C_VOR_{year:04d}_vertavg_T63/",
        filename="tr_trs_pos.2day_addT63vor7lev_addmslp_addwind925_addwind10m.tcident.new.nc",
    ),
    "CERA-20C": TrackDataset(
        fixed_path=huracan_project_path / "CERA20C/",
        extra_path="{hemisphere}/CERA20C_VOR_{year:04d}_{ensemble_member}_vertavg_T63/",
        filename="tr_trs_pos.2day_addT63vor7lev_addmslp_addwind925_addwind10m.tcident.new.nc",
    ),
    "20CRv3": TrackDataset(
        fixed_path=huracan_project_path / "NOAA-20CRv3/TC/NOAA-20CRv3",
        extra_path="NOAA-20CRv3_VOR_VERTAVG_jan-dec{year:04d}_{ensemble_member:03d}_T63/",
        filename="tr_trs_pos.2day_addT63vor_addw925_addw10m_addmslp_addprecip.tcident",
    ),

    # Climate model simulations
    "CMIP6": TrackDataset(
        fixed_path=huracan_project_path / "CMIP6/TC/CMIP6",
        extra_path="{model_parent}/{model_variant}/{experiment}/TC/{hemisphere}"
                   "{model_variant}_{experiment}_{variant}_{grid}_VOR850_jan-dec{year}_T42/",
        filename="tr_trs_pos.2day_addvorT63_addwind.tcident.new.nc",
    ),
    "HighResMip": TrackDataset(
        fixed_path=huracan_project_path / "HiResMIP/HiResMIP",
        extra_path="{model_parent}/{model_variant}/{experiment}/TC/{hemisphere}/"
                   "{model_variant}_{experiment}_{variant}_gn_VOR_vertavg_jan-dec{year}_T63",
        filename="tr_trs_pos.2day_addvorT63_addwind_addmslp.tcident.new.nc",
    ),
    "SPHINX": TrackDataset(
        fixed_path=huracan_project_path / "SPHINX/TC/SPHINX/",
        # Physics = "BASE" or "STOC"
        # Experiment = "PRESENT" or "FUTURE"
        # Hemisphere = "-SH" or "" for NH
        extra_path="T{spectral_resolution}-ATMOS-{physics}-{experiment}{hemisphere}/"
                   "{runid}_{year}_VOR_VERTAVG_T63/",
        filename="{tr_or_ff}_trs_pos.addT63vor_add925w_add10w_addmslp_addprecip.tcident.hart",
        variable_names=[f"vorticity_{n+1}" for n in range(6)] + ["v925hPa", "v10m", "mslp", "precip", "TL", "TU", "B"],
    ),
    # "d4PDF": TrackDataset(
    #     fixed_path=huracan_project_path / "d4pdf/TC",
    #     extra_path="{experiment}/HPB_VOR_VERTAVG_jan-dec{year:04d}_{ensemble_member:03d}_T63"
    #                "{HFB_VOR_VERTAVG_jan-dec{year}_{:03d}_T63/ or "
    #                "HFB_VOR_VERTAVG_jan-dec{year}_HFB_4k_{??}_{:03d}_T63/}",
    #     # "HPB_VOR_VERTAVG_jul-jun20092010_100_T63"
    #     filename="tr_trs_pos.2day_addT63vor_add925w_add10w_addmslp_addprecip.tcident.new.nc"
    # ),
    "d4PDF": None,
    "CMIP6-HighResMip": None,
    "nextGEMS": None,
    "N1280-UM": None,

    # Seasonal prediction ensembles
    "GloSea5": TrackDataset(
        fixed_path=huracan_project_path / "GLOSEA5/TC/GLOSEA5",
        extra_path="",
        filename="",
    ),
    "GloSea6": TrackDataset(
        fixed_path=huracan_project_path / "GLOSEA6/TC",
        # Broken links beyond here
        extra_path="GLOSEA6-{experiment}/",
        filename=""
    ),
    "ECMWF_coupled_hindcasts": TrackDataset(
        fixed_path=huracan_project_path / "ANTJE",
        extra_path="{experiment_id}/" + _YYYYMMDDHH + "/"
                   "S2S_VOR850_" + _YYYYMMDDHH + "_{ensemble_member}_T42_hilat",
        filename="tr_trs_{pos_or_neg}.2day_addvorT63_addwind850_addmslp.new",
    ),
    "C3S": None,

    # NWP
    # Year/Month/Day/Hour refer to initialisation time
    "TIGGE": TrackDataset(
        fixed_path=huracan_project_path / "TIGGE/TC/TIGGE",
        extra_path="{model}/Y{year:04d}/" + f"{_YYYYMMDDHH}/" +
                   "{model}_VOR_" + f"{_YYYYMMDDHH}" + "_{ensemble_member}",
        filename="tr_trs_pos.2day.addfullvor_addavgvor_addmslp_addw10m.new.gz",
    ),
    "ECMWF_hindcasts": TrackDataset(
        fixed_path=huracan_project_path / "ECMWF-HINDCASTS/TC/",
        extra_path=f"{_YYYYMMDDHH_model}/{_YYYYMMDDHH}/"
                   f"HIND_VOR_VERTAVG_{_YYYYMMDDHH_model}_{_YYYYMMDDHH}" +
                   "_{ensemble_member}/",
        filename="tr_trs_pos.2day_addvorT63_addwinds_addmslp.highres.hart.new",
        variable_names=[
            "vorticity850hPa",
            "vorticity700hPa",
            "vorticity500hPa",
            "vorticity400hPa",
            "vorticity300hPa",
            "vorticity200hPa",
            "vmax925hPa",
            "vmax10m",
            "mslp",
            "TL",
            "TU",
            "B",
        ],
    ),

    # Decadal Prediction Systems
    "DePreSys4": TrackDataset(
        fixed_path=huracan_project_path / "DePreSys4/TC/DePreSys4",
        extra_path="DePreSys4_{run_id}_{year:04d}_{ensemble_member:d}",
        filename="tr_trs_pos.2day_addT63vor_addw10m_addmslp_addprecip.tcident.new",
    ),
}

matched_tracks = {
    "ECMWF_hindcasts": TrackDataset(
        fixed_path=datasets["ECMWF_hindcasts"].fixed_path,
        extra_path=f"{_YYYYMMDDHH_model}/{_YYYYMMDDHH}/" +
                   "MATCH_{hemisphere}_ERA5_highres/",
        filename="trmatch_cntl_tr{storm_number:04d}",
    )
}
