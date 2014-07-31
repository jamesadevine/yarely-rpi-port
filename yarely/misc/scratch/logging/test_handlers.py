#!/usr/bin/env python3.2 -i
import logging
import logging.config

logging.config.fileConfig("yarely/misc/scratch/logging/logging.cfg")

foo=logging.getLogger("foo")
yarely=logging.getLogger("yarely")
yarelyfoo=logging.getLogger("yarely.foo")

foo.warn("Foo")
yarely.warn("Yarely")
yarelyfoo.warn("YarelyFoo")
