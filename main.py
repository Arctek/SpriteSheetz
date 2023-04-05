from PySide6.QtCore import QSize, Qt, QRectF, QPoint, QPointF, QDir, QSettings, QByteArray
from PySide6.QtGui import QTransform, QPen, QBrush, QColor, QAction, QPixmap
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QDockWidget, QListWidget, QTextEdit, QGraphicsScene, QGraphicsView, QFrame, QGraphicsSceneMouseEvent, QTabWidget, QToolBar, QGraphicsPixmapItem, QMenu, QTableWidget, QHeaderView, QTableWidgetItem, QComboBox, QCheckBox, QTreeView, QFileSystemModel, QFileDialog, QMessageBox

# Only needed for access to command line arguments
import sys
from enum import Enum, IntEnum
from math import ceil
from os.path import basename
import json

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

class WorkAreaType(IntEnum):
    MAP = 0
    SPRITE_SHEET = 1

class SpriteObjectOrigin(IntEnum):
    BOTTOM_LEFT = 0
    TOP_LEFT = 1
    BOTTOM_RIGHT = 2
    TOP_RIGHT = 3

class HitBoxType(IntEnum):
    RECT = 0
    ELLIPSE = 1
    POLYGON = 2

class SpriteItem:
    def __init__(self, view, rect, brush):
        self.rect = rect
        self.brush = brush
        self.view = view
        self.graphicsItem = None

        self.addToView()

    def addToView(self):
        self.graphicsItem = self.view.addRect(self.rect, QPen(Qt.black, 0), self.brush)

    def removeFromView(self):
        if self.graphicsItem:
            self.view.removeItem(self.graphicsItem)
            self.graphicsItem = None

class HitBox:
    def __init__(self, hitBoxType = HitBoxType.RECT):
        self.hitBoxType = hitBoxType
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.shape = None

    def asdict(self):
        return {
            'type': self.hitBoxType,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'shape': self.shape
        }

    @staticmethod
    def fromdict(obj):
        return HitBox()

class SpriteObject:
    def __init__(self,
                 name,
                 key = None,
                 objType = None,
                 tiles = [],
                 originMode = SpriteObjectOrigin.BOTTOM_LEFT,
                 renderTiles = True,
                 hasCollision = False,
                 extraProperties = {}):
        self.name = name

        if key is None:
           key = lower(name).replace(' ', '_')

        self.key = key
        self.objType = objType
        self.tiles = tiles
        self.originMode = originMode
        self.renderTiles = renderTiles
        self.hasCollision = hasCollision
        if self.hasCollision:
            self.hitBox = HitBox()

        self.extraProperties = extraProperties

    def asdict(self):
        data = {
            'name': self.name,
            'key': self.key,
            'type': self.objType,
            'tiles': self.tiles,
            'originMode': int(self.originMode),
            'renderTiles': self.renderTiles,
            'hasCollision': self.hasCollision
        }

        if self.hasCollision:
            data['hitbox'] = self.hitBox.asdict()

        return data

    @staticmethod
    def fromdict(obj):
        return SpriteObject(name = obj['name'],
                            key = obj['key'],
                            objType = obj['type'],
                            tiles = obj['tiles'],
                            originMode = SpriteObjectOrigin(obj['originMode']),
                            renderTiles = obj['renderTiles'],
                            hasCollision = obj['hasCollision'])


class GraphicsView(QGraphicsView):
    def __init__(self, application, scene):
        super().__init__(scene)
        self.application = application

        # Need this so all mouse move events are tracked
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)

    def wheelEvent(self, event):
        if self.application.controlHeld:
            """
            Zoom in or out of the view.
            """
            zoomInFactor = 1.25
            zoomOutFactor = 1 / zoomInFactor

            pointF = event.position()
            point = QPoint(int(pointF.x()), int(pointF.y()))

            # Save the scene pos
            oldPos = self.mapToScene(point)

            # Zoom
            if event.angleDelta().y() > 0:
                zoomFactor = zoomInFactor
            else:
                zoomFactor = zoomOutFactor
            self.scale(zoomFactor, zoomFactor)

            # Get the new position
            newPos = self.mapToScene(point)

            # Move scene to old position
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())
        else:
            super().wheelEvent(event)

class SpriteSheetView(GraphicsView):
    def __init__(self, application, scene):
        super().__init__(application, scene)

        #self.setContextMenuPolicy(Qt.ActionsContextMenu)
        #self.addAction("Test")

class MapScene(QGraphicsScene):
    def __init__(self, application):
        super().__init__()

        self.application = application

        self.mouseDown = False
        self.gridItems = None
        self.selectedGridItems = None

        self.gridPen = QPen(Qt.black, 1, Qt.DashLine)
        self.rectPen = QPen(Qt.black, 0)

        self.gridLines = []

        #rect = self.addRect(QRectF(0, 0, 100, 100), gridOutline, QBrush(Qt.green))
        #item = self.itemAt(50, 50, QTransform())

        #self.setMouseTracking(True)

        self.setBackgroundBrush(QBrush(QColor(220,220,220)))        

        self.createGrid()

        self.gridTurtle = self.addRect(QRectF(0, 0, self.size, self.size), QPen(Qt.blue, 0), QBrush(QColor(0,0,255, 75)))
        self.gridTurtle.setZValue(100) #always on top

    def removeGridLines(self):
        if len(self.gridLines):
            for line in self.gridLines:
                self.removeItem(line)

            self.gridLines = []

    def createGrid(self):
        self.rows = 50
        self.cols = 50
        self.size = 102 # extra 1 either side for borders
        endPoint = self.rows * self.size

        if len(self.gridLines):
            for line in self.gridLines:
                self.removeItem(line)

            self.gridLines = []

        if not self.gridItems:
            self.gridItems = [[None for col in range(self.cols)] for row in range(self.rows)]
            self.selectedGridItems = [[None for col in range(self.cols)] for row in range(self.rows)]

        if self.application.showGrid:
            # vertical lines
            for i in range(0, self.cols + 1):
                x = i * self.size
                self.gridLines.append(self.addLine(x, 0, x, endPoint, self.gridPen))

            # horizontal lines
            for i in range(0, self.rows + 1):
                y = i * self.size
                self.gridLines.append(self.addLine(0, y, endPoint, y, self.gridPen))

    def saveState(self):
        return {}

    def fillGridItemCoordinates(self, x, y):
        #print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY] is None:
            leftPos = gridItemX * self.size
            topPos = gridItemY * self.size

            self.gridItems[gridItemX][gridItemY] = SpriteItem(self,
                                                              QRectF(leftPos, topPos, self.size, self.size), 
                                                              QBrush(Qt.green))

    def clearGridItemCoordinates(self, x, y):
        #print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY]:
            spriteItem = self.gridItems[gridItemX][gridItemY]
            
            spriteItem.removeFromView()
            # Need to set data here
            self.gridItems[gridItemX][gridItemY] = None

    def selectGridItemCoordinates(self, x, y):
        #print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY]:
            if self.selectedGridItems[gridItemX][gridItemY] is None:
                #spriteItem = self.gridItems[gridItemX][gridItemY]
                leftPos = gridItemX * self.size
                topPos = gridItemY * self.size
            
                # Need to set data here
                self.selectedGridItems[gridItemX][gridItemY] = self.addRect(QRectF(leftPos, topPos, self.size, self.size), QPen(Qt.blue, 0), QBrush(QColor(0,0,255, 75)))
            else:
                # deselect
                self.removeItem(self.selectedGridItems[gridItemX][gridItemY])
                self.selectedGridItems[gridItemX][gridItemY] = None

    def deletePress(self):
        for index_x, x in enumerate(self.selectedGridItems):
            for index_y, cell in enumerate(self.selectedGridItems[index_x]):
                if not cell is None:
                    self.removeItem(cell)
                    self.selectedGridItems[index_x][index_y] = None

                    if self.gridItems[index_x][index_y]:
                        self.gridItems[index_x][index_y].removeFromView()
                        self.gridItems[index_x][index_y] = None

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        print("mousePressEvent")
        pos = e.scenePos()
        x = pos.x()
        y = pos.y()
        button = e.button()

        if button == Qt.MouseButton.LeftButton:
            self.mouseDown = True

            if self.application.controlHeld:
                self.clearGridItemCoordinates(x, y)
            else:
                self.fillGridItemCoordinates(x, y)
        elif button == Qt.MouseButton.MiddleButton:
            self.selectGridItemCoordinates(x, y)

    def moveGridTurtle(self, x, y):
        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if gridItemX < 0:
            gridItemX = 0
        elif gridItemX >= self.rows:
            gridItemX = self.rows - 1

        if gridItemY < 0:
            gridItemY = 0
        elif gridItemY >= self.cols:
            gridItemY = self.cols - 1

        self.gridTurtle.setPos(QPointF(float(gridItemX * self.size), float(gridItemY * self.size)))
        #print(f"Moved to {gridItemX}x{gridItemY}", flush=True)

        
    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        pos = e.scenePos()
        x = pos.x()
        y = pos.y()

        self.moveGridTurtle(x, y)

        if self.mouseDown:
            if self.application.controlHeld:
                self.clearGridItemCoordinates(x, y)
            else:
                self.fillGridItemCoordinates(x, y)


    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        self.mouseDown = False

class SpriteSheetScene(QGraphicsScene):
    def __init__(self, parent, application):
        super().__init__()

        self.parent = parent
        self.application = application

        self.mouseDown = False
        self.gridItems = None
        self.selectedGridItems = None
        self.size = 101 # extra 1 either side for borders
        self.tileWidth = 16
        self.tileHeight = 16

        self.name = "Untitled sprite sheet"

        self.gridPen = QPen(Qt.black, 1, Qt.DashLine)
        self.rectPen = QPen(Qt.black, 0)

        self.gridLines = []
        self.fileName = ""

        #rect = self.addRect(QRectF(0, 0, 100, 100), gridOutline, QBrush(Qt.green))
        #item = self.itemAt(50, 50, QTransform())

        #self.setMouseTracking(True)

        self.setBackgroundBrush(QBrush(QColor(220,220,220)))        

        self.gridTurtle = self.addRect(QRectF(0, 0, self.size, self.size), QPen(Qt.blue, 0), QBrush(QColor(0,0,255, 75)))
        self.gridTurtle.setZValue(100) #always on top

        self.tilesToObjectAction = QAction("Tile/s to object", self)
        self.tilesToObjectAction.triggered.connect(self.tilesToObject)

    def saveState(self):
        stateData = {
            'name': self.name,
            'type': 'sheet',
            'spriteFile': self.spriteFile,
            'tileWidth': self.tileWidth,
            'tileHeight': self.tileHeight,
            'width': self.width,
            'height': self.height,
            'items': {}
        }

        for obj in self.objects:
            obj_dict = obj.asdict()
            stateData['items'][obj_dict['key']] = obj_dict

        return stateData

    def restoreState(self, state):
        self.name = state['name']
        self.loadSpriteSheetFromImageFile(state['spriteFile'])

        for key in state['items']:
            self.objects.append(SpriteObject.fromdict(state['items'][key]))

    def saveFile(self, saveAs = False):
        fileData = self.saveState()

        if self.fileName == '' or saveAs:
            fileName, _ = QFileDialog.getSaveFileName(self.application, 'Save Sprite Sheet', filter='*.json')
        else:
            fileName = self.fileName

        if fileName:
            self.fileName = fileName

            with open(fileName, 'w') as file:
                file.write(json.dumps(fileData, indent=4))

            print(fileData, flush=True)
            print(fileName, flush=True)

    def loadSpriteSheetFromImageFile(self, filePath):
        self.spriteFile = filePath
        self.spriteFilename = basename(filePath)
        masterPixmap = QPixmap(filePath)
        self.masterPixmap = masterPixmap

        width = masterPixmap.width()
        height = masterPixmap.height()

        self.width = width
        self.height = height

        self.horizontalTiles = ceil(self.width / self.tileWidth)
        self.verticalTiles = ceil(self.width / self.tileWidth)
        self.tiles = [[None for col in range(self.verticalTiles)] for row in range(self.horizontalTiles)]
        self.objects = []
        self.objectSelected = False

        for x, row in enumerate(range(self.horizontalTiles)):
            for y, col in enumerate(range(self.verticalTiles)):
                copy_x = x * self.tileWidth
                copy_y = y * self.tileHeight
                # copy + scale
                pixmap = masterPixmap.copy(copy_x, copy_y, self.tileWidth, self.tileHeight).scaled(self.size - 2, self.size - 2)
                pixmapItem = QGraphicsPixmapItem(pixmap)

                # placement
                x_pos = 1 + (x * (self.size))
                y_pos = 1 + (y * (self.size))

                pixmapItem.setOffset(x_pos, y_pos)
                self.tiles[x][y] = [pixmap, pixmapItem]
                self.addItem(pixmapItem)

        self.parent.propertiesDock.setDetails(self)
        self.createGrid()

    def test(self):
        print("trigger context", flush=True)

    def removeGridLines(self):
        if len(self.gridLines):
            for line in self.gridLines:
                self.removeItem(line)

            self.gridLines = []

    def createGrid(self):
        self.rows = self.horizontalTiles
        self.cols = self.verticalTiles
        
        endPoint = self.rows * self.size

        if len(self.gridLines):
            for line in self.gridLines:
                self.removeItem(line)

            self.gridLines = []

        if not self.gridItems:
            self.gridItems = [[None for col in range(self.cols)] for row in range(self.rows)]
            self.selectedGridItems = [[None for col in range(self.cols)] for row in range(self.rows)]

        if self.application.showGrid:
            # vertical lines
            for i in range(0, self.cols + 1):
                x = i * self.size
                self.gridLines.append(self.addLine(x, 0, x, endPoint, self.gridPen))

            # horizontal lines
            for i in range(0, self.rows + 1):
                y = i * self.size
                self.gridLines.append(self.addLine(0, y, endPoint, y, self.gridPen))

    def fillGridItemCoordinates(self, x, y):
        #print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY] is None:
            leftPos = gridItemX * self.size
            topPos = gridItemY * self.size

            self.gridItems[gridItemX][gridItemY] = SpriteItem(self,
                                                              QRectF(leftPos, topPos, self.size, self.size), 
                                                              QBrush(Qt.green))

    def clearGridItemCoordinates(self, x, y):
        #print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY]:
            spriteItem = self.gridItems[gridItemX][gridItemY]
            
            spriteItem.removeFromView()
            # Need to set data here
            self.gridItems[gridItemX][gridItemY] = None

    def selectGridItemCoordinates(self, x, y, shouldDeselect = True):
        #print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if x < 0 or y < 0 or gridItemX >= self.horizontalTiles or gridItemY >= self.verticalTiles:
            return

        # check if object exists at coordinates
        foundObject = False

        #self.saveFile()

        if len(self.objects):
            for obj in self.objects:
                for tile in obj.tiles:
                    if tile[0] == gridItemX and tile[1] == gridItemY:
                        foundObject = True

                        startX = obj.tiles[0][0]
                        startY = obj.tiles[0][1]

                        endX = obj.tiles[-1][0]
                        endY = obj.tiles[-1][1]

                        leftPos = startX * self.size
                        topPos = startY * self.size

                        width = (endX - startX + 1) * self.size
                        height = (endY - startY + 1) * self.size

                        self.unselectAll()

                        self.selectedGridItems[startX][startY] = self.addRect(QRectF(leftPos, topPos, width, height), QPen(Qt.yellow, 0), QBrush(QColor(255,255,0, 75)))

                        self.objectSelected = True
                        self.parent.objectPropertiesDock.setObject(obj)

                        break

        if not foundObject and self.tiles[gridItemX][gridItemY]:

            if self.objectSelected:
                self.unselectAll()

            if self.selectedGridItems[gridItemX][gridItemY] is None:
                #spriteItem = self.gridItems[gridItemX][gridItemY]
                leftPos = gridItemX * self.size
                topPos = gridItemY * self.size
            
                # Need to set data here
                self.selectedGridItems[gridItemX][gridItemY] = self.addRect(QRectF(leftPos, topPos, self.size, self.size), QPen(Qt.blue, 0), QBrush(QColor(0,0,255, 75)))
            elif shouldDeselect:
                # deselect
                self.removeItem(self.selectedGridItems[gridItemX][gridItemY])
                self.selectedGridItems[gridItemX][gridItemY] = None

    def unselectAll(self):
        for index_x, x in enumerate(self.selectedGridItems):
            for index_y, cell in enumerate(self.selectedGridItems[index_x]):
                if not cell is None:
                    self.removeItem(cell)
                    self.selectedGridItems[index_x][index_y] = None
        self.objectSelected = False

    def deletePress(self):
        for index_x, x in enumerate(self.selectedGridItems):
            for index_y, cell in enumerate(self.selectedGridItems[index_x]):
                if not cell is None:
                    self.removeItem(cell)
                    self.selectedGridItems[index_x][index_y] = None

                    if self.gridItems[index_x][index_y]:
                        self.gridItems[index_x][index_y].removeFromView()
                        self.gridItems[index_x][index_y] = None

    def mousePressEvent(self, e: QGraphicsSceneMouseEvent):
        print("mousePressEvent")
        pos = e.scenePos()
        x = pos.x()
        y = pos.y()
        button = e.button()

        if button == Qt.MouseButton.LeftButton:
            self.mouseDown = True

            self.selectGridItemCoordinates(x, y)
            #if self.application.controlHeld:
            #    self.clearGridItemCoordinates(x, y)
            #else:
            #    self.fillGridItemCoordinates(x, y)
        elif button == Qt.MouseButton.MiddleButton:
            self.selectGridItemCoordinates(x, y)

    def moveGridTurtle(self, x, y):
        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if gridItemX < 0:
            gridItemX = 0
        elif gridItemX >= self.rows:
            gridItemX = self.rows - 1

        if gridItemY < 0:
            gridItemY = 0
        elif gridItemY >= self.cols:
            gridItemY = self.cols - 1

        self.gridTurtle.setPos(QPointF(float(gridItemX * self.size), float(gridItemY * self.size)))
        #print(f"Moved to {gridItemX}x{gridItemY}", flush=True)

        
    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        pos = e.scenePos()
        x = pos.x()
        y = pos.y()

        self.moveGridTurtle(x, y)

        if self.mouseDown:
            self.selectGridItemCoordinates(x, y, False)

    def tilesToObject(self):
        print("Combine", flush=True)

        tiles = []

        # grab all the selected tiles
        for index_x, x in enumerate(self.selectedGridItems):
            for index_y, cell in enumerate(self.selectedGridItems[index_x]):
                if not cell is None:
                    tiles.append([index_x, index_y])

        if len(tiles) == 0:
            pos = self.gridTurtle.pos()
            x = pos.x()
            y = pos.y()
            
            gridItemX = int(x // self.size) 
            gridItemY = int(y // self.size)

            if self.tiles[gridItemX][gridItemY]:
                tiles.append([gridItemX, gridItemY])

        if len(tiles) == 0:
            return False

        self.objects.append(SpriteObject("Object " + str(len(self.objects) + 1), "object_" + str(len(self.objects) + 1), '', tiles))
        # select it
        self.selectGridItemCoordinates(tiles[0][0] * self.size, tiles[0][1] * self.size)

        return True

    def contextMenuEvent(self, e):
        print("contextMenuEvent", flush=True)
        pos = e.scenePos()
        x = pos.x()
        y = pos.y()

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.tiles[gridItemX][gridItemY]:
            # show context menu
            menu = QMenu()
            menu.addAction(self.tilesToObjectAction)
            menu.popup(e.screenPos())

            # Else it gets garbage collected
            self.contextMenu = menu

            e.setAccepted(True)

    def mouseReleaseEvent(self, e: QGraphicsSceneMouseEvent):
        self.mouseDown = False

class WorkAreaTab(QMainWindow):
    def __init__(self, application, title, areaType):
        super().__init__()

        self.application = application
        self.title = title
        self.areaType = areaType

        self.setDockOptions(self.dockOptions() & ~QMainWindow.AllowTabbedDocks)

        # Graphics area
        centralFrame = QFrame()
        centralFrame.setLayout(QVBoxLayout())

        if areaType == WorkAreaType.MAP:
            scene = MapScene(application)
        else:
            scene = SpriteSheetScene(self, application)

        self.scene = scene
        view = SpriteSheetView(application, scene);
        self.view = view
        view.setScene(scene)

        #view.fitInView(scene.itemsBoundingRect())

        centralFrame.layout().addWidget(view)

        self.setCentralWidget(centralFrame)

        view.verticalScrollBar().setSliderPosition(1)
        view.horizontalScrollBar().setSliderPosition(1)

    def saveFile(self):
        self.scene.saveFile()

    def saveState(self):
        return self.scene.saveState()

class WorkAreaTabMap(WorkAreaTab):
    def __init__(self, application, title, areaType):
        super().__init__(application, title, areaType)

        self.layersDock = QDockWidget("Layers", self)
        self.layersWidget = QListWidget()
        self.layersWidget.addItem("ground")
        
        self.layersDock.setWidget(self.layersWidget)
        self.layersDock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layersDock)

        self.tilesetsDock = QDockWidget("Tilesets", self)
        self.tilesetsWidget = QListWidget()
        self.tilesetsWidget.addItem("ground")
        
        self.tilesetsDock.setWidget(self.tilesetsWidget)
        self.tilesetsDock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.tilesetsDock)

        # Using a title
        fileToolBar = self.addToolBar("Map")
        fileToolBar.addAction("Test")

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
        #print("Changed item", flush=True)
        #print(item.row())
        #print(item.type())

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
        #print(tileWidth, flush=True)
        # name, spriteFilename, sheetWidth, sheetHeight, tileWidth, tileHeight, horizontalTiles, verticalTiles)
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

class WorkAreaTabSpriteSheet(WorkAreaTab):
    def __init__(self, application, title, areaType):
        super().__init__(application, title, areaType)

        self.propertiesDock = SpriteSheetPropertiesWidget("Sprite Sheet Properties", self, application)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.propertiesDock)

        self.objectPropertiesDock = ObjectPropertiesWidget("Object Properties", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.objectPropertiesDock)

        self.objectsDock = QDockWidget("Objects", self)
        self.objectsWidget = QListWidget()
        self.objectsWidget.addItem("ground")
        
        self.objectsDock.setWidget(self.objectsWidget)
        self.objectsDock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.objectsDock)

        #self.scene.loadSpriteSheetFromImageFile("tilemap2.png")
        #self.scene.createGrid()

    def restoreState(self, state):
        print(state)
        self.scene.restoreState(state)


class WorkAreaTabWidget(QTabWidget):
    def __init__(self, application = None):
        super().__init__(application)

        #self.tabs = []
        self.application = application

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeHandler)

        #self.addTab("Untitled sprite sheet", WorkAreaType.SPRITE_SHEET)
        #self.addTab("Untitled map", WorkAreaType.MAP)

        
    def closeHandler(self, index):
        msgBox = QMessageBox(self.application)

        msgBox.setWindowTitle("SpriteShits");
        msgBox.setText("Are you sure you want to close this tab?");
        msgBox.setStandardButtons(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        
        if msgBox.exec() == QMessageBox.Yes:
            self.removeTab(index)

    def addTab(self, title, areaType):
        if areaType == WorkAreaType.MAP:
            newTab = WorkAreaTabMap(self.application, title, areaType)
        else:
            newTab = WorkAreaTabSpriteSheet(self.application, title, areaType)

        #self.tabs.append(newTab)
        super().addTab(newTab, title)
        return newTab

    def activeTab(self):
        currentIndex = self.currentIndex()

        if currentIndex > -1:
            return self.widget(self.currentIndex())

    def saveState(self):
        tabStates = []

        for i in range(0, self.count()):
            tab = self.widget(i)
            tabStates.append(tab.saveState())

        return tabStates

    def restoreState(self, tabStates):
        print(tabStates)
        for state in tabStates:
            print(state)
            if 'type' in state:
                print("me", flush=True)
                if state['type'] == 'sheet':
                    self.addTab(state['name'], WorkAreaType.SPRITE_SHEET).restoreState(state)
        
class ResourcesDockWidget(QDockWidget):
    def __init__(self, name, parent = None):
        super().__init__(name, parent)

        model = QFileSystemModel()
        model.setNameFilters(['*.json'])
        model.setNameFilterDisables(False)
        #model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)
        model.setRootPath(QDir.currentPath())
        tree = QTreeView()
        tree.setRootIsDecorated(False)
        tree.setModel(model)
        tree.setRootIndex(model.index(QDir.currentPath()))

        #tree.hideColumn(0)

        for i in range(1, model.columnCount()):
            tree.hideColumn(i)

        #tree.setHeaderHidden(True)
        tree.setUniformRowHeights(True)
        #setDragEnabled(true);
        #setDefaultDropAction(Qt::MoveAction);

        #self.resourcesWidget = QListWidget()
        #self.resourcesWidget.addItem("map.rsc")
        self.tree = tree
        
        self.setWidget(tree)
        self.setFloating(False)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Bubble down
        self.controlHeld = False

        self.showGrid = True

        self.gridWidth = 16
        self.gridHeight = 16

        self.setWindowTitle("SpriteShits")
        self.setMinimumSize(QSize(1200, 900))

        self.createMenus()

        layout = QHBoxLayout()

        # Docks should be split by default not tabbed
        self.setDockOptions(self.dockOptions() & ~QMainWindow.AllowTabbedDocks)

        self.resourcesDock = ResourcesDockWidget("Project Files", self)
        self.resourcesDock.setObjectName("project_files")

        self.addDockWidget(Qt.LeftDockWidgetArea, self.resourcesDock)



        

        # Graphics area
        #centralFrame = QFrame()
        #centralFrame.setLayout(QVBoxLayout())

        #scene = SpriteScene(self);
        #self.scene = scene
        #view = SpriteView(self, scene);
        #view.setScene(scene)

        #view.fitInView(scene.itemsBoundingRect())

        #centralFrame.layout().addWidget(view);

        self.workAreaWidget = WorkAreaTabWidget(self)

        self.setCentralWidget(self.workAreaWidget)
        self.setLayout(layout)

        self.restoreApplicationState()

    def createMenus(self):
        bar = self.menuBar()

        fileMenu = bar.addMenu("&File")
        newAction = QAction("&New", self)
        newAction.triggered.connect(self.newFile)
        saveAction = QAction("&Save", self)
        saveAction.triggered.connect(self.saveFile)
        saveAction.setShortcut("Ctrl+S")

        exitAction = QAction("&Exit", self)
        exitAction.triggered.connect(self.quit)
        exitAction.setShortcut("Ctrl+E")

        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction("&Open")
        fileMenu.addAction(exitAction)

        viewMenu = bar.addMenu("&View")
        showGridAction = QAction("Show &grid", self)
        showGridAction.triggered.connect(self.toggleGrid)
        viewMenu.addAction(showGridAction)

    def newFile(self):
        print("New file", flush=True)
        pass

    def openFile(self):
        pass

    def saveFile(self):
        tab = self.workAreaWidget.activeTab()

        if tab:
            tab.saveFile()
        else:
            print("Not found", flush=True)

    def closeEvent(self, event):        
        if self.confirmQuit():
            self.saveApplicationState()
            event.accept()
        else:
            event.ignore()

    def confirmQuit(self):
        msgBox = QMessageBox(self)

        msgBox.setWindowTitle("SpriteShits");
        msgBox.setText("Are you sure you want to exit?");
        msgBox.setStandardButtons(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        
        return msgBox.exec() == QMessageBox.Yes

    def quit(self):
        if self.confirmQuit():
            self.saveApplicationState()
            exit()

    def saveApplicationState(self):
        settings = QSettings("Bamboo", "SpriteShits")
        settings.setValue("mainWindow/geometry", self.saveGeometry())
        settings.setValue("mainWindow/windowState", self.saveState())

        tabState = json.dumps(self.workAreaWidget.saveState()).encode('utf-8')
        settings.setValue("mainWindow/tabs", QByteArray(tabState))
    
    def restoreApplicationState(self):
        settings = QSettings("Bamboo", "SpriteShits")
        try:
            self.restoreGeometry(settings.value("mainWindow/geometry"))
            self.restoreState(settings.value("mainWindow/windowState"))
            
        except:
            pass

        tabState = json.loads(str(settings.value("mainWindow/tabs"), 'utf-8'))

        if tabState and len(tabState):
            self.workAreaWidget.restoreState(tabState)


    def toggleGrid(self):
        self.showGrid = not self.showGrid

        if self.showGrid:
            self.scene.createGrid()
        else:
            self.scene.removeGridLines()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.controlHeld = True
        elif event.key() == Qt.Key_Delete:
            self.scene.deletePress()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.controlHeld = False


# Create a Qt widget, which will be our window.
window = MainWindow()
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()

# Your application won't reach here until you exit and the event
# loop has stopped.