#! /usr/bin/env python

import executor


class Archiver(executor.Executor):

    def archive(self):
        self.logger.info("Archiving")
        self.ds.safe_archive_all()


if __name__ == "__main__":
    archiver = Archiver()
    archiver.archive()
