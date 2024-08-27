import pT_particle
import numpy as np
import subprocess
import time
from pathlib import Path
import os 

# A wrapper to handle interactions with pybind11 for pT_particle
def pT(particle_id, N, lhe_file_spec, size=100000):
    transverse_momenta = np.zeros(size, dtype=np.float64)
    rets = pT_particle.pT(transverse_momenta, particle_id, N, lhe_file_spec)
    if rets["number of particles"] > size:
        raise ValueError('Number of particles exceeds length of data buffer: '+str(rets["number of particles"])+' > '+str(size))
    return (rets, transverse_momenta[0:rets["number of particles"]])

# Generates mg5 framework given a proc card
def run_MG5(mg5_path, proc_card_path, proc_card_name='proc_card.dat'):
    INPUT_PATH = Path(os.getenv('MG5QS_INPUT_PATH'))
    OUTPUT_PATH = INPUT_PATH.parent/'output'
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir()
    OUTPUT_PATH.cwd()  # run from output dir, so output is spawned there 
    
    process = subprocess.Popen([mg5_path/'bin/mg5_aMC', proc_card_path/proc_card_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while process.poll() is None:
            time.sleep(.1)  # Add a small delay to reduce CPU usage
    finally:
        process.stdout.close()
        process.stderr.close()
        process.wait()  # Ensure the process is fully terminated
        print("Process cleaned up.")
