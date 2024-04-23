# jasmin-tracks

This library gives a convenient method of finding track files on JASMIN. The files are
tracks from the Huracan project and are (mostly) in the Huracan workspace. For a summary
of the data see (https://research.reading.ac.uk/huracan/science/data/).

jasmin-tracks gives a method for finding all the tracks for a given dataset. For
example, to get a list of all the track files for the ECMWF hindcasts run
```python
import jasmin_tracks

dataset = jasmin_tracks.datasets["ECMWF_hindcasts"]

all_files = dataset.find_files()
```

The find_files function also supports subsetting by different variables. These are
different for different datasets, but can be accessed by the keys attribute. For the
ECMWF hindcast loaded earlier
```python
print(dataset.keys)
```
returns 
```
['model_year', 'month', 'day', 'hour', 'year', 'ensemble_member']
```
We could then look for only the tracks from the control members run in 2023 by running
```python
control_2023_files = dataset.find_files(model_year=2023, ensemble_member="CNTRL")
```
I haven't listed out what all the valid keys are (yet) so that is something you would
have to check for yourself. A possible way to help with this is that once you have a
path you can pass it to dataset.file_details, e.g.
```python
dataset.file_details(all_files[0])
```
would return
```python
{'model_year': 2015, 'month': 5, 'day': 14, 'hour': 0, 'year': 1995, 'ensemble_member': '1'}
```

## Install
Since this is only intended to run on JASMIN, you can just add my copy to your
pythonpath (add to your .bashrc to make it permanent)
```shell
export PYTHONPATH="${PYTHONPATH}:/home/users/lsaffin/programming/jasmin-tracks"
```
If you want to your own copy to modify then clone this repository and install it in
editable mode
```shell
git clone https://github.com/leosaffin/jasmin-tracks.git
cd jasmin-tracks
pip install -e .
```
