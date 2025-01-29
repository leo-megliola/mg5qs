import pT_particle
import numpy as np
import subprocess
import time
from pathlib import Path
import os 
import shutil
from param_card_editor import *

# A wrapper to handle interactions with pybind11 for pT_particle
def generate_pT(particle_id, lhe_file_spec, size=5000000):
    transverse_momenta = np.zeros(size, dtype=np.float64)
    rets = pT_particle.pT(transverse_momenta, particle_id, str(lhe_file_spec))
    if rets["number of particles"] > size:
        raise ValueError('Number of particles exceeds length of data buffer: '+str(rets["number of particles"])+' > '+str(size))
    return (rets, transverse_momenta[0:rets["number of particles"]])


#==============================temp===================================#
def generate_vals(particle_id, lhe_file_spec, size=5000000):
    transverse_momenta = np.zeros(size, dtype=np.float64)
    status_codes = np.zeros((11, size), dtype=np.int32)
    rets = pT_particle.particle_info(transverse_momenta, status_codes, particle_id, str(lhe_file_spec))
    if rets["number of particles"] > size:
        raise ValueError('Number of particles exceeds length of data buffer: '+str(rets["number of particles"])+' > '+str(size))
    return (rets, transverse_momenta[0:rets["number of particles"]], status_codes[:,0:rets["number of particles"]])
#==============================temp===================================#



# Generates mg5 framework given a proc card
def run_MG5(mg5_path, proc_card_path, proc_card_name='proc_card.dat'):
    INPUT_PATH = Path(os.getenv('MG5QS_INPUT_PATH'))
    OUTPUT_PATH = INPUT_PATH.parent/'output'
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir()  # target working directory to spawn output in dedicated location 
    # Run mg5 with the proc card in the ouput directory 
    process = subprocess.Popen([mg5_path/'bin/mg5_aMC', proc_card_path/proc_card_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(OUTPUT_PATH))
    try:
        while process.poll() is None:
            time.sleep(.1)  # Add a small delay to reduce CPU usage
    finally:
        process.stdout.close()
        process.stderr.close()
        process.wait()  # Ensure the process is fully terminated

    output_name = _find(proc_card_path / proc_card_name, 'output').split()[1]
    return output_name, OUTPUT_PATH / output_name


def _find(f_spec, begins):
    with open(f_spec, 'r') as file:
        for line in file:
            if line.strip().upper().startswith(begins.upper()):
                return line

def _find_file(start_path, filename):
    return list(Path(start_path).rglob(filename))

def get_LHEs(OUTPUT_PATH):
    EVENTS_PATH = OUTPUT_PATH / 'Events'
    gzedLHEs = _find_file(EVENTS_PATH, 'unweighted_events.lhe.gz')
    for gz in gzedLHEs:
        subprocess.run(['gunzip', gz], check=True)
    LHEs = _find_file(EVENTS_PATH, 'unweighted_events.lhe')
    return LHEs

# Wraper to call generate_events excutable
def generate_LHE(card, framework_path):
    path = card.file_spec.parent
    shutil.copy(card.file_spec, path / 'param_card.bak') # make backup
    card.write(overwrite=True) # write over param_card.dat
    input_path = Path(os.getenv('MG5QS_INPUT_PATH')) # gran env verr
    # Assemble and run command to generate LHE 
    command = f"{framework_path / 'bin/generate_events'} -f < {input_path / 'gen_event_input.mg5'}"
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(path / 'param_card.bak', path / 'param_card.dat')  # restore the origional card
    os.remove(path / 'param_card.bak')   # cleanup artifact 

def _get_banner(LHE):
    banner = None
    for fname in os.listdir(LHE.parent):
        if 'banner' in fname:
            banner = fname
            break
    return banner

def get_run_params(LHE):
    banner = _get_banner(LHE)
    return ParamCard(LHE.parent / banner, quiet=True)

def get_LuminosityComponents(LHE):
    N, sigma, delta_sigma = None, None, None
    with open(LHE, 'r') as f:
        for line in f:
            if 'Number of Events' in line:
                N = int(line.split(':')[1].strip())
            elif '<init>' in line:
                f.readline()
                tokens = f.readline().split()
                sigma = float(tokens[0])
                delta_sigma = float(tokens[1])
        if all(item is not None for item in [N, sigma, delta_sigma]):
            return N, sigma, delta_sigma
    raise Exception("At least one value is missing")

def _weighted_average(values, uncertainties):
    values = np.array(values)
    uncertainties = np.array(uncertainties)
    if values.size != uncertainties.size:
        raise ValueError("The number of values must match the number of uncertainties.")
    weights = 1 / uncertainties**2
    weighted_avg = np.sum(weights * values) / np.sum(weights)
    combined_uncertainty = np.sqrt(1 / np.sum(weights))
    return weighted_avg, combined_uncertainty

def weighted_cross_section(LHEs):
    Ns, sigmas, delta_sigmas = [], [], []
    for LHE in LHEs:
        LC = get_LuminosityComponents(LHE)
        Ns.append(LC[0])
        sigmas.append(LC[1])
        delta_sigmas.append(LC[2])
    sigmas = np.array(sigmas)
    delta_sigmas = np.array(delta_sigmas)
    sigma, delta_sigma = _weighted_average(sigmas, delta_sigmas)
    return np.sum(Ns), sigma, delta_sigma