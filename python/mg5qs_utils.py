import pT_particle
import numpy as np
import subprocess
import time
from pathlib import Path
import os 
import shutil

# A wrapper to handle interactions with pybind11 for pT_particle
def generate_pT(particle_id, lhe_file_spec, size=5000000):
    transverse_momenta = np.zeros(size, dtype=np.float64)
    rets = pT_particle.pT(transverse_momenta, particle_id, str(lhe_file_spec))
    if rets["number of particles"] > size:
        raise ValueError('Number of particles exceeds length of data buffer: '+str(rets["number of particles"])+' > '+str(size))
    return (rets, transverse_momenta[0:rets["number of particles"]])

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
    shutil.copy(card.path / 'param_card.dat', card.path / 'param_card.bak') # make backup
    card.write(overwrite=True) # write over param_card.dat
    input_path = Path(os.getenv('MG5QS_INPUT_PATH')) # gran env verr
    # Assemble and run command to generate LHE 
    command = f"{framework_path / 'bin/generate_events'} -f < {input_path / 'gen_event_input.mg5'}"
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(card.path / 'param_card.bak', card.path / 'param_card.dat')  # restore the origional card
    os.remove(card.path / 'param_card.bak')   # cleanup artifact 
