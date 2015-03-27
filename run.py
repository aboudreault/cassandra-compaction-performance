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

COMPACTION_STRATEGIES=(
    'SizeTieredCompactionStrategy',
)

# Each scenario must implement these patterns
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
    return p

def run_test(scenario, pattern, variation, cs):
    print("Running scenario '{}' with compaction strategy '' and pattern: {}".format(
        os.path.basename(scenario), cs, pattern
    ))
    p = run("bash -c \"sed 's/{%% strategy %%}/%s/' < %s > scenarios/tmp.yaml\"" % (cs, scenario))
    ops = "{},{}".format(BASIC_PATTERNS[pattern], variation)
    p = run('ccm node1 stress -- user profile={} ops\({}) n={} -rate threads={}'.format(
        os.path.abspath('scenarios/tmp.yaml'), ops, N, THREADS)
    )
    if p.status_code != 0:
        raise Exception("Error while running stress for: {}".format(scenario))
    print("Waiting compaction to finish")
    pending_tasks = 1
    while pending_tasks != 0:
        p = run("ccm node1 nodetool compactionstats | cut -d' ' -f3")
        pending_tasks = int(p.std_out[0])
        time.sleep(10)
    

def get_results(match):
    results = glob.glob("{}/*{}*.txt".format(RESULT_DIR, match))
    return results

def rename_result_files(scenario, pattern, variation, cs):
    # Rename all results file to the proper name
    results = get_results('clientrequest*')
    results += get_results('compaction*')
    cs = cs.lower()
    scenario_name = os.path.basename(scenario).split('.')[0]
    for result in results:
        tmp_file = 'results/tmp'
        p = run("bash -c \"sed 's/^/{}./' < {} > {}\"" .format(scenario_name, result, tmp_file))
        print p.command
        new_name = "{}-{}-{}-{}".format(
            cs,
            os.path.basename(scenario).split('.')[0],
            pattern,
            os.path.basename(result)
        )
        os.rename(tmp_file, os.path.join(RESULT_DIR, new_name))

def combine_results(match, output):
    results = get_results(match)
    run('bash -c "cat {} > {}"'.format(
        ' '.join(results),
        os.path.join(RESULT_DIR, output)
    ))

def make_graphes(operation_mode_time_delim):
    # Produce the graph data files

    for cs in COMPACTION_STRATEGIES:
        for pattern in BASIC_PATTERNS:
            match = '{}-*-{}'.format(cs.lower(), pattern)
            prefix = '{}-{}'.format(cs.lower(), pattern)
            combine_results(match+'-clientrequest-read', prefix+'-clientrequest-read.data')
            combine_results(match+'-clientrequest-write', prefix+'-clientrequest-write.data')
            combine_results(match+'-compaction-totalcompactionscompleted', prefix+'-compaction-totalcompactionscompleted.data')
            combine_results(match+'-compaction-bytescompacted', prefix+'-compaction-bytescompacted.data')

    # Find R and generate the graphs
    p = run("which Rscript")
    if p.status_code != 0:
        raise Exception("Unable to find Rscript. Check your installation.")

    p = run('Rscript {} {}'.format(BUILD_GRAPH_SCRIPT, str(operation_mode_time_delim)))
    if p.status_code != 0:
        raise Exception("Error during graphes generation")
    print("Graphes generated.")

def main():
    # Run all the scenarios

    scenarios_path =  os.path.join(CURRENT_DIR, './scenarios/')

    for scenario in os.listdir(scenarios_path):
        if scenario == 'tmp.yaml': continue
        for pattern in BASIC_PATTERNS:
            for variation in PATTERN_VARIATIONS:
                for cs in COMPACTION_STRATEGIES:
                    # new ccm cluster for each run
                    run('{} stop'.format(CCM))
                    run('{} remove'.format(CCM))
                    run('{} create -v {} --nodes 1 {}'.format(
                        CCM, CASSANDRA_VERSION, CLUSTER_NAME
                    ))
                    run('{} start'.format(CCM))
                    s = os.path.join(scenarios_path, scenario)
                    run_test(s, pattern, variation, cs)
                    run('make stop-jmxtrans')
                    run('{} stop'.format(CCM))
                    run('{} remove'.format(CCM))
                    rename_result_files(s, pattern, variation, cs)

    make_graphes(time.time()*1000)
    

if __name__ == '__main__':
    main()
