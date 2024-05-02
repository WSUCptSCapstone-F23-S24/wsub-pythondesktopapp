# HOW TO RUN THE DATA PROCESSOR SCRIPT#
NOTE: A user may need to install a python environment. Please following instructions to download Python3+.
Following that you may need to navigate to this directory and execute the command "pip install -r requirements.txt"

1. Start mass spectrometer so that it is delivering data to this computer via usb. 

2. Double click "processData.bat" this will kick off the processing script, if everything goes to plan the data will be stored in a unique folder in the "Acquisitions" directory. 

3. If it doesn't work there may be an issue with the USB port being recognized. You may need to edit the naming of the "ComPort" variable in "main.py". The correct naming can be found by looking at the Device Manager, some guess and check may be required.  