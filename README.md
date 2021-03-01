# aECG viewer  
![aECG viewer icon](src/aecgviewer/resources/app.png)

## Abstract

This python application provides a graphical user interface to index and
visualize annotated electrocardiograms stored in XML files following
HL7 annotated ECG (aECG) standard. This graphical user interface requires the *aecg* python package that is available at [https://github.com/FDA/aecg-python](https://github.com/FDA/aecg-python). See the [TUTORIAL](TUTORIAL.md) for a quick introduction to examples of use.

See LICENSE and DISCLAIMER at the bottom of this document.

## Installing the software

These instructions assume you already have python 3.7.7 or conda as well as the *aecg* python package installed in your system. The use of a virtual environment is recommended.

### Setting up a virtual environment (optional)

#### Python venv

* Setup a virtual environment. In this example, we create the *aecgvenv* environment in ~/code/virtenvs
```
cd ~/code/virtenvs
python -m venv aecgvenv
```

* Next, activate the virtual environment
```
source ~/code/virtenvs/aecgvenv/bin/activate
```

* And upgrade pip to the most recent version
```
pip install --upgrade pip
```

#### Conda (Anaconda)

Launch anaconda prompt/console (from start menu or from anaconda navigator) from the base environment.  In this example, we create the *aecgvenv* environment using the path command line option of conda.

* Go to your project directory and create a new environment by typing:

```
conda create -p aecgvenv
```

* Next, activate the conda environment
```
conda activate .\aecgvenv
```

* Next, install python 3.7.7 in the conda environment
```
conda install python==3.7.7
```

### Installing from the source

* Prerequisite: you will need aecg-python installed. The aecg-python package is available at [https://github.com/FDA/aecg-python](https://github.com/FDA/aecg-python).

* Clone the aecgviewer repository from [https://github.com/FDA/aecgviewer](https://github.com/FDA/aecgviewer) or get a copy of the source code as a tar ball.

* Change to the directory where you have cloned or downloaded the source code
```
cd ~/code/aecgviewer
```

* Install aecgviewer in editable mode so you can both use it and make changes to its source code. Installing with pip will install the rest of aecgviewer dependencies. If you do not plan to do development or debugging, then you can omit the ```-e``` flag.

```
pip install -e .
```

## Development and deployment tips

### How to build the package for distribution from the source code

To create a source and wheels distributions by typing ```python setup.py sdist bdist_wheel``` in the command line.

### How to generate a local copy of the documentation

* Additional **requirements**
```
pip install sphinx sphinx-autobuild sphinx-autodoc-typehints mock autodoc myst-parser
```

Once you have installed the additional packages listed above and assuming you have a copy of the source code in ~/code/aecgviewer, you can generate a local html version of the documentation from the command line as follows:

```
cd ~/code/aecgviewer/docs
make html
```

## License

This code is in the public domain within the United States, and copyright and
related rights in the work worldwide are waived through the CC0 1.0 Universal
Public Domain Dedication. This example is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See DISCLAIMER section
below, the COPYING file in the root directory of this project and
https://creativecommons.org/publicdomain/zero/1.0/ for more details.

## Disclaimer

FDA assumes no responsibility whatsoever for use by other parties of the
Software, its source code, documentation or compiled executables, and makes no
guarantees, expressed or implied, about its quality, reliability, or any other
characteristic. Further, FDA makes no representations that the use of the
Software will not infringe any patent or proprietary rights of third parties.
The use of this code in no way implies endorsement by the FDA or confers any
advantage in regulatory decisions.
