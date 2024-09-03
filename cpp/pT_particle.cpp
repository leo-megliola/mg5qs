#include "Pythia8/Pythia.h"
#include <iostream>
#include <vector>
#include <fstream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

using namespace Pythia8;
namespace py = pybind11;

py::dict pT(py::array_t<double>& tranverse_momenta, int particle_id, std::string LHE_FILE_SPEC) {  //args: int argc, char* argv[]
    py::dict return_vals;  //dict will contain verous return values
    auto t_m = tranverse_momenta.mutable_unchecked<1>();
    Pythia pythia;   //make pythia object

    // Suppress command line output
    pythia.readString("Print:quiet = on");       // Completely silent mode
    // Read from lhe file (includes all perameters)
    pythia.readString("Beams:frameType = 4");      //these are the magic words; reading from lhe file
    pythia.readString("Beams:LHEF = "+LHE_FILE_SPEC); 


    pythia.readString("Random:setSeed = on");  //change the random number selection to be based on the system clock
    pythia.readString("Random:seed = 0");      //each .lhe will shower diffrently
    pythia.init();

    int taus = 0;
    while (pythia.next()) {
        for (int i=0; i < pythia.event.size(); i++) {
            if (std::abs(pythia.event[i].id()) == particle_id) {
                Particle &tau=pythia.event[i];
                double px = tau.px();
                double py = tau.py();
                double pT_ = pow((pow(px,2.)) + pow(py,2.), 0.5);
                t_m(taus) = pT_;
                taus++;
            }
        }
    }
    cout << std::endl << "TAUS: " << taus << std::endl;
    return_vals["number of particles"] = taus;
    return_vals["status"] = 0;    
    return(return_vals);
}   

PYBIND11_MODULE(pT_particle, m) {
    m.doc() = "Module to run Pythia showering from lhe file, and capture transverse momenta of tau particles.";
    m.def("pT", 
          &pT,
          "writes to output file",
          py::arg("transverse_momenta").noconvert(),
          py::arg("particle_id"),
          py::arg("LHE_FILE_SPEC")
          );
}
