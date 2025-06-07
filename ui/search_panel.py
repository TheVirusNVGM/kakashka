from PySide6 import QtCore, QtGui, QtWidgets
from modrinth_api import ModrinthAPI
import requests
from io import BytesIO


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


class ModListItemWidget(QtWidgets.QWidget):
    def __init__(self, mod: dict, parent=None):
        super().__init__(parent)
        self.mod = mod
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(32, 32)
        layout.addWidget(self.icon_label)

        text_layout = QtWidgets.QVBoxLayout()
        self.title_label = QtWidgets.QLabel(mod.get("title", ""))
        self.title_label.setStyleSheet("font-weight: bold")
        self.desc_label = QtWidgets.QLabel(mod.get("description", ""))
        self.desc_label.setWordWrap(True)
        self.desc_label.setFixedWidth(200)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)
        layout.addLayout(text_layout)

        icon_url = mod.get("icon_url")
        if icon_url:
            try:
                r = requests.get(icon_url)
                pix = QtGui.QPixmap()
                pix.loadFromData(r.content)
                self.icon_label.setPixmap(pix.scaled(32, 32, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
            except Exception:
                pass


class SearchPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = ModrinthAPI()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_button = QtWidgets.QPushButton("Search")
        self.results_list = ModListWidget()
        self.version_checks: list[QtWidgets.QCheckBox] = []
        self.loader_checks: list[QtWidgets.QCheckBox] = []
        self.results_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(True)

        layout = QtWidgets.QVBoxLayout(self)

        filter_layout = QtWidgets.QHBoxLayout()
        version_group = QtWidgets.QGroupBox("Versions")
        v_layout = QtWidgets.QHBoxLayout(version_group)
        for ver in ["1.21.5", "1.20.6", "1.20.5", "1.20.4", "1.19.4"]:
            cb = QtWidgets.QCheckBox(ver)
            v_layout.addWidget(cb)
            self.version_checks.append(cb)
        loader_group = QtWidgets.QGroupBox("Loaders")
        l_layout = QtWidgets.QHBoxLayout(loader_group)
        for loader in ["fabric", "forge", "quilt", "neoforge"]:
            cb = QtWidgets.QCheckBox(loader)
            l_layout.addWidget(cb)
            self.loader_checks.append(cb)
        filter_layout.addWidget(version_group)
        filter_layout.addWidget(loader_group)

        layout.addLayout(filter_layout)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.search_button)
        layout.addWidget(self.results_list)

        self.search_button.clicked.connect(self.on_search)

    def on_search(self):
        query = self.search_edit.text().strip()
        self.results_list.clear()
        if not query:
            return
        versions = [cb.text() for cb in self.version_checks if cb.isChecked()]
        loaders = [cb.text() for cb in self.loader_checks if cb.isChecked()]
        for mod in self.api.search_mods(query, versions=versions, loaders=loaders):
            item = QtWidgets.QListWidgetItem()
            widget = ModListItemWidget(mod)
            item.setSizeHint(widget.sizeHint())
            item.setData(QtCore.Qt.UserRole, mod)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)
