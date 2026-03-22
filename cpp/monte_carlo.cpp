#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <omp.h>
#include <random>
#include <cmath>
#include <iostream>

namespace py = pybind11;

py::array_t<double> simulate_paths(double S0, double drift, double vol, int days, int num_paths) {
    // Alokacja tablicy - sprawdzamy, czy num_paths nie jest absurdalne
    if (num_paths > 100000000) num_paths = 100000000; 
    
    auto result = py::array_t<double>(num_paths);
    auto ptr = result.mutable_data();

    double dt = 1.0 / 252.0;
    double drift_adj = (drift - 0.5 * vol * vol) * dt;
    double vol_adj = vol * std::sqrt(dt);

    #pragma omp parallel
    {
        // Seedowanie oparte na czasie i ID wątku - najstabilniejsze na Windows
        unsigned int seed = static_cast<unsigned int>(time(NULL)) ^ omp_get_thread_num();
        std::mt19937 gen(seed);
        std::normal_distribution<double> dist(0.0, 1.0);

        #pragma omp for
        for (int i = 0; i < num_paths; ++i) {
            double current_S = S0;
            for (int d = 0; d < days; ++d) {
                current_S *= std::exp(drift_adj + vol_adj * dist(gen));
            }
            ptr[i] = (current_S - S0) / S0;
        }
    }
    return result;
}

PYBIND11_MODULE(monte_carlo_cpp, m) {
    m.def("simulate_paths", &simulate_paths, "HPC Engine",
          py::call_guard<py::gil_scoped_release>());
}