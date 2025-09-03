# Base image
FROM ubuntu:22.04

# Metadata
LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Docker image with MadGraph, Pythia8, Pybind11, and JupyterLab"

# Avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install base packages
RUN apt update && \
    apt install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    gfortran build-essential cmake \
    libstdc++-12-dev \
    curl git wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Node.js (required for labextensions and proxy)
# -----------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt install -y nodejs && \
    npm install -g npm \
    && npm install -g configurable-http-proxy \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Python packages
# -----------------------------
RUN pip3 install --no-cache-dir \
    pybind11 \
    jupyterhub \
    jupyterlab \
    ipywidgets \
    notebook \
    numpy \
    pandas \
    scipy \
    matplotlib \
    jupyterhub-nativeauthenticator

# -----------------------------
# MadGraph installation
# -----------------------------
WORKDIR /opt/madgraph

RUN wget https://launchpad.net/mg5amcnlo/3.0/3.6.x/+download/MG5_aMC_v3.5.9.tar.gz \
    && tar --strip-components=1 -xvzf MG5_aMC_v3.5.9.tar.gz \
    && rm MG5_aMC_v3.5.9.tar.gz

ENV MG5AMCNLO=/opt/madgraph
ENV MG5QS_INPUT_PATH=/opt/madgraph/input
ENV PYTHONPATH=/opt/mg5qs/python:$PYTHONPATH

# -----------------------------
# Pythia installation
# -----------------------------
WORKDIR /opt
RUN wget --no-check-certificate https://pythia.org/download/pythia83/pythia8310.tgz && \
    tar xvfz pythia8310.tgz && \
    rm pythia8310.tgz
WORKDIR /opt/pythia8310
RUN make && ./configure
ENV PYTHIA8=/opt/pythia8310
ENV PYTHIA8DATA=/opt/pythia8310/share/Pythia8/xmldoc
ENV PYTHIA8_XMLDOC=${PYTHIA8DATA}
RUN chmod -R a+rX /opt/pythia8310

# -----------------------------
# Clone and build mg5qs
# -----------------------------
ENV PYTHIA8_INCLUDE_DIR=/opt/pythia8310/include
ENV PYTHIA8_LIB_DIR=/opt/pythia8310/lib
ENV PYTHON_INCLUDE_DIR=/usr/include/python3.10
ENV PYTHON_LIB_DIR=/usr/lib/python3.10/config-3.10-x86_64-linux-gnu

WORKDIR /opt
RUN rm -rf /opt/mg5qs && git clone https://github.com/leo-megliola/mg5qs.git /opt/mg5qs

# Set environment variable for MG5QS (optional, if you use it elsewhere)
ENV MG5QS_INPUT_PATH=/opt/mg5qs/input

# Run the compilation script
WORKDIR /opt/mg5qs/cpp
RUN chmod +x compile.sh && ./compile.sh

# NEW: Copy your JupyterHub config file into the image
# Assumes jupyterhub_config.py is in the same directory as your Dockerfile
COPY jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py

# Expose the default port for JupyterHub (usually 8000)
EXPOSE 8000
# EXPOSE 8888 # If you still need JupyterLab's default port for other reasons, keep this too.

# NEW: Set a default command to run when the container starts
# This will start JupyterHub using your specified config file
CMD ["jupyterhub", "-f", "/etc/jupyterhub/jupyterhub_config.py"]

