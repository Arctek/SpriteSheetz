from enum import IntEnum
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QWidget, QMainWindow, QFrame, QVBoxLayout, QMessageBox, QDockWidget, QListWidget, QGraphicsScene

from spritesheetz.graphics import MapScene, SpriteSheetScene, SpriteSheetView, GraphicsView, SpriteSheet, MiniSpriteSheetScene
from spritesheetz.docks import LayersDock, ObjectPropertiesWidget, SpriteSheetPropertiesWidget

class WorkAreaType(IntEnum):
    MAP = 0
    SPRITE_SHEET = 1

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

        self.layersDock = LayersDock("Layers", self)

        self.layersDock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layersDock)

        self.spriteSheetsDock = QDockWidget("Sprite Sheets", self)
        self.spriteSheetTabWidget = SpriteSheetTabWidget(application)
        
        self.spriteSheetsDock.setWidget(self.spriteSheetTabWidget)
        self.spriteSheetsDock.setFloating(False)
        self.addDockWidget(Qt.RightDockWidgetArea, self.spriteSheetsDock)

        halfHeight = self.height() // 2

        self.resizeDocks([self.layersDock, self.spriteSheetsDock], [halfHeight, halfHeight], Qt.Orientation.Vertical);
        self.resizeDocks([self.layersDock, self.spriteSheetsDock], [400, 400], Qt.Orientation.Horizontal);

        # Using a title
        fileToolBar = self.addToolBar("Map")
        fileToolBar.addAction("Test")

        self.spriteSheets = []

    def addSpriteSheet(self, filePath, data):
        spriteSheet = SpriteSheet.fromdict(data)

        self.spriteSheets.append(spriteSheet)
        self.spriteSheetTabWidget.addTab(spriteSheet)
        self.scene.addSpriteSheet(filePath, spriteSheet)

class SpriteSheetTabContentWidget(QWidget):
    def __init__(self, application, spriteSheet):
        super().__init__()

        self.spriteSheet = spriteSheet
        self.application = application

        self.setLayout(QVBoxLayout())
        self.scene = MiniSpriteSheetScene(self, application, spriteSheet)
        view = GraphicsView(application, self.scene)
        self.view = view
        view.setScene(self.scene)

        self.layout().addWidget(view)

        view.verticalScrollBar().setSliderPosition(1)
        view.horizontalScrollBar().setSliderPosition(1)

        view.scale(0.25, 0.25)
        view.translate(0.0, 0.0)

        self.spriteSheet.drawTiles(self.scene)
        self.spriteSheet.drawGrid(self.scene)

class SpriteSheetTabWidget(QTabWidget):
    def __init__(self, application = None):
        super().__init__(application)

        self.application = application

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeHandler)
        
    def closeHandler(self, index):
        msgBox = QMessageBox(self.application)

        msgBox.setWindowTitle("SpriteSheetz");
        msgBox.setText("Are you sure you want to remove this sprite sheet from the map?");
        msgBox.setStandardButtons(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        
        if msgBox.exec() == QMessageBox.Yes:
            pass

    def addTab(self, spriteSheet):
        tab = super().addTab(SpriteSheetTabContentWidget(self.application, spriteSheet), spriteSheet.name)

        self.setCurrentIndex(self.count() - 1)

        return tab

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

    def loadFile(self, filePath, data):
        if data['type'] == 'sheet':
            # if tab exists, swap to it instead
            self.addTab(data['name'], WorkAreaType.SPRITE_SHEET).restoreState(data)

    def restoreState(self, tabStates):
        print(tabStates)
        for state in tabStates:
            print(state)
            if 'type' in state:
                print("me", flush=True)
                if state['type'] == 'sheet':
                    self.addTab(state['name'], WorkAreaType.SPRITE_SHEET).restoreState(state)
 
class WorkAreaTabSpriteSheet(WorkAreaTab):
    def __init__(self, application, title, areaType):
        super().__init__(application, title, areaType)

        self.areaType = areaType

        self.propertiesDock = SpriteSheetPropertiesWidget("Sprite Sheet Properties", self, application)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.propertiesDock)

        self.objectPropertiesDock = ObjectPropertiesWidget("Object Properties", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.objectPropertiesDock)

    def restoreState(self, state):
        print(state)
        self.scene.restoreState(state)

    def loadSpriteSheetFromImageFile(self, filePath):
        self.scene.loadSpriteSheetFromImageFile(filePath)


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

        msgBox.setWindowTitle("SpriteSheetz");
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

        self.setCurrentIndex(self.count() - 1)

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

    def loadFile(self, filePath, data):
        if data['type'] == 'sheet':
            # if tab exists, swap to it instead
            self.addTab(data['name'], WorkAreaType.SPRITE_SHEET).restoreState(data)

    def restoreState(self, tabStates):
        print(tabStates)
        for state in tabStates:
            print(state)
            if 'type' in state:
                print("me", flush=True)
                if state['type'] == 'sheet':
                    self.addTab(state['name'], WorkAreaType.SPRITE_SHEET).restoreState(state)
 