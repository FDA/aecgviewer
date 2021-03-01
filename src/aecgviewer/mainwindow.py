"""This submodule implements the main windows of the GUI.
See authors, license and disclaimer at the top level directory of this project.
"""


import logging
import os
import pandas as pd
import pkg_resources

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QMainWindow, QFileDialog,
                               QProgressDialog,
                               QAction, QSizePolicy,
                               QMessageBox, QLabel)
from PySide2.QtGui import QKeySequence, QIcon

from aecgviewer.navigationwidget import NavigationWidget

import aecgviewer
import aecg
import aecg.tools.indexer


class MainWindow(QMainWindow):
    def __init__(self, index_filename):
        QMainWindow.__init__(self)

        # Initialize logging
        self.logger = logging.getLogger(__name__)

        self.setIcon()

        self.study_index_dir = os.getcwd()
        if index_filename:
            self.study_index_dir = os.path.dirname(index_filename)
        self.navwidget = NavigationWidget(index_filename)

        self.setWindowTitle(f"aECG viewer {aecgviewer.__version__} "
                            f"(aecg: {aecg.__version__})")
        self.setCentralWidget(self.navwidget)

        # Menu
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("&File")

        # Open study index
        openindex_action = QAction("&Open study index", self)
        openindex_action.setShortcut(QKeySequence.Open)
        openindex_action.triggered.connect(self.openindex_dialog)

        self.file_menu.addAction(openindex_action)

        # Import and index study
        importstudy_action = QAction("&Load study information", self)
        importstudy_action.setShortcut(QKeySequence.New)
        importstudy_action.triggered.connect(self.importstudy_dialog)

        self.file_menu.addAction(importstudy_action)

        # Save ECG waveform to image or pdf
        saveecg_action = QAction("&Save image", self)
        saveecg_action.setShortcut(QKeySequence.Save)
        saveecg_action.triggered.connect(self.save_aecg_to_image)

        self.file_menu.addAction(saveecg_action)

        # Exit QAction
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)

        self.file_menu.addAction(exit_action)

        # Status Bar
        self.status = self.statusBar()
        self.status_cwd = QLabel()
        self.status_index = QLabel()
        self.status_aecgs = QLabel()
        self.status.addWidget(self.status_cwd)
        self.status.addWidget(self.status_index)
        self.status.addWidget(self.status_aecgs)
        self.navwidget.projectindex_loaded.connect(
            self.new_project_index_loaded)
        self.navwidget.projectindexstats_loaded.connect(
            self.new_project_indexstats_loaded)
        if self.navwidget.project_loaded != "":
            self.new_project_indexstats_loaded()
        self.update_status_bar()

        # Window dimensions
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHeightForWidth(False)
        self.setSizePolicy(sizePolicy)

    def setIcon(self):
        icon_filename = pkg_resources.resource_filename(
            __name__, "resources/app.png")
        icon = QIcon(icon_filename)
        self.setWindowIcon(icon)

    def update_status_bar(self):
        self.status_cwd.setText(f"cwd: {os.getcwd()}")
        project_loaded = self.centralWidget().project_loaded
        if project_loaded != '':
            self.status_index.setText(f"project: {project_loaded}")
            ead = self.centralWidget().tabdisplays.effective_aecgs_dir(
                self.centralWidget(),
                silent=True)
            self.status_aecgs.setText(f"aECGs path: {ead}")
        else:
            self.status_index.setText("project: None")
            self.status_aecgs.setText("aECGs path: N/A")

    def new_project_index_loaded(self):
        project_loaded = self.centralWidget().project_loaded
        tabs = self.centralWidget().tabdisplays
        if project_loaded != '':
            tabs.setCurrentWidget(tabs.studyinfo)
        self.update_status_bar()

    def new_project_indexstats_loaded(self):
        tabs = self.centralWidget().tabdisplays
        progress = QProgressDialog(
            "Parsing statistics from index file...", "Cancel",
            0, 12,
            self)
        progress.setWindowTitle("Loading study index")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumWidth(300)
        progress.setMinimumDuration(0)
        progress.forceShow()
        progress.setValue(0)
        studyStats = self.centralWidget().data_index_stats

        # number of unique subjects in the index
        tabs.aecg_numsubjects.setText(str(studyStats.num_subjects))
        progress.setValue(1)
        # Num of unique aECG waveforms
        tabs.aecg_numaecg.setText(str(studyStats.num_aecgs))
        progress.setValue(2)
        # aECGs per subject
        tabs.aecg_aecgpersubject.setText(
            str(round(studyStats.avg_aecgs_subject, 2)))
        progress.setValue(3)

        # Other stats
        # Subjects with fewer ECGs
        if studyStats.num_subjects > 0:
            tabs.subjects_less_aecgs.setText(
                str(round(
                    studyStats.subjects_less_aecgs/float(
                        studyStats.num_subjects)*100,
                    2)) + " %")
        else:
            tabs.subjects_less_aecgs.setText(" %")
        progress.setValue(4)

        # Subjects with more ECGs
        if studyStats.num_subjects > 0:
            tabs.subjects_more_aecgs.setText(
                str(round(
                    studyStats.subjects_more_aecgs/float(
                        studyStats.num_subjects)*100,
                    2)) + " %")
        else:
            tabs.subjects_more_aecgs.setText(" %")
        progress.setValue(5)

        tabs.aecgs_no_annotations.setText(" %")
        tabs.aecgs_less_qt_in_primary_lead.setText(" %")
        tabs.aecgs_less_qt_in_primary_lead.setText(" %")
        tabs.aecgs_less_qts.setText(" %")
        tabs.aecgs_annotations_multiple_leads.setText(" %")
        tabs.aecgs_annotations_no_primary_lead.setText(" %")
        tabs.aecgs_potentially_digitized.setText(" %")
        if studyStats.num_aecgs > 0:
            tabs.aecgs_no_annotations.setText(
                str(round(
                    studyStats.aecgs_no_annotations /
                    studyStats.num_aecgs * 100, 2)) + " %")
            progress.setValue(6)

            # aECGs without expected number of QTs in primary lead
            tabs.aecgs_less_qt_in_primary_lead.setText(
                str(round(
                    studyStats.aecgs_less_qt_in_primary_lead /
                    studyStats.num_aecgs*100,
                    2)) + " %")
            progress.setValue(7)

            # num aecgs with at least num_qts in primary lead
            tabs.aecgs_less_qts.setText(
                str(round(
                    studyStats.aecgs_less_qts /
                    studyStats.num_aecgs*100, 2)) + " %")
            progress.setValue(8)

            # aECGs annotated in multiple leads
            tabs.aecgs_annotations_multiple_leads.setText(
                str(round(
                    studyStats.aecgs_annotations_multiple_leads /
                    studyStats.num_aecgs*100, 2)) + " %")
            progress.setValue(9)

            # aECGs with annotations not in primary lead
            tabs.aecgs_annotations_no_primary_lead.setText(
                str(round(
                    studyStats.aecgs_annotations_no_primary_lead /
                    studyStats.num_aecgs*100, 2)) + " %")
            progress.setValue(10)

            # aECGS with errors
            tabs.aecgs_with_errors.setText(str(studyStats.aecgs_with_errors))
            progress.setValue(11)

            # Potentially digitized aECGs
            tabs.aecgs_potentially_digitized.setText(
                str(studyStats.aecgs_potentially_digitized))
        progress.setValue(11)
        progress.close()

    def save_aecg_to_image(self):
        fileName, fileFilter = QFileDialog.getSaveFileName(
            self,
            caption="Save ECG as ...",
            filter="Image file (*.png);;PDF (*.pdf)")
        if fileName != "":
            self.centralWidget().tabdisplays.aecg_display.figure.\
                savefig(fileName,
                        dpi=self.centralWidget().tabdisplays.aecg_display.dpi)

    def openindex_dialog(self):
        fileName, fileFilter = QFileDialog.getOpenFileName(
            self,
            caption="Open study Index",
            filter="Index Files (*.xlsx)")
        if fileName != "":
            self.study_index_dir = os.path.dirname(fileName)
            self.centralWidget().load_projectindex(fileName)

    def importstudy_dialog(self):
        fileName, fileFilter = QFileDialog.getOpenFileName(
            self,
            caption="Import study",
            filter="Study information Files (*.xlsx)")
        if fileName != "":
            self.centralWidget().tabdisplays.load_study_info(fileName)
