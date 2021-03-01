"""aecgviewer: GUI for reviewing annotated electrocardiograms (aECG) files

This code implements a graphical user interface (GUI) to index and visualize
annotated electrocardiograms stored in XML files following HL7 annotated ECG
(aECG) standard.

See authors, license and disclaimer at the top level directory of this project.

"""


import argparse
import logging
import logging.config
import multiprocessing
import pkg_resources
import sys

from PySide2.QtWidgets import QApplication, QSizePolicy
from aecgviewer.mainwindow import MainWindow

import aecgviewer


def main():
    """ Launches the main aECG viewer window

    This function parses the command line arguments, intializesa logger, and
    launches the main user interface window.

    Command line arguments:

        indexfile (str, optional): Filename of the study index file to load
        logconffile (str, optional): logging configuration file
    """
    # Set start method for multiprocess to spawn for all platforms
    multiprocessing.set_start_method('spawn')

    logging_conf_file = pkg_resources.resource_filename(
        __name__, 'cfg/aecgviewer_aecg_logging.conf')

    options = argparse.ArgumentParser()
    options.add_argument("-i", "--indexfile", type=str,
                         help='Study index file to be loaded')
    options.add_argument("-l", "--logconffile", type=str,
                         help=f'logging configuration file (default: '
                              f'{logging_conf_file})',
                         default=logging_conf_file)
    args = options.parse_args()

    # Initialize logging
    print(f"Loading logging configuration from: {args.logconffile}")
    logging.config.fileConfig(args.logconffile)
    logger = logging.getLogger("aecgviewer")
    for h in logger.root.handlers:
        if isinstance(h, logging.FileHandler):
            print(f"Logging to {h.baseFilename} file with a "
                  f"{type(h).__name__}")
    logger.info("aECG viewer version %s loaded",
                aecgviewer.__version__)

    app = QApplication(sys.argv)
    window = MainWindow(args.indexfile)
    sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
    sizePolicy.setHeightForWidth(False)
    window.setSizePolicy(sizePolicy)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
