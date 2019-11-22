#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cdgprofilergenestoterm
----------------------------------

Tests for `cdgprofilergenestoterm` module.
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock
import requests
import requests_mock

import cdiquerygenestoterm
from cdiquerygenestoterm import cdiquerygenestotermcmd


class TestCdgprofilergenestoterm(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_read_inputfile(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            with open(tfile, 'w') as f:
                f.write('hellothere')
            res = cdiquerygenestotermcmd.read_inputfile(tfile)
            self.assertEqual('hellothere', res)
        finally:
            shutil.rmtree(temp_dir)

    def test_parse_args(self):
        myargs = ['inputarg']
        res = cdiquerygenestotermcmd._parse_arguments('desc',
                                                      myargs)
        self.assertEqual('inputarg', res.input)
        self.assertEqual('http://public.ndexbio.org', res.url)
        self.assertEqual(1, res.polling_interval)
        self.assertEqual(180, res.retrycount)
        self.assertEqual(30, res.timeout)

    def test_run_iquery_no_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = [tfile]
            theargs = cdiquerygenestotermcmd._parse_arguments('desc',
                                                              myargs)
            try:
                cdiquerygenestotermcmd.run_iquery(tfile,
                                                  theargs)
                self.fail('Expected FileNotFoundError')
            except FileNotFoundError:
                pass
        finally:
            shutil.rmtree(temp_dir)

    def test_run_iquery_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = [tfile]
            theargs = cdiquerygenestotermcmd._parse_arguments('desc',
                                                              myargs)
            res = cdiquerygenestotermcmd.run_iquery(tfile,
                                                    theargs)
            self.assertEqual(None, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_get_completed_result_error(self):
        with requests_mock.Mocker() as m:
            m.get('http://foo/integratedsearch/'
                  'v1/mytaskid?start=0&size=1',
                  status_code=500)
            res = cdiquerygenestotermcmd.\
                get_completed_result('http://foo',
                                     'mytaskid',
                                     'hi')

        self.assertEqual(None, res)

    def test_get_completed_result_successful(self):
        with requests_mock.Mocker() as m:
            m.get('http://foo/integratedsearch/'
                  'v1/mytaskid?start=0&size=1',
                  json={'hi': 'there'})
            res = cdiquerygenestotermcmd.\
                get_completed_result('http://foo',
                                     'mytaskid',
                                     'hi')

        self.assertEqual({'hi': 'there'}, res)

    def test_wait_for_result_done_immediately(self):
        with requests_mock.Mocker() as m:
            m.get('http://foo/integratedsearch/v1/t/status',
                  json={'progress': 100,
                        'status': 'complete'})
            res = cdiquerygenestotermcmd. \
                wait_for_result('http://foo',
                                't', user_agent='hi')
            self.assertEqual(True, res)

    def test_wait_for_result_error(self):
        with requests_mock.Mocker() as m:
            m.get('http://foo/integratedsearch/v1/t/status',
                  json={'progress': 100,
                        'status': 'error'})
            res = cdiquerygenestotermcmd. \
                wait_for_result('http://foo',
                                't', user_agent='hi')
            self.assertEqual(False, res)

    def test_wait_for_result_eventual_success(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'http://foo/'
                                  'integratedsearch/v1/t/status',
                           [{'json': {'progress': 50, 'status': ''},
                             'status_code': 200},
                            {'status_code': 500},
                            {'json': {'progress': 100, 'status': 'complete'},
                             'status_code': 200}])

            res = cdiquerygenestotermcmd. \
                wait_for_result('http://foo',
                                't', user_agent='hi',
                                polling_interval=0.001)
            self.assertEqual(True, res)

    def test_wait_for_call_timeout(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'http://foo/'
                                  'integratedsearch/v1/t/status',

                           [{'exc': requests.exceptions.ConnectTimeout},
                            {'status_code': 500},
                            {'json': {'progress': 100, 'status': 'complete'},
                             'status_code': 200}])

            res = cdiquerygenestotermcmd. \
                wait_for_result('http://foo',
                                't', user_agent='hi',
                                polling_interval=0.001)
            self.assertEqual(True, res)

    def test_wait_for_result_retry_exceeded(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'http://foo/'
                                  'integratedsearch/v1/t/status',
                           [{'json': {'progress': 50, 'status': ''},
                             'status_code': 200},
                            {'status_code': 500},
                            {'json': {'progress': 100, 'status': 'complete'},
                             'status_code': 200}])

            res = cdiquerygenestotermcmd. \
                wait_for_result('http://foo',
                                't', user_agent='hi',
                                polling_interval=0.001,
                                retrycount=2)
            self.assertEqual(False, res)

    def test_get_result_in_mapped_term_json_errors(self):
        # try None
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(None)
        self.assertEqual(None, res)

        # try empty dict
        result = {}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual(None, res)

        # try None sources
        result = {'sources': None}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual(None, res)

        # try empty sources
        result = {'sources': []}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual(None, res)

        # results not in first sources
        result = {'sources': [{'hi': 'there'}]}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual(None, res)

        # results is None
        result = {'sources': [{'results': None}]}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual(None, res)

        # results is empty
        result = {'sources': [{'results': []}]}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual(None, res)

    def test_get_result_in_mapped_term_json_with_colon_success(self):
        result = {'sources': [{'results': [{'description': 'hi: somedescription',
                                            'details': {'PValue': 5},
                                            'url': 'someurl',
                                            'hitGenes': ['1', '2']}]}]}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual('somedescription', res['name'])
        self.assertEqual('hi', res['source'])
        self.assertEqual('someurl', res['description'])
        self.assertEqual(5, res['p_value'])
        self.assertEqual(['1', '2'], res['intersections'])

    def test_get_result_in_mapped_term_json_no_colon_success(self):
        result = {'sources': [{'results': [{'description': 'somedescription',
                                            'details': {'PValue': 5},
                                            'url': 'someurl',
                                            'hitGenes': ['1', '2']}]}]}
        res = cdiquerygenestotermcmd.get_result_in_mapped_term_json(result)
        self.assertEqual('somedescription', res['name'])
        self.assertEqual('NA', res['source'])
        self.assertEqual('someurl', res['description'])
        self.assertEqual(5, res['p_value'])
        self.assertEqual(['1', '2'], res['intersections'])

    def test_successful_run(self):
        temp_dir = tempfile.mkdtemp()
        try:
            inputfile = os.path.join(temp_dir, 'input.txt')
            with open(inputfile, 'w') as f:
                f.write('hi,there\n')
            user_agent = 'cdiquerygenestoterm/' + cdiquerygenestoterm.__version__
            with requests_mock.Mocker() as m:
                qres = {'sources': [{'results': [{'description': 'somedescription',
                                                  'details': {'PValue': 5},
                                                  'url': 'someurl',
                                                  'hitGenes': ['1', '2']}]}]}
                m.get('http://foo/integratedsearch/v1/t?start=0&size=1',
                      json=qres, complete_qs=True)
                m.get('http://foo/integratedsearch/v1/t/status',
                      json={'progress': 100,
                            'status': 'complete'})

                m.post('http://foo/integratedsearch/v1/',
                       request_headers={'Content-Type': 'application/json',
                                        'User-Agent': user_agent},
                       status_code=202, json={'id': 't'})
                myargs = [inputfile, '--url', 'http://foo']
                p = cdiquerygenestotermcmd._parse_arguments('desc',
                                                            myargs)
                res = cdiquerygenestotermcmd.run_iquery(inputfile, p)
                self.assertEqual('somedescription', res['name'])
                self.assertEqual('NA', res['source'])
                self.assertEqual(5, res['p_value'])
                self.assertEqual('someurl', res['description'])
                self.assertEqual(['1', '2'], res['intersections'])

        finally:
            shutil.rmtree(temp_dir)

    def test_request_failed(self):
        temp_dir = tempfile.mkdtemp()
        try:
            inputfile = os.path.join(temp_dir, 'input.txt')
            with open(inputfile, 'w') as f:
                f.write('hi,there\n')
            user_agent = 'cdiquerygenestoterm/' + cdiquerygenestoterm.__version__
            with requests_mock.Mocker() as m:
                m.post('http://foo/integratedsearch/v1/',
                       request_headers={'Content-Type': 'application/json',
                                        'User-Agent': user_agent},
                       status_code=404, json={'id': 't'})
                myargs = [inputfile, '--url', 'http://foo']
                p = cdiquerygenestotermcmd._parse_arguments('desc',
                                                            myargs)
                res = cdiquerygenestotermcmd.run_iquery(inputfile, p)
                self.assertEqual(None, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_main_invalid_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = ['prog', tfile]
            res = cdiquerygenestotermcmd.main(myargs)
            self.assertEqual(2, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_main_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = ['prog', tfile]
            res = cdiquerygenestotermcmd.main(myargs)
            self.assertEqual(0, res)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(unittest.main())
