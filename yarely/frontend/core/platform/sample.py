"""Platform specific methods for the SAMPLE platform"""


def get_available_space_in_bytes(path):
    """Return the number of bytes available in the given path."""
    raise NotImplementedError()


def get_local_path_from_uri(uri):
    """Return a local file path from the specified file URI."""
    raise NotImplementedError()


def get_uri_from_local_path(path):
    """Return a file URI for the specified local file."""
    raise NotImplementedError()
