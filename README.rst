=====
cstat
=====

*A visual stat tool for Crate clusters*

... formerly known as ``ctop``.

``cstat`` is ispired by the awesome interactive process monitoring tool `htop`_.
``cstat`` should be a similar tool to `iostat`_, but for monitoring `Crate`_
clusters.

.. image:: screenshot.png
   :scale: 100%
   :alt: Screenshot of cstat in action

Installation
=============

Right now, ``stat`` is only available from `Github`_. Therefore you need to
checkout the repository and run ``pip install`` on the local directory.
A first version should be available from PyPi_ in summer 2016.

::

    git clone https://github.com/chaudum/crate-top.git cstat
    cd cstat
    python3.4 -m venv env
    source ./env/bin/activate
    pip install -e .

Usage
=====

After installation the program can be invoked by the following command::

    >>> cstat --help
    usage: cstat [-h] [--hosts HOST [HOST ...]] [--interval INTERVAL] [--version]

    A visual stat tool for Crate clusters

    optional arguments:
      -h, --help            show this help message and exit
      --hosts HOST [HOST ...], --crate-hosts HOST [HOST ...]
                            one or more Crate hosts to connect to
      --interval INTERVAL, --refresh-interval INTERVAL
                            amount of time in seconds between each update
      --version             show program's version number and exit

Hotkeys
=======

* ``0``  .. toggle cluster info
* ``1``  .. show utilization for CPU, process, memory, heap and disk
* ``2``  .. show I/O statistics for network and disk
* ``3``  .. show aggregated query duration based on `jobs_log`_
* ``x``  .. toggle nodes/aggregation view
* ``f1`` .. enable/disable job logging (this also sets the ``stats.jobs_log``
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
.. _iostat: http://linux.die.net/man/1/iostat
.. _Crate: https://crate.io
.. _PyPi: https://pypi.python.org/pypi
.. _Github: https://github.com/chaudum/crate-top
.. _jobs_log: https://crate.io/docs/reference/en/latest/configuration.html#collecting-stats
