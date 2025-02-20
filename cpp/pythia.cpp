#include "Pythia8/Pythia.h"
#include <iostream>
#include <vector>
#include <set>
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
constexpr int CHAIN = 14;
constexpr int CHAININDEX = 15;

py::dict pT(py::array_t<double>& tranverse_momentum, int particle_id, std::string LHE_FILE_SPEC) {  //args: int argc, char* argv[]
    py::dict return_vals;  //dict will contain verous return values
    auto t_m = tranverse_momentum.mutable_unchecked<1>();
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


py::dict particle_info(py::array_t<double>& four_momentum, py::array_t<int>& status_codes, int particle_id, std::string LHE_FILE_SPEC) {
    py::dict return_vals;  //dict will contain verous return values
    std::vector<std::set<int>> chains; //used to keep track of chain number
    auto t_m = four_momentum.mutable_unchecked<2>();
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
        chains.clear();
        for (int i=0; i < pythia.event.size(); i++) {
            if (std::abs(pythia.event[i].id()) == particle_id) {
                const Particle &particle=pythia.event[i];
                s_c(particles, EVENT) = event;
                s_c(particles, INDEX) = particle.index();
                s_c(particles, STATUS) = particle.status();
                s_c(particles, ISFINAL) = particle.isFinal() ? 1 : 0;
                s_c(particles, ISCHARGED) = particle.isCharged() ? 1 : 0;
                int mother1 = particle.mother1();
                int mother2 = particle.mother2();
                s_c(particles, MOTHER1) = mother1;
                s_c(particles, MOTHER2) = mother2;
                s_c(particles, MOTHER1ID) = pythia.event[mother1].id();
                s_c(particles, MOTHER2ID) = pythia.event[mother2].id();
                int daughter1 = particle.daughter1();
                int daughter2 = particle.daughter2();
                s_c(particles, DAUGHTER1) = daughter1;
                s_c(particles, DAUGHTER2) = daughter2;
                int daughter1id = pythia.event[daughter1].id();
                int daughter2id = pythia.event[daughter2].id();
                s_c(particles, DAUGHTER1ID) = daughter1id;
                s_c(particles, DAUGHTER2ID) = daughter2id;
                bool dup = particle_id==daughter1id || particle_id==daughter2id;
                s_c(particles, DUPLICATED) = dup ? 1 : 0;
                t_m(particles, 0) = particle.px();
                t_m(particles, 1) = particle.py();
                t_m(particles, 2) = particle.pz();
                t_m(particles, 3) = particle.e();
                // find to which chain this particle belongs
                bool found = false;
                for (std::size_t i=0; i<chains.size(); i++) {  
                    if(chains[i].count(mother1) || chains[i].count(mother2)) {
                        //add this particle to the set with its parents
                        found = true;
                        s_c(particles, CHAIN) = i+1;
                        s_c(particles, CHAININDEX) = static_cast<int>(chains[i].size());
                        chains[i].insert(particle.index());
                        break;
                    }
                } 
                if (!found) {
                    //particle constitutes a new chain
                    chains.push_back({particle.index()});
                    s_c(particles, CHAIN) = chains.size();
                    s_c(particles, CHAININDEX) = 0;
                }
                particles++;
            }
        }
    }
    return_vals["number of particles"] = particles;
    return_vals["status"] = 0;    
    std::string fld = "EVENT,INDEX,STATUS,ISFINAL,ISCHARGED,MOTHER1,MOTHER2,MOTHER1ID,MOTHER2ID,DAUGHTER1,DAUGHTER2,DAUGHTER1ID,DAUGHTER2ID,DUPLICATED,CHAIN,CHAININDEX";
    return_vals["fields"] = fld;
    return(return_vals);
}   


PYBIND11_MODULE(pythia, m) {  // Single module declaration
    m.doc() = "Module to run Pythia showering from LHE file and capture particle information.";
    // Define pT function
    m.def("pT", 
          &pT,
          "Writes output to pre-allocated memory",
          py::arg("transverse_momentum").noconvert(),
          py::arg("particle_id"),
          py::arg("LHE_FILE_SPEC")
    );
    // Define particle_info function
    m.def("particle_info", 
          &particle_info,
          "Writes output to pre-allocated memory",
          py::arg("four_momentum").noconvert(),
          py::arg("status_codes").noconvert(),
          py::arg("particle_id"),
          py::arg("LHE_FILE_SPEC")
    );
}
