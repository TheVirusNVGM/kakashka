from PySide6 import QtCore, QtGui, QtWidgets
from models import Mod, Category


class NodeItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, mod: Mod, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mod = mod
        self.setRect(0, 0, 120, 40)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.text = QtWidgets.QGraphicsTextItem(mod.title, self)
        self.text.setPos(5, 5)

    def expand_to_fit(self, item: QtWidgets.QGraphicsItem):
        rect = self.rect()
        child_rect = item.mapRectToParent(item.boundingRect())
        needed = rect.united(child_rect.adjusted(0, 0, 20, 20))
        self.setRect(0, 0, needed.width(), needed.height())

    def to_model(self) -> Mod:
        self.mod.x = self.scenePos().x()
        self.mod.y = self.scenePos().y()
        return self.mod


class CategoryItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, category: Category, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.setRect(0, 0, category.width, category.height)
        color = QtGui.QColor(category.color)
        color.setAlpha(100)
        self.setBrush(color)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.text = QtWidgets.QGraphicsTextItem(category.name, self)
        self.text.setDefaultTextColor(QtGui.QColor("white"))
        self.text.setPos(5, 5)

    def to_model(self) -> Category:
        self.category.x = self.scenePos().x()
        self.category.y = self.scenePos().y()
        self.category.width = self.rect().width()
        self.category.height = self.rect().height()
        self.category.color = self.brush().color().name()
        # collect mods inside
        self.category.mods = []
        for item in self.childItems():
            if isinstance(item, NodeItem):
                self.category.mods.append(item.to_model())
        return self.category


class BoardScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setBackgroundBrush(QtGui.QColor("#1e1e1e"))

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-mod"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasFormat("application/x-mod"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent):
        if event.mimeData().hasFormat("application/x-mod"):
            data = event.mimeData().data("application/x-mod").data().decode()
            mod_dict = eval(data)  # simple; assume safe
            mod = Mod(
                slug=mod_dict.get("slug", ""),
                title=mod_dict.get("title", ""),
                description=mod_dict.get("description", ""),
                author=mod_dict.get("author", ""),
                version=mod_dict.get("versions", ["unknown"])[0],
                url=f"https://modrinth.com/mod/{mod_dict.get('slug')}"
            )
            pos = event.scenePos()
            item = NodeItem(mod)
            target = self.itemAt(pos, QtGui.QTransform())
            parent_cat = None
            while target and not isinstance(target, CategoryItem):
                target = target.parentItem()
            if isinstance(target, CategoryItem):
                parent_cat = target
            if parent_cat:
                item.setParentItem(parent_cat)
                item.setPos(parent_cat.mapFromScene(pos))
                parent_cat.expand_to_fit(item)
                self.addItem(item)
            else:
                item.setPos(pos)
                self.addItem(item)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class BoardView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(BoardScene(self))
        self.setRenderHints(QtGui.QPainter.Antialiasing)
        self.setAcceptDrops(True)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        pos = self.mapToScene(event.pos())
        item = self.scene().itemAt(pos, QtGui.QTransform())
        if item is None:
            menu = QtWidgets.QMenu(self)
            act = menu.addAction("\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044e")
            chosen = menu.exec(event.globalPos())
            if chosen is act:
                self.create_category_dialog(pos)
        else:
            super().contextMenuEvent(event)

    def create_category_dialog(self, pos=None):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("\u041d\u043e\u0432\u0430\u044f \u043a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f")
        layout = QtWidgets.QFormLayout(dialog)
        name_edit = QtWidgets.QLineEdit()
        color_btn = QtWidgets.QPushButton()
        color = QtGui.QColor("#3c3c3c")

        def choose_color():
            nonlocal color
            c = QtWidgets.QColorDialog.getColor(color, self)
            if c.isValid():
                color = c
                color_btn.setStyleSheet(f"background:{c.name()}")

        color_btn.clicked.connect(choose_color)
        color_btn.setStyleSheet(f"background:{color.name()}")
        layout.addRow("Name", name_edit)
        layout.addRow("Color", color_btn)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addRow(buttons)

        def accept():
            dialog.accept()

        buttons.accepted.connect(accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() == QtWidgets.QDialog.Accepted and name_edit.text().strip():
            self.add_category(name_edit.text().strip(), color.name(), pos)

    def add_category(self, name="Category", color="#3c3c3c", pos=None):
        cat = Category(name=name, color=color)
        item = CategoryItem(cat)
        if pos:
            item.setPos(pos)
        else:
            item.setPos(0, 0)
        self.scene().addItem(item)
        return item

    def to_models(self):
        categories = []
        for item in self.scene().items():
            if isinstance(item, CategoryItem):
                categories.append(item.to_model())
        return categories

    def load_from_models(self, categories):
        self.scene().clear()
        for cat in categories:
            cat_item = CategoryItem(cat)
            cat_item.setPos(cat.x, cat.y)
            self.scene().addItem(cat_item)

            for mod in cat.mods:
                node = NodeItem(mod)
                node.setParentItem(cat_item)
                node.setPos(mod.x, mod.y)
                cat_item.expand_to_fit(node)


