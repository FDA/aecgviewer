"""This submodule implements classes that organize an index of an aECG file in
a hierarchical (tree) fashion.
See authors, license and disclaimer at the top level directory of this project.
"""


from PySide2 import QtCore


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData[column]
        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, parent=None):
        super(TreeModel, self).__init__(parent)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and \
                role == QtCore.Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()


class ProjectTreeModel(TreeModel):
    def __init__(self, index_df=None, parent=None, progress_dialog=None):
        super(ProjectTreeModel, self).__init__(parent)

        self.progress_dialog = progress_dialog
        self.rootItem = TreeItem(("Subject", "Time-point", "Rhythm", "Derived",
                                  "ZIPFILE", "AECGXML"))
        if index_df is not None:
            self.setupModelData(index_df, self.rootItem)

    def setupModelData(self, index_df, parent):
        newRhythmItem = None
        if index_df.shape[0] > 0:
            index_df = index_df.sort_values(["USUBJID", "EGTPTREF", "EGDTC"])
            i = 0
            for subj in index_df.groupby(["USUBJID"]):
                if self.progress_dialog and self.progress_dialog.wasCanceled():
                    break
                newSubjectItem = TreeItem(
                    (subj[0], '', '', '', '', '', ''), parent)
                parent.appendChild(newSubjectItem)
                for timepoint in subj[1].groupby(["EGTPTREF"]):
                    newTimepointItem = TreeItem(('', timepoint[0], '', '',
                                                 '', '', ''),
                                                newSubjectItem)
                    newSubjectItem.appendChild(newTimepointItem)
                    for ecgfile in timepoint[1].groupby(
                            ["EGDTC", "AECGXML", "EGREFID"]):
                        rhythmwf = ecgfile[1][ecgfile[1]["WFTYPE"] == "RHYTHM"]
                        derivedwf = ecgfile[1][ecgfile[1][
                                                   "WFTYPE"] == "DERIVED"]
                        if rhythmwf.shape[0] > 0:
                            newRhythmItem = TreeItem(
                                ('', '', str(rhythmwf["EGDTC"].iloc[0]), '',
                                 rhythmwf["ZIPFILE"].values[0],
                                 rhythmwf["AECGXML"].values[0]),
                                newTimepointItem)
                            newTimepointItem.appendChild(newRhythmItem)
                            if self.progress_dialog:
                                self.progress_dialog.setValue(i)
                            i += 1
                        if derivedwf.shape[0] > 0:
                            derivedwf_parent = newTimepointItem
                            if rhythmwf.shape[0] > 0:
                                derivedwf_parent = newRhythmItem
                            newDerivedItem = TreeItem(
                                ('', '', '', str(derivedwf["EGDTC"].iloc[0]),
                                 derivedwf["ZIPFILE"].values[0],
                                 derivedwf["AECGXML"].values[0]),
                                derivedwf_parent)
                            derivedwf_parent.appendChild(newDerivedItem)
                            if self.progress_dialog:
                                self.progress_dialog.setValue(i)
                            i += 1
            if self.progress_dialog:
                self.progress_dialog.setValue(index_df.shape[0])
