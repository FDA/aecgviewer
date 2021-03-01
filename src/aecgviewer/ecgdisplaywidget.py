"""This submodule implements classes to display aECGs in a GUI.
See authors, license and disclaimer at the top level directory of this project.
"""


import pandas as pd

from PySide2.QtCore import QSize
from PySide2.QtWidgets import QSizePolicy

from matplotlib.backends.backend_qt5agg import\
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import aecg


class MyMplCanvas(FigureCanvas):
    def __init__(self, fig, parent=None):
        FigureCanvas.__init__(self, fig)

        self.setParent(parent)

        size = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size.setHeightForWidth(True)
        self.setSizePolicy(size)
        FigureCanvas.updateGeometry(self)

    def sizeHint(self):
        return QSize(400, 400 * 0.2 / 0.5)

    def heightForWidth(self, width):
        return width * 0.200 / 0.5


class EcgDisplayWidget(MyMplCanvas):

    def __init__(self, parent=None, aecg_data=None,
                 dpi=300, textsize=6, ecg_linewidth=0.3,
                 plot_grid=True, grid_color="#a88332",
                 v_offset=1.5,
                 xmin=0.0, xmax=2000.0,
                 ymin=-1.5, ymax=1.5,
                 x_margin=280):
        MyMplCanvas.__init__(self, Figure(dpi=dpi), parent)

        self.aecg_data = aecg_data

        self.dpi = dpi
        self.textsize = textsize
        self.ecg_linewidth = ecg_linewidth
        self.plot_grid = plot_grid
        self.grid_color = grid_color
        self.v_offset = v_offset
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        # Assign extra margin on the left for calibration pulse and lead name
        self.x_margin = x_margin  # ms

        self.zoom_factor = 1.0
        self.default_width_height = self.get_width_height()

        # Compute maximum height range based on number of leads
        self.n_leads = 1  # Default to 1, assigning numleads in aecg_data later

        # Initialize empy dataframes for ECG waveform and annotations
        self.ecgwf = pd.DataFrame()
        self.ecganns = pd.DataFrame()

        self.plot_aecg()

    def plot_aecg(self, rhythm="", derived="", adjust_fig_size_to_aecg=True,
                  ecg_layout=aecg.utils.ECG_plot_layout.STACKED):
        # Load ECG data
        if self.aecg_data is not None:
            self.ecgwf = pd.DataFrame()
            self.ecganns = pd.DataFrame()
            if rhythm != "":
                self.ecgwf = self.aecg_data.rhythm_as_df()
                if len(self.aecg_data.RHYTHMANNS) > 0:
                    self.ecganns = pd.DataFrame(
                        self.aecg_data.RHYTHMANNS[0].anns)
                    if self.ecganns.shape[0] > 0:
                        self.ecganns = self.aecg_data.rhythm_anns_in_ms()
            elif derived != "":
                self.ecgwf = self.aecg_data.derived_as_df()
                if len(self.aecg_data.DERIVEDANNS) > 0:
                    self.ecganns = pd.DataFrame(
                        self.aecg_data.DERIVEDANNS[0].anns)
                    if self.ecganns.shape[0] > 0:
                        self.ecganns = self.aecg_data.derived_anns_in_ms()

            self.update_aecg_plot(adjust_fig_size_to_aecg, ecg_layout)
        else:
            self.default_width_height = self.get_width_height()

            prior_zoom = self.zoom_factor
            self.apply_zoom()
            self.apply_zoom(prior_zoom)

    def set_aecg(self, aecg_data=None):
        if aecg_data is not None:
            self.aecg_data = aecg_data

    def apply_zoom(self, zoom_factor=1.0):
        if zoom_factor < 0.1:
            self.zoom_factor = 0.2
        elif zoom_factor > 10:
            self.zoom_factor = 10
        else:
            self.zoom_factor = zoom_factor

        new_width = self.default_width_height[0] * self.zoom_factor
        new_height = self.default_width_height[1] * self.zoom_factor

        # Resize widget to match the new figure size
        self.resize(new_width, new_height)
        # Draw the widget
        self.draw_idle()

    def update_aecg_plot(self, adjust_fig_size_to_aecg=True,
                         ecg_layout=aecg.utils.ECG_plot_layout.STACKED):
        if self.ecgwf.shape[0] > 0:
            self.n_leads = self.ecgwf.shape[1]
            if adjust_fig_size_to_aecg:
                self.xmin = self.ecgwf.TIME.values[0]
                self.xmax = self.ecgwf.TIME.values[-1]
            self.figure = aecg.utils.plot_aecg(
                self.ecgwf, self.ecganns,
                ecg_layout,
                self.figure,
                xmin=self.xmin,
                xmax=self.xmax,
                x_margin=self.x_margin)
        else:
            self.figure = Figure()

        self._static_ax = self.figure.axes

        self.default_width_height = self.get_width_height()

        prior_zoom = self.zoom_factor
        self.apply_zoom()
        self.apply_zoom(prior_zoom)
