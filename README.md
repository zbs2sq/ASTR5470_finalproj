# ASTR5470_finalproj
Final Project for Computational Astro
By Zach Stevens

This project aims to evaluate quasar spectra within a Python GUI. 

----------------
HOW TO USE:
To use this code, all one has to do is run 
    >>> python interactive_plot.py
in the respective file location.
You will likely want to keep your command terminal open and visible, as there are occasional outputs that are printed to the command terminal.


-- OPENING FILES --
One should have a set of spectral files that are available for testing. 
The code assumes the file is a .csv file.
Numerous example files are provided in the github repository for convenience of testing.
Use the Open File button to navigate to a directory with a file you want to open.
This file will have a header with two column names - wavelength and flux, followed by a line #start.
The #start line is necessary for another analysis package that my advisor and I use, but is not necessarily needed in this package.
The file read-in can be changed in the .open_file() function.
Then, the two columns will have the respective data below.
An example of the header is provided below:

    Wavelength (Angstroms) Flux (erg/s/cm2/A)
    # start
    3400.00 0
    3401.50 5.5841e-17 
    3403.00 5.3685e-17 
    3404.50 7.3817e-17 
    ...     ...
   
(As a note - these files are outputs from yet unpublished research so... I guess be careful with them please :) )


-- OTHER FUNCTIONS --

The other functions are fairly well documented within interactive_plot.py, but for convenience their headers are listed below.


-- Defining Continua --

This function takes every 200th datapoint within the function and fits a third order polynomial to it, shown in red.
It then removes all points >1 * sigma away from the second order fit.
Removed points are shown in red.
It then fits a fifth order polynomial to the remaining points. Both the remaining points and the fit are shown in green.
This is done with very little user input other than clicking the button, but parameters for polyfit order can be changed within the function define_continuum().


-- Smooth --

This function isn't functioning quite how I'd like it to.
Currently all it does is take every other point.
In the future, I'd implement a flux conserving resampler and use that.
I've used it in the past - however, I remember it being a bit of a pain to implement because it uses astropy stuff, and I'd have to convert all my data into 1DSpectrum types...
Overall, that's *absolutely* what I would do going forward if I continued this project. 
However... time constraints :(


-- Fit Spectral Line --

First, activate the function by clicking Fit Spectral Line.
Then, click near the peak of the nearest emission line.

This function first finds the maximum flux value within a set range of where you click to fit in order to define the peak of the spectral line.
It is a bit of a narrow range, so be fairly precise when you're identifying a line!
The algorithm then subtracts the continuum from the data at 50 points to the left and the right and leaves us with the residuals, plotted in dotted red.
We then fit a Gaussian to the residual data.

Then, we seek to define an equivalent width of the line.
After fitting the Gaussian, we integrate to calculate the flux underneath.
Then, we divide this area by the flux value of the continuum at the peak wavelength of the line.
This assumes a flat, linear continuum, which is evidently untrue. 
However, this method roughly works, and provides a generally accurate evaluation.

This spectral line will be saved to the Spectral Line Catalog, which can be printed and saved later once all lines have been added.

Future work:
    - Should implement a part of the function where you click on the edges of the line to define it.
      Evidently, some lines are much more narrow and some much wider than the 50 datapoints allowed by my function. 
      In the future I'd like to allow the user to define the edges of the line a little easier.
    - Other calculations within the emission line data are very easy to add to the function.

-- Print and Save Line Catalog --

Print Line Catalog prints all saved spectral lines to the command terminal, with their respective wavelength values, maximum fluxes, and equivalent widths.
The Save Line Catalog button then saves the catalog to a .csv file titled with the object name, followed by 'Line Catalog.'
This file contains the data of each emission line.

-- Saving plots --

One will likely desire to save an image of emission lines, continua, and the like.
The toolbar at the top of the widget allows for zoom-ins of the plot, movement throughout, and saving the plot as any file type the user would like.


------------------------
GOALS:

In the project proposal, I laid out four main ideas for what this code would do:

1) It would calculate the continuum by calculating a low order fit, rejecting points outside a certain range, and refitting higher order polynomial.
2) It would detect the reshift of the object or have the redshift input by the user and automatically find emission lines.
3) Each emission line would then get multiple values measured:
    - First, it would subtract the continuum from the values of the spectra identified around where the line is.
    - It would then fit Gaussian fit to the emission line, retrieving the best fit parameters.
    - It would then have a function allowing to subtract emission lines from each other in the case of having multiple next to each other.
    - Overall, it would gather equivalent widths, maximum flux avlues, and other datapoints.
4) Finally, there was a possibility of implementing a method of identifying spectral types using machine learning from inputting numerous quasar files.

RESULTS:

1) The continuum fitting was successfully implemented!
2) A redshift calculation was not implemented, unfortunately, but this should be fairly easy to do in the future.
3) The emission line measurements were implemented with great success, and more calculations are very easy to add to the function.
4) To not much surprise, I did not get to implement the machine learning.

----------------------
TESTS OF SUCCESS:

1) Testing Residuals
Generally, the residuals of the spectral lines with the continuum subtracted have a baseline very close to y=0, which demonstrates a good fit of the continuum and a successful subtraction.

3) Examining Gaussian Fits
For each Gaussian fit to spectral data, we get a generally very good fit, which is promising.
We do have a few exceptions, however.
If the continuum subtraction isn't totally successful, or we have a second spectral line nearby, the Gaussian can capture this extra data and be skewed.
This would be important to fix in the future by implementing a way to define the edges of each emission line so that extra data is not added in.

4) Emission Line Data Confirmation
I tested how well my fits of emission lines were with a fairly robust program written by my advisor Prof. Mark Whittle.
I analyzed the line at ~4400A in the object J1246 in both programs and found the following.

Line Wavelength:
- Zach Program: 4399.0A
- Whittle Program: 4407A
(Offset is due to more ambiguous central definition in Whittle's program)

Eq. Width:
- Zach Program: 76.7 A
- Whittle Program: 97.2 A
Offset is likely because the automatic continuum created in my program is not as accurate as the continuum defined in Whittle's program.
I also assume a constant continuum using the value of the continuum at the peak of the emission line.
My method is not as accurate, but it is still on the correct order of magnitude, which is promising.

Total Flux:
- Zach Program: 5.32e-15 (erg/s/cm2/A)
- Whittle Program: 6.65e-15 (erg/s/cm2/A)
This is only a very slight offset, which is once again promising.
Offset likely comes from the issue that we are not capturing the entire line in my program, which will be fixed in the futre when one is able to define the edges of the line.

------------
SUMMARY

Overall, I am very proud of how this project turned out.
I've not created a GUI like this before, and this took a significant portion of my time to get set up.
I think the interface is very straightforward to use and the code is well implemented, and I'm proud of how it turned out.
It is very quick and easy to use and returns calculations very quickly and with fair accuracy.
