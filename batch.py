#!/usr/bin/env python

from relplan import Planner
import subprocess
import argparse
import logging
import reltree
import json
import sys
import os

jupiter = ['java', '-jar', 'lib/jupiter.jar']


def execute(sql, db, config):
    try:
        output = subprocess.check_output(jupiter + ['--json', db, sql])
    except subprocess.CalledProcessError as e:
        print e.output
        sys.exit(1)

    root = reltree.parse(output)
    planner = Planner(config)
    plans = planner.get_plans(root)
    bestplan = planner.get_best_plan(root)
    return (bestplan.totalcost(), len(plans))


def runquery(query, sql, db, confs, verbose=False):
    id = os.path.splitext(query)[0]
    costs, ns = zip(*[execute(sql, db, conf) for conf in confs])
    return '%s,%s,%s' % (id, ','.join(map(str, costs)), ','.join(map(str, ns)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Use Optiq to get a relational plan from SQL statements.')
    parser.add_argument('CONF', help='Folder containing servers config files')
    parser.add_argument('SQL', help='Folder containing the queries as files')
    parser.add_argument('DB', help='SQLite database to use as schema source')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
        help='Be more verbose (just print out also the configuration files)')
    args = parser.parse_args()

    if not os.path.isdir(args.CONF):
        print 'Configuration folder not found: %s' % args.CONF
        sys.exit(1)
    if not os.path.isdir(args.SQL):
        print 'Queries folder not found: %s' % args.SQL
        sys.exit(1)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    confs = [os.path.join(args.CONF, c) for c in sorted(os.listdir(args.CONF))]
    logging.info(confs)

    for query in sorted(os.listdir(args.SQL)):
        with open(os.path.join(args.SQL, query)) as sql:
            print runquery(query, sql.read(), args.DB, confs, args.verbose)
