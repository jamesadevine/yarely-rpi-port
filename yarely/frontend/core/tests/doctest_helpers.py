import doctest
import sys

SKIP_ON_PY2 = doctest.register_optionflag('SKIP_ON_PY2')
SKIP_ON_PY3 = doctest.register_optionflag('SKIP_ON_PY3')

_skip = None

if sys.version_info.major == 2:
    _skip = SKIP_ON_PY2
elif sys.version_info.major == 3:
    _skip = SKIP_ON_PY3


def PyVersionAwareDocTestSuite(*args, **kwargs):
    """A specialism of doctest.DocTestSuite providing the ability to SKIP
    doctests based on the Python major version.

    Two new doctest option flags are made available:
    SKIP_ON_PY2 and SKIP_ON_PY3.

    These cause the SKIP option flag to be set if the Python version matches.

    >>> print("Never")      # doctest: +SKIP
    Never
    >>> print("Not Py2")    # doctest: +SKIP_ON_PY2
    Not Py2
    >>> print("Not Py3")    # doctest: +SKIP_ON_PY3
    Not Py3


    If a doctest example has the 'SKIP_ON_PY2' option flag set and the test
    is launched under Python 2.x, the SKIP option flag will also be set.
    """
    orig_setUp = kwargs.get('setUp')

    def py_version_skip_setUp(test):
        for example in test.examples:
            if _skip in example.options:
                example.options[doctest.SKIP] = True

        if orig_setUp is not None:
            orig_setUp(test)

    kwargs['setUp'] = py_version_skip_setUp
    return doctest.DocTestSuite(*args, **kwargs)
