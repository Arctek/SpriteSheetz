import json
from PySide6.QtCore import Qt, QSize, QSettings, QByteArray
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QInputDialog, QMessageBox

from spritesheetz.docks import ResourcesDockWidget
from spritesheetz.tabs import WorkAreaTabWidget, WorkAreaType

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Bubble down
        self.controlHeld = False

        self.showGrid = True

        self.gridWidth = 16
        self.gridHeight = 16

        self.setWindowTitle("SpriteSheetz")
        self.setMinimumSize(QSize(1200, 900))

        self.createMenus()

        layout = QHBoxLayout()

        #self.setStyleSheet( """ QListWidget:item:selected:active {
        #                             background: blue;
        #                        }
        #                        QListWidget:item:selected:!active {
        #                             background: gray;
        #                        }
        #                        QListWidget:item:selected:disabled {
        #                             background: gray;
        #                        }
        #                        QListWidget:item:selected:!disabled {
        #                             background: blue;
        #                        }
        #                        """
        #                        )

        # Docks should be split by default not tabbed
        self.setDockOptions(self.dockOptions() & ~QMainWindow.AllowTabbedDocks)

        self.resourcesDock = ResourcesDockWidget(self, "Project Files", self)
        self.resourcesDock.setObjectName("project_files")

        self.addDockWidget(Qt.LeftDockWidgetArea, self.resourcesDock)

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
        item, ok = QInputDialog.getItem(self, "New File",
                                        "Type:", ["Map", "Sprite Sheet"], 0, False);
        if ok and item:
            if item == 'Map':
                self.workAreaWidget.addTab("Untitled Map", WorkAreaType.MAP)
            else:
                fileName, _ = QFileDialog.getOpenFileName(self, 'Open Sprite Sheet Image', filter='Images (*.png *.gif)')

                if fileName:
                    tab = self.workAreaWidget.addTab("Untitled Sprite Sheet", WorkAreaType.SPRITE_SHEET)
                    tab.loadSpriteSheetFromImageFile(fileName)

    def readFile(self, filePath):
        with open(filePath, 'r') as file:
            data = json.loads(file.read())
        return data

    def triggerFile(self, filePath):
        # if open then add to selected map instead
        data = self.readFile(filePath)

        tab = self.workAreaWidget.activeTab()

        if tab and tab.areaType == WorkAreaType.MAP:
            if self.confirmDialogue('SpriteSheetz', 'Would you like to add this sheet to the map?'):
                tab.addSpriteSheet(filePath, data)
        else:
            self.openFile(filePath, data)


    def openFile(self, filePath, data = None):
        if data is None:
            data = self.readFile(filePath)

        if data and 'type' in data:
            self.workAreaWidget.loadFile(filePath, data)

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

    def confirmDialogue(self, title, question):
        msgBox = QMessageBox(self)

        msgBox.setWindowTitle(title)
        msgBox.setText(question)
        msgBox.setStandardButtons(QMessageBox.Yes)
        msgBox.addButton(QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        
        return msgBox.exec() == QMessageBox.Yes

    def confirmQuit(self):
        return self.confirmDialogue('SpriteSheetz', 'Are you sure you want to exit?')

    def quit(self):
        if self.confirmQuit():
            self.saveApplicationState()
            exit()

    def saveApplicationState(self):
        settings = QSettings("Bamboo", "SpriteSheetz")
        settings.setValue("mainWindow/geometry", self.saveGeometry())
        settings.setValue("mainWindow/windowState", self.saveState())

        tabState = json.dumps(self.workAreaWidget.saveState()).encode('utf-8')
        settings.setValue("mainWindow/tabs", QByteArray(tabState))
    
    def restoreApplicationState(self):
        settings = QSettings("Bamboo", "SpriteSheetz")
        try:
            self.restoreGeometry(settings.value("mainWindow/geometry"))
            self.restoreState(settings.value("mainWindow/windowState"))
            tabState = json.loads(str(settings.value("mainWindow/tabs"), 'utf-8'))

            if tabState and len(tabState):
                self.workAreaWidget.restoreState(tabState)
        except:
            pass

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