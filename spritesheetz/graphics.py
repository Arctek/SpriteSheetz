from os.path import basename
from math import ceil
from PySide6.QtCore import Qt, QRectF, QPoint, QPointF
from PySide6.QtGui import QTransform, QPen, QBrush, QColor, QAction, QPixmap
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsSceneMouseEvent, QGraphicsPixmapItem

from spritesheetz.objects import SpriteItem, SpriteObject, SpriteObjectOrigin

class SpriteSheet:
    def __init__(self, name, spriteFile, tileWidth, tileHeight, width, height, objects):
        self.name = name
        self.spriteFile = spriteFile
        self.tileWidth = tileWidth
        self.tileHeight = tileHeight
        self.width = width
        self.height = height
        self.objects = objects

        self.size = 102

        self.gridLines = []

        self.gridPen = QPen(Qt.black, 1, Qt.DashLine)

        self._loadSpriteFile()

    def _loadSpriteFile(self):
        masterPixmap = QPixmap(self.spriteFile)
        self.masterPixmap = masterPixmap

        self.horizontalTiles = ceil(self.width / self.tileWidth)
        self.verticalTiles = ceil(self.width / self.tileWidth)
        self.tiles = [[None for col in range(self.verticalTiles)] for row in range(self.horizontalTiles)]

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
                #self.addItem(pixmapItem)

    def drawTiles(self, scene):
        for x, row in enumerate(range(self.horizontalTiles)):
            for y, col in enumerate(range(self.verticalTiles)):
                scene.addItem(self.tiles[x][y][1])

    def drawGrid(self, scene):
        self.rows = self.horizontalTiles
        self.cols = self.verticalTiles
        
        endPoint = self.rows * self.size

        if len(self.gridLines):
            for line in self.gridLines:
                self.removeItem(line)

            self.gridLines = []

        #if not self.gridItems:
        #    self.gridItems = [[None for col in range(self.cols)] for row in range(self.rows)]
        #    self.selectedGridItems = [[None for col in range(self.cols)] for row in range(self.rows)]

        #if self.application.showGrid:
        # vertical lines
        for i in range(0, self.cols + 1):
            x = i * self.size
            self.gridLines.append(scene.addLine(x, 0, x, endPoint, self.gridPen))

        # horizontal lines
        for i in range(0, self.rows + 1):
            y = i * self.size
            self.gridLines.append(scene.addLine(0, y, endPoint, y, self.gridPen))

    @staticmethod
    def fromdict(obj):
        items = []

        for key in obj['items']:
            items.append(SpriteObject.fromdict(obj['items'][key]))

        return SpriteSheet(obj['name'], obj['spriteFile'], obj['tileWidth'], obj['tileHeight'], obj['width'], obj['height'], items)

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

class MapLayer:
    def __init__(self, name, rows, cols):
        self.name = name
        self.rows = rows
        self.cols = cols
        
        self.tiles = [[None for col in range(self.cols)] for row in range(self.rows)]

    def tile(x, y):
        return self.tiles[x][y]

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
        self.spriteSheets = []
        self.spriteSheetFiles = []
        self.layers = [ MapLayer('ground', 50, 50) ]
        self.currentLayerIndex = 0

        self.name = "Untitled map"

        #rect = self.addRect(QRectF(0, 0, 100, 100), gridOutline, QBrush(Qt.green))
        #item = self.itemAt(50, 50, QTransform())

        #self.setMouseTracking(True)

        self.setBackgroundBrush(QBrush(QColor(220,220,220)))

        self.createGrid()

        self.gridTurtle = self.addRect(QRectF(0, 0, self.size, self.size), QPen(Qt.blue, 0), QBrush(QColor(0,0,255, 75)))
        self.gridTurtle.setZValue(100) #always on top

    def setPlacementObject(self, obj, spriteSheet):
        self.placementObject = obj
        self.spriteSheet = spriteSheet
        self.placementTiles = None

    def setPlacementTiles(self, tiles, spriteSheet):
        self.placementObject = None
        self.spriteSheet = spriteSheet
        self.placementTiles = tiles

    def addSpriteSheet(self, filePath, spriteSheet):
        self.spriteSheets.append(spriteSheet)
        self.spriteSheetFiles.append(filePath)

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
        stateData = {
            'name': self.name,
            'type': 'map',
            'tileWidth': self.tileWidth,
            'tileHeight': self.tileHeight,
            'width': self.width,
            'height': self.height,
            'spriteSheets': self.spriteSheetFiles,
            'layers': []
        }

        return stateData

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

# For the view inside the dock when interacting with a map
class MiniSpriteSheetScene(QGraphicsScene):
    def __init__(self, parent, application, spriteSheet):
        super().__init__()

        self.parent = parent
        self.application = application

        self.selectedGridItems = None
        self.spriteSheet = spriteSheet

        self.setBackgroundBrush(QBrush(QColor(220,220,220)))        

        self.gridTurtle = self.addRect(QRectF(0, 0, spriteSheet.size, spriteSheet.size), QPen(Qt.yellow, 0), QBrush(QColor(128,128,0, 75)))
        self.gridTurtle.setZValue(100) #always on top

    def moveGridTurtle(self, x, y):
        # align to inside grid item
        gridItemX = int(x // self.spriteSheet.size) 
        gridItemY = int(y // self.spriteSheet.size)

        if gridItemX < 0:
            gridItemX = 0
        elif gridItemX >= self.spriteSheet.verticalTiles:
            gridItemX = self.spriteSheet.verticalTiles - 1

        if gridItemY < 0:
            gridItemY = 0
        elif gridItemY >= self.spriteSheet.horizontalTiles:
            gridItemY = self.spriteSheet.horizontalTiles - 1

        self.gridTurtle.setPos(QPointF(float(gridItemX * self.spriteSheet.size), float(gridItemY * self.spriteSheet.size)))

        
    def mouseMoveEvent(self, e: QGraphicsSceneMouseEvent):
        pos = e.scenePos()
        x = pos.x()
        y = pos.y()

        self.moveGridTurtle(x, y)