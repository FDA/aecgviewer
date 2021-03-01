"""This submodule implements the load and navigation logic of the GUI.
See authors, license and disclaimer at the top level directory of this project.
"""

from openpyxl import load_workbook

import aecg
import aecg.tools.indexer
import os
import pandas as pd

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import (QVBoxLayout, QHeaderView,
                               QLineEdit,
                               QProgressDialog,
                               QSizePolicy,
                               QTreeView, QWidget, QSplitter,
                               QMessageBox)

from aecgviewer.aecgtreemodel import ProjectTreeModel
from aecgviewer.tabdisplays import TabDisplays


class NavigationWidget(QWidget):
    def __init__(self, index_filename):
        QWidget.__init__(self)

        self.data_index = pd.DataFrame()
        self.data_info = aecg.tools.indexer.StudyInfo()
        self.data_index_stats = aecg.tools.indexer.StudyStats(
            self.data_info,
            self.data_index
        )

        # Getting the Models
        self.project_loaded = ''
        self.projectmodel = ProjectTreeModel()

        # Creating a QTreeView for displaying the selected project index
        self.project_treeview = QTreeView()
        self.project_treeview.setModel(self.projectmodel)
        self.phorizontal_header = self.project_treeview.header()
        self.phorizontal_header.setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.phorizontal_header.setStretchLastSection(True)

        self.sp_right = QSplitter(Qt.Orientation.Horizontal)
        self.sp_left = QSplitter(Qt.Orientation.Vertical, self.sp_right)
        # NavigationWidget Layout
        self.main_layout = QVBoxLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Left side
        # Left side - Top layout
        # Left side - Bottom Layout
        size.setVerticalStretch(4)
        self.project_treeview.setSizePolicy(size)

        self.sp_left.addWidget(self.project_treeview)

        # Right side
        size = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size.setHorizontalStretch(2)
        size.setHeightForWidth(False)
        self.tabdisplays = TabDisplays(self)
        self.sp_right.addWidget(self.tabdisplays)
        self.tabdisplays.validator_data_ready.connect(
            self.load_projectindex_after_validation)
        self.sp_right.setSizePolicy(size)

        # Set the layout to the QWidget
        self.main_layout.addWidget(self.sp_right)
        self.setLayout(self.main_layout)

        self.tabdisplays.setCurrentWidget(self.tabdisplays.validator)

        # Load study index
        if index_filename and (index_filename != ""):
            if os.path.exists(index_filename):
                self.load_projectindex(os.path.normpath(index_filename))
            else:
                QMessageBox.warning(
                    self,
                    f"Study index file not found",
                    f"{index_filename} not found")

    projectindex_loaded = Signal()
    projectindexstats_loaded = Signal()

    def load_projectindex_after_validation(self):
        self.load_projectindex(
            os.path.normpath(self.tabdisplays.study_info_file.text()))

    def load_projectindex(self, project_idx_file):
        index_loaded = False
        stats_loaded = False
        if project_idx_file != "":
            if os.path.exists(project_idx_file):
                try:
                    self.parent().status.showMessage(
                        f"Loading {project_idx_file}")
                    progress = QProgressDialog(
                        "Loading index file...", "Cancel",
                        0, 3,
                        self)
                    progress.setWindowTitle("Loading study index")
                    progress.setWindowModality(Qt.WindowModal)
                    progress.setMinimumWidth(300)
                    progress.setMinimumDuration(0)
                    progress.forceShow()
                    progress.setValue(0)
                    wb = load_workbook(project_idx_file, read_only=True)
                    progress.setValue(1)
                    ws = wb['Index']
                    ws.reset_dimensions()
                    data = ws.values
                    cols = next(data)
                    data = list(data)
                    progress.setValue(2)
                    self.data_index = pd.DataFrame(
                        data, columns=cols).fillna("")
                    progress.setValue(3)
                    progress.close()
                    # Parse index to the tree
                    num_ecgs = 0
                    if "EGREFID" in self.data_index.columns:
                        num_ecgs = self.data_index[
                            ["ZIPFILE", "AECGXML",
                             "EGREFID", "WFTYPE"]].drop_duplicates().shape[0]
                        progress = QProgressDialog(
                            "Parsing index ...", "Cancel",
                            0, num_ecgs,
                            self)
                        progress.setWindowTitle("Loading study index")
                        progress.setLabelText("Parsing index...")
                        progress.setWindowModality(Qt.WindowModal)
                        progress.setMinimumWidth(300)
                        progress.setMinimumDuration(0)
                        progress.forceShow()
                        progress.setValue(0)
                        self.projectmodel = ProjectTreeModel(
                            self.data_index, progress_dialog=progress)
                        self.project_treeview.setModel(self.projectmodel)
                        self.project_treeview.selectionModel().\
                            selectionChanged.connect(self.load_data)
                        progress.close()
                    else:
                        QMessageBox.warning(
                            self,
                            "EGREFID missing",
                            f"EGREFID column missing Index sheet of "
                            f"{project_idx_file}")
                    self.project_loaded = project_idx_file

                    # Reset aECG display
                    self.tabdisplays.aecg_display.aecg_data = None
                    self.tabdisplays.aecg_display.plot_aecg()

                    # Populate study information/validator tab
                    self.tabdisplays.load_study_info(project_idx_file)
                    self.data_index_info = self.tabdisplays.studyindex_info

                    index_loaded = True
                    try:
                        progress = QProgressDialog(
                            "Loading study index stats...", "Cancel",
                            0, 3,
                            self)
                        progress.setWindowTitle("Loading study index stats")
                        progress.setWindowModality(Qt.WindowModal)
                        progress.setMinimumWidth(300)
                        progress.setMinimumDuration(0)
                        progress.forceShow()
                        progress.setValue(0)
                        ws = wb['Stats']
                        ws.reset_dimensions()
                        data = ws.values
                        cols = next(data)
                        data = list(data)
                        progress.setValue(1)
                        progress.forceShow()
                        statsdf = pd.DataFrame(
                            data, columns=cols).fillna("")
                        progress.setValue(2)
                        progress.forceShow()
                        self.data_index_stats = aecg.tools.indexer.StudyStats()
                        self.data_index_stats.__dict__.update(
                            statsdf.set_index(
                                "Property").transpose().reset_index(
                                    drop=True).to_dict('index')[0])
                        progress.setValue(3)
                        progress.forceShow()
                        progress.close()
                        stats_loaded = True
                    except Exception as ex:
                        QMessageBox.warning(
                            self,
                            f"Error loading study index stats",
                            f"Error loading study index stats from"
                            f"{project_idx_file}\n{str(ex)}")
                except Exception as ex:
                    QMessageBox.warning(
                        self,
                        f"Error loading study index",
                        f"Error loading study index from {project_idx_file}"
                        f"\n{str(ex)}")
            else:
                QMessageBox.warning(
                    self,
                    f"Study index file not found",
                    f"{project_idx_file} not found")

            if index_loaded:
                self.projectindex_loaded.emit()
                if stats_loaded:
                    self.projectindexstats_loaded.emit()
            self.parentWidget().status.clearMessage()

    def load_data(self, selected, deselected):
        self.tabdisplays.setCurrentWidget(self.tabdisplays.waveforms)
        rhythm = self.projectmodel.itemData(selected.indexes()[2])[0]
        derived = self.projectmodel.itemData(selected.indexes()[3])[0]
        # Get study directory provided in the GUI
        studydir = self.tabdisplays.effective_aecgs_dir(self, silent=True)
        # Calculate effective study dir
        aecg_xml_file = self.projectmodel.itemData(selected.indexes()[5])[0]
        if aecg_xml_file != "":
            zipfile = self.projectmodel.itemData(selected.indexes()[4])[0]
            if zipfile != "":
                zipfile = os.path.join(studydir, zipfile)
            else:
                aecg_xml_file = os.path.join(
                    studydir, aecg_xml_file)
            # Load aECG file
            aecg_data = aecg.io.read_aecg(aecg_xml_file, zipfile,
                                          include_digits=True,
                                          in_memory_xml=True,
                                          log_validation=False)
            if aecg_data.xmlfound:
                # Plot aECG
                self.tabdisplays.aecg_display.set_aecg(aecg_data)
                self.tabdisplays.aecg_display.plot_aecg(
                    rhythm,
                    derived,
                    ecg_layout=aecg.utils.ECG_plot_layout(
                        self.tabdisplays.cbECGLayout.currentIndex() + 1))

                # Populate XML viewer
                self.tabdisplays.xml_display.setText(aecg_data.xmlstring())
            else:
                QMessageBox.warning(self,
                                    "aECG XML file not found",
                                    f"aECG XML {aecg_xml_file} not found")
                self.parentWidget().update_status_bar()
