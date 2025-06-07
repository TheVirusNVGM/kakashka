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

    def to_model(self) -> Mod:
        self.mod.x = self.scenePos().x()
        self.mod.y = self.scenePos().y()
        return self.mod


class CategoryItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, category: Category, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.setRect(0, 0, category.width, category.height)
        self.setBrush(QtGui.QColor(60, 60, 60, 100))
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

    def add_category(self, name="Category"):
        cat = Category(name=name)
        item = CategoryItem(cat)
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


