#include "Pythia8/Pythia.h"
#include <iostream>
#include <vector>
#include <set>
#include <fstream>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

using namespace Pythia8;
namespace py = pybind11;

constexpr int PROCESS_ID_LHE = 1;
constexpr int PROCESS_ID_PYTHIA = 2;

const std::string LHE_TOPIC = "LHE";
const std::string PARENT_TOPIC = "PARENT";
const std::string P_TOPIC = "P_mu";
const std::string CHAIN_TOPIC = "CHAIN";

const std::string BASIC_FIELDS  = ",EVENT,ID,INDEX,PROCESS,STATUS,ISFINAL,ISCHARGED";
const std::string PARENT_FIELDS = ",MOTHER1,MOTHER2,MOTHER1ID,MOTHER2ID,DAUGHTER1,DAUGHTER2,DAUGHTER1ID,DAUGHTER2ID";
const std::string CHAIN_FIELDS = ",CHAIN,CHAININDEX,CHAINLENGTH";
const std::string P_FIELDS = ",px,py,pz,E";

const uint8_t BASIC_MASK  = 0b00000001;
const uint8_t LHE_MASK    = 0b00000010;
const uint8_t PARENT_MASK = 0b00000100;
const uint8_t P_MASK      = 0b00001000;
const uint8_t CHAIN_MASK  = 0b00010000;

/**
 * inner function to record events from LHE hard process or pythia shower
 */
void recordEvent(Pythia& pythia,
                 int event_n,
                 int process_id,
                 int& n,
                 uint8_t topic_mask,
                 Event& event, 
                 const std::set<int>& pid_set,
                 std::unordered_map<int, std::vector<std::set<int>>>& chains,
                 std::unordered_map<int, std::vector<std::set<int>>>& ch_len,
                 py::array_t<double> fvals,
                 py::array_t<int> ivals,
                 int nmax) {

    chains.clear();
    ch_len.clear();
    int chain_num = 1; 
    auto fv = fvals.mutable_unchecked<2>();
    auto iv = ivals.mutable_unchecked<2>();
    int chain_length_col = 0;

    for (int i=0; i < event.size(); i++) {
        Particle &particle = event[i];
        int col = 0;
        if (pid_set.count(std::abs(particle.id()))) { //include specificed particles and related anti-particles
            if (topic_mask & BASIC_MASK) {
                iv(n, col++) = event_n;
                iv(n, col++) = particle.id();
                iv(n, col++) = particle.index();
                iv(n, col++) = process_id;
                iv(n, col++) = particle.status();
                iv(n, col++) = particle.isFinal() ? 1 : 0;
                iv(n, col++) = particle.isCharged() ? 1 : 0;
            }
            if (topic_mask & PARENT_MASK) {
                int mother1 = particle.mother1();
                int mother2 = particle.mother2();
                iv(n, col++) = mother1;
                iv(n, col++) = mother2;
                iv(n, col++) = event[mother1].id();
                iv(n, col++) = event[mother2].id();
                int daughter1 = particle.daughter1();
                int daughter2 = particle.daughter2();
                iv(n, col++) = daughter1;
                iv(n, col++) = daughter2;
                int daughter1id = event[daughter1].id();
                int daughter2id = event[daughter2].id();
                iv(n, col++) = daughter1id;
                iv(n, col++) = daughter2id;
            }
            if (topic_mask & P_MASK) {
                fv(n, 0) = particle.px();
                fv(n, 1) = particle.py();
                fv(n, 2) = particle.pz();
                fv(n, 3) = particle.e();
            }
            if (topic_mask & CHAIN_MASK) {             
                //find to which chain this particle belongs
                int p = particle.id();
                if (chains.find(p) == chains.end()) {
                    chains[p] = std::vector<std::set<int>>();
                    ch_len[p] = std::vector<std::set<int>>();
                }
                std::vector<std::set<int>>& chain = chains[p]; //use a reference (don't make a copy)
                std::vector<std::set<int>>& ch_n  = ch_len[p]; //use a reference (don't make a copy)
                bool found = false;
                for (std::size_t i=0; i<chain.size(); i++) {  
                    if(chain[i].count(particle.mother1()) || chain[i].count(particle.mother2())) {
                        //add this particle to the set with its parents
                        found = true;
                        iv(n, col++) = i+1;
                        chain[i].insert(particle.index());
                        ch_n[i].insert(n);
                        iv(n, col++) = chain[i].size();
                        iv(n, col++) = 0; //reserved for chain length
                        break; 
                    }
                } 
                if (!found) {
                    //particle constitutes a new chain
                    chain.push_back({particle.index()});
                    ch_n.push_back({n});
                    iv(n, col++) = chain_num++;
                    iv(n, col++) = 1;
                    chain_length_col = col;
                    iv(n, col++) = 0; //reserved for chain length
                }            
            }
            n++; //n is passed by reference so value is maintained after return
            if (n == nmax) { //check for overflow of preallocated numpy array
                n = -1;
                return;
            }
        }
    }
    if (topic_mask & CHAIN_MASK) {
        for (const std::pair<const int, std::vector<std::set<int>>>& pair : ch_len) {
            const std::vector<std::set<int>>& v = pair.second;
            for (const std::set<int>& s : v) {
                for (int i : s) {
                    iv(i, chain_length_col) = s.size();
                }
            }
        }
    }
}

/**
 * Group IDs:
 *   BASIC = event, index, type, status, final, charged (always included)
 *   LHE = upstream values from LHE process
 *   PARENT = mother/daughter types and IDs
 *   P_mu = four momenta
 *   CHAIN = decay chain index, length, position
 */
py::dict pythia8(py::array_t<double>& fvals, 
                 py::array_t<int>& ivals, 
                 py::array_t<int>& PIDs, 
                 std::string topics, 
                 std::string LHE_FILE_SPEC) {
    
    //particle IDs of interest
    auto pids = PIDs.mutable_unchecked<1>();
    std::set<int> pid_set; 
    for (ssize_t i = 0; i < pids.shape(0); i++) {
        pid_set.insert(pids(i));
    }

    //topics of interest
    uint8_t topic_mask = BASIC_MASK;
    if (topics.find(LHE_TOPIC) != std::string::npos) topic_mask |= LHE_MASK;  
    if (topics.find(PARENT_TOPIC) != std::string::npos) topic_mask |= PARENT_MASK;
    if (topics.find(P_TOPIC) != std::string::npos) topic_mask |= P_MASK;
    if (topics.find(CHAIN_TOPIC) != std::string::npos) topic_mask |= CHAIN_MASK;
    
    //return values
    py::dict return_vals;  //dict will contain verous return values
    std::unordered_map<int, std::vector<std::set<int>>> chains; //used to keep track of chain numbers
    std::unordered_map<int, std::vector<std::set<int>>> ch_len; //used to keep track of chain lengths
    
    Pythia pythia("",false);   //make pythia object (supress banner)

    //suppress command line output
    pythia.readString("SLHA:verbose = 0");
    pythia.readString("Print:quiet = on");     //completely silent mode

    //read from lhe file (includes all perameters)
    pythia.readString("Beams:frameType = 4");  //these are the magic words; reading from lhe file
    pythia.readString("Beams:LHEF = " + LHE_FILE_SPEC); 
    pythia.readString("Random:setSeed = on");  //change the random number selection to be based on the system clock
    pythia.readString("Random:seed = 0");      //each .lhe will shower diffrently
    pythia.init();
    
    //Record results from pythia events
    int n = 0;
    int event_n = 1;
    auto info = fvals.request(); //get max rows allocated to numpy array
    int nmax = static_cast<int>(info.shape[0]);

    while (pythia.next()) {
        if (topic_mask & LHE_MASK) {
            recordEvent(pythia, event_n, PROCESS_ID_LHE, n, topic_mask, pythia.process, pid_set, chains, ch_len, fvals, ivals, nmax);
        }
        recordEvent(pythia, event_n, PROCESS_ID_PYTHIA, n, topic_mask, pythia.event, pid_set, chains, ch_len, fvals, ivals, nmax);
        event_n++;
        if (n == -1) { //overflow of numpy array
            break;
        }
    }
    return_vals["n"] = n;

    //column heading for dataframe
    std::string fld = "";
    if (topic_mask & BASIC_MASK) fld += BASIC_FIELDS;
    if (topic_mask & PARENT_MASK) fld += PARENT_FIELDS;
    if (topic_mask & CHAIN_MASK) fld += CHAIN_FIELDS;
    if (topic_mask & P_MASK) fld += P_FIELDS;
    return_vals["fields"] = fld.substr(1); //remove leading comma

    return (return_vals);
};

std::string get_topics() {
    return "LHE, PARENT, P_mu, CHAIN";
}

py::dict get_topic_widths() {
    py::dict widths;
    widths["BASIC"] = 7;
    widths["PARENT"] = 8;
    widths["CHAIN"] = 3;
    return widths;
}

PYBIND11_MODULE(pythia, m) {
    m.doc() = "Module to run Pythia showering from LHE file and capture particle information.";
    m.def("pythia8", 
          &pythia8,
          "Writes output to pre-allocated memory",
          py::arg("fvals").noconvert(),
          py::arg("ivals").noconvert(),
          py::arg("PIDs").noconvert(),
          py::arg("topics"),
          py::arg("LHE_FILE_SPEC")
    );
    m.def("get_topics", 
        &get_topics,
        "Returns a string listing topics");
    m.def("get_topic_widths", 
          &get_topic_widths,
          "Returns a dictionary of topic widths");
}
