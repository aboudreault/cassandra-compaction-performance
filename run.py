#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import envoy

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
BUILD_GRAPH_SCRIPT = os.path.join(CURRENT_DIR, 'make_graph.R')

# test constants
THREADS=50
N=10000000
# Each scenario must implemented these patterns
BASIC_PATTERNS=(
    'insert=1',
#    "read=1",
#    "insert=1,read=1",
#    "read=1,insert=2",
#    "read=2,insert=1"
)

PATTERN_VARIATIONS=(
    "",  # no variation
#    "update=X",  # should not be 1:1, maybe 1:4 ?
#   "delete=X",
#   "ttl=X"    
)


def make_graphes(operation_mode_time_delim):
    # Find R and generate the graphs
    p = envoy.run("which Rscript")
    if p.status_code != 0:
        raise Exception("Unable to find Rscript. Check your installation.")

    p = envoy.run('Rscript {} {}'.format(BUILD_GRAPH_SCRIPT, str(operation_mode_time_delim)))
    if p.status_code != 0:
        print(p.std_err)
        raise Exception("Error during graphes generation")
    print("Graphes generated.")
            
def main():
    # Run all the scenarios

    scenarios_path =  os.path.join(CURRENT_DIR, './scenarios/')

    for scenario in os.listdir(scenarios_path):
        for pattern in BASIC_PATTERNS:
            for variation in PATTERN_VARIATIONS:
                ops = "{},{}".format(pattern, variation)
                print("Running scenario '{}' with pattern: {}".format(scenario, ops))
                path = os.path.join(scenarios_path, scenario)
                p = envoy.run('ccm node1 stress -- user profile={} ops\({}) n={} -rate threads={}'.format(path, ops, N, THREADS))
                if p.status_code != 0:
                    print(p.std_err)
                    raise Exception("Error while running stress for: {}".format(scenario))

    make_graphes(time.time()*1000)
    

if __name__ == '__main__':
    main()
