from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QAction
from .search_panel import SearchPanel
from .board import BoardView
from storage import save_schema, load_schema


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modpack Designer")
        self.resize(1200, 800)

        self.board = BoardView()
        self.search_panel = SearchPanel()

        central = QtWidgets.QSplitter()
        central.addWidget(self.search_panel)
        central.addWidget(self.board)
        central.setStretchFactor(1, 1)
        self.setCentralWidget(central)

        toolbar = self.addToolBar("Main")
        add_cat = QAction("Add Category", self)
        save_act = QAction("Save", self)
        load_act = QAction("Load", self)
        toolbar.addAction(add_cat)
        toolbar.addAction(save_act)
        toolbar.addAction(load_act)

        add_cat.triggered.connect(self.add_category)
        save_act.triggered.connect(self.save)
        load_act.triggered.connect(self.load)

    def add_category(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Category name", "Name:")
        if ok and name:
            self.board.add_category(name)

    def save(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save", filter="JSON Files (*.json)")
        if path:
            save_schema(self.board.to_models(), path)

    def load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load", filter="JSON Files (*.json)")
        if path:
            cats = load_schema(path)
            self.board.load_from_models(cats)

