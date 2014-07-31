IMPORTANT
=========

You really do need to select the egg from the correct directory, even though the
files have similar names.

On 10.6, 10.7 & 10.8 we use PyObjC 2.3 against Python 3.2.

Install with:

(10.6, 10.7 & 10.8)

$ sudo python3.2 -m easy_install --no-deps ./pyobjc_core-2.3.egg
$ sudo python3.2 -m easy_install --no-deps ./pyobjc_framework_Cocoa-2.3.egg
$ sudo python3.2 -m easy_install --no-deps ./pyobjc_framework_WebKit-2.3.egg
$ sudo python3.2 -m easy_install --no-deps ./pyobjc_framework_Quartz-2.3.egg
$ sudo python3.2 -m easy_install --no-deps ./pyobjc_framework_QTKit-2.3.egg

Confirm success with:             
$ python3.2 -c "from Foundation import NSString; foo=NSString.alloc().initWithString_(\"Foo\"); print(type(foo))"

<class 'objc.pyobjc_unicode'>


Super Secret Build Notes
========================

You don't need to follow these steps unless you want fresh eggs.
Fried or boiled?


PyObjC 2.3
----------

(10.6)
    Pull the pre-built eggs for:
    * pyobjc-core
    * pyobjc-framework-Cocoa
    * pyobjc-framework-WebKit
    * pyobjc-framework-Quartz
    * pyobjc-framework-QTKit
    from pypi.python.org

(10.7 & 10.8)
    sudo python3.2 -m easy_install -b /tmp/pyobjc-core pyobjc_core
    cd /tmp/pyobjc-core/pyobjc-core
    sudo python3.2 setup.py build bdist_egg

    The egg is now in /tmp/pyobjc-core/pyobjc-core/dist/

    sudo python3.2 -m easy_install -b /tmp/pyobjc-framework-Cocoa pyobjc_framework_Cocoa
    cd /tmp/pyobjc-framework-Cocoa/pyobjc-framework-cocoa
    sudo python3.2 setup.py build bdist_egg

    The egg is now in /tmp/pyobjc-framework-Cocoa/pyobjc-framework-Cocoa/dist/

    * Pull the pre-built egg for pyobjc-framework-WebKit

    sudo python3.2 -m easy_install -b /tmp/pyobjc-framework-quartz pyobjc-framework-quartz
    cd /tmp/pyobjc-framework-quartz/pyobjc-framework-quartz
    sudo python3.2 setup.py build bdist_egg

    The egg is now in /tmp/pyobjc-framework-quartz/pyobjc-framework-quartz/dist/

    * Pull the pre-built egg for pyobjc-framework-QTKit
