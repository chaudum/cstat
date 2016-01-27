# crate-top

**A top for Crate.IO**

**ctop** is ispired by the awesome interactive process monitoring tool [htop](http://hisham.hm/htop/). **ctop** should be a similar tool, but for monitoring a [Crate.IO](https://crate.io) cluster.

![Screenshot of ctop in action](screenshot.png)

## Hotkeys

* `[1]` ... toggle detail bars for `CPU`, `PROC`, `MEM`, `HEAP`
* `[2]` ... toggle detail bars for `DISK`
* `[f1]` ... enable/disable job logging (this also sets the `stats.jobs_log` cluster setting)

## What I want to do

[x] display disk usage
[ ] display disk i/o
[ ] display network i/o
[x] display node names in detail views
