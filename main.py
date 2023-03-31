from PySide6.QtCore import QSize, Qt, QRectF, QPoint, QPointF
from PySide6.QtGui import QTransform, QPen, QBrush, QColor, QAction
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QDockWidget, QListWidget, QTextEdit, QGraphicsScene, QGraphicsView, QFrame, QGraphicsSceneMouseEvent, QTabWidget, QToolBar

# Only needed for access to command line arguments
import sys
from enum import Enum

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

class WorkAreaType(Enum):
    MAP = 1
    SPRITE_SHEET = 2

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

class SpriteView(QGraphicsView):
    def __init__(self, application, scene):
        super().__init__(scene)
        self.application = application

        # Need this so all mouse move events are tracked
        self.setMouseTracking(True)

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

    def fillGridItemCoordinates(self, x, y):
        print(f"{x}x{y}", flush=True)

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
        print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY]:
            spriteItem = self.gridItems[gridItemX][gridItemY]
            
            spriteItem.removeFromView()
            # Need to set data here
            self.gridItems[gridItemX][gridItemY] = None

    def selectGridItemCoordinates(self, x, y):
        print(f"{x}x{y}", flush=True)

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
        print(f"Moved to {gridItemX}x{gridItemY}", flush=True)

        
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

    def fillGridItemCoordinates(self, x, y):
        print(f"{x}x{y}", flush=True)

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
        print(f"{x}x{y}", flush=True)

        # align to inside grid item
        gridItemX = int(x // self.size) 
        gridItemY = int(y // self.size)

        if self.gridItems[gridItemX][gridItemY]:
            spriteItem = self.gridItems[gridItemX][gridItemY]
            
            spriteItem.removeFromView()
            # Need to set data here
            self.gridItems[gridItemX][gridItemY] = None

    def selectGridItemCoordinates(self, x, y):
        print(f"{x}x{y}", flush=True)

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
        print(f"Moved to {gridItemX}x{gridItemY}", flush=True)

        
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
            scene = SpriteSheetScene(application)

        self.scene = scene
        view = SpriteView(application, scene);
        view.setScene(scene)

        #view.fitInView(scene.itemsBoundingRect())

        centralFrame.layout().addWidget(view);

        self.setCentralWidget(centralFrame)

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

class WorkAreaTabSpriteSheet(WorkAreaTab):
    def __init__(self, application, title, areaType):
        super().__init__(application, title, areaType)

        self.propertiesDock = QDockWidget("Sprite Sheet Properties", self)
        self.propertiesWidget = QListWidget()
        self.propertiesWidget.addItem("ground")
        
        self.propertiesDock.setWidget(self.propertiesWidget)
        self.propertiesDock.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.propertiesDock)

        self.objectsDock = QDockWidget("Objects", self)
        self.objectsWidget = QListWidget()
        self.objectsWidget.addItem("ground")
        
        self.objectsDock.setWidget(self.objectsWidget)
        self.objectsDock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.objectsDock)

    def loadSpriteSheetFromImageFile(self, filePath):
        pass

class WorkAreaTabWidget(QTabWidget):
    def __init__(self, application = None):
        super().__init__(application)

        self.tabs = []
        self.application = application

        self.addTab("Untitled sprite sheet", WorkAreaType.SPRITE_SHEET)
        self.addTab("Untitled map", WorkAreaType.MAP)
        

    def addTab(self, title, areaType):
        if areaType == WorkAreaType.MAP:
            newTab = WorkAreaTabMap(self.application, title, areaType)
        else:
            newTab = WorkAreaTabSpriteSheet(self.application, title, areaType)

        self.tabs.append(newTab)
        super().addTab(newTab, title)
        

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

        self.resourcesDock = QDockWidget("Resources", self)
        self.resourcesWidget = QListWidget()
        self.resourcesWidget.addItem("map.rsc")
        
        self.resourcesDock.setWidget(self.resourcesWidget)
        self.resourcesDock.setFloating(False)
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

        self.setCentralWidget(WorkAreaTabWidget(self))
        self.setLayout(layout)

    def createMenus(self):
        bar = self.menuBar()

        fileMenu = bar.addMenu("&File")
        newAction = QAction("&New", self)
        newAction.triggered.connect(self.newFile)

        fileMenu.addAction(newAction)
        fileMenu.addAction("&Save")
        fileMenu.addAction("&Open")
        fileMenu.addAction("&Quit")

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
        pass

    def quit(self):
        exit()

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