import sys
import tempfile
import unittest
import urllib.parse

from yarely.frontend.core import platform
from yarely.frontend.core.tests.doctest_helpers import \
        PyVersionAwareDocTestSuite


def load_tests(loader, tests, ignore):
    tests.addTests(PyVersionAwareDocTestSuite(platform))
    return tests


class GetAvailableSpaceInBytesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._path = tempfile.gettempdir()

    def setUp(self):
        self._result = platform.get_available_space_in_bytes(self._path)

    def test_numerical_result(self):
        # Python 2 might give an int or a long.
        # We use eval() to prevent pyflakes from tripping out on the missing
        # long type.
        if sys.version_info.major == 2:
            acceptable_types_str = "(int, long)"
        else:
            acceptable_types_str = "(int,)"
        acceptable_types = eval(acceptable_types_str)

        self.assertIsInstance(self._result, acceptable_types)

    def test_positive_result(self):
        self.assertGreaterEqual(self._result, 0)


class URILocalPathConversionTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._path = tempfile.gettempdir()

    def setUp(self):
        self._result = platform.get_uri_from_local_path(self._path)

    def test_geturi_string_result(self):
        self.assertIsInstance(self._result, str)

    def test_geturi_reverse_result(self):
        self.assertEqual(
            self._path, platform.get_local_path_from_uri(self._result)
        )

    def test_getlocalpath_raises(self):
        erroneous_result = urllib.parse.ParseResult(scheme='http', netloc='',
            path=self._path, params='', query='', fragment='')
        parsed_erroneous = urllib.parse.urlunparse(erroneous_result)
        with self.assertRaises(platform.PlatformError):
            platform.get_local_path_from_uri(parsed_erroneous)
