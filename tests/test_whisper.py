#!/usr/bin/env python
import unittest
from unittest import TestCase
from whisper import getUnitString, parseRetentionDef, create, info, aggregate
from whisper import update, fetch
from whisper import validateArchiveList
from whisper import InvalidConfiguration
from whisper import InvalidAggregationMethod
from whisper import CorruptWhisperFile
from whisper import TimestampNotCovered
import whisper

import time
import random
import os

class UnitStringTest(TestCase):
    """ Basic test for getUnitString(s)"""
    def setUp(self):
        pass

    def test_unitstring_valid_full(self):
        for unit in ['seconds', 'minutes', 'hours', 'days', 'weeks', 'years']:
            self.assertEqual(getUnitString(unit), unit)

    def test_unitstring_valid_l1(self):
        for unit in ['seconds', 'minutes', 'hours', 'days', 'weeks', 'years']:
            test_string = "".join(unit.split()[0:1])
            self.assertEqual(getUnitString(test_string), unit)

    def test_unitstring_valid_l2(self):
        for unit in ['seconds', 'minutes', 'hours', 'days', 'weeks', 'years']:
            test_string = "".join(unit.split()[0:2])
            self.assertEqual(getUnitString(test_string), unit)

    def test_unitstring_valid_l3(self):
        for unit in ['seconds', 'minutes', 'hours', 'days', 'weeks', 'years']:
            test_string = "".join(unit.split()[0:3])
            self.assertEqual(getUnitString(test_string), unit)

    def test_unitstring_valid_l4(self):
        for unit in ['seconds', 'minutes', 'hours', 'days', 'weeks', 'years']:
            test_string = "".join(unit.split()[0:4])
            self.assertEqual(getUnitString(test_string), unit)


    def test_unitstring_invalid(self):
        with self.assertRaises(ValueError):
            getUnitString("BAD")

class parseRetentionDefTest(TestCase):
    """ Make sure we can parse the retentionDef files """
    def test_bad_precision(self):
        with self.assertRaises(ValueError):
            parseRetentionDef("x:400")
        with self.assertRaises(ValueError):
            parseRetentionDef("BAD")
        with self.assertRaises(ValueError):
            parseRetentionDef("400:")
        with self.assertRaises(ValueError):
            parseRetentionDef("1:1 x")
        with self.assertRaises(ValueError):
            parseRetentionDef("1 :1x")

        with self.assertRaises(ValueError):
            parseRetentionDef("1:1x")

    def test_basic_good_preceision(self):
        (preceision, points) = parseRetentionDef("1:1")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 1)

    def test_second_preceision(self):
        (preceision, points) = parseRetentionDef("1:1s")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 1)

    def test_minute_preceision(self):
        (preceision, points) = parseRetentionDef("1:1m")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 60)

    def test_hour_preceision(self):
        (preceision, points) = parseRetentionDef("1:1h")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 3600)

    def test_days_preceision(self):
        (preceision, points) = parseRetentionDef("1:1d")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 86400)

    def test_weeks_preceision(self):
        (preceision, points) = parseRetentionDef("1:1w")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 604800)

    def test_years_preceision(self):
        (preceision, points) = parseRetentionDef("1:1y")
        self.assertEqual(preceision, 1)
        self.assertEqual(points, 31536000)

class createWhisperTest(TestCase):
    """ Basic test for create Whispers"""
    def setUp(self):
        "Setup a path in /tmp to create test whisper files"
        self.test_path = "/tmp/test_whisper_file.%s" % random.randint(0, 1000)

    def tearDown(self):
        "If a temp file was create delete it, so we can create it again"
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)

    def test_num_args(self):
        with self.assertRaises(TypeError):
            create()
        with self.assertRaises(TypeError):
            create("")

    def test_invalidConfiguration(self):
        with self.assertRaises(InvalidConfiguration):
            create("", "")
        with self.assertRaises(InvalidConfiguration):
            create(None, [])

    def test_withoutarchive_info(self):
        with self.assertRaises(InvalidConfiguration):
            create(self.test_path, [])

    def test_validate_configuraiton_no_file(self):
        with self.assertRaises(TypeError):
            create(None, [(1, 1)])
        with self.assertRaises(TypeError):
            create(None, [(1, 10)])
        with self.assertRaises(TypeError):
            create(None, [(1, 10), (10, 100)])

    def test_basic_create_success(self):
        create(self.test_path, [(1, 1)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        size = os.stat(self.test_path).st_size
        self.assertEqual(size, 40)

    def test_create_different_sizes_consistance(self):
        for count in range(1, 100):
            expected_size = 28 + (count * 12)
            create(self.test_path, [(1, count)])
            created_file = os.path.exists(self.test_path)
            self.assertEqual(created_file, True)
            size = os.stat(self.test_path).st_size
            self.assertEqual(size, expected_size)
            os.unlink(self.test_path)

    def test_create_fileexists(self):
        create(self.test_path, [(1, 1)])
        with self.assertRaises(InvalidConfiguration):
            create(self.test_path, [(1, 1)])

    def test_xfilesfactor(self):
        create(self.test_path, [(1, 1)])
        data = info(self.test_path)
        self.assertEqual(data['xFilesFactor'], 0.5)
        os.unlink(self.test_path)
        
        create(self.test_path, [(1, 1)], xFilesFactor=5.0)
        data = info(self.test_path)
        self.assertEqual(data['xFilesFactor'], 5.0)

    def test_bad_xfilesfactor(self):
        create(self.test_path, [(1, 1)], xFilesFactor=True)
        data = info(self.test_path)
        self.assertEqual(data['xFilesFactor'], 1)
        os.unlink(self.test_path)

        with self.assertRaises(ValueError):
            create(self.test_path, [(1, 1)], xFilesFactor="BAD")

        os.unlink(self.test_path)
        with self.assertRaises(TypeError):
            create(self.test_path, [(1, 1)], xFilesFactor=[])

        os.unlink(self.test_path)
        with self.assertRaises(TypeError):
            create(self.test_path, [(1, 1)], xFilesFactor={})

    def test_sparse(self):
        create(self.test_path, [(1, 100)], sparse=False, useFallocate=False)
        size = os.stat(self.test_path).st_size
        self.assertEqual(size, 1228)
        os.unlink(self.test_path)

        create(self.test_path, [(1, 100)], sparse=True, useFallocate=False)
        size = os.stat(self.test_path).st_size
        self.assertEqual(size, 1228)
        os.unlink(self.test_path)

        create(self.test_path, [(1, 100)], sparse=True, useFallocate=True)
        size = os.stat(self.test_path).st_size
        self.assertEqual(size, 1228)
        os.unlink(self.test_path)



    def test_aggregationmethod(self):
        create(self.test_path, [(1, 1)])
        data = info(self.test_path)
        self.assertEqual(data['xFilesFactor'], 0.5)
        os.unlink(self.test_path)
        
        create(self.test_path, [(1, 1)], xFilesFactor=5.0)
        data = info(self.test_path)
        self.assertEqual(data['xFilesFactor'], 5.0)
        


class validateArchiveListTest(TestCase):
    def test_args(self):
        with self.assertRaises(TypeError):
            validateArchiveList()
        with self.assertRaises(TypeError):
            validateArchiveList("", "")
        with self.assertRaises(InvalidConfiguration):
            validateArchiveList("")

    def test_duplicate_precision(self):
        validateArchiveList([(1, 1)])
        validateArchiveList([(2, 2), (4, 4)])

        with self.assertRaises(InvalidConfiguration):
            validateArchiveList([(1, 1), (1, 1)])

    def test_lower_to_high_precision(self):
        validateArchiveList([(1, 1)])
        validateArchiveList([(2, 2), (4, 4)])

        with self.assertRaises(InvalidConfiguration):
            validateArchiveList([(1, 1), (1, 10)])

    def test_points_to_consolidate(self):
        with self.assertRaises(InvalidConfiguration):
            validateArchiveList([(3, 10), (2, 10)])

class validateInfoTest(TestCase):
    def setUp(self):
        "Setup a path in /tmp to create test whisper files"
        self.test_path = "/tmp/test_whisper_file.%s" % random.randint(0, 1000)

    def tearDown(self):
        "If a temp file was create delete it, so we can create it again"
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)

    def test_args(self):
        with self.assertRaises(TypeError):
            validateArchiveList()
        with self.assertRaises(TypeError):
            validateArchiveList("", "")

    def test_read_info(self):
        create(self.test_path, [(1, 1)])
        data = info(self.test_path)
        self.assertEqual(type(data), type({}))

    def test_info_content(self):
        create(self.test_path, [(1, 1)])
        expected_keys = ['maxRetention', 'xFilesFactor', 'aggregationMethod',
                         'archives']
        expected_archive_keys = ['retention', 'secondsPerPoint', 'points',
                                 'size', 'offset']

        data = info(self.test_path)
        for key in expected_keys:
            self.assertEqual(key in data.keys(), True)

        for key in expected_archive_keys:
            self.assertEqual(key in data['archives'][0].keys(), True)

    def test_missing_file(self):
        with self.assertRaises(IOError):
            info(self.test_path)

class aggregate_test(TestCase):
    def test_args(self):
        with self.assertRaises(TypeError):
            aggregate()
        with self.assertRaises(TypeError):
            aggregate("")
        with self.assertRaises(TypeError):
            aggregate("","","")
        for agg_type in whisper.aggregationTypeToMethod.values():
            aggregate(agg_type, [1])
        with self.assertRaises(InvalidAggregationMethod):
            aggregate("BAD", [1,2])

    def test_agg_avgerage(self):
        known_values = range(5)
        total = aggregate('average', known_values)
        self.assertEqual(total, 2)

        known_values = range(25)
        total = aggregate('average', known_values)
        self.assertEqual(total, 12)

    def test_agg_sum(self):
        known_values = range(5)
        total = aggregate('sum', known_values)
        self.assertEqual(total, 10)

        known_values = range(25)
        total = aggregate('sum', known_values)
        self.assertEqual(total, 300)

    def test_agg_last(self):
        known_values = range(5)
        total = aggregate('last', known_values)
        self.assertEqual(total, 4)

        known_values = range(25)
        total = aggregate('last', known_values)
        self.assertEqual(total, 24)

    def test_agg_max(self):
        known_values = range(5)
        total = aggregate('max', known_values)
        self.assertEqual(total, 4)

        known_values = range(25)
        total = aggregate('max', known_values)
        self.assertEqual(total, 24)

    def test_agg_min(self):
        known_values = range(5)
        total = aggregate('min', known_values)
        self.assertEqual(total, 0)

        known_values = range(25)
        total = aggregate('min', known_values)
        self.assertEqual(total, 0)

class CorruptWhisperFileDetection(TestCase):
    def setUp(self):
        "Setup a path in /tmp to create test whisper files"
        self.test_path = "/tmp/test_whisper_file.%s" % random.randint(0, 1000)

    def tearDown(self):
        "If a temp file was create delete it, so we can create it again"
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)

    def test_badheader(self):
        create(self.test_path, [(1, 1)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        fh = open(self.test_path, 'w')
        fh.seek(0)
        fh.write('BAD')
        fh.close()
        with self.assertRaises(CorruptWhisperFile):
            info(self.test_path)

        os.unlink(self.test_path)

        create(self.test_path, [(1, 1)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        fh = open(self.test_path, 'w')
        fh.seek(4)
        fh.write('BAD')
        fh.close()
        with self.assertRaises(CorruptWhisperFile):
            info(self.test_path)

    def test_destory_archive(self):
        create(self.test_path, [(1, 1)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        fh = open(self.test_path, 'w')
        fh.seek(32)
        fh.write('BAD')
        fh.close()
        # Read headerinfo
        _info = info(self.test_path)
        self.assertEqual(len(_info['archives']), 0)

        with self.assertRaises(CorruptWhisperFile):
            info(self.test_path)

    def test_destory_multi_archive(self):
        create(self.test_path, [(1, 10), (10,100)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        fh = open(self.test_path, 'w')
        fh.seek(40)
        fh.write('BAD')
        fh.close()
        # Read headerinfo
        _info = info(self.test_path)
        self.assertEqual(len(_info['archives']), 0)

        with self.assertRaises(CorruptWhisperFile):
            info(self.test_path)

    def test_destory_archive_then_update(self):

        create(self.test_path, [(1, 10)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        _info = info(self.test_path)
        self.assertEqual(len(_info['archives']), 1)
        update(self.test_path, 1)
        os.unlink(self.test_path)


        create(self.test_path, [(1, 10)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)
        fh = open(self.test_path, 'w')
        fh.seek(40)
        fh.write('BAD')
        fh.close()
        _info = info(self.test_path)
        self.assertEqual(_info['archives'], [])
        with self.assertRaises(TimestampNotCovered):
            update(self.test_path, 1)

class StoreAndRetive(TestCase):
    def create_archive(self, points, perceision):
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)
        create(self.test_path, [(points, perceision)])
        created_file = os.path.exists(self.test_path)
        self.assertEqual(created_file, True)

    def setUp(self):
        self.test_path = "/tmp/test_whisper_file.%s" % random.randint(0, 1000)

    def tearDown(self):
        "If a temp file was create delete it, so we can create it again"
        if os.path.exists(self.test_path):
            os.unlink(self.test_path)

    def test_basic_singlepoint_store(self):
        self.create_archive(1,1)
        for test_run_count in range(0,20):
            random_float = random.randint(0, 100000) * .1
            update(self.test_path, random_float)
            (timeinfo, valuelist) = fetch(self.test_path, 0)
            self.assertEqual(valuelist, [random_float])

    def test_basic_multipoint_store_with_sleep(self):
        return
        self.create_archive(1,5)
        random_float_list = []
        for test_run_count in range(0,4):
            random_float = random.randint(0, 100000) * .1
            update(self.test_path, random_float)
            random_float_list.append(random_float)
            time.sleep(1)
        random_float = random.randint(0, 100000) * .1
        update(self.test_path, random_float)
        random_float_list.append(random_float)

        (timeinfo, valuelist) = fetch(self.test_path, 0)
        self.assertEqual(valuelist, random_float_list)

    def test_basic_multipoint_store_with_mock_ts(self):
        test_points = 50
        self.create_archive(1, test_points)
        untilTime = int(time.time())
        fromTime = untilTime - test_points
        random_float_list = []
        for mock_ts in range(fromTime, untilTime):
            mock_ts += 1
            random_float = random.randint(0, 100000) * .1
            update(path=self.test_path, value=random_float, timestamp=mock_ts)
            random_float_list.append(random_float)

        (timeinfo, valuelist) = fetch(self.test_path, fromTime, untilTime)
        self.assertEqual(valuelist, random_float_list)

        (info_from, info_until, info_step) = timeinfo
        self.assertEqual(info_from, fromTime + 1)
        self.assertEqual(info_until, untilTime + 1)
        self.assertEqual(info_step, 1)


if __name__ == '__main__':
    unittest.main()
