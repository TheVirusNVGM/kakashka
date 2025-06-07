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


class ModCard(QtWidgets.QFrame):
    def __init__(self, mod: dict, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.mod = mod
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame {"
            "background-color: #2a2a2a;"
            "border-radius: 8px;"
            "padding: 6px;"
            "}"
            "QFrame:hover {"
            "background-color: #333;"
            "}"
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setStyleSheet("border-radius:6px;")
        layout.addWidget(self.icon_label)

        text_layout = QtWidgets.QVBoxLayout()
        self.title_label = QtWidgets.QLabel(mod.get("title", ""))
        title_font = self.title_label.font()
        title_font.setBold(True)
        title_font.setPointSizeF(title_font.pointSizeF() * 1.1)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #f0f0f0;")

        self.desc_label = QtWidgets.QLabel(mod.get("description", ""))
        self.desc_label.setWordWrap(True)
        line_h = self.desc_label.fontMetrics().lineSpacing()
        self.desc_label.setFixedHeight(line_h * 2 + 4)
        self.desc_label.setStyleSheet("color: #cccccc;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)
        layout.addLayout(text_layout)

        icon_url = mod.get("icon_url")
        if icon_url:
            try:
                r = requests.get(icon_url)
                r.raise_for_status()
                buffer = BytesIO(r.content)
                pix = QtGui.QPixmap()
                pix.loadFromData(buffer.read())
                if not pix.isNull():
                    pix = pix.scaled(48, 48, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
                    self.icon_label.setPixmap(pix)
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

        self.filter_box = QtWidgets.QGroupBox("Filters")
        self.filter_box.setCheckable(True)
        self.filter_box.setChecked(False)
        filter_inner = QtWidgets.QWidget()
        filter_layout = QtWidgets.QHBoxLayout(filter_inner)

        version_group = QtWidgets.QGroupBox("Minecraft Versions")
        vg_layout = QtWidgets.QVBoxLayout(version_group)
        ver_scroll = QtWidgets.QScrollArea()
        ver_scroll.setWidgetResizable(True)
        ver_widget = QtWidgets.QWidget()
        ver_layout = QtWidgets.QVBoxLayout(ver_widget)
        for ver in self.generate_versions():
            cb = QtWidgets.QCheckBox(ver)
            ver_layout.addWidget(cb)
            self.version_checks.append(cb)
        ver_layout.addStretch()
        ver_scroll.setWidget(ver_widget)
        vg_layout.addWidget(ver_scroll)

        loader_group = QtWidgets.QGroupBox("Loaders")
        lg_layout = QtWidgets.QVBoxLayout(loader_group)
        for loader in ["fabric", "forge", "quilt", "neoforge"]:
            cb = QtWidgets.QCheckBox(loader)
            lg_layout.addWidget(cb)
            self.loader_checks.append(cb)
        lg_layout.addStretch()

        filter_layout.addWidget(version_group)
        filter_layout.addWidget(loader_group)

        box_layout = QtWidgets.QVBoxLayout(self.filter_box)
        box_layout.addWidget(filter_inner)
        filter_inner.setVisible(False)
        self.filter_box.toggled.connect(filter_inner.setVisible)

        layout.addWidget(self.filter_box)
        search_row = QtWidgets.QHBoxLayout()
        search_row.addWidget(self.search_edit)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)
        layout.addWidget(self.results_list)

        self.search_button.clicked.connect(self.on_search)

    @staticmethod
    def generate_versions() -> list[str]:
        from decimal import Decimal
        v = Decimal("21.5")
        versions = []
        while v >= 1:
            s = str(v.normalize())
            if s.endswith(".0"):
                s = s[:-2]
            versions.append(f"1.{s}")
            v -= Decimal("0.1")
        versions.append("1.0")
        return versions

    def on_search(self):
        query = self.search_edit.text().strip()
        self.results_list.clear()
        if not query:
            return
        versions = [cb.text() for cb in self.version_checks if cb.isChecked()]
        loaders = [cb.text() for cb in self.loader_checks if cb.isChecked()]
        for mod in self.api.search_mods(query, versions=versions, loaders=loaders):
            item = QtWidgets.QListWidgetItem()
            widget = ModCard(mod)
            item.setSizeHint(widget.sizeHint())
            item.setData(QtCore.Qt.UserRole, mod)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)
