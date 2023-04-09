from PySide6.QtWidgets import QApplication
from spritesheetz.application import MainWindow

app = QApplication()
window = MainWindow().show()
app.exec()