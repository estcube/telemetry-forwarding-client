import logging
from ax_listener import AXFrame


class FileLogger():

    def __init__(self, logfile):
        self._logger = logging.getLogger(__name__)
        self.file_logger = logging.FileHandler(logfile)

    """ Log received package to a .log file"""

    def log_ax_frame(self, frame: AXFrame):
        log = "Timestamp: {}; DST: {}; SRC: {}; Control field: {}; Info field: {};".format(frame.recv_time, frame.dest,
                                                                                           frame.source, frame.ctrl,
                                                                                           frame.info.hex())
        self.file_logger.handle(self._logger.makeRecord(None, logging.DEBUG, None, None, log, None, None))
