# Platform specific methods that are common across POSIX platforms

import os
import os.path
import urllib.parse

from yarely.frontend.core.platform import PlatformError


def get_available_space_in_bytes(path):
    """Return the number of bytes available in the given path."""
    vfs_stats = os.statvfs(path)
    available_space_in_bytes = vfs_stats.f_bavail * vfs_stats.f_frsize
    return available_space_in_bytes


def get_local_path_from_uri(uri):
    """Return a local file path from the specified file URI."""
    parse_result = urllib.parse.urlparse(uri)
    if parse_result.scheme != 'file':
        raise PlatformError('URI must have scheme of type file')
    quoted_path = parse_result.path
    return urllib.parse.unquote(quoted_path)


def get_uri_from_local_path(path):
    """Return a file URI for the specified local file."""
    abs_path = os.path.abspath(path)
    quoted_path = urllib.parse.quote(abs_path)
    parse_result = urllib.parse.ParseResult(scheme='file', netloc='',
        path=quoted_path, params='', query='', fragment='')
    return urllib.parse.urlunparse(parse_result)
