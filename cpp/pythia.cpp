#include "Pythia8/Pythia.h"
#include <iostream>
#include <vector>
#include <fstream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

using namespace Pythia8;
namespace py = pybind11;
constexpr int EVENT = 0; //used in status
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
constexpr int DAUGHTER1ID = 11;
constexpr int DAUGHTER2ID = 12;
constexpr int DUPLICATED = 13;

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

    int particles = 0;
    while (pythia.next()) {
        for (int i=0; i < pythia.event.size(); i++) {
            Particle &particle = pythia.event[i];
            if (std::abs(particle.id()) == particle_id) {
                int daughter1id = pythia.event[particle.daughter1()].id();
                int daughter2id = pythia.event[particle.daughter2()].id();
                bool duplicated = particle_id==daughter1id || particle_id==daughter2id;
                if (!duplicated) {
                    t_m(particles) = particle.pT();
                    particles++;
                }
            }
        }
    }
    cout << std::endl << "particles: " << particles << std::endl;
    return_vals["number of particles"] = particles;
    return_vals["status"] = 0;    
    return(return_vals);
}  


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

    int particles = 0;
    int event = 0;
    while (pythia.next()) {
        ++event;
        for (int i=0; i < pythia.event.size(); i++) {
            if (std::abs(pythia.event[i].id()) == particle_id) {
                const Particle &particle=pythia.event[i];
                s_c(EVENT, particles) = event;
                s_c(INDEX, particles) = particle.index();
                s_c(STATUS, particles) = particle.status();
                s_c(ISFINAL, particles) = particle.isFinal() ? 1 : 0;
                s_c(ISCHARGED, particles) = particle.isCharged() ? 1 : 0;
                int mother1 = particle.mother1();
                int mother2 = particle.mother2();
                s_c(MOTHER1, particles) = mother1;
                s_c(MOTHER2, particles) = mother2;
                s_c(MOTHER1ID, particles) = pythia.event[mother1].id();
                s_c(MOTHER2ID, particles) = pythia.event[mother2].id();
                int daughter1 = particle.daughter1();
                int daughter2 = particle.daughter2();
                s_c(DAUGHTER1, particles) = daughter1;
                s_c(DAUGHTER2, particles) = daughter2;
                int daughter1id = pythia.event[daughter1].id();
                int daughter2id = pythia.event[daughter2].id();
                s_c(DAUGHTER1ID, particles) = daughter1id;
                s_c(DAUGHTER2ID, particles) = daughter2id;
                bool dup = particle_id==daughter1id || particle_id==daughter2id;
                s_c(DUPLICATED, particles) = dup ? 1 : 0;
                t_m(particles) = particle.pT();
                particles++;
            }
        }
    }
    return_vals["number of particles"] = particles;
    return_vals["status"] = 0;    
    std::string fld = "EVENT,INDEX,STATUS,ISFINAL,ISCHARGED,MOTHER1,MOTHER2,MOTHER1ID,MOTHER2ID,DAUGHTER1,DAUGHTER2,DAUGHTER1ID,DAUGHTER2ID,DUPLICATED";
    return_vals["fields"] = fld;
    return(return_vals);
}   


PYBIND11_MODULE(pythia, m) {  // Single module declaration
    m.doc() = "Module to run Pythia showering from LHE file and capture particle information.";
    // Define pT function
    m.def("pT", 
          &pT,
          "Writes output to pre-allocated memory",
          py::arg("transverse_momenta").noconvert(),
          py::arg("particle_id"),
          py::arg("LHE_FILE_SPEC")
    );
    // Define particle_info function
    m.def("particle_info", 
          &particle_info,
          "Writes output to pre-allocated memory",
          py::arg("transverse_momenta").noconvert(),
          py::arg("status_codes").noconvert(),
          py::arg("particle_id"),
          py::arg("LHE_FILE_SPEC")
    );
}
