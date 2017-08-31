#! /usr/bin/env python

import sys

import executor


class Warner(executor.Executor):
    def warn(self, force_warn=False):
        self.logger.info("Warning")
        self.ds.warn_all(force_warn)


if __name__ == "__main__":
    warner = Warner()
    force_warn = False
    if len(sys.argv) == 2 and sys.argv[1] == "force":
        force_warn = True
    warner.warn(force_warn=force_warn)
