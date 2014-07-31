import logging

from yarely.frontend.core.helpers.base_classes import HandlerStub, Manager, \
    Struct
from yarely.frontend.core.helpers.base_classes.manager import \
        check_handler_token

LOG_FORMAT = "%(asctime)s %(module)s:%(lineno)d %(levelname)s %(message)s"

stubs = Struct()

MANAGER_PORT = 55341  # random guess that this isn't in use


class HandlerHarness(Manager):
    def _init_handlers(self):
        pass


def main(harness_cls):
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
    harness = harness_cls(MANAGER_PORT, description="Handler test harness")
    harness.start()
    print("harness = {harness!r}".format(harness=harness))
    print("Hints:")
    print("stub=stubs.<PICK_ONE>")
    print("spid=harness.start_handler(stub)")
    print("harness.stop_handler(spid)")
    print("list_stubs()")
    print("")
    list_stubs()
    return harness


def list_stubs():
    print("Available stubs:")

    stub_list = []
    for attr_name in dir(stubs):
        if not attr_name.startswith("_"):
            stub_list.append("stubs.{name}".format(name=attr_name))

    print("{stubs}".format(stubs=stub_list))
