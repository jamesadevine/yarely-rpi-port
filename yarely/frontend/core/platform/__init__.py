import importlib as _importlib
import sys as _sys


class PlatformError(Exception):
    """Base class for platform errors"""
    pass


# Map the platform (sys.platform - key), to the module name that provides
# the concrete implementation (value).
#
# Linux has multiple entries because:
#   python < 3.2 reports 'linux2' or 'linux3'
#   python = 3.2 reports 'linux2'
#   python > 3.2 reports 'linux'
_PLATFORM_MODULE_MAP = {
        "darwin": "darwin",

        "linux": "linux",
        "linux2": "linux",
        "linux3": "linux",

        "win32": "win32"
}

_UNSUPPORTED_PLATFORM_TEMPLATE = "Platform '{platform}' is not supported"
_MODULE_PATH_TEMPLATE = "yarely.frontend.core.platform.{module}"

if _sys.platform not in _PLATFORM_MODULE_MAP:
    _msg = _UNSUPPORTED_PLATFORM_TEMPLATE.format(platform=_sys.platform)
    raise NotImplementedError(_msg)


_module = _PLATFORM_MODULE_MAP[_sys.platform]
_module_path = _MODULE_PATH_TEMPLATE.format(module=_module)

_concrete = _importlib.import_module(_module_path)

# Actual implementation follows(!)
# By design we provide the docstring here so it doesn't need to be duplicated
# for each supported OS


def get_available_space_in_bytes(path):
    """Return the number of bytes available in the given path.

    The meaning of 'available' varies between host platforms but the
    intention is to return the writable space available to this process
    (i.e. implentations try to take user quotas or filesystem restrictions
    into account).

    The space is not reserved so this value can only be used as a
    hint - it is not a guarantee that the space will be available for
    consumption at a later point.

    Example:

      >>> get_available_space_in_bytes("/tmp") # doctest: +SKIP
      1443432565
      >>> get_available_space_in_bytes("c:\\") # doctest: +SKIP
      1435425335

    """
    return _concrete.get_available_space_in_bytes(path=path)


def get_local_path_from_uri(uri):
    """Return a local file path from the specified file URI.

       Example:

         >>> get_local_path_from_uri('file:///etc/fstab') # doctest: +SKIP
         '/etc/fstab'
         >>> path = 'file:///c:/WINDOWS/clock.avi'
         >>> get_local_path_from_uri(path)                # doctest: +SKIP
         'c:\\WINDOWS\\clock.avi'

    """
    return _concrete.get_local_path_from_uri(uri=uri)


def get_uri_from_local_path(path):
    """Return a file URI for the specified local file.

       Example:

         >>> get_uri_from_local_path('/etc/fstab')             # doctest: +SKIP
         'file:///etc/fstab'
         >>> get_uri_from_local_path('c:\\WINDOWS\\clock.avi') # doctest: +SKIP
         'file:///c:/WINDOWS/clock.avi'

    """
    return _concrete.get_uri_from_local_path(path=path)
