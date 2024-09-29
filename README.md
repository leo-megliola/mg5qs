Welcome to mg5qs! 

This package is designed to extend and streamline the functionality of MadGraph (https://github.com/mg5amcnlo/mg5amcnlo) and Pythia (https://www.pythia.org/) for new or intermediate users. Advanced users may be interested in some of the source code for automation or efficiency. 

mg5qs is a framework that: 
- automates interaction with the machinery within MadGraph and Pythia
- exposes the functionality of its underlying packages within python (interactable using notebooks like jupyter)
- provides an example of interaction directly with Pythia in C++, therefore retaining efficiency of computation and gaining in storage optimization
- wraps Pythia/C++ in python/numpy, allowing for analysis using standard libraries (scipy, pandas, etc.) 

Prerequisites: 
- Runtime environment
  - MadGraph5 (https://github.com/mg5amcnlo/mg5amcnlo) 
  - Pythia8 (https://www.pythia.org/)
- Development environment
  - pybind11
  - essential build tools (build-essential)
  - Python development environment (python3.X-dev), version <= 3.10; 3.8 works well with Pythia

Environment variables (export from ~/.bashrc):
- Runtime environment
  - MG5QS_MG5_PATH=/path/to/mg5amcnlo
  - MG5QS_INPUT_PATH=/path/to/mg5qs/input
- Development environment
  - PYTHIA8_INCLUDE_DIR=/path/to/pythia8/include
  - PYTHIA8_LIB_DIR=/path/to/pythia8/lib
  - PYTHON_INCLUDE_DIR=/path/to/include/python3.x
  - PYTHON_LIB_DIR=/path/to/lib (contains directory python3.x)

