from setuptools import setup, Extension
import pybind11
import os

# Get environment variables
PYTHIA8_INCLUDE_DIR = os.getenv('PYTHIA8_INCLUDE_DIR')
PYTHIA8_LIB_DIR = os.getenv('PYTHIA8_LIB_DIR')
PYTHON_INCLUDE_DIR = os.getenv('PYTHON_INCLUDE_DIR')
PYTHON_LIB_DIR = os.getenv('PYTHON_LIB_DIR')

# Define output directory
output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../lib"))

ext_modules = [
    Extension(
        'pT_particle',  # Name of the output module
        ['pT_particle.cpp'],  # Source file
        include_dirs=[
            pybind11.get_include(),  # Pybind11 include directory
            PYTHIA8_INCLUDE_DIR,  # Pythia8 include directory
            PYTHON_INCLUDE_DIR  # Python include directory
        ],
        library_dirs=[
            PYTHIA8_LIB_DIR,  # Pythia8 library directory
            PYTHON_LIB_DIR  # Python library directory
        ],
        libraries=[
            'pythia8',  # Pythia8 library
            'stdc++'  # Standard C++ library
        ],
        language='c++',
        extra_compile_args=['-std=c++11'],
        extra_link_args=['-Wl,-rpath,' + PYTHIA8_LIB_DIR]  # Runtime path for shared libraries
    ),
]

setup(
    name='pT_particle',
    version='0.1',
    ext_modules=ext_modules,
    options={
        'build': {'build_lib': output_dir},
        'install': {'install_lib': output_dir}
    }
)

