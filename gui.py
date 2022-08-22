import sys
import os
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QDialog, QTreeWidget, QTreeWidgetItem

disk_folders = []
path_list = []
for root, dirs, files in os.walk('D:\\', topdown=True):
    split_ = root.split('\\')
    path = {}
    index = range(len(split_))

    for i, ind in zip(split_, index):
        path[ind] = i
    path['files'] = files
    path_list.append(path)

# print(path_list)
structure = {}
structure['Partycja'] = 'D:'

for path in path_list:
    print(path)
    index = range(1, len(path.keys()))
    for i in index:
        structure
exit()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(400, 300))

        file_browser_button = QPushButton('Load file')
        file_browser_button.setCheckable(False)
        file_browser_button.clicked.connect(self.file_browser)

        self.setCentralWidget(file_browser_button)

    def file_browser(self):
        file_browser_window = FileBrowser(self)
        file_browser_window.setWindowTitle('File browser')
        file_browser_window.exec()

class FileBrowser(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('File browser')
        self.tree = QTreeWidget(self)
        self.tree.setMinimumSize(300, 200)
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(['file'])

    def _get_path(self):
        path_list = []
        for root, dirs, files in os.walk('D:\\', topdown=True):
            split_ = root.split('\\')
            path = {}
            index = range(len(split_))

            for i, ind in zip(split_, index):
                path[ind] = i
            path['files'] = files
            path_list.append(path)

        return path_list

    def populate_treelist(self):
        path_list = self._get_path()
        items = []
        for path in path_list:
            for level in path.keys():
                particion = QTreeWidgetItem([path[level]])







app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()