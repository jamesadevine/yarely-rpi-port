import unittest

from yarely.frontend.core.helpers import conversions
from yarely.frontend.core.tests.doctest_helpers import \
        PyVersionAwareDocTestSuite


def load_tests(loader, tests, ignore):
    tests.addTests(PyVersionAwareDocTestSuite(conversions))
    return tests


class UnitOfInformationInBytesTestCase(unittest.TestCase):
    def test_suffixless_number(self):
        result = conversions.unit_of_information_in_bytes("1")
        self.assertEqual(result, 1)

    def test_unparsable(self):
        with self.assertRaises(conversions.UnitOfInformationConversionError):
            conversions.unit_of_information_in_bytes("unparsable")

    def test_1KB_value(self):
        result = conversions.unit_of_information_in_bytes("1KB")
        self.assertEqual(result, 1000)

    def test_1KIB_value(self):
        result = conversions.unit_of_information_in_bytes("1KIB")
        self.assertEqual(result, 1024)

    def test_1K_value(self):
        result = conversions.unit_of_information_in_bytes("1K")
        self.assertEqual(result, 1000)

    def test_1KI_value(self):
        result = conversions.unit_of_information_in_bytes("1KI")
        self.assertEqual(result, 1024)

    def test_1kb_value(self):
        result = conversions.unit_of_information_in_bytes("1kb")
        self.assertEqual(result, 1000)

    def test_1kib_value(self):
        result = conversions.unit_of_information_in_bytes("1kib")
        self.assertEqual(result, 1024)

    def test_1k_value(self):
        result = conversions.unit_of_information_in_bytes("1k")
        self.assertEqual(result, 1000)

    def test_1ki_value(self):
        result = conversions.unit_of_information_in_bytes("1ki")
        self.assertEqual(result, 1024)

    def test_in_str_spacing(self):
        result = conversions.unit_of_information_in_bytes("1 KB")
        self.assertEqual(result, 1000)

    def test_1TB_value(self):
        byte = 1
        kb = 1000 * byte
        mb = 1000 * kb
        gb = 1000 * mb
        tb = 1000 * gb

        result = conversions.unit_of_information_in_bytes("1TB")
        self.assertEqual(result, tb)

    def test_1TIB_value(self):
        byte = 1
        kib = 1024 * byte
        mib = 1024 * kib
        gib = 1024 * mib
        tib = 1024 * gib

        result = conversions.unit_of_information_in_bytes("1TIB")
        self.assertEqual(result, tib)


class TimeIntervalInSecondsTestCase(unittest.TestCase):
    def test_suffixless_number(self):
        result = conversions.time_interval_in_seconds("1")
        self.assertEqual(result, 1)

    def test_unparsable(self):
        with self.assertRaises(conversions.TimeIntervalConversionError):
            conversions.time_interval_in_seconds("unparsable")

    def test_1minute_value(self):
        result = conversions.time_interval_in_seconds("1minute")
        self.assertEqual(result, 60)

    def test_1minutes_value(self):
        result = conversions.time_interval_in_seconds("1minutes")
        self.assertEqual(result, 60)

    def test_1min_value(self):
        result = conversions.time_interval_in_seconds("1min")
        self.assertEqual(result, 60)

    def test_1mins_value(self):
        result = conversions.time_interval_in_seconds("1mins")
        self.assertEqual(result, 60)

    def test_in_str_spacing(self):
        result = conversions.time_interval_in_seconds("60 seconds")
        self.assertEqual(result, 60)

    def test_2week_value(self):
        second = 1
        minute = 60 * second
        hour = 60 * minute
        day = 24 * hour
        week = 7 * day

        result = conversions.time_interval_in_seconds("2 week")
        self.assertEqual(result, 2 * week)
