'''
Zachary Stevens
Final Project - ASTR 5470
Quasar Spectral Analysis in Python
'''

# ----------------------------
# Import statements
# ----------------------------
import os
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
from scipy import integrate

from prettytable import PrettyTable
# ----------------------------


# ----------------------------
# Canvas class
# ----------------------------
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        
        
# ----------------------------
# For any equations used throughout
# ----------------------------
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
        self.object_name = ''
        
        self.wavelengths = []
        self.fluxes = []
        
        self.continuum_wavelengths = []
        self.continuum_fluxes = []
        
        self.continuum_fit = []
        
        self.xclick = 0.
        self.yclick = 0.
        
        self.line_catalog = []
        
        self.line_catalog_output = PrettyTable()
        
        
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
        
        self.def_cont_button = QPushButton("Define Continuum", self)
        self.def_cont_button.clicked.connect(self.define_continuum)
        self.def_cont_button.setGeometry(170, 10, 80, 30)
        
        self.fit_line_button = QPushButton("Fit Spectral Line", self)
        self.fit_line_button.clicked.connect(self.toggle_fit_spectral_line)
        self.fit_line_button.setGeometry(170, 10, 80, 30)
        
        self.smooth_button = QPushButton("Smooth", self)
        self.smooth_button.clicked.connect(self.smooth)
        self.smooth_button.setGeometry(170, 10, 80, 30)
        
        self.line_catalog_button = QPushButton("Print Line Catalog - (View Data Before Saving File and Closing Program)", self)
        self.line_catalog_button.clicked.connect(self.print_line_catalog)
        self.line_catalog_button.setGeometry(170, 10, 80, 30)
        
        self.save_line_catalog_button = QPushButton("Save Line Catalog - (Will END Program!)", self)
        self.save_line_catalog_button.clicked.connect(self.save_line_catalog)
        self.save_line_catalog_button.setGeometry(170, 10, 80, 30)
        
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
        '''
        Future Functions to Add
        - Revert to original (save the original file somewhere, then revert back to that if needed)
        - Smoothing function should have a feature to allow you to choose how much to smooth by...
        - Haircut clip
        - A subtract continuum function
        '''
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.open_file_button)
        layout.addWidget(self.def_cont_button)
        layout.addWidget(self.smooth_button)
        layout.addWidget(self.fit_line_button)
        layout.addWidget(self.line_catalog_button)
        layout.addWidget(self.save_line_catalog_button)
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
        
        Future Work:
        - This should be adaptable to many more filetypes such as fits files and more general csv files. Currently it really only takes the csv filetypes that are provided.
        '''
        filename, _ = QFileDialog.getOpenFileName(self, "Open Spectrum", "", "CSV files (*.csv)")
        if filename:
            self.file_is_loaded = True
            self.object_name = str(filename[-16:-11])
            data = pd.read_csv(filename, delim_whitespace=True, skiprows=1)
            self.wavelengths, self.fluxes = (data.iloc[:, 0], data.iloc[:, 1])
            self.canvas.axes.cla()
            self.canvas.axes.plot(self.wavelengths, self.fluxes)
            self.canvas.axes.axhline(0, color = 'black')
            self.canvas.axes.set_title(f'{self.object_name}')
            self.canvas.axes.set_xlabel("Wavelength (Angstroms)")
            self.canvas.axes.set_ylabel("Flux (erg/s/cm2/A)")
            self.canvas.draw()
            
            
    def define_continuum(self):
        '''
        This function takes every 200th datapoint within the function and fits a third order polynomial to it, shown in red.
        It then removes all points >1*sigma away from the second order fit.
        Removed points are shown in red.
        It then fits a fifth order polynomial to the remaining points. Both the remaining points and the fit are shown in green.
        '''
        try:
            x = self.wavelengths
            y = self.fluxes
            f = interpolate.interp1d(x, y)
            orig_continuum_wavelengths = np.arange(self.wavelengths[0], self.wavelengths[len(self.wavelengths) - 1], 200)
            orig_continuum_fluxes = f(orig_continuum_wavelengths)
            
            original_fit = np.polyfit(orig_continuum_wavelengths, orig_continuum_fluxes, 3, full=True)
            original_yfit = np.polyval(original_fit[0], orig_continuum_wavelengths)
            
            residuals = orig_continuum_fluxes - original_yfit
            std_residuals = np.std(residuals)
            filtered_indices = np.abs(residuals) <= std_residuals

            self.continuum_wavelengths = orig_continuum_wavelengths[filtered_indices]
            self.continuum_fluxes = orig_continuum_fluxes[filtered_indices]
            
            filtered_fit = np.polyfit(self.continuum_wavelengths, self.continuum_fluxes, 5, full=True)
            filtered_yfit = np.polyval(filtered_fit[0], self.continuum_wavelengths)
            self.continuum_fit = np.polyval(filtered_fit[0], self.wavelengths)

            self.canvas.axes.plot(orig_continuum_wavelengths, orig_continuum_fluxes, 'o', color = 'red')
            self.canvas.axes.plot(self.continuum_wavelengths, self.continuum_fluxes, 'o', color='green')
            
            self.canvas.axes.plot(orig_continuum_wavelengths, original_yfit, '-', color='red', label = 'Original Continuum Fit')
            self.canvas.axes.plot(self.wavelengths, self.continuum_fit, '-', color='green', label = 'Final Continuum Fit')
            self.canvas.axes.legend()
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
        Currently all it does is take every other point. However, I should actually implement a smoothing filter. I will hopefully do that.
        If I *don't* (which, as the days pass, it looks less and less like I will), I'd implement a flux conserving resampler and use that.
        I've used it in the past - however, I remember it being a bit of a pain to implement because it uses astropy stuff, and I'd have to convert all my data
            into 1DSpectrum types...
        Overall, that's *absolutely* what I would do going forward if I continued this project. However... time constraints :(
        '''
        try:
            self.wavelengths = self.wavelengths[::2]
            self.fluxes = self.fluxes[::2]
            # self.fluxes = f(self.wavelengths)
            self.canvas.axes.cla()
            self.canvas.axes.plot(self.wavelengths, self.fluxes, '-', color = 'blue')
            self.canvas.draw()
        except:
            if not self.file_is_loaded:
                print("Load a file in!!")
            else:
                traceback.print_exc()
    
    
    def on_click(self, event):
        if event.button == 1 and event.inaxes:
            self.xclick, self.yclick = event.xdata, event.ydata
            try:
                if self.fitting_line:
                    MainWindow.fit_spectral_line(self)
            except:
                if not self.file_is_loaded:
                    print("Load a file in!!")
                elif not self.continuum_is_calculated:
                    print("Make sure to define your continuum!")
                else:
                    traceback.print_exc()
                    

    def toggle_fit_spectral_line(self):
        self.fitting_line = True        
        
    
    def fit_spectral_line(self):
        '''
        This function first finds the maximum flux value within a set range of where you click to fit in order to define the peak of the spectral line.
        It is a bit of a narrow range, so be fairly precise when you're identifying a line!
        The algorithm then subtracts the continuum from the data at 50 points to the left and the right and leaves us with the residuals, plotted in dotted red.
        We then fit a Gaussian to the residual data.
        
        After fitting the Gaussian, we integrate to calculate the flux underneath.
        This is saved as total flux.
        Then, we divide this area by the flux value of the continuum at the peak wavelength of the line in order to get the equivalent width.
        This assumes a flat, linear continuum, which is evidently untrue. 
        However, this method is rough, and provides a generally accurate evaluation.
        
        Future work:
            - Should implement a part of the function where you click on the edges of the line to define it.
              Evidently, some lines are much more narrow and some much wider than the 50 datapoints allowed by my function. 
              In the future I'd like to allow the user to define the edges of the line a little easier.
        '''
        
        # This section searches for the nearest local maximum
        line_index = np.searchsorted(self.wavelengths, self.xclick)
        click_wavelength = self.wavelengths[np.searchsorted(self.wavelengths, self.xclick)]
        flux_range = self.fluxes[line_index - 15:line_index + 15]
        flux_max_index = np.argmax(flux_range)
        max_wavelength_index = line_index - 15 + flux_max_index
        max_flux_value = flux_range[max_wavelength_index]
        
        # This block then fits a Gaussian to the flux values for 50 points to the left and right. 
        # I might change this soon because this is obviously not enough for some lines, and far too much for others.
        linewidth = 50
        cont_subtracted_fluxes = self.fluxes[max_wavelength_index - linewidth:max_wavelength_index + linewidth] - self.continuum_fit[max_wavelength_index - linewidth:max_wavelength_index + linewidth]
        xdata = np.array(self.wavelengths[max_wavelength_index - linewidth:max_wavelength_index + linewidth])
        p0 = [np.max(cont_subtracted_fluxes), xdata[np.argmax(cont_subtracted_fluxes)], 1.0] 
        params, covariance = curve_fit(Eq.gaussian, xdata, cont_subtracted_fluxes, p0=p0)
        fit_y = Eq.gaussian(xdata, *params)
        
        # Now we calculate the equivalent width
        area = integrate.simpson(fit_y, x=xdata)
        equivalent_width = area/self.continuum_fit[max_wavelength_index]
    
        # This block now saves the data of that line. I hope.
        line = SpectralLine(wavelength = self.wavelengths[max_wavelength_index], fit = fit_y, eq_wid=equivalent_width, max_flux=max_flux_value, total_flux = area)
        self.line_catalog.append(line)

               
        # Plotting!
        self.canvas.axes.plot(xdata, fit_y, '--', label=f'Line {self.wavelengths[max_wavelength_index]}')    
        self.canvas.axes.plot(self.wavelengths[max_wavelength_index - linewidth:max_wavelength_index + linewidth], cont_subtracted_fluxes, '--', color = 'red')        
        self.canvas.axes.legend()
        self.canvas.draw()
        self.fitting_line = False
        
        
    def print_line_catalog(self):
        print('-----------')
        for line in self.line_catalog:
            print("\nWavelength:  ", line.line_wav, "(Angstroms)")
            print("- Max Flux:  ", line.max_flux, "(erg/s/cm2/A)")
            print("- Tot. Flux: ", line.total_flux, "(erg/s/cm2/A)")
            print("- Eq. Width: ", line.equivalent_width, "(Angstroms)")
        print('-----------')
            
            
    def save_line_catalog(self):
        '''
        Saves a .csv file of the emission line data
        '''
        
        self.line_catalog_output.field_names = ["Wavelength (Angstroms)", "Equivalent Width", "Peak Flux", "Total Flux"]
        for line in self.line_catalog:
            self.line_catalog_output.add_row([line.line_wav, line.equivalent_width, line.max_flux, line.total_flux])
            
        print(self.line_catalog_output)
        
        if not os.path.exists("./Line Catalogs/"):
            os.mkdir("./Line Catalogs/")
            
        with open(f'./Line Catalogs/{self.object_name} Line Catalog.csv', 'w', newline='') as obj_output:
            obj_output.write(self.line_catalog_output.get_csv_string(delimiter = ' '))
            
        self.close()
            

        
class SpectralLine():
    '''
    For each line, should store:
    - Wavelength
    - Maximum flux
    - Equivalent width
    '''
    
    def __init__(self, wavelength, fit, eq_wid, max_flux, total_flux):
        self.line_wav = wavelength
        self.line_fit = fit
        self.equivalent_width = eq_wid
        self.max_flux = max_flux
        self.total_flux = total_flux

        

app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()