'''
Zachary Stevens
Final Project - ASTR 5470
Quasar Spectral Analysis in Python

Sources of Help:
https://www.pythonguis.com/tutorials/plotting-matplotlib/
Probably Alex Garcia
'''

# ----------------------------
# Import statements
# ----------------------------
import sys
import matplotlib
matplotlib.use('Qt5Agg')
import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
# ----------------------------


# ----------------------------
# Canvas Class
# ----------------------------
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        
        
# ----------------------------
# Main window class
# ----------------------------
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        '''
        Initialize the window along with corresponding buttons
        '''
        super(MainWindow, self).__init__(*args, **kwargs)

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        # self.setCentralWidget(self.canvas)  
        
        # sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.axes.plot([0,1,2,3,4], [10,1,20,3,40], label = f"Some random data\n\nLoad in a file!")
        self.canvas.axes.set_xlabel("some random data")
        self.canvas.axes.legend()
        
        self.setWindowTitle("Spectrum Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        toolbar = NavigationToolbar(self.canvas, self)
        
        self.open_file_button = QPushButton("Open File", self)
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setGeometry(170, 10, 80, 30)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.open_file_button)
        layout.addWidget(self.canvas)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.show()
    
    
    def read_csv(filename):
        data = pd.read_csv(filename, delim_whitespace=True, skiprows=1)
        return data.iloc[:, 0], data.iloc[:, 1]
    
    def open_file(self):
        '''
        Open a csv file!
        File conventions should have a title line, then two columns - one for wavelength and one for flux.
        '''
        filename, _ = QFileDialog.getOpenFileName(self, "Open Spectrum", "", "CSV files (*.csv)")
        if filename:
            data = pd.read_csv(filename, delim_whitespace=True, skiprows=1)
            wavelength, flux = (data.iloc[:, 0], data.iloc[:, 1])
            self.canvas.axes.cla()
            self.canvas.axes.plot(wavelength, flux)
            self.canvas.draw()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()