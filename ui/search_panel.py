from PySide6 import QtCore, QtGui, QtWidgets
from modrinth_api import ModrinthAPI
import requests
import math
from deep_translator import GoogleTranslator


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
        self.setFixedHeight(80)
        self.setStyleSheet(
            "QFrame { background-color: #2a2a2a; border-radius: 8px; padding: 6px; margin-bottom: 6px; }"
            "QFrame:hover { background-color: #333; }"
        )

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        layout.setAlignment(QtCore.Qt.AlignVCenter)

        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(64, 64)
        self.icon_label.setStyleSheet("border-radius:4px;")
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QtWidgets.QLabel(mod.get("title", ""))
        title_font = self.title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(15)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #f0f0f0; margin-bottom: 2px;")

        desc = mod.get("description", "")
        self.desc_label = QtWidgets.QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #cccccc;")
        self.desc_label.setMaximumWidth(400)
        fm = self.desc_label.fontMetrics()
        self.desc_label.setFixedHeight(fm.lineSpacing() * 2)
        elided = fm.elidedText(
            desc, QtCore.Qt.ElideRight, self.desc_label.maximumWidth() * 2
        )
        self.desc_label.setText(elided)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch()
        layout.addLayout(text_layout)

        icon_url = mod.get("icon_url")
        if icon_url:
            try:
                r = requests.get(icon_url)
                r.raise_for_status()
                pix = QtGui.QPixmap()
                pix.loadFromData(r.content)
                pix = pix.scaled(
                    64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
                )
                self.icon_label.setPixmap(pix)
            except Exception:
                pass


class Worker(QtCore.QObject, QtCore.QRunnable):
    finished = QtCore.Signal(object)

    def __init__(self, fn, *args, callback=None):
        QtCore.QObject.__init__(self)
        QtCore.QRunnable.__init__(self)
        self.fn = fn
        self.args = args
        if callback:
            self.finished.connect(callback)

    @QtCore.Slot()
    def run(self):
        result = self.fn(*self.args)
        self.finished.emit(result)


class SearchPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = ModrinthAPI()
        self.search_edit = QtWidgets.QLineEdit()
        self.search_button = QtWidgets.QPushButton("Поиск")
        self.results_list = ModListWidget()
        self.version_checks: list[QtWidgets.QCheckBox] = []
        self.loader_checks: list[QtWidgets.QCheckBox] = []
        self.page = 0
        self.page_size = 10
        self.mods: list[dict] = []
        self.progress = QtWidgets.QProgressDialog(
            "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430\u2026", None, 0, 0, self
        )
        self.progress.setCancelButton(None)
        self.progress.setWindowModality(QtCore.Qt.ApplicationModal)

        self.results_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.results_list.setDragEnabled(True)

        layout = QtWidgets.QVBoxLayout(self)

        self.filter_box = QtWidgets.QGroupBox("Фильтры")
        self.filter_inner = QtWidgets.QWidget()
        filter_layout = QtWidgets.QHBoxLayout(self.filter_inner)

        version_group = QtWidgets.QGroupBox("Версии Minecraft")
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

        loader_group = QtWidgets.QGroupBox("Загрузчики")
        lg_layout = QtWidgets.QVBoxLayout(loader_group)
        for loader in ["fabric", "forge", "quilt", "neoforge"]:
            cb = QtWidgets.QCheckBox(loader)
            lg_layout.addWidget(cb)
            self.loader_checks.append(cb)
        lg_layout.addStretch()

        filter_layout.addWidget(version_group)
        filter_layout.addWidget(loader_group)

        toggle_row = QtWidgets.QHBoxLayout()
        self.filter_toggle = QtWidgets.QToolButton()
        self.filter_toggle.setArrowType(QtCore.Qt.RightArrow)
        self.filter_toggle.setCheckable(True)
        toggle_row.addWidget(self.filter_toggle)
        toggle_row.addWidget(QtWidgets.QLabel("Фильтры"))
        toggle_row.addStretch()

        box_layout = QtWidgets.QVBoxLayout(self.filter_box)
        box_layout.addLayout(toggle_row)
        box_layout.addWidget(self.filter_inner)
        self.filter_inner.setVisible(False)
        self.filter_toggle.toggled.connect(self.filter_inner.setVisible)
        self.filter_toggle.toggled.connect(
            lambda ch: self.filter_toggle.setArrowType(
                QtCore.Qt.DownArrow if ch else QtCore.Qt.RightArrow
            )
        )

        layout.addWidget(self.filter_box)

        search_row = QtWidgets.QHBoxLayout()
        search_row.addWidget(self.search_edit)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)
        layout.addWidget(self.results_list)

        pag_row = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton("<")
        self.page_label = QtWidgets.QLabel("1/1")
        self.next_btn = QtWidgets.QPushButton(">")
        pag_row.addStretch()
        pag_row.addWidget(self.prev_btn)
        pag_row.addWidget(self.page_label)
        pag_row.addWidget(self.next_btn)
        pag_row.addStretch()
        layout.addLayout(pag_row)

        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)

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
        self.page = 0
        if not query:
            self.mods = []
            self.display_page()
            return
        versions = [cb.text() for cb in self.version_checks if cb.isChecked()]
        loaders = [cb.text() for cb in self.loader_checks if cb.isChecked()]

        worker = Worker(
            self.api.search_mods,
            query,
            100,
            versions,
            loaders,
            callback=self._on_search_finished,
        )
        QtCore.QThreadPool.globalInstance().start(worker)
        self.search_button.setEnabled(False)
        self.progress.show()

    def _on_search_finished(self, result):
        self.progress.hide()
        self.search_button.setEnabled(True)
        if isinstance(result, list):
            self.mods = result
        else:
            self.mods = []
        self.display_page()

    def display_page(self):
        self.results_list.clear()
        start = self.page * self.page_size
        end = start + self.page_size
        subset = self.mods[start:end]
        for mod in subset:
            desc = mod.get("description", "")
            if desc:
                try:
                    desc = GoogleTranslator(source="en", target="ru").translate(desc)
                except Exception:
                    pass
            card_mod = mod.copy()
            card_mod["description"] = desc
            item = QtWidgets.QListWidgetItem()
            widget = ModCard(card_mod)
            item.setSizeHint(widget.sizeHint())
            item.setData(QtCore.Qt.UserRole, mod)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)
        self.update_page_label()

    def update_page_label(self):
        total = max(1, math.ceil(len(self.mods) / self.page_size))
        self.page_label.setText(f"{self.page + 1}/{total}")
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page < total - 1)

    def next_page(self):
        total = math.ceil(len(self.mods) / self.page_size)
        if self.page < total - 1:
            self.page += 1
            self.display_page()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.display_page()
