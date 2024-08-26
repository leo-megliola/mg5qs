import pT_particle
import numpy as np

# A wrapper to handle interactions with pybind11
def pT(particle_id, N, lhe_file_spec, size=100000):
    transverse_momenta = np.zeros(size, dtype=np.float64)
    rets = pT_particle.pT(transverse_momenta, particle_id, N, lhe_file_spec)
    if rets["number of particles"] > size:
        raise ValueError('Number of particles exceeds length of data buffer: '+str(rets["number of particles"])+' > '+str(size))
    return (rets, transverse_momenta[0:rets["number of particles"]])
