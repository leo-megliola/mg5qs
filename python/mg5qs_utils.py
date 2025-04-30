import pythia
import pandas as pd
import numpy as np
import subprocess
import time
from pathlib import Path
import os 
import shutil
import pickle
import concurrent.futures
from param_card_editor import *


def _run_pythia(particle_ids, lhe_file_spec, topics, dataframe, size):
    if topics is None:
        topics = pythia.get_topics()
    topic_widths = pythia.get_topic_widths()
    if 'P_mu' in topics:
        fvs = np.zeros((size,4), dtype=np.float64)
    else:
        fvs = np.zeros((0,0), dtype=np.float64)
    width = topic_widths['BASIC']
    for k,v in topic_widths.items():
        if k in topics:
            width += v
    ivs = np.zeros((size, width), dtype=np.int32)
    pids = np.array(particle_ids, dtype=np.int32)
    rets = pythia.pythia8(fvs, ivs, pids, topics, str(lhe_file_spec))
    if rets['n'] == -1:
        raise ValueError('Number of particles exceeds length of data buffer (increase buffer size?).')
    df = pd.DataFrame(ivs[0:rets['n']])
    if dataframe:
        if 'P_mu' in topics:
            df_P = pd.DataFrame(fvs[0:rets['n']])
            df = pd.concat((df,df_P), axis=1)
        df.columns = rets['fields'].split(',')
        return df
    return {'fvs': fvs[0:rets['n']],'ivs': ivs[0:rets['n']]} | rets #WORK IN PROGRESS; need to pass through return values

def _process_LHE(n, LHE, particle_ids, topics, dataframe, output_path, framework_name, size):
    print(f"showering: {LHE} \n", end="")
    df = _run_pythia(particle_ids, LHE, topics, dataframe, size)
    params = get_run_params(LHE)
    fname = f"{framework_name}_SM_{n}.pkl"
    with open(output_path / fname, 'wb') as f:
        pickle.dump((params, df), f)

def pythia_parallel(particle_ids, framework_path, output_dir, topics=None, dataframe=True, cores=10, size=5000000):
    if topics is None:
        topics = pythia.get_topics()
    output_path = Path(output_dir)  # Output path relative to Jupyter
    LHEs = get_LHEs(framework_path)
    output_path.mkdir(parents=True, exist_ok=True)
    for fname in output_path.glob('*.pkl'):
        fname.unlink()
    with concurrent.futures.ProcessPoolExecutor(max_workers=cores) as executor:
        futures = {
            executor.submit(_process_LHE, i, LHE, particle_ids, topics, dataframe, output_path, framework_path.name, size)
            for i, LHE in enumerate(LHEs)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error in parallel execution: {e}") 
    print(f"\nfinished showering {len(LHEs)} LHE files")

def unpickle(inputdir, concat=True):
    if concat:
        return _unpickle_batch(inputdir)
    else:
        return _unpickle_dict(inputdir)

def _unpickle_batch(inputdir):   
    if isinstance(inputdir, str):
        inputdir = Path(inputdir)
    df = None
    params = None
    for filepath in inputdir.glob("*.pkl"):
        with open(filepath, 'rb') as f:
            params, df_n = pickle.load(f)
            if df is None:
                df = df_n
            else:
                df = pd.concat([df, df_n], ignore_index=True)
    return params, df

def _unpickle_dict(inputdir):   
    if isinstance(inputdir, str):
        inputdir = Path(inputdir)
    kv = {}    
    for filepath in inputdir.glob("*.pkl"):
        with open(filepath, 'rb') as f:
            kv[filepath.stem] = pickle.load(f)
    return kv

# Generates mg5 framework given a proc card
def run_MG5(mg5_path, proc_card_path, proc_card_name='proc_card.dat'):
    INPUT_PATH = Path(os.getenv('MG5QS_INPUT_PATH'))
    OUTPUT_PATH = INPUT_PATH.parent/'output'
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir()  # target working directory to spawn output in dedicated location 
    # Run mg5 with the proc card in the ouput directory 
    process = subprocess.Popen([mg5_path/'bin/mg5_aMC', proc_card_path/proc_card_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(OUTPUT_PATH))
    print('starting process...')
    try:
        while process.poll() is None:
            time.sleep(.1)  # Add a small delay to reduce CPU usage
    finally:
        process.stdout.close()
        process.stderr.close()
        process.wait()  # Ensure the process is fully terminated

    print('done')
    output_name = _find(proc_card_path / proc_card_name, 'output').split()[1] #used to construct FRAMEWORK_PATH local
    return output_name, OUTPUT_PATH / output_name

# find line which begins with specified token
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

# Wrapper to call generate_events excutable
def generate_LHE(card, framework_path):
    path = card.file_spec.parent
    shutil.copy(card.file_spec, path / 'param_card.bak') # make backup
    card.write(overwrite=True) # write over param_card.dat
    input_path = Path(os.getenv('MG5QS_INPUT_PATH')) # grab env verr
    # Assemble and run command to generate LHE 
    command = f"{framework_path / 'bin/generate_events'} -f < {input_path / 'gen_event_input.mg5'}"
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(path / 'param_card.bak', path / 'param_card.dat')  # restore the origional card
    os.remove(path / 'param_card.bak')   # cleanup artifact 

def get_run_params(LHE):
    banner = _get_banner(LHE)
    return ParamCard(LHE.parent / banner, quiet=True)

def _get_banner(LHE):
    banner = None
    for fname in os.listdir(LHE.parent):
        if 'banner' in fname:
            banner = fname
            break
    return banner

# reads .lhe file to find number of events and cross section with uncertinty 
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

# compute weighted cross section for list of .lhe files 
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