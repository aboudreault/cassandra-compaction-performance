#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import envoy
import glob

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
RESULT_DIR = os.path.join(CURRENT_DIR, 'results')
BUILD_GRAPH_SCRIPT = os.path.join(CURRENT_DIR, 'make_graph.R')
BIN = os.path.join(CURRENT_DIR, 'env/bin')
CCM = os.path.join(BIN, 'ccm')
CASSANDRA_VERSION = '2.1.3'
CLUSTER_NAME = 'perftest'

# test constants
THREADS=50
N=100000

# Each scenario must implemented these patterns
BASIC_PATTERNS={
    'write': 'insert=1',
#    'read': "read=1",
#    'mixed': "insert=1,read=1",
#    'mixed-write': "read=1,insert=2",
#    'mixed-read': "read=2,insert=1"
}

PATTERN_VARIATIONS=(
    "",  # no variation
#    "update=X",  # should not be 1:1, maybe 1:4 ?
#   "delete=X",
#   "ttl=X"    
)

def run(command):
    p = envoy.run(command)
    if p.status_code != 0:
        print(p.std_err)
        return False
    return True

def run_test(scenario, pattern, variation):
    ops = "{},{}".format(BASIC_PATTERNS[pattern], variation)
    print("Running scenario '{}' with pattern: {}".format(
        os.path.basename(scenario), pattern
    ))
    r = run('ccm node1 stress -- user profile={} ops\({}) n={} -rate threads={}'.format(scenario, ops, N, THREADS))
    if not r:
        raise Exception("Error while running stress for: {}".format(scenario))

def get_results(match):
    results = glob.glob("{}/*{}*.txt".format(RESULT_DIR, match))
    return results

def rename_result_files(scenario, pattern, variation):
    # Rename all results file to the proper name
    results = get_results('clientrequest*')
    results += get_results('compaction*')
    for result in results:
        new_name = "{}-{}-{}".format(
            os.path.basename(scenario).split('.')[0],
            pattern,
            os.path.basename(result)
        )
        os.rename(result, os.path.join(RESULT_DIR, new_name))

def combine_results(match, output):
    results = get_results(match)
    run('bash -c "cat {} > {}"'.format(
        ' '.join(results),
        os.path.join(RESULT_DIR, output)
    ))

def make_graphes(operation_mode_time_delim):
    # Produce the graph data files

    combine_results('clientrequest-read', 'clientrequest-read.data')
    combine_results('clientrequest-write', 'clientrequest-write.data')
    combine_results('compaction-totalcompactionscompleted', 'compaction-totalcompactionscompleted.data')
    combine_results('compaction-bytescompacted', 'compaction-bytescompacted.data')

    # Find R and generate the graphs
    r = run("which Rscript")
    if not r:
        raise Exception("Unable to find Rscript. Check your installation.")

    r = run('Rscript {} {}'.format(BUILD_GRAPH_SCRIPT, str(operation_mode_time_delim)))
    if not r:
        raise Exception("Error during graphes generation")
    print("Graphes generated.")

def main():
    # Run all the scenarios

    scenarios_path =  os.path.join(CURRENT_DIR, './scenarios/')

    for scenario in os.listdir(scenarios_path):
        for pattern in BASIC_PATTERNS:
            for variation in PATTERN_VARIATIONS:
                # new ccm cluster for each run
                run('{} stop'.format(CCM))
                run('{} remove'.format(CCM))
                run('{} create -v {} --nodes 1 {}'.format(
                    CCM, CASSANDRA_VERSION, CLUSTER_NAME
                ))
                run('{} start'.format(CCM))
                s = os.path.join(scenarios_path, scenario)
                run_test(s, pattern, variation)
                run('make stop-jmxtrans')
                run('{} stop'.format(CCM))
                run('{} remove'.format(CCM))
                rename_result_files(s, pattern, variation)

    make_graphes(time.time()*1000)
    

if __name__ == '__main__':
    main()
