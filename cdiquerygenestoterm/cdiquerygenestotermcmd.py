#!/usr/bin/env python

import os
import sys
import argparse
import json
import requests
import time
import cdiquerygenestoterm


def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)
    parser.add_argument('input',
                        help='comma delimited list of genes in file')
    parser.add_argument('--url', default='http://public.ndexbio.org',
                        help='Endpoint of REST service')
    parser.add_argument('--polling_interval', default=1,
                        type=float, help='Time in seconds to'
                                         'wait between '
                                         'checks on task '
                                         'completion')
    parser.add_argument('--timeout', default=30,
                        type=int, help='Timeout for http '
                                       'requests in seconds')
    parser.add_argument('--retrycount', default=180, type=int,
                        help='Number times to check for completed'
                             'request. Take this value times'
                             'the --polling_interval to determine'
                             'how long this tool will wait'
                             'for a completed result')
    return parser.parse_args(args)


def read_inputfile(inputfile):
    """

    :param inputfile:
    :return:
    """
    with open(inputfile, 'r') as f:
        return f.read()


def get_completed_result(resturl, taskid, user_agent,
                         timeout=30):
    """

    :param resultasdict:
    :return:
    """
    res = requests.get(resturl + '/integratedsearch/v1/' + taskid +
                       '?start=0&size=1',
                       headers={'Content-Type': 'application/json',
                                'User_agent': user_agent},
                       timeout=timeout)
    if res.status_code != 200:
        sys.stderr.write('Received http error: ' +
                         str(res.status_code) + '\n')
        return None
    return res.json()


def wait_for_result(resturl, taskid, user_agent, polling_interval=1,
                    timeout=30,
                    retrycount=180):
    """
    Polls **resturl** with **taskid**
    :param resturl:
    :param taskid:
    :param user_agent:
    :param polling_interval:
    :param timeout:
    :param retrycount:
    :return: True if task completed successfully False otherwise
    :rtype: bool
    """
    counter = 0
    while counter < retrycount:
        try:
            res = requests.get(resturl + '/integratedsearch/v1/' +
                               taskid + '/status',
                               headers={'Content-Type': 'application/json',
                                        'User_agent': user_agent},
                               timeout=timeout)

            if res.status_code is 200:
                jsonres = res.json()
                if jsonres['progress'] == 100:
                    if jsonres['status'] != 'complete':
                        sys.stderr.write('Got error: ' + str(jsonres) + '\n')
                        return False
                    return True
            else:
                sys.stderr.write('Received error : ' +
                                 str(res.status_code) +
                                 ' while polling for completion')
        except requests.exceptions.RequestException as e:
            sys.stderr.write('Received exception waiting for task'
                             'completion: ' + str(e))

        counter += 1
        time.sleep(polling_interval)
    return False


def get_result_in_mapped_term_json(resultasdict):
    """

    :param resultasdict:
    :return:
    """
    sources = 'sources'
    results = 'results'
    if resultasdict is None:
        sys.stderr.write('Results are None\n')
        return None

    if sources not in resultasdict:
        sys.stderr.write('No sources found in results\n')
        return None

    if resultasdict[sources] is None:
        sys.stderr.write('Source is None\n')
        return None

    if len(resultasdict[sources]) <= 0:
        sys.stderr.write('Source is empty\n')
        return None

    if results not in resultasdict[sources][0]:
        sys.stderr.write('Results not in source\n')
        return None

    if resultasdict[sources][0][results] is None:
        sys.stderr.write('First result is None')
        return None

    if len(resultasdict[sources][0][results]) <= 0:
        sys.stderr.write('No result found\n')
        return None

    firstresult = resultasdict[sources][0][results][0]
    colon_loc = firstresult['description'].find(':')
    if colon_loc == -1:
        source = 'NA'
    else:
        source = firstresult['description'][0:colon_loc]
    theres = {'name': firstresult['description'][colon_loc + 1:].lstrip(),
              'source': source,
              'p_value': firstresult['details']['PValue'],
              'description': firstresult['url'],
              'intersections': firstresult['hitGenes']}

    return theres


def run_iquery(inputfile, theargs):
    """
    todo

    :param inputfile:
    :param theargs:
    :param gprofwrapper:
    :return:
    """
    genes = read_inputfile(inputfile)
    genes = genes.strip(',').strip('\n').split(',')
    if genes is None or (len(genes) == 1 and len(genes[0].strip()) == 0):
        sys.stderr.write('No genes found in input')
        return None
    user_agent = 'cdiquerygenestoterm/' + cdiquerygenestoterm.__version__
    resturl = theargs.url

    query = {'geneList': genes,
             'sourceList': ['enrichment']}
    res = requests.post(resturl + '/integratedsearch/v1/',
                       json=query, headers={'Content-Type': 'application/json',
                                            'User-Agent': user_agent},
                        timeout=theargs.timeout)
    if res.status_code != 202:
        sys.stderr.write('Got error status from service: ' + str(res.status_code) + ' : ' + res.text + '\n')
        return None

    taskid = res.json()['id']

    if wait_for_result(resturl, taskid, user_agent,
                       timeout=theargs.timeout,
                       retrycount=theargs.retrycount,
                       polling_interval=theargs.polling_interval) is False:
        return None

    resjson = get_completed_result(resturl, taskid, user_agent,
                                   timeout=theargs.timeout)
    return get_result_in_mapped_term_json(resjson)


def main(args):
    """
    Main entry point for program

    :param args: command line arguments usually :py:const:`sys.argv`
    :return: 0 for success otherwise failure
    :rtype: int
    """
    desc = """
        Running gene enrichment against Integrated Query

        Takes file with comma delimited list of genes as input and
        outputs matching term if any
    """

    theargs = _parse_arguments(desc, args[1:])

    try:
        inputfile = os.path.abspath(theargs.input)
        theres = run_iquery(inputfile, theargs)
        if theres is None:
            sys.stderr.write('No terms found\n')
        else:
            json.dump(theres, sys.stdout)
        sys.stdout.flush()
        return 0
    except Exception as e:
        sys.stderr.write('Caught exception: ' + str(e))
        return 2


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
