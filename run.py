#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import envoy
import glob
import subprocess
import re


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
RESULT_DIR = os.path.join(CURRENT_DIR, 'results')
BUILD_GRAPH_SCRIPT = os.path.join(CURRENT_DIR, 'make_graph.R')
BIN = os.path.join(CURRENT_DIR, 'env/bin')
CCM = os.path.join(BIN, 'ccm')
CASSANDRA_DIR = "/home/aboudreault/git/cstar/cassandra"
CLUSTER_NAME = 'perftest'

# test constants
THREADS=50
N=10000000

STRESS_LINE_REGEX = r"^([\d\.]+\s*,\s*)+"

COMPACTION_STRATEGIES=(
    ('SizeTieredCompactionStrategy', ''),
    ('LeveledCompactionStrategy', ''),
    ('DateTieredCompactionStrategy', ''),
    ('LeveledCompactionStrategyMOL2', ", \\'max_overlapping_level\\':\\'2\\'"),
    ('LeveledCompactionStrategyMOL5', ", \\'max_overlapping_level\\':\\'5\\'")
)

# Each scenario must implement these patterns
BASIC_PATTERNS={
    'write': 'insert=1',
    'read': "read=1",
    'mixed': "insert=1,read=1",
    'mixed-write': "read=1,insert=2",
    'mixed-read': "read=2,insert=1"
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
    print("Running scenario '{}' with compaction strategy {} and pattern: {}".format(
        os.path.basename(scenario), cs[0], pattern
    ))
    c = cs[0]
    cs_ = c if c.find("MOL") == -1 else c[0: c.find("MOL")]
    p = run("bash -c \"sed 's/{%% strategy %%}/%s/' < %s > scenarios/tmp_.yaml\"" % (cs_, scenario))
    sed = r"sed \"s/{%% strategyOptions %%}/%s/\" < scenarios/tmp_.yaml > scenarios/tmp.yaml" % (cs[1],)
    p = run("bash -c \"%s\"" % sed)
    ops = "{},{}".format(BASIC_PATTERNS[pattern], variation)
    p = run('ccm node1 stress -- user profile={} ops\({}\) n={} -rate threads={}'.format(
        os.path.abspath('scenarios/tmp.yaml'), ops, N, THREADS)
    )
    output = p.std_out
    if p.status_code != 0:
        raise Exception("Error while running stress for: {}".format(scenario))
    print("Waiting compaction to finish")
    pending_tasks = 1
    while pending_tasks != 0:
        p = run("ccm node1 nodetool compactionstats | cut -d' ' -f3")
        pending_tasks = int(p.std_out[0]) if p.std_out else 0
        time.sleep(10)

    return output

def get_results(match):
    results = glob.glob("{}/{}.txt".format(RESULT_DIR, match))
    return results

def fix_results(scenario, pattern, variation, cs):
    # Apply time fix and rename result files
    results = get_results('clientrequest*')
    results += get_results('compaction*')
    results += get_results('ops*')
    scenario_name = os.path.basename(scenario).split('.')[0]
    cs = cs[0].lower()
    for result in results:
        lines = []
        with open(result, 'r') as r:
            lines = r.readlines()
        min_time = min(map(lambda line: long(line.split('\t')[2]), lines))
        new_name = "{}-{}-{}-{}".format(
            cs,
            os.path.basename(scenario).split('.')[0],
            pattern,
            os.path.basename(result)
        )
        with open(os.path.join(RESULT_DIR, new_name), 'w+') as r:
            for line in lines:
                line_parts = line.split('\t')
                # fix type
                line_parts[0] = "%s\t%s" % (cs, line_parts[0])
                # fix time
                line_parts[2] = str(long(line_parts[2]) - min_time)
                r.write('\t'.join(line_parts)+"\n")
        os.remove(result)

def write_stress_stats(scenario, pattern, variation, cs, output):
    lines = output.split('\n')
    regex = re.compile(STRESS_LINE_REGEX)
    scenario_name = os.path.basename(scenario).split('.')[0]
    cs = cs[0].lower()
    with open(os.path.join(RESULT_DIR, '{}-{}-{}-{}.txt'.format(
            cs, scenario_name, pattern, 'ops')), 'w+') as f:
        last_time = 0
        for line in lines:
            match = regex.match(line)
            if match:
                metrics = match.group(0).split(',')
                ops = metrics[2]
                t = long(float(metrics[11])*1000)
                if last_time == 0 or (t - last_time) < 10000:  # write a metric every 10 seconds
                    f.write("{}\tops\t{}\t{}\n".format(cs, ops, t))
                    last_time = t

def combine_results(match, output):
    results = get_results(match)
    run('bash -c "cat {} > {}"'.format(
        ' '.join(sorted(results)),
        os.path.join(RESULT_DIR, output)
    ))

def make_graphes(scenario, pattern, operation_mode_time_delim):
    # Produce the graph data files

    prefix = '{}-{}'.format(scenario, pattern)
    for type_ in ['ops', 'clientrequest-read', 'clientrequest-write',
                  'compaction-totalcompactionscompleted', 'compaction-bytescompacted']:
        combine_results("*-{}-{}*".format(prefix, type_), "{}-{}.data".format(prefix, type_))

    # Find R and generate the graphs
    p = run("which Rscript")
    if p.status_code != 0:
        raise Exception("Unable to find Rscript. Check your installation.")

    p = run('Rscript {} {} {} {}'.format(BUILD_GRAPH_SCRIPT, scenario, pattern, str(operation_mode_time_delim)))
    if p.status_code != 0:
        raise Exception("Error during graphes generation")
    print("Graphes generated.")

def main():
    # Run all the scenarios

    scenarios_path =  os.path.join(CURRENT_DIR, './scenarios/')

    for scenario in os.listdir(scenarios_path):
        if scenario.startswith('tmp'): continue
        for pattern in BASIC_PATTERNS:
            for variation in PATTERN_VARIATIONS:  # not taken into account yet
                for cs in COMPACTION_STRATEGIES:
                    # new ccm cluster for each run
                    run('make stop-jmxtrans')
                    run('{} stop'.format(CCM))
                    run('{} remove'.format(CCM))
                    run('{} create --install-dir {} --nodes 1 {}'.format(
                        CCM, CASSANDRA_DIR, CLUSTER_NAME
                    ))
                    run('{} start'.format(CCM))
                    s = os.path.join(scenarios_path, scenario)
                    if pattern == 'read':  # must run a write before
                        run_test(s, "write", "", cs)
                        run('{} stop'.format(CCM))
                        run('{} start'.format(CCM))
                    # BUG, the following command hangs indefinitely using envoy
                    p = subprocess.Popen(['make', 'start-jmxtrans'])
                    p.communicate()
                    time.sleep(30)
                    output = run_test(s, pattern, variation, cs)
                    write_stress_stats(s, pattern, variation, cs, output)
                    run('make stop-jmxtrans')
                    run('{} stop'.format(CCM))
                    run('{} remove'.format(CCM))
                    fix_results(s, pattern, variation, cs)

                make_graphes(scenario.split('.')[0], pattern, time.time()*1000)


if __name__ == '__main__':
    main()
