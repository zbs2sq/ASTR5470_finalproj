'''
Zachary Stevens
Final Project - ASTR 5470
Quasar Spectral Analysis in Python

Sources of Help:
https://www.pythonguis.com/tutorials/plotting-matplotlib/

'''

# ----------------------------
# Import statements
# ----------------------------
import sys
import matplotlib
matplotlib.use('Qt5Agg')
import pandas as pd
import numpy as np
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from scipy import interpolate
from scipy.optimize import curve_fit
from scipy.stats import norm
from scipy.optimize import minimize
# ----------------------------


# ----------------------------
# Canvas class
# ----------------------------
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Eq():
    
    def gaussian(x, amplitude, mean, stddev):
        return amplitude * np.exp(-((x - mean) / stddev) ** 2 / 2)
    
        
# ----------------------------
# Main window class
# ----------------------------
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        '''
        Initialize the window along with corresponding buttons
        '''
        super(MainWindow, self).__init__(*args, **kwargs)
        
        # Data storage
        self.wavelengths = []
        self.fluxes = []
        
        self.continuum_wavelengths = []
        self.continuum_fluxes = []
        
        self.continuum_fit = []
        
        self.xclick = 0.
        self.yclick = 0.
        
        
        # Some booleans to keep track of whether things have been done
        self.file_is_loaded = False
        self.continuum_is_calculated = False
        self.fitting_line = False
        
        
        # Set up canvas
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        
        self.canvas.axes.plot([0,1,2,3,4], [10,1,20,3,40], label = f"Some random data\n\nLoad in a file!")
        self.canvas.axes.set_xlabel("some random data")
        self.canvas.axes.legend()
        
        self.setWindowTitle("Spectrum Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        
        # Buttons
        toolbar = NavigationToolbar(self.canvas, self)
        
        self.open_file_button = QPushButton("Open File", self)
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setGeometry(170, 10, 80, 30)
        
        self.haircut_clip_button = QPushButton("Haircut Clip", self)
        self.haircut_clip_button.clicked.connect(self.haircut_clip)
        self.haircut_clip_button.setGeometry(170, 10, 80, 30)
        
        self.def_cont_button = QPushButton("Define Continuum", self)
        self.def_cont_button.clicked.connect(self.define_continuum)
        self.def_cont_button.setGeometry(170, 10, 80, 30)
        
        self.fit_line_button = QPushButton("Fit Spectral Line", self)
        self.fit_line_button.clicked.connect(self.toggle_fit_spectral_line)
        self.fit_line_button.setGeometry(170, 10, 80, 30)
        
        self.smooth_button = QPushButton("Smooth", self)
        self.smooth_button.clicked.connect(self.smooth)
        self.smooth_button.setGeometry(170, 10, 80, 30)
        
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
        
        '''
        To Do/Functions I Want To Add
        - Revert to original (save the original file somewhere, then revert back to that if needed)
        - Smoothing function should have a feature to allow you to choose how much to smooth by...
        - Continuum fit should have an extra feature where you can refine it by rejected points outside of the stddev 
            - Requires a continuum to already be fit...
        - A subtract continuum function
        '''
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.open_file_button)
        layout.addWidget(self.haircut_clip_button)
        layout.addWidget(self.def_cont_button)
        layout.addWidget(self.smooth_button)
        layout.addWidget(self.fit_line_button)
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
        File conventions should have a title line, then two columns with a space as a delimiter - one for wavelength and one for flux.
        '''
        filename, _ = QFileDialog.getOpenFileName(self, "Open Spectrum", "", "CSV files (*.csv)")
        if filename:
            self.file_is_loaded = True
            data = pd.read_csv(filename, delim_whitespace=True, skiprows=1)
            self.wavelengths, self.fluxes = (data.iloc[:, 0], data.iloc[:, 1])
            self.canvas.axes.cla()
            self.canvas.axes.plot(self.wavelengths, self.fluxes)
            self.canvas.axes.axhline(0, color = 'black')
            self.canvas.axes.set_title(filename[-14:-9])
            self.canvas.axes.set_xlabel("Wavelength (Angstroms)")
            self.canvas.axes.set_ylabel("Flux (erg/s/cm2/A)")
            self.canvas.axes.legend()
            self.canvas.draw()
            
            
    def define_continuum(self):
        '''
        This function takes every 200th datapoint within the function and fits a second order polynomial to it, shown in red.
        It then removes all points >1*sigma away from the second order fit.
        Removed points are shown in red.
        It then fits a fifth order polynomial to the remaining points, shown in green.
        '''
        try:
            x = self.wavelengths
            y = self.fluxes
            f = interpolate.interp1d(x, y)
            orig_continuum_wavelengths = np.arange(self.wavelengths[0], self.wavelengths[len(self.wavelengths) - 1], 200)
            orig_continuum_fluxes = f(orig_continuum_wavelengths)
            
            original_fit = np.polyfit(orig_continuum_wavelengths, orig_continuum_fluxes, 2, full=True)
            original_yfit = np.polyval(original_fit[0], orig_continuum_wavelengths)
            
            residuals = orig_continuum_fluxes - original_yfit
            std_residuals = np.std(residuals)
            filtered_indices = np.abs(residuals) <= std_residuals

            self.continuum_wavelengths = orig_continuum_wavelengths[filtered_indices]
            self.continuum_fluxes = orig_continuum_fluxes[filtered_indices]
            
            filtered_fit = np.polyfit(self.continuum_wavelengths, self.continuum_fluxes, 5, full=True)
            filtered_yfit = np.polyval(filtered_fit[0], self.continuum_wavelengths)
            self.continuum_fit = np.polyval(filtered_fit[0], self.wavelengths)
            
            print(type(filtered_fit))
            print(filtered_fit)

            self.canvas.axes.plot(orig_continuum_wavelengths, orig_continuum_fluxes, 'o', color = 'red')
            self.canvas.axes.plot(self.continuum_wavelengths, self.continuum_fluxes, 'o', color='green')
            
            self.canvas.axes.plot(orig_continuum_wavelengths, original_yfit, '-', color='red')
            self.canvas.axes.plot(self.wavelengths, self.continuum_fit, '-', color='green')
            # self.canvas.axes.plot(self.continuum_wavelengths, filtered_yfit, '-', color='green')
            self.canvas.draw()
            self.continuum_is_calculated = True
        except:
            if not self.file_is_loaded:
                print("Load a file in!!")
            else:
                traceback.print_exc()
                
    
    def smooth(self):
        '''
        This function isn't functioning quite how I'd like it to yet...
        '''
        try:
            x = self.wavelengths
            y = self.fluxes
            f = interpolate.interp1d(x, y)

            self.wavelengths = np.arange(self.wavelengths[0], self.wavelengths[len(self.wavelengths) - 1], 5)
            self.fluxes = f(self.wavelengths)
            self.canvas.axes.cla()
            self.canvas.axes.plot(self.wavelengths, self.fluxes, '-', color = 'blue')
            self.canvas.draw()
        except:
            if not self.file_is_loaded:
                print("Load a file in!!")
            else:
                traceback.print_exc()
                
    
    def haircut_clip(self):
        pass
    
    def on_click(self, event):
        if event.button == 1 and event.inaxes:
            self.xclick, self.yclick = event.xdata, event.ydata
            try:
                if self.fitting_line:
                    AnalysisFunc.fit_spectral_line(self)
            except:
                if not self.file_is_loaded:
                    print("Load a file in!!")
                elif not self.continuum_is_calculated:
                    print("Make sure to define your continuum!")
                else:
                    traceback.print_exc()

    def toggle_fit_spectral_line(self):
        self.fitting_line = True
        
        
        
        
class AnalysisFunc():
    def fit_spectral_line(self):
        print("I am fitting a line now")
        print(self.wavelengths[np.searchsorted(self.wavelengths, self.xclick)])

        # This block finds the nearest flux maximum to where you click
        line_index = np.searchsorted(self.wavelengths, self.xclick)
        click_wavelength = self.wavelengths[np.searchsorted(self.wavelengths, self.xclick)]
        flux_range = self.fluxes[line_index - 15:line_index + 15]

        flux_max_index = np.argmax(flux_range)
        max_wavelength_index = line_index - 15 + flux_max_index
        linewidth = 50

        cont_subtracted_fluxes = self.fluxes[max_wavelength_index - linewidth:max_wavelength_index + linewidth] - self.continuum_fit[max_wavelength_index - linewidth:max_wavelength_index + linewidth]


        xdata = np.array(self.wavelengths[max_wavelength_index - linewidth:max_wavelength_index + linewidth])
        
        p0 = [np.max(cont_subtracted_fluxes), xdata[np.argmax(cont_subtracted_fluxes)], 1.0] 

        popt, pcov = curve_fit(Eq.gaussian, xdata, cont_subtracted_fluxes, p0=p0)

        fit_y = Eq.gaussian(xdata, *popt)

        self.canvas.axes.plot(xdata, fit_y, '--', color='blue', label=f'Line {self.wavelengths[max_wavelength_index]}')
        
        
        self.canvas.axes.plot(self.wavelengths[max_wavelength_index - linewidth:max_wavelength_index + linewidth], cont_subtracted_fluxes, '--', color = 'red')        
        # self.canvas.axes.axvline(click_wavelength, color = 'orange')
        # self.canvas.axes.plot(self.wavelengths[max_wavelength_index], self.fluxes[flux_max_index], color = 'red')
        self.canvas.axes.legend()
        
        self.canvas.draw()
        self.fitting_line = False

class SpectralLine():
    '''
    For each line, should store:
    - Wavelength
    - Maximum flux
    - Equivalent width
    '''
        

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()