"""This submodule implements multiple tabs displayed in the GUI.
See authors, license and disclaimer at the top level directory of this project.
"""

from PySide2.QtCore import (QThreadPool, Signal, QElapsedTimer)
from PySide2.QtWidgets import (QLabel, QWidget, QTabWidget, QFormLayout,
                               QHBoxLayout, QVBoxLayout, QGridLayout,
                               QLineEdit, QSizePolicy, QScrollArea,
                               QSpinBox, QSplitter,
                               QTextEdit, QPushButton,
                               QProgressBar,
                               QCheckBox,
                               QComboBox,
                               QMessageBox, QFileDialog)
from PySide2.QtGui import QIntValidator

import datetime
import logging
import logging.config
import os
import pandas as pd

from aecgviewer.ecgdisplaywidget import EcgDisplayWidget
from aecgviewer.backgroundworks import Worker

import aecg
import aecg.tools.indexer


class TabDisplays(QTabWidget):
    def __init__(self, parent=None):
        super(TabDisplays, self).__init__(parent)

        # Initialize logging
        logging_conf_file = os.path.join(
            os.path.dirname(__file__), 'cfg/aecgviewer_aecg_logging.conf')
        logging.config.fileConfig(logging_conf_file)
        self.logger = logging.getLogger(__name__)

        self.studyindex_info = aecg.tools.indexer.StudyInfo()

        self.validator = QWidget()

        self.studyinfo = QWidget()

        self.statistics = QWidget()

        self.waveforms = QWidget()

        self.waveforms.setAccessibleName("Waveforms")

        self.scatterplot = QWidget()

        self.histogram = QWidget()

        self.trends = QWidget()

        self.xmlviewer = QWidget()
        self.xml_display = QTextEdit(self.xmlviewer)

        self.options = QWidget()

        self.aecg_display_area = QScrollArea()
        self.cbECGLayout = QComboBox()
        self.aecg_display = EcgDisplayWidget(self.aecg_display_area)
        self.aecg_display_area.setWidget(self.aecg_display)

        self.addTab(self.validator, "Study information")
        self.addTab(self.waveforms, "Waveforms")
        self.addTab(self.xmlviewer, "XML")
        self.addTab(self.options, "Options")

        self.setup_validator()
        self.setup_waveforms()
        self.setup_xmlviewer()
        self.setup_options()

        size = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size.setHeightForWidth(False)
        self.setSizePolicy(size)

        # Initialized a threpool with 2 threads 1 for the GUI, 1 for long
        # tasks, so GUI remains responsive
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(2)
        self.validator_worker = None
        self.indexing_timer = QElapsedTimer()

    def setup_validator(self):
        self.directory_indexer = None  # aecg.indexing.DirectoryIndexer()
        self.validator_layout_container = QWidget()
        self.validator_layout = QFormLayout()
        self.validator_form_layout = QFormLayout(
            self.validator_layout_container)
        self.validator_grid_layout = QGridLayout()
        self.study_info_file = QLineEdit()
        self.study_info_file.setToolTip("Study index file")
        self.study_info_description = QLineEdit()
        self.study_info_description.setToolTip("Description")
        self.app_type = QLineEdit()
        self.app_type.setToolTip("Application type (e.g., NDA, IND, BLA, IDE)")
        self.app_num = QLineEdit()
        self.app_num.setToolTip("Six-digit application number")
        self.app_num.setValidator(QIntValidator(self.app_num))
        self.study_id = QLineEdit()
        self.study_id.setToolTip("Study identifier")
        self.study_sponsor = QLineEdit()
        self.study_sponsor.setToolTip("Sponsor of the study")

        self.study_annotation_aecg_cb = QComboBox()
        self.study_annotation_aecg_cb.addItems(["Rhythm", "Derived beat",
                                                "Holter-rhythm",
                                                "Holter-derived"])
        self.study_annotation_aecg_cb.setToolTip(
            "Waveforms used to perform the ECG measurements (i.e., "
            "annotations)\n"
            "\tRhythm: annotations in a rhythm strip or discrete ECG "
            "extraction (e.g., 10-s strips)\n"
            "\tDerived beat: annotations in a representative beat derived "
            "from a rhythm strip\n"
            "\tHolter-rhythm: annotations in a the analysis window of a "
            "continuous recording\n"
            "\tHolter-derived: annotations in a representative beat derived "
            "from analysis window of a continuous recording\n")
        self.study_annotation_lead_cb = QComboBox()
        self.ui_leads = ["GLOBAL"] + aecg.STD_LEADS[0:12] +\
            [aecg.KNOWN_NON_STD_LEADS[1]] + aecg.STD_LEADS[12:15] + ["Other"]
        self.study_annotation_lead_cb.addItems(self.ui_leads)
        self.study_annotation_lead_cb.setToolTip(
            "Primary analysis lead annotated per protocol. There could be "
            "annotations in other leads also, but only the primary lead should"
            " be selected here.\n"
            "Select global if all leads were used at the "
            "same time (e.g., superimposed on screen).\n"
            "Select other if the primary lead used is not in the list.")

        self.study_numsubjects = QLineEdit()
        self.study_numsubjects.setToolTip(
            "Number of subjects with ECGs in the study")
        self.study_numsubjects.setValidator(
            QIntValidator(self.study_numsubjects))

        self.study_aecgpersubject = QLineEdit()
        self.study_aecgpersubject.setToolTip(
            "Number of scheduled ECGs (or analysis windows) per subject as "
            "specified in the study protocol.\n"
            "Enter average number of ECGs "
            "per subject if the protocol does not specify a fixed number of "
            "ECGs per subject.")
        self.study_aecgpersubject.setValidator(
            QIntValidator(self.study_aecgpersubject))

        self.study_numaecg = QLineEdit()
        self.study_numaecg.setToolTip(
            "Total number of aECG XML files in the study")
        self.study_numaecg.setValidator(
            QIntValidator(self.study_numaecg))

        self.study_annotation_numbeats = QLineEdit()
        self.study_annotation_numbeats.setToolTip(
            "Minimum number of beats annotated in each ECG or analysis window"
            ".\nEnter 1 if annotations were done in the derived beat.")
        self.study_annotation_numbeats.setValidator(
            QIntValidator(self.study_annotation_numbeats))

        self.aecg_numsubjects = QLineEdit()
        self.aecg_numsubjects.setToolTip(
            "Number of subjects found across the provided aECG XML files")
        self.aecg_numsubjects.setReadOnly(True)

        self.aecg_aecgpersubject = QLineEdit()
        self.aecg_aecgpersubject.setToolTip(
            "Average number of ECGs per subject found across the provided "
            "aECG XML files")
        self.aecg_aecgpersubject.setReadOnly(True)

        self.aecg_numaecg = QLineEdit()
        self.aecg_numaecg.setToolTip(
            "Number of aECG XML files found in the study aECG directory")
        self.aecg_numaecg.setReadOnly(True)

        self.subjects_less_aecgs = QLineEdit()
        self.subjects_less_aecgs.setToolTip(
            "Percentage of subjects with less aECGs than specified per "
            "protocol")
        self.subjects_less_aecgs.setReadOnly(True)

        self.subjects_more_aecgs = QLineEdit()
        self.subjects_more_aecgs.setToolTip(
            "Percentage of subjects with more aECGs than specified per "
            "protocol")
        self.subjects_more_aecgs.setReadOnly(True)

        self.aecgs_no_annotations = QLineEdit()
        self.aecgs_no_annotations.setToolTip(
            "Percentage of aECGs with no annotations")
        self.aecgs_no_annotations.setReadOnly(True)

        self.aecgs_less_qt_in_primary_lead = QLineEdit()
        self.aecgs_less_qt_in_primary_lead.setToolTip(
            "Percentage of aECGs with less QT intervals in the primary lead "
            "than specified per protocol")
        self.aecgs_less_qt_in_primary_lead.setReadOnly(True)

        self.aecgs_less_qts = QLineEdit()
        self.aecgs_less_qts.setToolTip(
            "Percentage of aECGs with less QT intervals than specified per "
            "protocol")
        self.aecgs_less_qts.setReadOnly(True)

        self.aecgs_annotations_multiple_leads = QLineEdit()
        self.aecgs_annotations_multiple_leads.setToolTip(
            "Percentage of aECGs with QT annotations in multiple leads")
        self.aecgs_annotations_multiple_leads.setReadOnly(True)

        self.aecgs_annotations_no_primary_lead = QLineEdit()
        self.aecgs_annotations_no_primary_lead.setToolTip(
            "Percentage of aECGs with QT annotations not in the primary lead")
        self.aecgs_annotations_no_primary_lead.setReadOnly(True)

        self.aecgs_with_errors = QLineEdit()
        self.aecgs_with_errors.setToolTip(
            "Number of aECG files with errors")
        self.aecgs_with_errors.setReadOnly(True)

        self.aecgs_potentially_digitized = QLineEdit()
        self.aecgs_potentially_digitized.setToolTip(
            "Number of aECG files potentially digitized (i.e., with more than "
            "5% of samples missing)")
        self.aecgs_potentially_digitized.setReadOnly(True)

        self.study_dir = QLineEdit()
        self.study_dir.setToolTip("Directory containing the aECG files")
        self.study_dir_button = QPushButton("...")
        self.study_dir_button.clicked.connect(self.select_study_dir)
        self.study_dir_button.setToolTip("Open select directory dialog")

        self.validator_form_layout.addRow(
            "Application Type", self.app_type)
        self.validator_form_layout.addRow(
            "Application Number", self.app_num)
        self.validator_form_layout.addRow(
            "Study name/ID", self.study_id)
        self.validator_form_layout.addRow(
            "Sponsor", self.study_sponsor)
        self.validator_form_layout.addRow(
            "Study description", self.study_info_description)

        self.validator_form_layout.addRow(
            "Annotations in",
            self.study_annotation_aecg_cb)
        self.validator_form_layout.addRow(
            "Annotations primary lead", self.study_annotation_lead_cb)

        self.validator_grid_layout.addWidget(QLabel(""), 0, 0)
        self.validator_grid_layout.addWidget(
            QLabel("Per study protocol or report"), 0, 1)
        self.validator_grid_layout.addWidget(
            QLabel("Found in aECG files"), 0, 2)

        self.validator_grid_layout.addWidget(QLabel(
            "Number of subjects"), 1, 0)
        self.validator_grid_layout.addWidget(self.study_numsubjects, 1, 1)
        self.validator_grid_layout.addWidget(self.aecg_numsubjects, 1, 2)

        self.validator_grid_layout.addWidget(QLabel(
            "Number of aECG per subject"), 2, 0)
        self.validator_grid_layout.addWidget(self.study_aecgpersubject, 2, 1)
        self.validator_grid_layout.addWidget(self.aecg_aecgpersubject, 2, 2)

        self.validator_grid_layout.addWidget(QLabel(
            "Total number of aECG"), 3, 0)
        self.validator_grid_layout.addWidget(self.study_numaecg, 3, 1)
        self.validator_grid_layout.addWidget(self.aecg_numaecg, 3, 2)

        self.validator_grid_layout.addWidget(QLabel(
            "Number of beats per aECG"), 4, 0)
        self.validator_grid_layout.addWidget(
            self.study_annotation_numbeats, 4, 1)

        self.validator_grid_layout.addWidget(QLabel(
            "Subjects with fewer ECGs"), 5, 1)
        self.validator_grid_layout.addWidget(
            self.subjects_less_aecgs, 5, 2)
        self.validator_grid_layout.addWidget(QLabel(
            "Subjects with more ECGs"), 6, 1)
        self.validator_grid_layout.addWidget(
            self.subjects_more_aecgs, 6, 2)
        self.validator_grid_layout.addWidget(QLabel(
            "aECGs without annotations"), 7, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_no_annotations, 7, 2)
        self.validator_grid_layout.addWidget(QLabel(
            "aECGs without expected number of QTs in primary lead"), 8, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_less_qt_in_primary_lead, 8, 2)
        self.validator_grid_layout.addWidget(QLabel(
            "aECGs without expected number of QTs"), 9, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_less_qts, 9, 2)

        self.validator_grid_layout.addWidget(QLabel(
            "aECGs annotated in multiple leads"), 10, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_annotations_multiple_leads, 10, 2)
        self.validator_grid_layout.addWidget(QLabel(
            "aECGs with annotations not in primary lead"), 11, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_annotations_no_primary_lead, 11, 2)
        self.validator_grid_layout.addWidget(QLabel(
            "aECGs with errors"), 12, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_with_errors, 12, 2)

        self.validator_grid_layout.addWidget(QLabel(
            "Potentially digitized aECGs"), 13, 1)
        self.validator_grid_layout.addWidget(
            self.aecgs_potentially_digitized, 13, 2)

        self.validator_form_layout.addRow(self.validator_grid_layout)

        tmp = QHBoxLayout()
        tmp.addWidget(self.study_dir)
        tmp.addWidget(self.study_dir_button)
        self.validator_form_layout.addRow(
            "Study aECGs directory", tmp)

        self.validator_form_layout.addRow(
            "Study index file", self.study_info_file)

        self.validator_layout.addWidget(self.validator_layout_container)
        self.validator_effective_dirs = QLabel("")
        self.validator_effective_dirs.setWordWrap(True)
        self.validator_layout.addWidget(self.validator_effective_dirs)

        self.val_button = QPushButton("Generate/update study index")
        self.val_button.clicked.connect(self.importstudy_dialog)
        self.validator_layout.addWidget(self.val_button)
        self.cancel_val_button = QPushButton(
            "Cancel study index generation")
        self.cancel_val_button.clicked.connect(self.cancel_validator)
        self.cancel_val_button.setEnabled(False)
        self.validator_layout.addWidget(self.cancel_val_button)
        self.validator_pl = QLabel("")
        self.validator_layout.addWidget(self.validator_pl)
        self.validator_pb = QProgressBar()
        self.validator_layout.addWidget(self.validator_pb)
        self.validator.setLayout(self.validator_layout)
        self.stop_indexing = False

        self.lastindexing_starttime = None

        self.update_validator_effective_dirs()

    def effective_aecgs_dir(self, navwidget, silent=False):
        aecgs_effective_dir = self.study_dir.text()
        if navwidget.project_loaded != '':
            # Path specified in the GUI
            potential_aecgs_dirs = [self.study_dir.text()]
            # StudyDir path from current working directory
            potential_aecgs_dirs += [
                self.studyindex_info.StudyDir]
            # StudyDir path from directory where the index is located
            potential_aecgs_dirs += [
                os.path.join(
                    os.path.dirname(navwidget.project_loaded),
                    self.studyindex_info.StudyDir)]
            # StudyDir replaced with the directory where the index is located
            potential_aecgs_dirs += [
                os.path.dirname(navwidget.project_loaded)]
            dir_found = False
            # Get xml and zip filenames from first element in the index
            aecg_xml_file = navwidget.data_index["AECGXML"][0]
            zipfile = ""
            if aecg_xml_file != "":
                zipfile = navwidget.data_index["ZIPFILE"][0]
            for p in potential_aecgs_dirs:
                testfn = os.path.join(p, aecg_xml_file)
                if zipfile != "":
                    testfn = os.path.join(p, zipfile)
                if os.path.isfile(testfn):
                    dir_found = True
                    aecgs_effective_dir = p
                    break
            if not silent:
                if not dir_found:
                    QMessageBox.warning(
                        self,
                        f"Study aECGs directory not found",
                        f"The following paths were checked:"
                        f"{[','.join(p) for p in potential_aecgs_dirs]} and "
                        f"none of them is valid")
                elif p != self.study_dir.text():
                    QMessageBox.warning(
                        self,
                        f"Study aECGs directory not found",
                        f"The path specified in the study aECGs directory is "
                        f"not valid and {p} is being used instead. Check and "
                        f"update the path in Study aECGs directory textbox if "
                        f"the suggested path is not the adequate path")
        return aecgs_effective_dir

    def update_validator_effective_dirs(self):
        msg = f"Working directory: {os.getcwd()}"
        if self.parent() is not None:
            if isinstance(self.parent(), QSplitter):
                navwidget = self.parent().parent()
            else:  # Tabs widget has not been allocated the QSplitter yet
                navwidget = self.parent()
            project_loaded = navwidget.project_loaded
            if project_loaded != '':
                msg = f"{msg}\nLoaded project index: "\
                      f"{navwidget.project_loaded}"
                effective_aecgs_path = self.effective_aecgs_dir(navwidget)
                msg = f"{msg}\nEffective study aECGs directory: "\
                      f"{effective_aecgs_path}"
            else:
                msg = f"{msg}\nLoaded project index: None"
        else:
            msg = f"{msg}\nLoaded project index: None"
        self.validator_effective_dirs.setText(msg)

    def load_study_info(self, fileName):
        self.study_info_file.setText(fileName)
        try:
            study_info = pd.read_excel(fileName, sheet_name="Info")
            self.studyindex_info = aecg.tools.indexer.StudyInfo()
            self.studyindex_info.__dict__.update(
                study_info.set_index(
                    "Property").transpose().reset_index(
                        drop=True).to_dict('index')[0])
            sponsor = ""
            description = ""
            if self.studyindex_info.Sponsor is not None and\
                    isinstance(self.studyindex_info.Sponsor, str):
                sponsor = self.studyindex_info.Sponsor
            if self.studyindex_info.Description is not None and\
                    isinstance(self.studyindex_info.Description, str):
                description = self.studyindex_info.Description
            self.study_sponsor.setText(sponsor)
            self.study_info_description.setText(description)
            self.app_type.setText(self.studyindex_info.AppType)
            self.app_num.setText(f"{int(self.studyindex_info.AppNum):06d}")
            self.study_id.setText(self.studyindex_info.StudyID)
            self.study_numsubjects.setText(str(self.studyindex_info.NumSubj))
            self.study_aecgpersubject.setText(
                str(self.studyindex_info.NECGSubj))
            self.study_numaecg.setText(str(self.studyindex_info.TotalECGs))

            anns_in = self.studyindex_info.AnMethod.upper()
            idx = 0
            if anns_in == "RHYTHM":
                idx = 0
            elif anns_in == "DERIVED":
                idx = 1
            elif anns_in == "HOLTER_RHYTHM":
                idx = 2
            elif anns_in == "HOLTER_MEDIAN_BEAT":
                idx = 3
            else:
                idx = int(anns_in) - 1
            self.study_annotation_aecg_cb.setCurrentIndex(idx)

            the_lead = self.studyindex_info.AnLead
            idx = self.study_annotation_lead_cb.findText(str(the_lead))
            if idx == -1:
                idx = self.study_annotation_lead_cb.findText(
                    "MDC_ECG_LEAD_" + str(the_lead))
            if idx == -1:
                idx = int(the_lead)
            self.study_annotation_lead_cb.setCurrentIndex(idx)

            self.study_annotation_numbeats.setText(
                str(self.studyindex_info.AnNbeats))
            if self.studyindex_info.StudyDir == "":
                self.studyindex_info.StudyDir = os.path.dirname(fileName)
            self.study_dir.setText(self.studyindex_info.StudyDir)

            self.update_validator_effective_dirs()
            self.setCurrentWidget(self.validator)

        except Exception as ex:
            QMessageBox.critical(
                self,
                "Import study error",
                "Error reading the study information file: '" +
                fileName + "'")

    def setup_waveforms(self):
        wflayout = QVBoxLayout()

        # ECG plot layout selection box
        self.cbECGLayout.addItems(['12-lead stacked',
                                   '3x4 + lead II rhythm',
                                   'Superimposed'])
        self.cbECGLayout.currentIndexChanged.connect(
            self.ecgplotlayout_changed)

        # Zoom buttons
        blayout = QHBoxLayout()

        pb_zoomin = QPushButton()
        pb_zoomin.setText("Zoom +")
        pb_zoomin.clicked.connect(self.zoom_in)

        pb_zoomreset = QPushButton()
        pb_zoomreset.setText("Zoom 1:1")
        pb_zoomreset.clicked.connect(self.zoom_reset)

        pb_zoomout = QPushButton()
        pb_zoomout.setText("Zoom -")
        pb_zoomout.clicked.connect(self.zoom_out)

        blayout.addWidget(self.cbECGLayout)
        blayout.addWidget(pb_zoomout)
        blayout.addWidget(pb_zoomreset)
        blayout.addWidget(pb_zoomin)

        wflayout.addLayout(blayout)

        # Add QScrollArea to main layout of waveforms tab
        self.aecg_display_area.setWidgetResizable(False)
        wflayout.addWidget(self.aecg_display_area)
        self.waveforms.setLayout(wflayout)
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size.setHeightForWidth(False)
        self.aecg_display_area.setSizePolicy(size)
        self.waveforms.setSizePolicy(size)

    def setup_xmlviewer(self):
        wf_layout = QHBoxLayout()
        wf_layout.addWidget(self.xml_display)
        self.xmlviewer.setLayout(wf_layout)

    def setup_options(self):
        self.options_layout = QFormLayout()
        self.aecg_schema_filename = QLineEdit(aecg.get_aecg_schema_location())
        self.options_layout.addRow(
            "aECG XML schema path", self.aecg_schema_filename)

        self.save_index_every_n_aecgs = QSpinBox()
        self.save_index_every_n_aecgs.setMinimum(0)
        self.save_index_every_n_aecgs.setMaximum(50000)
        self.save_index_every_n_aecgs.setValue(0)
        self.save_index_every_n_aecgs.setSingleStep(100)
        self.save_index_every_n_aecgs.setSuffix(" aECGs")
        self.save_index_every_n_aecgs.setToolTip(
            "Set o 0 to save the study index file only after its generation "
            "is completed.\nOtherwise, the file is saved everytime the "
            " specified number of ECGs have been appended to the index.")
        self.options_layout.addRow(
            "Save index every ", self.save_index_every_n_aecgs)

        self.save_all_intervals_cb = QCheckBox("")
        self.save_all_intervals_cb.setChecked(False)
        self.options_layout.addRow(
            "Save individual beat intervals", self.save_all_intervals_cb)

        self.parallel_processing_cb = QCheckBox("")
        self.parallel_processing_cb.setChecked(True)
        self.options_layout.addRow(
            "Parallel processing of files", self.parallel_processing_cb)

        self.options.setLayout(self.options_layout)

    def zoom_in(self):
        self.aecg_display.apply_zoom(self.aecg_display.zoom_factor + 0.1)

    def zoom_out(self):
        self.aecg_display.apply_zoom(self.aecg_display.zoom_factor - 0.1)

    def zoom_reset(self):
        self.aecg_display.apply_zoom(1.0)

    def ecgplotlayout_changed(self, i):
        self.aecg_display.update_aecg_plot(
            ecg_layout=aecg.utils.ECG_plot_layout(i+1))

    def update_search_progress(self, i, n):
        self.validator_pl.setText(
            f"Searching aECGs in directory ({n} XML files found)")

    def update_progress(self, i, n):
        j = i
        m = n
        if i <= 1:
            j = 1
            if self.validator_pb.value() > 0:
                j = self.validator_pb.value() + 1
            m = self.validator_pb.maximum()
        running_time = self.indexing_timer.elapsed()*1e-3  # in seconds
        time_per_item = running_time/j
        # reamining = seconds per item so far * total pending items to process
        remaining_time = time_per_item * (m - j)
        eta = datetime.datetime.now() +\
            datetime.timedelta(seconds=round(remaining_time, 0))
        self.validator_pl.setText(
            f"Validating aECG {j}/{m} | "
            f"Execution time: "
            f"{str(datetime.timedelta(0,seconds=round(running_time)))} | "
            f"{round(1/time_per_item,2)} aECGs per second | "
            f"ETA: {eta.isoformat(timespec='seconds')}")
        self.validator_pb.setValue(j)
        if self.save_index_every_n_aecgs.value() > 0 and\
                len(self.directory_indexer.studyindex) % \
                self.save_index_every_n_aecgs.value() == 0:
            self.save_validator_results(
                pd.concat(self.directory_indexer.studyindex,
                          ignore_index=True))

    def save_validator_results(self, res):
        if res.shape[0] > 0:
            self.studyindex_info = aecg.tools.indexer.StudyInfo()
            self.studyindex_info.StudyDir = self.study_dir.text()
            self.studyindex_info.IndexFile = self.study_info_file.text()
            self.studyindex_info.Sponsor = self.study_sponsor.text()
            self.studyindex_info.Description =\
                self.study_info_description.text()
            self.studyindex_info.Date = self.lastindexing_starttime.isoformat()
            self.studyindex_info.End_date = datetime.datetime.now().isoformat()
            self.studyindex_info.Version = aecg.__version__
            self.studyindex_info.AppType = self.app_type.text()
            self.studyindex_info.AppNum = f"{int(self.app_num.text()):06d}"
            self.studyindex_info.StudyID = self.study_id.text()
            self.studyindex_info.NumSubj = int(self.study_numsubjects.text())
            self.studyindex_info.NECGSubj = int(
                self.study_aecgpersubject.text())
            self.studyindex_info.TotalECGs = int(self.study_numaecg.text())
            anmethod = aecg.tools.indexer.AnnotationMethod(
                self.study_annotation_aecg_cb.currentIndex())
            self.studyindex_info.AnMethod = anmethod.name
            self.studyindex_info.AnLead =\
                self.study_annotation_lead_cb.currentText()
            self.studyindex_info.AnNbeats = int(
                self.study_annotation_numbeats.text())

            # Calculate stats
            study_stats = aecg.tools.indexer.StudyStats(
                self.studyindex_info, res)

            # Save to file
            aecg.tools.indexer.save_study_index(
                self.studyindex_info, res, study_stats)

    validator_data_ready = Signal()

    def save_validator_results_and_load_index(self, res):
        self.save_validator_results(res)
        self.validator_data_ready.emit()

    def indexer_validator_results(self, res):
        self.studyindex_df = pd.concat(
            [self.studyindex_df, res], ignore_index=True)

    def subindex_thread_complete(self):
        return

    def index_directory_thread_complete(self):
        tmp = self.validator_pl.text().replace(
            "ETA:", "Completed: ").replace("Validating", "Validated")
        self.validator_pl.setText(tmp)
        self.val_button.setEnabled(True)
        self.cancel_val_button.setEnabled(False)
        self.validator_layout_container.setEnabled(True)

    def index_directory(self, progress_callback):
        self.lastindexing_starttime = datetime.datetime.now()
        self.indexing_timer.start()

        studyindex_df = []
        n_cores = os.cpu_count()
        aecg_schema = None
        if self.aecg_schema_filename.text() != "":
            aecg_schema = self.aecg_schema_filename.text()
        if self.parallel_processing_cb.isChecked():
            studyindex_df = self.directory_indexer.index_directory(
                self.save_all_intervals_cb.isChecked(),
                aecg_schema,
                n_cores,
                progress_callback)
        else:
            studyindex_df = self.directory_indexer.index_directory(
                self.save_all_intervals_cb.isChecked(),
                aecg_schema,
                1,
                progress_callback
            )

        return studyindex_df

    def importstudy_dialog(self):
        dirName = os.path.normpath(self.study_dir.text())
        if dirName != "":
            if os.path.exists(dirName):
                self.directory_indexer = aecg.indexing.DirectoryIndexer()
                self.directory_indexer.set_aecg_dir(
                    dirName, self.update_search_progress)
                self.validator_pb.setMaximum(self.directory_indexer.num_files)
                self.validator_pb.reset()
                self.stop_indexing = False
                self.validator_layout_container.setEnabled(False)
                self.val_button.setEnabled(False)
                self.cancel_val_button.setEnabled(True)
                self.validator_worker = Worker(self.index_directory)
                self.validator_worker.signals.result.connect(
                    self.save_validator_results_and_load_index)
                self.validator_worker.signals.finished.connect(
                    self.index_directory_thread_complete)
                self.validator_worker.signals.progress.connect(
                    self.update_progress)

                # Execute
                self.threadpool.start(self.validator_worker)
            else:
                QMessageBox.critical(
                    self, "Directory not found",
                    f"Specified study directory not found:\n{dirName}")
        else:
            QMessageBox.critical(
                self, "Import study error", "Study directory cannot be empty")

    def cancel_validator(self):
        self.cancel_val_button.setEnabled(False)
        self.stop_indexing = True
        self.directory_indexer.cancel_indexing = True
        self.threadpool.waitForDone(3000)
        self.val_button.setEnabled(True)

    def select_study_dir(self):
        cd = self.study_dir.text()
        if cd == "":
            cd = "."
        dir = QFileDialog.getExistingDirectory(
            self, "Open Directory",
            cd,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dir != "":
            self.study_dir.setText(dir)
