class Struct:
    """A base-class for C-style structs -- it's just a dictionary
    with class-style attribute access.

    """
    def __init__(self, **kwargs):
        # We could do this in a single line:
        #     self.__dict__.update(**kwargs)
        # BUT we don't because doing it this way allows subclasses to
        # override __setattr__().
        for key, value in kwargs.items():
            self.__setattr__(key, value)
