# qdatalib 
### Note this project is under development, and will undergo a massive number of breaking changes 

# Description

QDataLib is a library of wrappers around some of the most useful ”data”-functions in QCoDeS. The Idea of QDataLib is to keep track of your data files using a MongoDB database, and ease the export to other file formats than SQLite

# Installation
To install QDataLib from source do the following:
```bash
$ git clone https://github.com/RasmusBC59/QDataLib.git
$ cd QDataLib
$ pip install .
```
# Usage

## Running the tests

If you have gotten 'qdatalib' from source, you may run the tests locally.

Install `qdatalib` along with its test dependencies into your virtual environment by executing the following in the root folder

```bash
$ pip install .
$ pip install -r test_requirements.txt
```

Then run `pytest` in the `tests` folder.

## Building the documentation

If you have gotten `qdatalib` from source, you may build the docs locally.

Install `qdatalib` along with its documentation dependencies into your virtual environment by executing the following in the root folder

```bash
$ pip install .
$ pip install -r docs_requirements.txt
```

You also need to install `pandoc`. If you are using `conda`, that can be achieved by

```bash
$ conda install pandoc
```
else, see [here](https://pandoc.org/installing.html) for pandoc's installation instructions.

Then run `make html` in the `docs` folder. The next time you build the documentation, remember to run `make clean` before you run `make html`.
