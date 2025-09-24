**Welcome to mg5qs**

The purpose of this package is to offer a tractable, efficient, and easy way to perform initial simulations using MadGraph5 and Pythia8. mg5qs runs in Jupyterlab, exposing simulation results to common Python packages (NumPy, SciPy, pandas, etc). 

mg5qs offers:

- Integrated Jupyterlab environment offering end-to-end Python interaction for MadGraph and Pythia
- Interactive access to MadGraph’s parameters from within Jupyter
- Flattened and reduced output data structures
- Reduced output storage requirement by factor of 10^5 for typically sized runs (~1MB)
- Compatible with common Python libraries (e.g. Numpy, SciPy, pandas) 
- Automated simulation pipeline 
- Supports multithreading during Pythia showering (speed up by factor of number of cores)
- Containerized image of MadGraph, Pythia, and mg5qs using Docker (easy install)
- Remotely-hosted, fully-functional demo environment
- Documented with interactive example notebooks 

Give it a try in any of the following ways. The best way to start is by running the four interactive example notebooks on the test server.

**Full Demo (Test Server)**
https://lab.mg5qs.org/ make a free account (enter a username and password).

**Docker (image includes MadGraph5 3.5.x & Pythia 8.310)**
https://hub.docker.com/repository/docker/leomegliola/mg5qs/general. 

**GitHub**
https://github.com/leo-megliola/mg5qs. 
