from os.path import join
from PySide6.QtCore import Qt, QDir, QItemSelectionModel
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QDockWidget, QTableWidget, QTableWidgetItem, QComboBox, QCheckBox, QTreeView, QFileSystemModel, QFileDialog, QAbstractItemView, QHeaderView, QListWidget, QAbstractItemView

from spritesheetz.objects import SpriteObjectOrigin

class ObjectPropertiesWidget(QDockWidget):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.obj = None

        self.objectPropertiesTable = QTableWidget(6, 2, self)
        self.objectPropertiesTable.setHorizontalHeaderLabels(['Property', 'Value'])
        self.objectPropertiesTable.verticalHeader().setVisible(False)
        self.objectPropertiesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.objectPropertiesTable.itemChanged.connect(self.itemChanged)

        nameTitleItem = QTableWidgetItem("Name")
        keyTitleItem = QTableWidgetItem("Key")
        typeTitleItem = QTableWidgetItem("Type")
        originTitleItem = QTableWidgetItem("Origin")
        shouldRenderTitleItem = QTableWidgetItem("Should Render")
        hasCollisionTitleItem = QTableWidgetItem("Has Collision")

        for row, item in enumerate([nameTitleItem, keyTitleItem, typeTitleItem, originTitleItem, shouldRenderTitleItem, hasCollisionTitleItem]):
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEditable))
            self.objectPropertiesTable.setItem(row, 0, item)

        self.setWidget(self.objectPropertiesTable)
        self.setFloating(False)

    def itemChanged(self, item):
        match item.type():
            case 11:
                self.obj.name = item.text()
            case 12:
                self.obj.key = item.text()
            case 13:
                self.obj.objType = item.text()

    def renderChanged(self, state):
        self.obj.renderTiles = Qt.CheckState(state) == Qt.CheckState.Checked

    def collisionChanged(self, state):
        self.obj.hasCollision = Qt.CheckState(state) == Qt.CheckState.Checked

    def originChanged(self, text):
        self.obj.originMode = self.originBox.currentData()

    def setObject(self, obj):
        self.obj = obj

        table = self.objectPropertiesTable

        nameItem = QTableWidgetItem(obj.name, 11)

        table.setItem(0, 1, nameItem)
        table.setItem(1, 1, QTableWidgetItem(obj.key, 12))
        table.setItem(2, 1, QTableWidgetItem(obj.objType, 13))

        originBox = QComboBox()
        originBox.addItem("Bottom Left", SpriteObjectOrigin.BOTTOM_LEFT)
        originBox.addItem("Top Left", SpriteObjectOrigin.TOP_LEFT)
        originBox.addItem("Bottom Right", SpriteObjectOrigin.BOTTOM_RIGHT)
        originBox.addItem("Top Right", SpriteObjectOrigin.TOP_RIGHT)
        originBox.setCurrentIndex(int(obj.originMode))
        originBox.currentTextChanged.connect(self.originChanged)

        self.originBox = originBox

        table.setCellWidget(3, 1, originBox)

        shouldRenderCheckbox = QCheckBox()
        if obj.renderTiles:
            shouldRenderCheckbox.setChecked(True)
        shouldRenderCheckbox.stateChanged.connect(self.renderChanged)

        hasCollisionCheckbox = QCheckBox()
        if obj.hasCollision:
            hasCollisionCheckbox.setChecked(True)
        hasCollisionCheckbox.stateChanged.connect(self.collisionChanged)

        table.setCellWidget(4, 1, shouldRenderCheckbox)
        table.setCellWidget(5, 1, hasCollisionCheckbox)

class SpriteSheetPropertiesWidget(QDockWidget):
    def __init__(self, name, parent, application):
        super().__init__(name, parent)

        self.application = application

        self.spriteSheetPropertiesTable = QTableWidget(8, 2, self)
        self.spriteSheetPropertiesTable.setHorizontalHeaderLabels(['Property', 'Value'])
        self.spriteSheetPropertiesTable.verticalHeader().setVisible(False)
        self.spriteSheetPropertiesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.spriteSheetPropertiesTable.itemChanged.connect(self.itemChanged)

        nameTitleItem = QTableWidgetItem("Name")
        spriteFilenameTitleItem = QTableWidgetItem("Sprite Filename")
        sheetWidthTitleItem = QTableWidgetItem("Sheet Width")
        sheetHeightTitleItem = QTableWidgetItem("Sheet Height")
        tileWidthTitleItem = QTableWidgetItem("Tile Width")
        tileHeightTitleItem = QTableWidgetItem("Tile Height")
        horizontalTilesTitleItem = QTableWidgetItem("Horizontal Tiles")
        verticalTilesTitleItem = QTableWidgetItem("Vertical Tiles")

        for row, item in enumerate([nameTitleItem, spriteFilenameTitleItem, sheetWidthTitleItem, sheetHeightTitleItem, tileWidthTitleItem, tileHeightTitleItem, horizontalTilesTitleItem, verticalTilesTitleItem]):
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEditable))
            self.spriteSheetPropertiesTable.setItem(row, 0, item)

        self.setWidget(self.spriteSheetPropertiesTable)
        self.setFloating(False)

    def setDetails(self, sheet):
        self.sheet = sheet

        nameItem = QTableWidgetItem(sheet.name, 11)
        spriteFilenameItem = QTableWidgetItem(sheet.spriteFilename, 12)
        sheetWidthItem = QTableWidgetItem(str(sheet.width), 13)
        sheetHeightItem = QTableWidgetItem(str(sheet.height), 14)
        tileWidthItem = QTableWidgetItem(str(sheet.tileWidth), 15)
        tileHeightItem = QTableWidgetItem(str(sheet.tileHeight), 16)
        horizontalTilesItem = QTableWidgetItem(str(sheet.horizontalTiles), 17)
        verticalTilesItem = QTableWidgetItem(str(sheet.verticalTiles), 18)


        self.spriteSheetPropertiesTable.setItem(0, 1, nameItem)

        for row, item in enumerate([spriteFilenameItem, sheetWidthItem, sheetHeightItem, tileWidthItem, tileHeightItem, horizontalTilesItem, verticalTilesItem]):
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEditable))
            self.spriteSheetPropertiesTable.setItem(row + 1, 1, item)

    def itemChanged(self, item):
        match item.type():
            case 11:
                self.sheet.name = item.text()
                if hasattr(self.application, 'workAreaWidget'):
                    tabWidget = self.application.workAreaWidget

                    tabWidget.setTabText(tabWidget.currentIndex(), item.text())

class ResourcesTreeView(QTreeView):
    def __init__(self, application):
        super().__init__()

        self.application = application

    def edit(self, index, trigger, event):
        if trigger == QAbstractItemView.DoubleClicked:
            # Prevent renaming files, double click to open the file instead in a tab
            self.application.triggerFile(join(QDir.currentPath(), index.data()))

            return False
        if trigger == QAbstractItemView.EditKeyPressed:
            return False
        return super().edit(index, trigger, event)

class ResourcesDockWidget(QDockWidget):
    def __init__(self, application, name, parent = None):
        super().__init__(name, parent)

        self.application = application

        model = QFileSystemModel()
        model.setNameFilters(['*.json'])
        model.setNameFilterDisables(False)
        model.setReadOnly(False)
        model.setRootPath(QDir.currentPath())
        tree = ResourcesTreeView(application)
        tree.setRootIsDecorated(False)
        tree.setModel(model)
        tree.setRootIndex(model.index(QDir.currentPath()))

        for i in range(1, model.columnCount()):
            tree.hideColumn(i)

        tree.setUniformRowHeights(True)

        self.tree = tree
        
        self.setWidget(tree)
        self.setFloating(False)

class MapPropertiesWidget(QDockWidget):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.obj = None

        self.objectPropertiesTable = QTableWidget(6, 2, self)
        self.objectPropertiesTable.setHorizontalHeaderLabels(['Property', 'Value'])
        self.objectPropertiesTable.verticalHeader().setVisible(False)
        self.objectPropertiesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.objectPropertiesTable.itemChanged.connect(self.itemChanged)

        nameTitleItem = QTableWidgetItem("Type")
        keyTitleItem = QTableWidgetItem("Key")
        typeTitleItem = QTableWidgetItem("Type")
        originTitleItem = QTableWidgetItem("Origin")
        shouldRenderTitleItem = QTableWidgetItem("Should Render")
        hasCollisionTitleItem = QTableWidgetItem("Has Collision")

        for row, item in enumerate([nameTitleItem, keyTitleItem, typeTitleItem, originTitleItem, shouldRenderTitleItem, hasCollisionTitleItem]):
            item.setFlags(item.flags() ^ (Qt.ItemIsSelectable | Qt.ItemIsEditable))
            self.objectPropertiesTable.setItem(row, 0, item)

        self.setWidget(self.objectPropertiesTable)
        self.setFloating(False)

    def itemChanged(self, item):
        match item.type():
            case 11:
                self.obj.name = item.text()
            case 12:
                self.obj.key = item.text()
            case 13:
                self.obj.objType = item.text()

    def renderChanged(self, state):
        self.obj.renderTiles = Qt.CheckState(state) == Qt.CheckState.Checked

    def collisionChanged(self, state):
        self.obj.hasCollision = Qt.CheckState(state) == Qt.CheckState.Checked

    def originChanged(self, text):
        self.obj.originMode = self.originBox.currentData()

    def setObject(self, obj):
        self.obj = obj

        table = self.objectPropertiesTable

        nameItem = QTableWidgetItem(obj.name, 11)

        table.setItem(0, 1, nameItem)
        table.setItem(1, 1, QTableWidgetItem(obj.key, 12))
        table.setItem(2, 1, QTableWidgetItem(obj.objType, 13))

        originBox = QComboBox()
        originBox.addItem("Bottom Left", SpriteObjectOrigin.BOTTOM_LEFT)
        originBox.addItem("Top Left", SpriteObjectOrigin.TOP_LEFT)
        originBox.addItem("Bottom Right", SpriteObjectOrigin.BOTTOM_RIGHT)
        originBox.addItem("Top Right", SpriteObjectOrigin.TOP_RIGHT)
        originBox.setCurrentIndex(int(obj.originMode))
        originBox.currentTextChanged.connect(self.originChanged)

        self.originBox = originBox

        table.setCellWidget(3, 1, originBox)

        shouldRenderCheckbox = QCheckBox()
        if obj.renderTiles:
            shouldRenderCheckbox.setChecked(True)
        shouldRenderCheckbox.stateChanged.connect(self.renderChanged)

        hasCollisionCheckbox = QCheckBox()
        if obj.hasCollision:
            hasCollisionCheckbox.setChecked(True)
        hasCollisionCheckbox.stateChanged.connect(self.collisionChanged)

        table.setCellWidget(4, 1, shouldRenderCheckbox)
        table.setCellWidget(5, 1, hasCollisionCheckbox)

class LayersDock(QDockWidget):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.layersList = QListWidget()
        self.layersList.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.layersList.addItem("ground")

        for index in range(self.layersList.count()):
            item = self.layersList.item(index)
            item.setFlags(item.flags() | Qt.ItemIsEditable)

            if index == 0:
                self.layersList.setCurrentItem(item)
        
        self.layersList.selectionModel().selectionChanged.connect(self.selectionChanged)
#myList->selectionModel()->            

        # Always keep selection even when blurred
        customPalette = QPalette()
        orginalPallete = self.layersList.palette()
        #customPalette.setBrush(QPalette.Inactive, QPalette.Highlight, orginalPallete.brush(QPalette.Active, QPalette.Highlight))
        customPalette.setColor(QPalette.Inactive, QPalette.Highlight, orginalPallete.color(QPalette.Active, QPalette.Highlight))
        customPalette.setColor(QPalette.Inactive, QPalette.HighlightedText, orginalPallete.color(QPalette.Active, QPalette.HighlightedText))
        self.layersList.setPalette(customPalette)

        self.setWidget(self.layersList)

    def selectionChanged(self, selected, deselected):
        # Prevent nothing being selected
        if len(selected) == 0:
            if len(deselected) > 0:
                self.layersList.selectionModel().select(deselected, QItemSelectionModel.Select)
            else:
                self.layersList.selectionModel().select(0, QItemSelectionModel.Select)
                