#include "Pythia8/Pythia.h"
#include <iostream>
#include <vector>
#include <fstream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

using namespace Pythia8;
namespace py = pybind11;
constexpr int EVENT = 0;
constexpr int INDEX = 1;
constexpr int STATUS = 2;
constexpr int ISFINAL = 3;
constexpr int ISCHARGED = 4;
constexpr int MOTHER1 = 5;
constexpr int MOTHER2 = 6;
constexpr int MOTHER1ID = 7;
constexpr int MOTHER2ID = 8;
constexpr int DAUGHTER1 = 9;
constexpr int DAUGHTER2 = 10;

py::dict particle_info(py::array_t<double>& tranverse_momenta, py::array_t<int>& status_codes, int particle_id, std::string LHE_FILE_SPEC) {
    py::dict return_vals;  //dict will contain verous return values
    auto t_m = tranverse_momenta.mutable_unchecked<1>();
    auto s_c = status_codes.mutable_unchecked<2>();
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
    int event = 0;
    while (pythia.next()) {
        ++event;
        for (int i=0; i < pythia.event.size(); i++) {
            if (std::abs(pythia.event[i].id()) == particle_id) {
                const Particle &tau=pythia.event[i];
                s_c(EVENT, taus) = event;
                s_c(INDEX, taus) = tau.index();
                s_c(STATUS, taus) = tau.status();
                s_c(ISFINAL, taus) = tau.isFinal() ? 1 : 0;
                s_c(ISCHARGED, taus) = tau.isCharged() ? 1 : 0;
                int mother1 = tau.mother1();
                int mother2 = tau.mother2();
                s_c(MOTHER1, taus) = mother1;
                s_c(MOTHER2, taus) = mother2;
                s_c(MOTHER1ID, taus) = pythia.event[mother1].id();
                s_c(MOTHER2ID, taus) = pythia.event[mother2].id();
                s_c(DAUGHTER1, taus) = tau.daughter1();
                s_c(DAUGHTER2, taus) = tau.daughter2();
                t_m(taus) = tau.pT();
                taus++;
            }
        }
    }
    return_vals["number of particles"] = taus;
    return_vals["status"] = 0;    
    std::string fld = "EVENT,INDEX,STATUS,ISFINAL,ISCHARGED,MOTHER1,MOTHER2,MOTHER1ID,MOTHER2ID,DAUGHTER1,DAUGHTER2";
    return_vals["fields"] = fld;
    return(return_vals);
}   

PYBIND11_MODULE(pT_particle, m) {
    m.doc() = "Module to run Pythia showering from lhe file, and capture various particle data information.";
    m.def("particle_info", 
          &particle_info,
          "writes output to pre-alocated memory",
          py::arg("transverse_momenta").noconvert(),
          py::arg("status_codes").noconvert(),
          py::arg("particle_id"),
          py::arg("LHE_FILE_SPEC")
          );
}
