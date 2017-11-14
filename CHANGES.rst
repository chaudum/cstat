===================
Changelog for cstat
===================

Unreleased
==========

0.2.0
=====

Released on **2017/11/14** with the following changes:

- Implemented asynchronous database access using aiopg_ which uses the Postgres
  Wire Protocol instead of the official CrateDB Python client which uses the
  HTTP protocol.

- Added ``median``, ``percentile 95``, and ``percentile 99`` to query stats
  table view.

- Added ``--user``/``--db-user`` command line argument to support user
  authentication for clusters which run CrateDB 2.0 or greater.

- Changed the toggle key for enabling/disabling query stats from ``F1`` to
  ``F3``, because in the Terminator_ terminal the ``F1`` key is reserved for
  "help".

- Pre-calculate used and idle CPU in SQL statement to avoid rounding issues
  that can cause an display overflow in CPU widget.

.. _aiopg: https://github.com/aio-libs/aiopg
.. _Terminator: https://launchpad.net/terminator

0.1.0
=====

Initial release on **2017/03/30**:
