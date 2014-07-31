import traceback

from yarely.frontend.core.config import YarelyConfig

conf = YarelyConfig("yarely.cfg")

def demonstrate(section, option):
    print("-> Trying section '{section}' option '{option}'".format(
        section=section, option=option))

    print()
    print("conf.getcolour")
    try:
        result = conf.getcolour(section, option)
        print("Got result {result}".format(result=result))

    except:
        traceback.print_exc(limit=0,chain=False)


    print()
    print("conf.getint")

    try:
        result = conf.getint(section, option)
        print("Got result {result}".format(result=result))

    except:
        traceback.print_exc(limit=0,chain=False)

    print()


print()
demonstrate("NoSection", "NoOption")
demonstrate("Section", "NoOption")
demonstrate("Section", "Option")
