from PySide6 import QtCore, QtGui, QtWidgets
from modrinth_api import ModrinthAPI


class ModListWidget(QtWidgets.QListWidget):
    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
        mod = item.data(QtCore.Qt.UserRole)
        mime = QtCore.QMimeData()
        mime.setData("application/x-mod", QtCore.QByteArray(str(mod).encode()))
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.exec(QtCore.Qt.CopyAction)


class SearchPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = ModrinthAPI()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_button = QtWidgets.QPushButton("Search")
        self.results_list = ModListWidget()
        self.results_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.search_button)
        layout.addWidget(self.results_list)

        self.search_button.clicked.connect(self.on_search)

    def on_search(self):
        query = self.search_edit.text().strip()
        self.results_list.clear()
        if not query:
            return
        for mod in self.api.search_mods(query):
            item = QtWidgets.QListWidgetItem(mod.get("title", "no title"))
            item.setToolTip(mod.get("description", ""))
            item.setData(QtCore.Qt.UserRole, mod)
            self.results_list.addItem(item)
