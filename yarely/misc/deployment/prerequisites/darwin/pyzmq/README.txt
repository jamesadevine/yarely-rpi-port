IMPORTANT
=========

You really do need to select the egg from the correct directory, even though the
files have similar names.

Install with:

$ sudo python3.2 -m easy_install --no-deps ./pyzmq-2.1.10.egg

Confirm success with:

$ python3.2 -c "import zmq; print(zmq.zmq_version())"
2.1.10



Super Secret Build Notes
========================

You don't need to follow these steps unless you want fresh eggs.
Poached or scrambled?


Build ZeroMQ
------------

Step 1:

  If you are building for a 32-bit Python (10.3-10.6 inclusive), use this:

    export CFLAGS="-arch i386 -m32"
    export CXXFLAGS="$CFLAGS"

Step 2:

  To pick the version of ZeroMQ to download and build, use this:

    ZMQ_VERSION="2.1.10"

Step 3:

mkdir /tmp/zeromq
cd /tmp/zeromq
curl -O http://download.zeromq.org/zeromq-$ZMQ_VERSION.tar.gz
tar -zxf zeromq-$ZMQ_VERSION.tar.gz
cd zeromq-$ZMQ_VERSION
./configure --prefix=/tmp/zeromq/build
make
make install


Build PyZMQ
-----------

Step 1:

  If you are building for a 32-bit Python (10.3-10.6 inclusive), use this:

    export ARCHFLAGS="-arch i386"

  OR: If you are building for a 64-bit Python (10.6-10.8 inclusive), you may
  need this magic:

    sudo ln -s llvm-gcc-4.2 /usr/bin/gcc-4.2

Step 2:

  To pick the version of PyZMQ to download and build, use this:

    PYZMQ_VERSION="2.1.10"

Step 3:

unset CFLAGS
unset CXXFLAGS
mkdir /tmp/pyzmq
cd /tmp/pyzmq
curl -kLO https://github.com/downloads/zeromq/pyzmq/pyzmq-$PYZMQ_VERSION.tar.gz
tar -zxf pyzmq-$PYZMQ_VERSION.tar.gz
cd pyzmq-$PYZMQ_VERSION
export DYLD_LIBRARY_PATH="/tmp/zeromq/build/lib"
python3.2 setup.py configure --zmq=/tmp/zeromq/build
python3.2 setupegg.py build bdist --format=egg


The egg is now in /tmp/pyzmq/pyzmq-$PYZMQ_VERSION/dist/
