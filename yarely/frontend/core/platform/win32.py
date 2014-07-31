"""Platform specific methods for the win32 platform"""

import urllib.parse

import win32file

from yarely.frontend.core.platform import PlatformError


def get_available_space_in_bytes(path):
    """Return the number of bytes available in the given path."""
    return win32file.GetDiskFreeSpaceEx(path)[0]


def get_local_path_from_uri(uri):
    """Return a local file path from the specified file URI."""
    # On Windows, urllib.parse.urlparse() doesn't return a path with
    # forward slashes so we put them in before we return the value.
    # Windows also keeps the localhost '/' in at the start of path
    # so we chop this off before the replace operation.
    parse_result = urllib.parse.urlparse(uri)
    if parse_result.scheme != 'file':
        raise PlatformError('URI must have scheme of type file')
    path = parse_result.path.lstrip('/').replace('/', '\\')
    return path


def get_uri_from_local_path(path):
    """Return a file URI for the specified local file."""
    # On Windows, urllib.parse.urlunparse() doesn't do the right thing with
    # forward slashes so we replace these before we start.
    path = path.replace('\\', '/')
    parse_result = urllib.parse.ParseResult(
        scheme='file', netloc='', path=path, params='', query='', fragment=''
    )
    return urllib.parse.urlunparse(parse_result)
