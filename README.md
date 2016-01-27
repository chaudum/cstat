# crate-top

**A top for Crate.IO**

**ctop** is ispired by the awesome interactive process monitoring tool [htop](http://hisham.hm/htop/). **ctop** should be a similar tool, but for monitoring a [Crate.IO](https://crate.io) cluster.

![Screenshot of ctop in action](screenshot.png)

## Usage

```
git clone
cd crate-top
python3.4 bootstrap.py
bin/buildout -N
```

```console
$ bin/ctop --help
usage: CrateTop [-h] [--hosts HOSTS]

optional arguments:
  -h, --help            show this help message and exit
  --hosts HOSTS, --crate-hosts HOSTS
                        Comma separated list of Crate hosts to connect to.
```

## Hotkeys

- `1` ... toggle detail bars for `CPU`, `PROC`, `MEM`, `HEAP`
- `2` ... toggle detail bars for `DISK`
- `f1` ... enable/disable job logging (this also sets the `stats.jobs_log` cluster setting)

## Todo

- [x] display disk usage
- [ ] display disk i/o
- [ ] display network i/o
- [x] display node names in detail views
- [ ] use multiprocessing to perform http requests
