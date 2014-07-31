from yarely.frontend.core.helpers import colour
from yarely.frontend.core.tests.doctest_helpers import \
        PyVersionAwareDocTestSuite


def load_tests(loader, tests, ignore):
    tests.addTests(PyVersionAwareDocTestSuite(colour))
    return tests
