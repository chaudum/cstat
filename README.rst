=========
crate-top
=========

*A top for Crate*

``ctop`` is ispired by the awesome interactive process monitoring tool `htop`_.
``ctop`` should be a similar tool, but for monitoring `Crate`_ clusters.

.. image:: screenshot.png
   :scale: 100%
   :alt: Screenshot of ctop in action

Installation
=============

Right now, ``ctop`` is only available from `Github`_. Therefore you need to
checkout the repository and run ``pip install`` on the local directory.
A first version should be available from PyPi_ in summer 2016.

::

    git clone https://github.com/chaudum/crate-top.git
    cd crate-top
    python3.4 -m env
    source ./env/bin/activate
    pip install -e .

Usage
=====

After installation the program can be invoked by the following command::


    >>> ctop --help
    usage: CrateTop [-h] [--hosts HOSTS]

    optional arguments:
      -h, --help            show this help message and exit
      --hosts HOSTS, --crate-hosts HOSTS
                            Comma separated list of Crate hosts to connect to.

Hotkeys
=======

- ``1``  ... toggle detail bars for ``CPU``, ``PROC``, ``MEM``, ``HEAP``, ``DISK``
- ``2``  ... toggle detail bars for ``NET I/O``, ``DISK I/O``
- ``f1`` ... enable/disable job logging (this also sets the ``stats.jobs_log``
             cluster setting)

Known Issues
============

- Small terminal sizes will raise CanvasErrors because of content overflow.

Todo
====

- [x] display disk usage
- [x] display disk i/o
- [x] display network i/o
- [x] display node names in detail views
- [ ] use asyncio to perform http requests
- [x] coloring of i/o stats
- [ ] responsive i/o widget


.. _htop: http://hisham.hm/htop/
.. _Crate: https://crate.io
.. _PyPi: https://pypi.python.org/pypi

