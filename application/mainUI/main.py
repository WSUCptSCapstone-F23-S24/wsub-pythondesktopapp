
"""
__author__ = "Ritik Agarwal, Zoe Parker"
__credits__ = ["Ritik Agarwal", "Zoe Parker"]
__version__ = "1.0.0"
__maintainer__ = ""
__email__ = ["agarwal.ritik1101@gmail.com", "zoeparker@comcast.net"]
__status__ = "Completed"
"""

# from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QSizePolicy, QMainWindow, QMenuBar, QFileDialog, QAction
from PyQt5.QtWidgets import QSizePolicy, QDialogButtonBox
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QMovie

import pyqtgraph as pg
import sys, os, csv
from worker import Worker
from newFileNotifierThread import NewFileNotifierThread
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, QSize
import numpy as np
from time import time
from stopwatch import Stopwatch
from datetime import datetime
from math import floor
from plotAllThread import PlotAllThread


#####################################################################

# 1. Idle (When the application is started and no data folder is selected.)
# 2. Selected (Data folder is selected but thread is not running)
# 3. Running (Thread is Running and data is plotting)
# 4. Paused (Application is paused)
# 5. Out_Of_Data (Application is out of data and is idle. Thread also ended.)

#####################################################################

# adding read-data to the system path
sys.path.append('../read-data')

# adding uiElements to the system path
sys.path.append('../uiElements')

# adding read-data to the system path
sys.path.append('../calculations')

from getData import GetData
from sharedSingleton import SharedSingleton
from curve import Curve
from graph import Graph
from frame import Frame
from Calculations import Calculations
from button import Button
from dialog import Dialog
from LineEdit import LineEdit
from dataUtility import DataUtility


class LabView(QtWidgets.QMainWindow):

    def __init__(self, width, height, app):
        """
        This method initializes the LabView class.
        This is where we initialize values and call the methods that create the User Interface
        """
        super(LabView, self).__init__()

        self.app = app
        self.screen_width = width
        self.screen_height = height

        self.setGeometry(0, 0, width, height)
        self.setMinimumSize(int(width//2), int(width//2))

        # get current user's username
        self.user = os.getlogin()

        # Setting varibales that will be used for the logic

        self.pauseBit = False
        self.startBit = False
        self.setWindowTitle("LabView")
        self.sharedData = SharedSingleton()
        self.sharedData.fileList = []
        self.sharedData.dataPoints = {}
        self.sharedData.folderAccessed = False
        self.sharedData.xPoint = 0
        self.delay = 200
        self.stopwatch = Stopwatch()
        self.firstPoint = False
        self.yAllMax = None
        self.yAllMin = None
        self.isYChanged = False
        self.fileCheckThreadStarted = False

        self.application_state = "Idle"

        # List of UI elements
        self.lineEditList = []

        # Dictionaries to hold data for graphs
        self.assayBufferData = {}
        self.hclData = {}
        self.o2VelocityConcentrationData = {}
        self.co2VelocityConcentrationData = {}

        # Initialize O2 and CO2 Calibrations
        self.temperature = 0
        self.o2Calibration = 0
        self.co2BufferCalibration = 0
        self.co2HCLCalibration = 0
        self.biCarbCo2Ratio = 0

        # Initialize CO2 and O2 Blank values
        self.co2Blank = 0
        self.o2Blank = 0

        # Initialize CO2 and O2 Extract values
        self.co2Extract = 0
        self.o2Extract = 0

        #Initialize CO2 and O2 net rate of consumption
        self.co2ConsumptionRate = 0
        self.o2ConsumptionRate = 0

        # Initialize CO2 and O2 rate of consumption and concentrations
        self.vC = 0
        self.vO = 0
        self.co2Concentration = 0
        self.o2Concentration = 0

        self.co2Zero44Reading = 0
        

        self.keepCals = False
        self.folder_path = ''

        # Data Object for getting the points.
        self.dataObj = GetData()

        # Initialize scroll area
        self.initializeScrollArea()

        # Initialzie the QFrames
        self.initializeQFrames()

        # Initializing raw data plot.
        self.rawDataPlotUI()

        # Initializing calculation plot
        self.calculatedPlotsUI()

        # Initializing calculation buttons
        self.calculationButtonsUI()

        # List of calibration line edits
        self.calibrationLineEdits = [self.temperatureLineEdit, self.o2CalibrationLineEdit, self.o2ZeroLineEdit, self.biCarbCo2LineEdit,
                                    self.co2CalZeroLineEdit, self.co2Cal1ulLineEdit, self.co2Cal2ulLineEdit, self.co2Cal3ulLineEdit,
                                    self.biCarbCalZeroLineEdit, self.biCarbCal2ulLineEdit, self.biCarbCal4ulLineEdit,
                                    self.biCarbCal6ulLineEdit]
                                    

        # Add curves and Mean bar to the real time plot
        self.addCurveAndMeanBar()

        # Connect UI to Methods
        self.connectUItoMethods()

        self.show()



        
#################################################################################################################################
################################################# User Interface Creation #################################################
    """
    The user interface is broken up into three frames:
    - one frame for the raw data plot (rawDataPlotUI)
    - one for the calculated plots(calculatedPlotsUI)
    - one for the calculation buttons and table (calculationButtonsUI)

    For each frame, we create the user interface elements(graphs/plots, buttons, line edits, labels, checkboxes, etc.)
    We then have to add these elements to layouts 
    Layouts are then added to the frame.

    Other UI creation methods
    - initializeScrollArea: Give app ability to scroll
    - initializeQFrames: Initializes the frames mentioned above
    - addCurveAndMeanBar: Adds the 8 data stream curves to the raw data plot, creates the mean bars
    - connectUItoMethods: Connects the UI elements to methods - tells the program what to do when a UI element is interacted with

    """


    def rawDataPlotUI(self):
        """
        Generates the all the UI elements for the Raw Data Plot:
        - Graph Checkboxes
        - BarButton, Rescale, Start Pause/Resume Slider
        - Raw Plot Graph
        """

        ############################## Check Boxes Layout ##################################
        # Initializing all the graphs
        self.graph1CheckBox = QtWidgets.QCheckBox("Mass 32",self)
        self.graph1CheckBox.setStyleSheet("color: #800000")
        self.graph2CheckBox = QtWidgets.QCheckBox("Mass 44",self)
        self.graph2CheckBox.setStyleSheet("color: #4363d8")
        
        # Initially all the graphs checkboxes should be checked.
        self.graph1CheckBox.setChecked(False) 
        self.graph2CheckBox.setChecked(False)
        
        # Creating vertical layout for check boxes.
        self.checkBoxVLayout = QtWidgets.QVBoxLayout()
        self.checkBoxVLayout.setSpacing(10)

        # Adding check boxes to the checkBoxWidget layout
        self.checkBoxVLayout.addWidget(self.graph1CheckBox)
        self.checkBoxVLayout.addWidget(self.graph2CheckBox)
       
        
        #############################################################################################


        ############################## BarButton, Rescale, Start Pause/Resume Slider Layout #############################

        # Mean Bar Button
        self.barsButton = Button("| |", 26, 26)
        # Start Button
        self.startButton = Button("Start", 120, 26)

        self.plotAllButton = Button("Plot All", 120, 26)

        # Pause/Resume Button
        self.pauseResumeButton = Button("Pause", 120, 26)

        # Rescale Button
        self.rescaleButton = Button("Rescale", 120, 26)

        self.processSpinnerLabel = QtWidgets.QLabel()
        self.processSpinnerLabel.setMinimumSize(QtCore.QSize(50, 50))
        self.processSpinnerLabel.setMaximumSize(QtCore.QSize(50, 50))

        self.movie = QMovie("spinner50px.gif")
        self.movie.jumpToFrame(0)
        self.processSpinnerLabel.setMovie(self.movie)
        self.processSpinnerLabel.hide()

        # self.movie.start()

        # Slider
        self.speedSlider = QtWidgets.QSlider(Qt.Horizontal)
        self.speedSlider.setRange(0, 3200)
        self.speedSlider.setValue(100)
        self.speedSlider.setTickInterval(100)
        self.speedSlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.speedSlider.setFixedSize(900, 50)
        self.speedSlider.valueChanged.connect(self.speedSliderValueChanged)

        self.slidervbox = QtWidgets.QVBoxLayout()
        self.slidervbox.addWidget(self.speedSlider)

        # Create labels for each tick value
        self.hTickbox = QtWidgets.QHBoxLayout()
        self.speedLabels = [".05x", "2x", "4x", "6x","8x", "10x", "12x", "14x", "16x", "18x", "20x", "22x",
                            "24x", "26x", "28x", "30x", "32x"]
        for label in self.speedLabels:
            tickLabel = QtWidgets.QLabel(label, self)
            # tickLabel.setAlignment(Qt.AlignCenter)
            self.hTickbox.addWidget(tickLabel)

        self.slidervbox.addLayout(self.hTickbox)
        self.slidervbox.setSpacing(0)
        self.hTickbox.setSpacing(30)

        # Creating a Horizontal Layout for Start Pause/Resume and Slider 
        self.rescaleStartPauseResumeSliderGridLayout = QtWidgets.QGridLayout()
        self.rescaleStartPauseResumeSliderGridLayout.addWidget(self.processSpinnerLabel, 0, 1)
        self.rescaleStartPauseResumeSliderGridLayout.addWidget(self.barsButton, 0, 2)
        self.rescaleStartPauseResumeSliderGridLayout.addWidget(self.plotAllButton, 0, 3)
        self.rescaleStartPauseResumeSliderGridLayout.addWidget(self.rescaleButton, 0, 4)
        self.rescaleStartPauseResumeSliderGridLayout.addWidget(self.startButton, 0, 5)
        self.rescaleStartPauseResumeSliderGridLayout.addWidget(self.pauseResumeButton, 0, 6)
        self.rescaleStartPauseResumeSliderGridLayout.addLayout(self.slidervbox, 0, 10)
        self.rescaleStartPauseResumeSliderGridLayout.setSpacing(30)
        self.rescaleStartPauseResumeSliderGridLayout.setColumnStretch(0,0)
        self.rescaleStartPauseResumeSliderGridLayout.setColumnStretch(0,1)
        #############################################################################################

        ############################## {Graph} AND {Start Pause/Resume Slider Layout} ###############
        
        # Graph
        self.realTimeGraph = Graph(100,100)
        self.realTimeGraph.setLabel(axis='left', text = 'Voltage (mV)')
        self.realTimeGraph.setLabel(axis='bottom', text = 'Time (s)')
        # self.realTimeGraph.getViewBox().wheelEvent = self.on_wheel_event
        
        self.graphVLayout = QtWidgets.QVBoxLayout()
        self.graphVLayout.setContentsMargins(0, 40, 0, 0)
        self.graphVLayout.addWidget(self.realTimeGraph)

        # Layout for {Graph} AND {Start Pause/Resume Slider Layout}
        self.graphStartPauseResumeSliderVLayout = QtWidgets.QVBoxLayout()
        self.graphStartPauseResumeSliderVLayout.addLayout(self.graphVLayout)   # Widget containing graph
        self.graphStartPauseResumeSliderVLayout.addLayout(self.rescaleStartPauseResumeSliderGridLayout)  # Widget containing start pause/resume and slider
        ###############################################################################################

        ############### {Checkboxes} AND {{Graph} AND {Start Pause/Resume Slider Layout}} ###############

        # QFrame Widget is already initialized. Adding layout to the layout.
        self.rawDataPlotHLayout = QtWidgets.QHBoxLayout()
        self.rawDataPlotFrame.setFrameLayout(self.rawDataPlotHLayout)
        self.rawDataPlotHLayout.addLayout(self.checkBoxVLayout)
        self.rawDataPlotHLayout.addLayout(self.graphStartPauseResumeSliderVLayout)
        ###############################################################################################
        

    def calculatedPlotsUI(self):

        ###################################### QFormLayout for Assay Buffer #####################################

        # Widgets to be added in the layout
        self.intercept1Label = QtWidgets.QLabel("Intercept")
        self.biCarbCalLabel = QtWidgets.QLabel("BiCarb cal\n(nmol/ml/mV)")
        self.assayBufferLabel = QtWidgets.QLabel("Assay Buffer")
        self.emptyLabel = QtWidgets.QLabel("")

        self.intercept1LineEdit = LineEdit()
        self.biCarbCalLineEdit = LineEdit()
        
        self.lineEditList.extend([self.intercept1LineEdit, self.biCarbCalLineEdit])

        self.assayBufferBoxGridLayout = QtWidgets.QGridLayout()
        self.assayBufferBoxGridLayout.addWidget(self.emptyLabel, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.assayBufferBoxGridLayout.addWidget(self.intercept1Label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.assayBufferBoxGridLayout.addWidget(self.biCarbCalLabel, 1, 3, alignment=QtCore.Qt.AlignCenter)
        self.assayBufferBoxGridLayout.addWidget(self.assayBufferLabel, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.assayBufferBoxGridLayout.addWidget(self.intercept1LineEdit, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.assayBufferBoxGridLayout.addWidget(self.biCarbCalLineEdit, 2, 3, alignment=QtCore.Qt.AlignCenter)
        self.assayBufferBoxGridLayout.setHorizontalSpacing(10)
        ###############################################################################################

        ###################################### QFormLayout for HCL #####################################

        # Widgets to be added in the layout
        self.intercept2Label = QtWidgets.QLabel("Intercept 2")
        self.nmolLabel = QtWidgets.QLabel("(nmol/ml/mV)\n")
        self.hclLabel = QtWidgets.QLabel("HCL")

        self.intercept2LineEdit = LineEdit()
        self.nmolLineEdit = LineEdit()

        self.lineEditList.extend([self.intercept2LineEdit, self.nmolLineEdit])

        self.hclBoxGridLayout = QtWidgets.QGridLayout()
        self.hclBoxGridLayout.addWidget(self.emptyLabel, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.hclBoxGridLayout.addWidget(self.intercept2Label, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.hclBoxGridLayout.addWidget(self.nmolLabel, 1, 3, alignment=QtCore.Qt.AlignCenter)
        self.hclBoxGridLayout.addWidget(self.hclLabel, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.hclBoxGridLayout.addWidget(self.intercept2LineEdit, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.hclBoxGridLayout.addWidget(self.nmolLineEdit, 2, 3, alignment=QtCore.Qt.AlignCenter)
        ###############################################################################################



        ######################## {QFormLayout for Assay Buffer} AND {Assay Buffer Graph} #######################

        self.assayBufferGraph = Graph(100,180)
        self.assayBufferGraph.setLabel(axis='left', text = 'CO2 (nmol/ml)')
        self.assayBufferGraph.setLabel(axis='bottom', text = 'Voltage (mV)')
        self.assayBufferGraph.getViewBox().wheelEvent = self.on_wheel_event
        self.assayBufferGraphVLayout = QtWidgets.QVBoxLayout()
        self.assayBufferGraphVLayout.setContentsMargins(0, 40, 0, 0)
        self.assayBufferGraphVLayout.addWidget(self.assayBufferGraph)

        self.assayBufferGraphBoxGridVLayout = QtWidgets.QVBoxLayout()
        self.assayBufferGraphBoxGridVLayout.addLayout(self.assayBufferBoxGridLayout)
        self.assayBufferGraphBoxGridVLayout.addLayout(self.assayBufferGraphVLayout)
        #################################################################################################

        ######################## {QFormLayout for HCL} AND {HCL Graph} #######################

        self.hclGraph = Graph(100,180)
        self.hclGraph.setLabel(axis='left', text = 'BiCarb (nmol/ml)')
        self.hclGraph.setLabel(axis='bottom', text = 'Voltage (mV)')
        self.hclGraph.getViewBox().wheelEvent = self.on_wheel_event
        self.hclGraphVLayout = QtWidgets.QVBoxLayout()
        self.hclGraphVLayout.setContentsMargins(0, 40, 0, 0)
        self.hclGraphVLayout.addWidget(self.hclGraph)


        self.uBarGraph = Graph(100,180)
        self.uBarGraph.setLabel(axis='left', text = 'uBar')
        self.uBarGraph.setLabel(axis='bottom', text = 'Time')
        self.uBarGraph.getViewBox().wheelEvent = self.on_wheel_event
        self.uBarGraphVLayout = QtWidgets.QVBoxLayout()
        self.uBarGraphVLayout.setContentsMargins(0, 40, 0, 0)
        self.uBarGraphVLayout.addWidget(self.uBarGraph)

        self.hclGraphBoxGridVLayout = QtWidgets.QVBoxLayout()
        self.hclGraphBoxGridVLayout.addLayout(self.hclBoxGridLayout)
        self.hclGraphBoxGridVLayout.addLayout(self.uBarGraphVLayout)
        ################################################################################################



        ######################## {Concentration Label} AND {Concentration Graph} #######################

        self.concentrationGraph = Graph(100,180)
        self.concentrationGraph.setLabel(axis='left', text = 'Velocity')
        self.concentrationGraph.setLabel(axis='bottom', text = '[CO2] (nmol/ml/sec)')
        self.concentrationGraph.getViewBox().wheelEvent = self.on_wheel_event
        self.concentrationGraphVLayout = QtWidgets.QVBoxLayout()
        self.concentrationGraphVLayout.setContentsMargins(0, 78, 0, 0)
        self.concentrationGraphVLayout.addWidget(self.concentrationGraph)

        self.concentrationLabelGraphVLayout = QtWidgets.QVBoxLayout()
        self.concentrationGraphLabel = QtWidgets.QLabel("Velocity - Concentration Graph")
        self.concentrationGraphLabel.setContentsMargins(0,10,0,0)
        self.concentrationLabelGraphVLayout.addWidget(self.concentrationGraphLabel, alignment=QtCore.Qt.AlignCenter)
        self.concentrationLabelGraphVLayout.addLayout(self.concentrationGraphVLayout)
        #################################################################################################


        # {{QFormLayout for Assay Buffer} AND {Assay Buffer Graph}} AND {{Concentration Label} AND {Concentration Graph}} AND {{Concentration Label} AND {Concentration Graph}} #

        self.calculatedPlotsHLayout = QtWidgets.QHBoxLayout()
        self.calculatedPlotsHLayout.addLayout(self.assayBufferGraphBoxGridVLayout)
        self.calculatedPlotsHLayout.addLayout(self.hclGraphBoxGridVLayout)
        self.calculatedPlotsHLayout.addLayout(self.concentrationLabelGraphVLayout)

        self.calculatedPlotsFrame.setLayout(self.calculatedPlotsHLayout)



    def calculationButtonsUI(self):

        """
            Initializes file menu, calculation button.
            :param {_ : }
            :return -> None
        
        """

        ############################## File Selection QDialog ##############################

        # Create a menu bar
        self.menu_bar = self.menuBar()

        # Create a 'File' menu
        self.file_menu = self.menu_bar.addMenu('File')

        # Add an action to select a folder
        self.select_folder_action = QAction('Select Acq Folder', self)
        self.select_file_action = QAction('Select Cal File', self)
        self.select_folder_action.triggered.connect(self.select_folder)
        self.select_file_action.triggered.connect(self.select_file)
        self.file_menu.addAction(self.select_folder_action)
        self.file_menu.addAction(self.select_file_action)

        ######################## O2 Zero and CO2 cal #############################

        # Initializing all the buttons
        self.o2ZeroButton = Button("O2 Zero", 120, 26)
        self.co2CalZeroButton = Button("CO2 Cal Zero", 120, 26)
        self.co2Cal1ulButton = Button("CO2 Cal 1ul", 120, 26)
        self.co2Cal2ulButton = Button("CO2 Cal 2ul", 120, 26)
        self.co2Cal3ulButton = Button("CO2 Cal 3ul", 120, 26)

        # Initializing line edits
        self.o2ZeroLineEdit = LineEdit()
        self.o2ZeroLineEdit.setReadOnly(False)
        self.co2CalZeroLineEdit = LineEdit()
        self.co2Cal1ulLineEdit = LineEdit()
        self.co2Cal2ulLineEdit = LineEdit()
        self.co2Cal3ulLineEdit = LineEdit()
        self.temperatureLineEdit = LineEdit()

        # Make line edits editable
        self.co2CalZeroLineEdit.setReadOnly(False)
        self.co2Cal1ulLineEdit.setReadOnly(False)
        self.co2Cal2ulLineEdit.setReadOnly(False)
        self.co2Cal3ulLineEdit.setReadOnly(False)
        
        # make temperature LineEdit editable
        self.temperatureLineEdit.setReadOnly(False)

        self.lineEditList.extend([self.o2ZeroLineEdit, self.co2CalZeroLineEdit, self.co2Cal1ulLineEdit, self.co2Cal2ulLineEdit, self.co2Cal3ulLineEdit, self.temperatureLineEdit])

        # Initializing QLabels
        self.o2AssayBufferZeroLabel = QtWidgets.QLabel("O2 Zero")
        self.temperatureLabel = QtWidgets.QLabel("Temperature (C)")
        self.assayBufferLabel = QtWidgets.QLabel("Assay Buffer")

        # Creating a QGrid Layout
        self.o2ZeroCo2CalGridLayout = QtWidgets.QGridLayout()
        self.o2ZeroCo2CalGridLayout.addWidget(self.o2AssayBufferZeroLabel, 1, 1, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.o2ZeroButton, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.o2ZeroLineEdit, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.assayBufferLabel, 3, 1, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2CalZeroButton, 4, 1, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2CalZeroLineEdit, 4, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2Cal1ulButton, 5, 1, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2Cal1ulLineEdit, 5, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2Cal2ulButton, 6, 1, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2Cal2ulLineEdit, 6, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2Cal3ulButton, 7, 1, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.co2Cal3ulLineEdit, 7, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.temperatureLabel, 8, 1, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.o2ZeroCo2CalGridLayout.addWidget(self.temperatureLineEdit, 9, 1, 1, 2, alignment=QtCore.Qt.AlignCenter) # Main Layout 1
        self.o2ZeroCo2CalGridLayout.setRowStretch(1,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(2,2)
        self.o2ZeroCo2CalGridLayout.setRowStretch(3,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(4,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(5,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(6,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(7,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(8,1)
        self.o2ZeroCo2CalGridLayout.setRowStretch(9,1)
        #################################################################################################



        ######################## BiCarb/CO2 and BiCarb cal #############################

        # Initializing all the buttons
        self.biCarbCo2Button = Button("BiCarb/CO2", 120, 26)
        self.biCarbCalZeroButton = Button("BiCarb Cal Zero", 120, 26)
        self.biCarbCal2ulButton = Button("BiCarb Cal 2ul", 120, 26)
        self.biCarbCal4ulButton = Button("BiCarb Cal 4ul", 120, 26)
        self.biCarbCal6ulButton = Button("BiCarb Cal 6ul", 120, 26)

        # Initializing line edits
        self.biCarbCo2LineEdit = LineEdit()
        self.biCarbCalZeroLineEdit = LineEdit()
        self.biCarbCal2ulLineEdit = LineEdit()
        self.biCarbCal4ulLineEdit = LineEdit()
        self.biCarbCal6ulLineEdit = LineEdit()
        self.o2CalibrationLineEdit = LineEdit()

        # Make line edits editable
        self.biCarbCo2LineEdit.setReadOnly(False)
        self.biCarbCalZeroLineEdit.setReadOnly(False)
        self.biCarbCal2ulLineEdit.setReadOnly(False)
        self.biCarbCal4ulLineEdit.setReadOnly(False)
        self.biCarbCal6ulLineEdit.setReadOnly(False)
        self.o2CalibrationLineEdit.setReadOnly(False)

        self.lineEditList.extend([self.biCarbCo2LineEdit, self.biCarbCalZeroLineEdit, self.biCarbCal2ulLineEdit, self.biCarbCal4ulLineEdit, self.biCarbCal6ulLineEdit, self.o2CalibrationLineEdit])

        # Initializing QLabels
        self.biCarbCo2Label = QtWidgets.QLabel("BiCarb/CO2")
        self.o2CalibrationLabel = QtWidgets.QLabel("O2 Calibration")
        self.hclLabel = QtWidgets.QLabel("HCL")

        # Creating a QGrid Layout
        self.biCarbCo2BiCarbCalGridLayout = QtWidgets.QGridLayout()
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCo2Label, 1, 1, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCo2Button, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCo2LineEdit, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.hclLabel, 3, 1, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCalZeroButton, 4, 1, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCalZeroLineEdit, 4, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCal2ulButton, 5, 1, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCal2ulLineEdit, 5, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCal4ulButton, 6, 1, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCal4ulLineEdit, 6, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCal6ulButton, 7, 1, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.biCarbCal6ulLineEdit, 7, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.o2CalibrationLabel, 8, 1, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.biCarbCo2BiCarbCalGridLayout.addWidget(self.o2CalibrationLineEdit, 9, 1, 1, 2, alignment=QtCore.Qt.AlignCenter) # Main Layout 2
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(1,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(2,2)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(3,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(4,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(5,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(6,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(7,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(8,1)
        self.biCarbCo2BiCarbCalGridLayout.setRowStretch(9,1)
        #################################################################################################



        ########################{CO2 Zero Blank Extract} AND {CO2 O2 LineEdit Layout} #############################

        # Initializing line edits
        self.co2LineEdit1 = LineEdit()
        self.co2LineEdit2 = LineEdit()
        self.co2LineEdit3 = LineEdit()
        self.co2LineEdit4 = LineEdit()
        self.o2LineEdit1 = LineEdit()
        self.o2LineEdit2 = LineEdit()
        self.o2LineEdit3 = LineEdit()
        self.o2LineEdit4 = LineEdit()

        self.co2ZeroLineEdit1 = LineEdit()
        self.co2ZeroLineEdit2 = LineEdit()

        self.lineEditList.extend([self.co2LineEdit1, self.co2LineEdit2, self.co2LineEdit3, self.co2LineEdit4, self.o2LineEdit1, self.o2LineEdit2, self.o2LineEdit3, self.o2LineEdit4])
        self.lineEditList.extend([self.co2ZeroLineEdit1, self.co2ZeroLineEdit2])
        
        # Initializing QLabels
        self.co2Label = QtWidgets.QLabel("CO2")
        self.o2Label = QtWidgets.QLabel("O2")

        self.co2Zero44Label =  QtWidgets.QLabel("CO2 Zero\n(Mass 44)")

        self.blankButton = Button("Blank", 120, 26)
        self.extractButton = Button("Extract", 120, 26)

        self.co2ZeroButton = Button("CO2 Zero", 120, 26)


        # Creating a QGrid Layout
        self.co2o2GridLayout = QtWidgets.QGridLayout()
        self.co2o2GridLayout.addWidget(self.co2Zero44Label, 1, 2, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2ZeroButton, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2ZeroLineEdit1, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2ZeroLineEdit2, 2, 3, alignment=QtCore.Qt.AlignCenter)
        
        self.co2o2GridLayout.addWidget(self.co2Label, 3, 2, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.o2Label, 3, 3, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.blankButton, 4, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2LineEdit1, 4, 2, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.o2LineEdit1, 4, 3, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.extractButton, 5, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2LineEdit2, 5, 2, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.o2LineEdit2, 5, 3, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2LineEdit3, 6, 2, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.o2LineEdit3, 6, 3, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.co2LineEdit4, 7, 2, alignment=QtCore.Qt.AlignCenter)
        self.co2o2GridLayout.addWidget(self.o2LineEdit4, 7, 3, alignment=QtCore.Qt.AlignCenter)

        #################################################################################################



        ########################{CO2 Zero Blank Extract} AND {CO2 O2 LineEdit Layout} ###################
        
        # Module 1 concentration labels
        self.percentCO2Label = QtWidgets.QLabel("%CO2")
        self.ubarCO2Label = QtWidgets.QLabel("Ubar CO2")
        
        # Module 1 concentration text boxes
        self.percentCO2LineEdit = LineEdit()
        self.ubarCO2LineEdit = LineEdit()
        
        # Module 1 concentration grid layout
        self.co2ConcentrationGridLayout = QtWidgets.QGridLayout()
        self.co2ConcentrationGridLayout.addWidget(self.percentCO2Label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2ConcentrationGridLayout.addWidget(self.percentCO2LineEdit, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.co2ConcentrationGridLayout.addWidget(self.ubarCO2Label, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.co2ConcentrationGridLayout.addWidget(self.ubarCO2LineEdit, 2, 2, alignment=QtCore.Qt.AlignCenter)
        
        # unused leftover elements
        #Velocity and CO2 O2 Concentration Labels
        self.v0Label = QtWidgets.QLabel("V0")
        self.vcLabel = QtWidgets.QLabel("Vc")
        self.co2ConcentrationLabel = QtWidgets.QLabel("[CO2]")
        self.o2ConcentrationLabel = QtWidgets.QLabel("[O2]")

        #Velocity and CO2 O2 Concentration Text Edit
        self.v0LineEdit = LineEdit()
        self.vcLineEdit = LineEdit()
        self.co2Concentrationv0LineEdit = LineEdit()
        self.o2Concentrationv0LineEdit = LineEdit()

        self.lineEditList.extend([self.v0LineEdit, self.vcLineEdit, self.co2Concentrationv0LineEdit, self.o2Concentrationv0LineEdit])

        self.velocityConcentrationGridLayout = QtWidgets.QGridLayout()
        self.velocityConcentrationGridLayout.addWidget(self.v0Label, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.vcLabel, 1, 2, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.co2ConcentrationLabel, 1, 3, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.o2ConcentrationLabel, 1, 4, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.v0LineEdit, 2, 1, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.vcLineEdit, 2, 2, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.co2Concentrationv0LineEdit, 2, 3, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.addWidget(self.o2Concentrationv0LineEdit, 2, 4, alignment=QtCore.Qt.AlignCenter)
        self.velocityConcentrationGridLayout.setColumnStretch(1,1)
        self.velocityConcentrationGridLayout.setColumnStretch(2,1)
        self.velocityConcentrationGridLayout.setColumnStretch(3,1)
        self.velocityConcentrationGridLayout.setColumnStretch(4,1)
        

        # Add to table and Purge Button
        self.addToTableButton = Button("Add to Table", 120, 26)
        self.purgeTableButton = Button("Purge Table", 120, 26)
        self.exportTableButton = Button("Export Table", 120, 26)
        self.copyTableRowButton = Button("Copy", 120, 26)
        self.stopButton = Button("STOP", 120, 26)

        self.addPurgeTableVLayout = QtWidgets.QVBoxLayout()
        self.addPurgeTableVLayout.addWidget(self.addToTableButton)
        self.addPurgeTableVLayout.addWidget(self.exportTableButton)
        self.addPurgeTableVLayout.addWidget(self.copyTableRowButton)
        self.addPurgeTableVLayout.addWidget(self.stopButton)
        self.addPurgeTableVLayout.addWidget(self.purgeTableButton)


        self.table = QtWidgets.QTableWidget()
        # Dummy row count
        #self.table.setRowCount(4)
        # set column count
        self.table.setColumnCount(4)

        self.tableVLayout = QtWidgets.QVBoxLayout()
        self.tableVLayout.addWidget(self.table)
        
        # Table and addTable purgeTable layout
        self.tableVelocityConcentrationVLayout = QtWidgets.QVBoxLayout()
        self.tableVelocityConcentrationVLayout.addLayout(self.velocityConcentrationGridLayout)
        self.tableVelocityConcentrationVLayout.addLayout(self.tableVLayout)

        # Velocity Concentration Table layout
        self.tableVelocityConcentrationAddPurgeHLayout = QtWidgets.QHBoxLayout()
        self.tableVelocityConcentrationAddPurgeHLayout.addLayout(self.addPurgeTableVLayout)
        self.tableVelocityConcentrationAddPurgeHLayout.addLayout(self.tableVelocityConcentrationVLayout)        # Main Layout 4

        self.calculationButtonsFrameHLayout = QtWidgets.QHBoxLayout()
        self.calculationButtonsFrameHLayout.addLayout(self.o2ZeroCo2CalGridLayout)
        self.calculationButtonsFrameHLayout.addLayout(self.biCarbCo2BiCarbCalGridLayout)
        self.calculationButtonsFrameHLayout.addLayout(self.co2o2GridLayout)
        self.calculationButtonsFrameHLayout.addLayout(self.co2ConcentrationGridLayout)

        self.calculationButtonsFrame.setLayout(self.calculationButtonsFrameHLayout)
        #################################################################################################


    def initializeScrollArea(self):

        # Creating a scroll area and setting its properties.
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)

        # Creating a widget to set on the scroll area.
        self.scrollAreaWidget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.scrollAreaWidget)

        # Creating and setting a layout for scroll area widget.
        self.scrollAreaWidgetLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidget)
        self.scrollAreaWidget.setLayout(self.scrollAreaWidgetLayout)

        # Setting the central widget with the scroll area.
        self.setCentralWidget(self.scrollArea)


    def initializeQFrames(self):

        # Creating a QFrame from User defined QFrame class.
        self.calculatedPlotsFrame = Frame(self.scrollArea)
        self.calculationButtonsFrame = Frame(self.scrollArea)
        self.rawDataPlotFrame = Frame(self.scrollArea)
        
        # Adding QFrames to the scroll area widget layout.
        self.scrollAreaWidgetLayout.addWidget(self.calculatedPlotsFrame)
        self.scrollAreaWidgetLayout.addWidget(self.rawDataPlotFrame)
        self.scrollAreaWidgetLayout.addWidget(self.calculationButtonsFrame)


    def addCurveAndMeanBar(self):

        # Adding the plot curves
        self.curve1 = Curve("Curve 1", [], pg.mkPen(color="#800000", width=4), self.realTimeGraph)
        self.curve1.plotCurve()

        self.curve2 = Curve("Curve 2", [], pg.mkPen(color="#4363d8", width=4), self.realTimeGraph)
        self.curve2.plotCurve()

        self.curve3 = Curve("Curve 1", [], pg.mkPen(color="#800000", width=4), self.uBarGraph)
        self.curve3.plotCurve()

        self.curve4 = Curve("Curve 2", [], pg.mkPen(color="#4363d8", width=4), self.uBarGraph)
        self.curve4.plotCurve()

        # Initializing the mean bars.
        self.meanBar = pg.LinearRegionItem(values=(0, 1), orientation='vertical', brush=None, pen=None, hoverBrush=None, hoverPen=None, movable=True, bounds=None, span=(0, 1), swapMode='sort', clipItem=None)
        
        # Adding the Mean bars when the plotting is paused
        self.realTimeGraph.addItem(self.meanBar)


    def connectUItoMethods(self):
        """
            Connects all the UI Components to their respective methods.
            :param {_ : }
            :return -> None

            We need to tell the program what to do when a UI component is interacted with (e.g. a button is clicked).
            So we connect the ui elements to methods that define the behavior of the element.
            
        """

        # QFileDialog Folder selection
        self.barsButton.clicked.connect(self.barsButtonPressed)

        self.plotAllButton.clicked.connect(self.plotAllButtonPressed)

        # Rescale button connect method.
        self.rescaleButton.clicked.connect(self.rescaleButtonPressed)

        # Start button connect method.
        self.startButton.clicked.connect(self.startButtonPressed)

        # Pause/Resume button connect method.
        self.pauseResumeButton.clicked.connect(self.pauseResumeAction)

        self.graph1CheckBox.stateChanged.connect(lambda: self.graphCheckStateChanged(self.graph1CheckBox, self.curve1))
        self.graph2CheckBox.stateChanged.connect(lambda: self.graphCheckStateChanged(self.graph2CheckBox, self.curve2))
        

        # O2 Assay Buffer Zero Button connect method
        self.o2ZeroButton.clicked.connect(lambda: self.o2ZeroButtonPressed())

        # O2 Assay Buffer Zero LineEdit text edited connect method
        self.o2ZeroLineEdit.returnPressed.connect(lambda: self.OnEditedO2AssayCal())

        # Temperature Lineedir text edited connect method
        self.temperatureLineEdit.returnPressed.connect(lambda: self.OnEditedTemp())

        # CO2 Cal buttons connect method
        self.co2CalZeroButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.co2CalZeroLineEdit, 3, 0, 0))
        self.co2Cal1ulButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.co2Cal1ulLineEdit, 3, 0, 1000))
        self.co2Cal2ulButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.co2Cal2ulLineEdit, 3, 0, 2000))
        self.co2Cal3ulButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.co2Cal3ulLineEdit, 3, 0, 3000))

        # CO2 Cal LineEdits connect text edited connet method
        self.co2CalZeroLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.co2CalZeroLineEdit, 3, 0, 0))
        self.co2Cal1ulLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.co2Cal1ulLineEdit, 3, 0, 1000))
        self.co2Cal2ulLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.co2Cal2ulLineEdit, 3, 0, 2000))
        self.co2Cal3ulLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.co2Cal3ulLineEdit, 3, 0, 3000))
        

        # BiCarb Cal buttons connect method
        self.biCarbCalZeroButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.biCarbCalZeroLineEdit, 3, 1, 0))
        self.biCarbCal2ulButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.biCarbCal2ulLineEdit, 3, 1, 33.3))
        self.biCarbCal4ulButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.biCarbCal4ulLineEdit, 3, 1, 66.6))
        self.biCarbCal6ulButton.clicked.connect(lambda: self.GraphMeanButtonPressed(self.biCarbCal6ulLineEdit, 3, 1, 99.9))

        # BiCarb Cal LineEdits connect text edited cnnnect method
        self.biCarbCalZeroLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.biCarbCalZeroLineEdit, 3, 1, 0))
        self.biCarbCal2ulLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.biCarbCal2ulLineEdit, 3, 1, 33.3))
        self.biCarbCal4ulLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.biCarbCal4ulLineEdit, 3, 1, 66.6))
        self.biCarbCal6ulLineEdit.returnPressed.connect(lambda: self.OnEditedCO2Cal(self.biCarbCal6ulLineEdit, 3, 1, 99.9))

        self.o2CalibrationLineEdit.returnPressed.connect(lambda: self.OnEditedO2Cal())
        

        # BiCarb / CO2 button connect method
        self.biCarbCo2Button.clicked.connect(lambda: self.biCarbCo2ButtonPressed())

        # BiCarb / CO2 LineEdit text edited connect method
        self.biCarbCo2LineEdit.returnPressed.connect(lambda: self.OnEditedBiCarbCo2())

        # CO2 Zero button connect method
        self.co2ZeroButton.clicked.connect(self.co2ZeroButtonPressed)

        # Blank button connect method
        self.blankButton.clicked.connect(self.blankButtonPressed)

        # Extract button connect method
        self.extractButton.clicked.connect(self.extractButtonPressed)

        # Add to Table connect method
        self.addToTableButton.clicked.connect(self.addToTableButtonPressed)

        # Stop Button connect method
        self.stopButton.clicked.connect(self.stopButtonPressed)

        # Purge Table connect method
        self.purgeTableButton.clicked.connect(self.purgeTableButtonPressed)

        # Export Table connect method
        self.exportTableButton.clicked.connect(self.tableFileSave)

    def select_folder(self):
        # Open a file dialog to select a folder
        self.folder_path = QFileDialog.getExistingDirectory(self, 'Select a folder')
        self.setWindowTitle(f"LabView {os.path.basename(self.folder_path)}")
        self.dataObj.setDirectory(self.folder_path)
        self.application_state = "Folder_Selected"
        self.select_folder_action.setEnabled(False)



################################################# End - User Interface Creation #################################################
#################################################################################################################################




#################################################################################################################################
##################################################### ButtonPressed Methods #####################################################


    def stopButtonPressed(self):
        self.throwStopButtonWarning()

        
    def barsButtonPressed(self):

        xRange = self.realTimeGraph.getXAxisRange()
        scale = xRange[1] - xRange[0]
        midPoint = (xRange[1] + xRange[0]) / 2
        scale = int(scale / 10)
        self.meanBar.setRegion([midPoint-scale, midPoint+scale])

    def rescaleButtonPressed(self):
        
        if self.realTimeGraph.graphInteraction == False:
            return
        elif self.realTimeGraph.graphInteraction == True:
            self.isYChanged = True
            self.realTimeGraph.graphInteraction = False
            

    def plotAllButtonPressed(self):

        if self.application_state == "Out_Of_Data":
            pass
        else:
            self.plotAllButton.setEnabled(False)
            self.processSpinnerLabel.show()
            self.movie.start()

        self.plotAllButtonThread = QThread(parent=self)
        # Step 3: Create a worker object
        self.plotAllThread = PlotAllThread(self)

        # Step 4: Move worker to the thread
        self.plotAllThread.moveToThread(self.plotAllButtonThread)

        # Step 5: Connect signals and slots and start the stop watch
        self.plotAllButtonThread.started.connect(self.plotAllThread.run)
        
        self.plotAllButtonThread.start()

        self.plotAllThread.newDataPointSignal.connect(self.update_plot_data)
        self.plotAllThread.throwOutOfDataExceptionSignal.connect(self.throwOutOfDataException)
        self.plotAllThread.throwFolderNotSelectedExceptionSignal.connect(self.throwFolderNotSelectedException)
        self.plotAllThread.filesParsedSignal.connect(self.startNewFileNotifier)

        self.pauseBit = False
        self.pauseResumeButton.setText("Pause")
        self.pauseResumeButton.setToolTip('Pause the graph')
        self.application_state = "Out_Of_Data"

        self.plotAllThread.finished.connect(self.endPlotAllThread)
        self.plotAllThread.finished.connect(self.plotAllThread.deleteLater)


    def startButtonPressed(self):

        """
            Starts the real time plot.
            :param {_ : } 
            :return -> None
            
        """
        if self.application_state == "Folder_Selected" or self.application_state == "Out_Of_Data":
            
            self.startBit = True
            self.pauseBit = False

            # Step 2: Create a QThread object
            self.realTimePlotthread = QThread(parent=self)
            self.uBarPlotthread = QThread(parent=self)

            # Step 3: Create a worker object
            self.worker = Worker(self)
            self.worker2 = Worker(self)
            # Step 4: Move worker to the thread
            self.worker.moveToThread(self.realTimePlotthread)
            self.worker2.moveToThread(self.uBarPlotthread)

            # Step 5: Connect signals and slots and start the stop watch
            self.realTimePlotthread.started.connect(self.worker.run)
            self.worker.finished.connect(self.realTimePlotthread.quit)

            self.uBarPlotthread.started.connect(self.worker2.run)
            self.worker2.finished.connect(self.uBarPlotthread.quit)

            # Connecting the signals to the methods.
            self.worker.plotEndBitSignal.connect(self.outOfDataCondition)
            self.worker.newDataPointSignal.connect(self.update_plot_data)
            self.worker2.plotEndBitSignal.connect(self.outOfDataCondition)
            self.worker2.newDataPointSignal.connect(self.update_plot_data)

            # Deleting the reference of the worker and the thread from the memory to free up space.
            self.worker.finished.connect(self.worker.deleteLater)
            self.realTimePlotthread.finished.connect(self.realTimePlotthread.deleteLater)
            self.worker2.finished.connect(self.worker2.deleteLater)
            self.realTimePlotthread.finished.connect(self.realTimePlotthread.deleteLater)

            # Step 6: Start the thread
            if self.stopwatch.paused == True:
                self.stopwatch.resume()
            else:
                self.stopwatch.start()

            self.realTimePlotthread.start()
            self.uBarPlotthread.start()

            # Unhide graphs
            self.curve3.unhide()
            self.curve4.unhide()

            # Final resets
            self.startButton.setEnabled(False)
            self.application_state = "Running"


            # change-file-reading
            # Write code to recieve the signal and start a new thread for dirwatch.
            self.worker.filesParsedSignal.connect(self.startNewFileNotifier)
            
        else:
            self.throwFolderNotSelectedException()


    # change-file-reading
    # Start the thread as soon all files are read.
    def startNewFileNotifier(self):

        if not self.fileCheckThreadStarted:
            self.fileNotiferThread = QThread(parent=self)
            # Step 3: Create a worker object
            self.newFileNotifierThread = NewFileNotifierThread(self.folder_path)
            # Step 4: Move worker to the thread
            self.newFileNotifierThread.moveToThread(self.fileNotiferThread)

            # Step 5: Connect signals and slots and start the stop watch
            self.fileNotiferThread.started.connect(self.newFileNotifierThread.run)
            
            self.fileNotiferThread.start()
            self.fileCheckThreadStarted = True
        
        else:
            pass
        
    def meanButtonPressed(self, lineEdit, curve):
        """
            When a mean button is pressed, sets the lineEdit with
            the current mean value from the mean bars on a certain curve.
            :param { lineEdit : QLineEdit} -> line edit that will display the mean value
            :param { curve : int} -> int that indicates the curve to take the mean from
            :return -> mean_value
        """
        
        # Get the left and right x points from the mean bars
        xleft, xright = self.meanBar.getRegion()

        # if no data exists, return undefined
        if (not self.sharedData.dataPoints.keys()):
            self.throwUndefined(lineEdit)
            return None

        # if one or both of the x values is not in the range of the dataset, return undefined
        elif (xright < list(self.sharedData.dataPoints.keys())[0] or xleft > list(self.sharedData.dataPoints.keys())[-1] or
                 xleft < list(self.sharedData.dataPoints.keys())[0] or xright > list(self.sharedData.dataPoints.keys())[-1]):
            
            self.throwUndefined(lineEdit)
            return None
        
        else:
            # get mean value between points
            
            # Find the closest x values in the data to the x values from the mean bars
            xleft = min(self.sharedData.dataPoints.keys(), key=lambda x:abs(x-xleft))
            xright = min(self.sharedData.dataPoints.keys(), key=lambda x:abs(x-xright))

            # Get mean from graph
            mean_value = Calculations.getMean(self.sharedData.dataPoints, xleft, xright, curve)
        
            # Set line edit with mean value
            lineEdit.setText(str(mean_value))

            return mean_value
        

    def GraphMeanButtonPressed(self, lineEdit, curve, graph, concentration, manualEntry=False):
        """
            When a mean button is pressed, calls meanButtonPressed to get mean
            and then graphs concentration vs. mean on the proper graph and gets the slope
            of the line (calibration value).
            :param { lineEdit : QLineEdit} -> line edit that will display the mean value
            :param { curve : int} -> int that indicates the curve to take the mean from
            :param { graph : int} -> 0 if assay graph, 1 if hcl graph
            :param { concentration : int} -> concentration that will graph against mean
            :return -> None
        """

        # if mean value was entered manually, set mean_value to lineEdit text
        if manualEntry:
            if lineEdit.text() == '' or lineEdit.text() == 'undef':
                mean_value = None
            else:
                mean_value = float(lineEdit.text())
        else:
            # else, find the mean value
            mean_value = self.meanButtonPressed(lineEdit, curve)

        # graph mean value on the appropiate graph vs concentration
        self.graphConcentrationVsMean(mean_value, graph, concentration)

        # get the slope and intercept of the graph (calibration value)
        if (graph == 0):
            # find co2 buffer calibration (slope)
            self.co2BufferCalibration = Calculations.calculateSlope(self.assayBufferData)

            if self.co2BufferCalibration == None:
                self.throwUndefined(self.biCarbCalLineEdit)
                self.throwUndefined(self.intercept1LineEdit)
            else:
                # set slope line edit
                self.biCarbCalLineEdit.setText(str(round(self.co2BufferCalibration, 4)))

                # find intercept
                intercept = Calculations.calculateIntercept(self.assayBufferData, self.co2BufferCalibration)

                # set intercept line edit
                self.intercept1LineEdit.setText(str(round(intercept, 4)))

        else:
            # find co2 HCL calibration (slope)
            self.co2HCLCalibration = Calculations.calculateSlope(self.hclData)

            if self.co2HCLCalibration == None:
                self.throwUndefined(self.nmolLineEdit)
                self.throwUndefined(self.intercept2LineEdit)
            else:
                # set slope line edit
                self.nmolLineEdit.setText(str(round(self.co2HCLCalibration, 4)))

                # find intercept
                intercept = Calculations.calculateIntercept(self.hclData, self.co2HCLCalibration)

                # set intercept line edit
                self.intercept2LineEdit.setText(str(round(intercept, 4)))



    def co2ZeroButtonPressed(self):
        """
        Sets the CO2Zero Mass 44 line edits with the mean value
        from the mean bars from the respective curve.
        :param {_ : }
        :return -> None
        """

        # Set mean value from mean bars for Mass 44 graph
        self.co2Zero44Reading = self.meanButtonPressed(self.co2ZeroLineEdit1, 3)                          

    def o2ZeroButtonPressed(self, manualEntry=False):
        """
        Gets the mean of Mass 32 from the mean bars and uses that mean value to
        get the O2 concentration. Sets the appropirate line edits with
        these values.
        :param {manualEntry: bool} -> Check bit for allowing manual entry of the 
        :return -> True or False

        """

        if (manualEntry):

            # use entered value as mean value
            mean_value = float(self.o2ZeroLineEdit.text())
        else:

            # Set mean value from mean bars on the Mass 32 graph
            mean_value = self.meanButtonPressed(self.o2ZeroLineEdit, 0)

        if self.temperatureLineEdit.text():

            # get the O2 Calbriation
            self.o2Calibration = Calculations.calculate02Calibration(mean_value, self.temperature)

            # set O2 Calibration line edit
            self.o2CalibrationLineEdit.setText(str(round(self.o2Calibration, 4)))

        else:
            self.throwUndefined(self.o2CalibrationLineEdit)

    def biCarbCo2ButtonPressed(self):
        """
        When the BiCarb/CO2 button is pressed, the ratio of BiCarb to CO2 is calculated and set
        as long as the HCL calibration is not equal to zero
        :param {_ : }
        :return -> None
        """

        if (manualEntry):
            if (self.biCarbCo2LineEdit.text() != ''):
                self.biCarbCo2Ratio = float(self.biCarbCo2LineEdit.text())
            else:
                self.biCarbCo2Ratio = 0
        else:
            if self.co2BufferCalibration != 0 and self.co2HCLCalibration != 0:
                # calculate ratio
                self.biCarbCo2Ratio = self.co2BufferCalibration / self.co2HCLCalibration

                # set line edit with calculation
                self.biCarbCo2LineEdit.setText(str(round(self.biCarbCo2Ratio, 4)))
            else:
                self.throwUndefined(self.biCarbCo2LineEdit)


    def blankButtonPressed(self):
        """
        Executed when the Blank button is pressed.
        Finds the slope from Mass 44 and Mass 45 from the points on the mean bars.
        :param {_ : }
        :return -> None
        """

        # Get the left and right x points from the mean bars
        xleft, xright = self.meanBar.getRegion()

        # if no data exists, return undefined
        if (not self.sharedData.dataPoints.keys()):
            self.throwUndefined(self.co2LineEdit1)
            self.throwUndefined(self.o2LineEdit1)
            return

        # if one or both of the x values is not in the range of the dataset, return undefined
        elif (xright < list(self.sharedData.dataPoints.keys())[0] or xleft > list(self.sharedData.dataPoints.keys())[-1] or
                 xleft < list(self.sharedData.dataPoints.keys())[0] or xright > list(self.sharedData.dataPoints.keys())[-1]):
            
            self.throwUndefined(self.co2LineEdit1)
            self.throwUndefined(self.o2LineEdit1)
            self.co2Blank = 0
            self.o2Blank = 0
            return

        else:

            # Find the closest x values in the data to the x values from the mean bars
            xleft = min(self.sharedData.dataPoints.keys(), key=lambda x:abs(x-xleft))
            xright = min(self.sharedData.dataPoints.keys(), key=lambda x:abs(x-xright))

            # Calculate slope between these two points for graph Mass 44
            self.co2Blank = (self.sharedData.dataPoints[xright][3] - self.sharedData.dataPoints[xleft][3]) / (xright - xleft)
            
            # Calculate slope between these two points for graph Mass 32
            self.o2Blank = (self.sharedData.dataPoints[xright][0] - self.sharedData.dataPoints[xleft][0]) / (xright - xleft)

            # Set CO2 and O2 line edits
            self.co2LineEdit1.setText(str(round(self.co2Blank, 4)))
            self.o2LineEdit1.setText(str(round(self.o2Blank, 4)))


    def extractButtonPressed(self):
        """
        Executed when the Extract button is pressed.
        Fills in the first line of line edits with the extract values (slope values taken from the mean bars).
        Second line of line edits are filled with the extract - blank.
        Third line of line edits filled with mean values from Mass 44 and Mass32 from the mean bars.
        Lastly calculates and fills in velocities and concentrations.
        :param {_ : }
        :return -> None
        """

        ################ First Line ###############

        # Get the left and right x points from the mean bars
        xleft, xright = self.meanBar.getRegion()

        # if no data exists, return undefined
        if (not self.sharedData.dataPoints.keys()):
            self.throwUndefined(self.co2LineEdit2)
            self.throwUndefined(self.o2LineEdit2)
            return

        # if one or both of the x values is not in the range of the dataset, return undefined
        elif (xright < list(self.sharedData.dataPoints.keys())[0] or xleft > list(self.sharedData.dataPoints.keys())[-1] or
                 xleft < list(self.sharedData.dataPoints.keys())[0] or xright > list(self.sharedData.dataPoints.keys())[-1]):
            
            self.throwUndefined(self.co2LineEdit2)
            self.throwUndefined(self.o2LineEdit2)
            return

        # Find the closest x values in the data to the x values from the mean bars
        xleft = min(self.sharedData.dataPoints.keys(), key=lambda x:abs(x-xleft))
        xright = min(self.sharedData.dataPoints.keys(), key=lambda x:abs(x-xright))

        # Calculate slope between these two points for graph Mass 44
        self.co2Extract = (self.sharedData.dataPoints[xright][3] - self.sharedData.dataPoints[xleft][3]) / (xright - xleft)
        
        # Calculate slope between these two points for graph Mass 32
        self.o2Extract = (self.sharedData.dataPoints[xright][0] - self.sharedData.dataPoints[xleft][0]) / (xright - xleft)

        # Set CO2 and O2 line edits
        self.co2LineEdit2.setText(str(round(self.co2Extract, 4)))
        self.o2LineEdit2.setText(str(round(self.o2Extract, 4)))

        ################ Secone Line ###############
        
        # if Blank has not been found yet, return undefined
        if (self.co2Blank == 0):
            self.throwUndefined(self.co2LineEdit3)
            self.throwUndefined(self.o2LineEdit3)
            return

        # calculate net rate of consumption for CO2 and O2
        self.co2ConsumptionRate = self.co2Extract - self.co2Blank
        self.o2ConsumptionRate = self.o2Extract - self.o2Blank

        # Set Line Edits
        self.co2LineEdit3.setText(str(round(self.co2ConsumptionRate, 4)))
        self.o2LineEdit3.setText(str(round(self.o2ConsumptionRate, 4)))

        ################ Third Line ###############

        # Get mean value from mean bars from Mass 44 and Mass 32 graphs
        co2Reading = self.meanButtonPressed(self.co2LineEdit4, 3)
        o2Reading = self.meanButtonPressed(self.o2LineEdit4, 0)

        ######### Populate Velocities and Concentrations for Table ########

        # If the o2 calibration or co2 calibration are not defined, return undefined
        if (self.o2Calibration == 0 or self.co2BufferCalibration == 0 or self.biCarbCo2Ratio == 0):
            self.throwUndefined(self.v0LineEdit)
            self.throwUndefined(self.vcLineEdit)
            self.throwUndefined(self.co2Concentrationv0LineEdit)
            self.throwUndefined(self.o2Concentrationv0LineEdit)
            return
        
        self.vO = self.o2ConsumptionRate * self.o2Calibration * -1
        self.vC = self.co2ConsumptionRate * self.co2BufferCalibration * -1
        self.co2Concentration = (self.co2BufferCalibration * (co2Reading - self.co2Zero44Reading)) / self.biCarbCo2Ratio
        self.o2Concentration = self.o2Calibration * o2Reading

        # Set Line Edits

        self.v0LineEdit.setText(str(round(self.vO, 4)))
        self.vcLineEdit.setText(str(round(self.vC, 4)))
        self.co2Concentrationv0LineEdit.setText(str(round(self.co2Concentration, 4)))
        self.o2Concentrationv0LineEdit.setText(str(round(self.o2Concentration, 4)))

    def addToTableButtonPressed(self):
        """
        Executed when the Add To Table button is pressed.
        Adds the CO2/O2 velocity and concentration values to the table
        and graphs them on the velocity/concentration graph.
        :param {_ : }
        :return -> None
        """

        ####  Add values to the table  ####

        # create a new row
        newRowPosition = self.table.rowCount()
        self.table.insertRow(newRowPosition)

        # set values in row (VO, VC, [CO2], [O2])
        self.table.setItem(newRowPosition, 0, QtWidgets.QTableWidgetItem(str(round(self.vO, 4))))
        self.table.setItem(newRowPosition, 1, QtWidgets.QTableWidgetItem(str(round(self.vC, 4))))
        self.table.setItem(newRowPosition, 2, QtWidgets.QTableWidgetItem(str(round(self.co2Concentration, 4))))
        self.table.setItem(newRowPosition, 3, QtWidgets.QTableWidgetItem(str(round(self.o2Concentration, 4))))

        #### Add new table row values to the velocity/concentration graph ####

        self.o2VelocityConcentrationData[self.o2Concentration] = self.vO
        self.co2VelocityConcentrationData[self.co2Concentration] = self.vC

        self.concentrationGraph.plot(list(self.o2VelocityConcentrationData.keys()), list(self.o2VelocityConcentrationData.values()), pen=None, symbol='o',
                                       symbolsize=1, symbolPen=pg.mkPen(color="#00fa9a", width=0), symbolBrush=pg.mkBrush("#00fa9a"))

        self.concentrationGraph.plot(list(self.co2VelocityConcentrationData.keys()), list(self.co2VelocityConcentrationData.values()), pen=None, symbol='o',
                                       symbolsize=1, symbolPen=pg.mkPen(color="#ff0000", width=0), symbolBrush=pg.mkBrush("#ff0000"))
        
        self.concentrationGraph.plotItem.getViewBox().autoRange()
        
            

    def purgeTableButtonPressed(self):
        """
        Executed when Purge Table button is pressed.
        Saves table data to a csv file.
        Clears the table and velocity/concentration graph.
        :param {_ : }
        :return -> None
        """

        self.purgeTablepButtonWarning()


    def copyTableRowButtonPressed(self):
        """
        Copies selected table row to clipboard. Can only copy one row at a time
        :param {_ : }
        :return -> None
        """
        rowIndex = self.table.currentRow()

        # if a row is selected
        if rowIndex != -1:
            
            row = ''

            # create string with row values, separated by spaces
            for i in range(4):
                row += self.table.item(rowIndex, i).text() + ' '

            # copy row string to clipboard
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(row, mode=cb.Clipboard)




################################################## End - ButtonPressed Methods ##################################################
#################################################################################################################################


#################################################################################################################################
###################################################### On Edit Line Edits #######################################################

    def OnEditedTemp(self):
        
        # check for numerical input
        if (not self.isFloat(self.temperatureLineEdit.text()) and self.temperatureLineEdit.text() != ''):
            #throw execption
            self.throwFloatValueWarning()
            return
        
        if self.temperatureLineEdit.text() == '':
            self.temperature = 0
        else:
            self.temperature = float(self.temperatureLineEdit.text())
            

    def OnEditedO2AssayCal(self):
        """
        When the O2 Assay Buffer Zero line edit is edited, the O2ZeroButtonPressed method
        is called with manualEntry set as true.
        """

        # check for numerical input
        if (not self.isFloat(self.o2ZeroLineEdit.text()) and self.o2ZeroLineEdit.text() != ''):
            #throw execption
            self.throwFloatValueWarning()
            return

        # called method with manualEntry as True
        self.o2ZeroButtonPressed(True)
        
        

    def OnEditedCO2Cal(self, lineEdit, curve, graph, concentration):
        """
        When a CO2 cal line edit is edited, the GraphMeanButtonPressed method is called
        with manualEntry set as true.
        """

        if (not self.isFloat(lineEdit.text()) and lineEdit.text() != ''):
            #throw execption
            self.throwFloatValueWarning()
            lineEdit.setText('undef')
            
        self.GraphMeanButtonPressed(lineEdit, curve, graph, concentration, True)

    def OnEditedO2Cal(self):
        
        # check for numerical input
        if (not self.isFloat(self.o2CalibrationLineEdit.text()) and self.o2CalibrationLineEdit.text() != ''):
            #throw execption
            self.throwFloatValueWarning()
            return

        if self.o2CalibrationLineEdit.text() == '':
            self.o2Calibration = 0
        else:
            self.o2Calibration = float(self.o2CalibrationLineEdit.text())
            

    def OnEditedBiCarbCo2(self):

        # check for numerical input
        if (not self.isFloat(self.biCarbCo2LineEdit.text()) and self.biCarbCo2LineEdit.text() != ''):
            #throw execption
            self.throwFloatValueWarning()
            return

        self.biCarbCo2ButtonPressed(True)



#################################################### End - On Edit Line Edits ###################################################
#################################################################################################################################


#################################################################################################################################
####################################################### Raw Plot Methods ########################################################


    def speedSliderValueChanged(self):
        
        #0.05   0.5   1   1.5     2.0

        speed = self.speedSlider.value()

        if speed <= 5:
            self.stopwatch.set_speed(0.05)

        self.stopwatch.set_speed(speed/100)


    def endPlotAllThread(self):
        
        self.movie.stop()
        self.processSpinnerLabel.hide()
        self.plotAllButtonThread.quit()
        self.plotAllButtonThread.wait()
        self.plotAllButtonThread.deleteLater()
        self.plotAllButton.setEnabled(True)

    

    # change-file-reading
    # Start the thread as soon all files are read.
    def startNewFileNotifier(self):

        if not self.fileCheckThreadStarted:
            self.fileNotiferThread = QThread(parent=self)
            # Step 3: Create a worker object
            self.newFileNotifierThread = NewFileNotifierThread(self.folder_path)
            # Step 4: Move worker to the thread
            self.newFileNotifierThread.moveToThread(self.fileNotiferThread)

            # Step 5: Connect signals and slots and start the stop watch
            self.fileNotiferThread.started.connect(self.newFileNotifierThread.run)
            
            self.fileNotiferThread.start()
            self.fileCheckThreadStarted = True
        
        else:
            pass

    def update_plot_data(self, dataPoints):
    
           # Updates the real time plot after reading each row of data points from the file ONLY IF the pause bit is False.
           # :param {x_value : Float} -> x point value of the data point.
           # :param {y_value : Float} -> list of the y point values of the data point for different plots.
           # :return -> None
    

        y_value = [[],[],[],[],[],[],[],[]]

        # Getting the next data points from the list of all the points emitted by the worker thread.
        while len(dataPoints) != 0:

            # Popping the first data points
            dataPoint = dataPoints.pop(0)

            # Getting the x coordinate and list of y coordinates from the tuple
            x, y = dataPoint

            # Updating the data points in the singleton class.
            self.sharedData.dataPoints[x] = y

            # self.stopwatch.set_time(x)

            for i in range(len(y_value)):
                y_value[i].append(y[i])

            # print(x_value, y_value)
        # x_value, y_value = self.getNextPoint(self.dataObj)

        # Updating the shared singleton plot data
        
        # Updating all the curves
        # start = time()
        yAllMax = max(y)
        yAllMin = min(y)

        if self.yAllMin == None and self.yAllMax == None:
            self.yAllMax = yAllMax
            self.yAllMin = yAllMin
            self.isYChanged = True
            
        else:

            if yAllMin < self.yAllMin:
                self.yAllMin = yAllMin
                self.isYChanged = True

            if yAllMax > self.yAllMax:
                self.yAllMax = yAllMax
                self.isYChanged = True
        
        self.changeGraphRange(x)
        
        self.curve1.updateDataPoints(x, y_value[0])
        self.curve2.updateDataPoints(x, y_value[1])

        self.curve3.updateDataPoints(x, y_value[0])
        self.curve4.updateDataPoints(x, y_value[1])
        # print("Time taken plot all the points: ", time()-start)

    def changeGraphRange(self, x):
        
        # Changing X Axes Scale
        self.currentXRange = self.realTimeGraph.getXAxisRange()

        if x > self.currentXRange[1]:
            
            currentXScale = self.currentXRange[1] - self.currentXRange[0]
            # print("CurrentXScale = ", currentXScale)
            self.currentXRange = [self.currentXRange[0] + currentXScale, self.currentXRange[1] + currentXScale]
            if not self.realTimeGraph.graphInteraction:
                self.realTimeGraph.setNewXRange(self.currentXRange[0], self.currentXRange[1])
            if not self.uBarGraph.graphInteraction:
                self.uBarGraph.setNewXRange(self.currentXRange[0], self.currentXRange[1])

        # Changing Y Axes Scale:

        if self.isYChanged:
            if not self.realTimeGraph.graphInteraction:
                offsetMin = (20*self.yAllMin)/100
                offsetMax = (20*self.yAllMax)/100
                self.realTimeGraph.setNewYRange(self.yAllMin-offsetMin, self.yAllMax+offsetMax)
                self.isYChanged = False
            if not self.uBarGraph.graphInteraction:
                offsetMin = (20*self.yAllMin)/100
                offsetMax = (20*self.yAllMax)/100
                self.uBarGraph.setNewYRange(self.yAllMin-offsetMin, self.yAllMax+offsetMax)
                self.isYChanged = False
    

    def on_wheel_event(self,event, axis=1):
        """
            For disabling the scroll on the axes.
        
        """
        event.ignore()

   
    def pauseResumeAction(self):

        """
            Pauses or Resumes the graph plot.
            :param {_ : }
            :return -> None
        """
        
        if self.application_state == "Out_Of_Data" or self.application_state == "Folder_Selected" or self.application_state == "Idle":
            self.throwGraphInActiveException()

        else:
            # Pause the Plot
            if self.pauseBit == False:
                self.application_state = "Paused"
                self.pauseBit = True
                self.stopwatch.stop()
                self.pauseResumeButton.setText("Resume")
                self.pauseResumeButton.setToolTip('Resume the graph')

            # Resume the Plot
            elif self.pauseBit == True:
                self.application_state = "Running"
                self.pauseBit = False
                self.stopwatch.start()
                self.pauseResumeButton.setText("Pause")
                self.pauseResumeButton.setToolTip('Pause the graph')

    def graphCheckStateChanged(self, checkBox, curve):

        """
            Hide/Unhide the graph 8.
            :param {_ : }
            :return -> None
        """

        if checkBox.isChecked() == True:
            curve.unhide()
        elif checkBox.isChecked() != True:
            curve.hide()


##################################################### End - Raw Plot Methods ####################################################
#################################################################################################################################


#################################################################################################################################
#################################################### File export and import #####################################################


    def saveCalibrations(self):
        """
        Opens a save file dialog and saves all calibration files to a csv file. Default location is . Default name
        is the date and time.
        """

        # datetime object containing current date and time
        now = datetime.now()

        # file name = dd/mm/YY H:M:S
        file_name = now.strftime("%d-%m-%y %H-%M-%S")

        # create path if it doesn't exist
        path = 'C:\\Users\\'+self.user+'\\Documents\\Calibrations'
        if not os.path.exists(path):
            os.makedirs(path)


        # Invoke Save File Dialog - returns the path of the file and file type
        path, ok = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', path+"\\"+file_name, "CSV Files (*.csv)")

        # if file type is not null
        if ok:

            # open file and write in calibrations
            with open(path, 'w') as csvfile:
                writer = csv.writer(csvfile, dialect='excel', lineterminator='\n')
                
                writer.writerow(['Temp', 'O2 Calibration', 'O2 Buffer Zero', 'BiCarb/CO2',
                                 'CO2 Cal 0', 'CO2 Cal 6', 'CO2 Cal 12', 'CO2 Cal 18',
                                 'BiCarb Cal 0', 'BiCarb Cal 2', 'BiCarb Cal 4', 'BiCarb Cal 6'])

                row = (lineEdit.text() for lineEdit in  self.calibrationLineEdits)

                writer.writerow(row)
                
    
    def loadCals(self, file_path):

        """
        Loads calibration values from a csv file.
        """

        with open(file_path[0], newline='') as cal_file:
            reader = csv.reader(cal_file)
            next(reader) # read in header
            data = next(reader) # read in cal data


            for i in range(len(self.calibrationLineEdits)):
                self.calibrationLineEdits[i].setText(data[i])

            # Update values
            self.OnEditedTemp()  # temperature

            self.OnEditedO2Cal()  # O2 Assay Buffer Zero

            self.OnEditedBiCarbCo2()  # BiCarb/Co2 ratio

            # CO2 Assay Buffer Cals

            self.OnEditedCO2Cal(self.calibrationLineEdits[4], 3, 0, 0)
            self.OnEditedCO2Cal(self.calibrationLineEdits[5], 3, 0, 1000)
            self.OnEditedCO2Cal(self.calibrationLineEdits[6], 3, 0, 2000)
            self.OnEditedCO2Cal(self.calibrationLineEdits[7], 3, 0, 3000)

            # CO2 HCl Cals
            self.OnEditedCO2Cal(self.calibrationLineEdits[8], 3, 1, 0)
            self.OnEditedCO2Cal(self.calibrationLineEdits[9], 3, 1, 33.3)
            self.OnEditedCO2Cal(self.calibrationLineEdits[10], 3, 1, 66.6)
            self.OnEditedCO2Cal(self.calibrationLineEdits[11], 3, 1, 99.9)


    def tableFileSave(self):
        """
        Creates a Save File Dialog for user to decide what to name file and where to save it.
        Saves all the data currently in the table to a file (.csv by default)
        """

        # create directory if it doesn't already exist
        path = 'C:\\Users\\'+self.user+'\\Documents\\TableData'
        if not os.path.exists(path):
            os.makedirs(path)

        # Invoke Save File Dialog - returns the path of the file and file type
        path, ok = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', path, "CSV Files (*.csv)")

        # if file type is not null
        if ok:
            columns = range(self.table.columnCount()) # get column count

            # open file and write in table contents
            with open(path, 'w') as csvfile:
                writer = csv.writer(csvfile, dialect='excel', lineterminator='\n')

                # write each row into the file
                for row in range(self.table.rowCount()):
                    writer.writerow(self.table.item(row, column).text() for column in columns)



    def exportRawData(self):
        """
        Exports all the data from the raw data plot to a csv file.
        """

        # create directory if it doesn't already exist
        path = 'C:\\Users\\'+self.user+'\\Documents\\RawData'
        if not os.path.exists(path):
            os.makedirs(path)

        # open file for writing, will create file if it doesn't already exist
        file = open(path + os.path.basename(self.folder_path) + "Data.csv", 'w+')

        writer = csv.writer(file)   # create csv writer

        # write header to csv file
        writer.writerow(['Count', 'Time', 'm32', 'm34', 'm36', 'm44', 'm45', 'm46', 'm47', 'm49'])

        # get list of time and voltage values from data
        times = list(self.sharedData.dataPoints.keys())
        voltages = list(self.sharedData.dataPoints.values())

        # write lines of data to csv file
        for i in range(len(self.sharedData.dataPoints)):
            row = [i, times[i]*1000, voltages[i][0], voltages[i][1], voltages[i][2], voltages[i][3],
                               voltages[i][4], voltages[i][5], voltages[i][6], voltages[i][7]]

            writer.writerow(row)

        # close file
        file.close


    
################################################## End - File epxort and import #################################################
#################################################################################################################################


#################################################################################################################################
############################################# Warning Dialog and Exception Methods ##############################################

    # Stop button warning

    def throwStopButtonWarning(self):
        stopWarningDlg = Dialog(title="WARNING!!", buttonCount=2, message="Are you sure you want to STOP?.\nPress Cancel to abort or OK to continue", parent=self)
        stopWarningDlg.buttonBox.accepted.connect(lambda: self.stopDiaAccepted(stopWarningDlg))
        stopWarningDlg.buttonBox.rejected.connect(lambda: self.stopDiaRejected(stopWarningDlg))
        stopWarningDlg.exec()

    def stopDiaAccepted(self, obj):
        obj.close()

        saveCalsDlg = Dialog(title="Save Calibrations?", buttonCount=3, message="Would you like to keep calibrations in the program?\n Press Save to export calibrations", parent=self)
        saveCalsDlg.buttonBox.addButton("Save", QDialogButtonBox.HelpRole)
        saveCalsDlg.buttonBox.helpRequested.connect(lambda: self.saveCals(saveCalsDlg))
        saveCalsDlg.buttonBox.accepted.connect(lambda: self.keepCalsAccepted(saveCalsDlg))
        saveCalsDlg.buttonBox.rejected.connect(lambda: self.keepCalsRejected(saveCalsDlg))
        saveCalsDlg.exec()

        if self.application_state == "Out_Of_Data" or self.application_state == "Folder_Selected" or self.application_state == "Idle": 
            
            pass

        else:

            try:

                self.realTimePlotthread.quit()
                self.realTimePlotthread.wait()
                self.realTimePlotthread.deleteLater()

                self.newFileNotifierThread.stop()
                self.fileNotiferThread.quit()
            
            except RuntimeError as exception:
                print(exception)

        #export all raw data if there is data to load
        if self.folder_path != '':
            self.exportRawData()

        self.clearApplication(self.keepCals)

    def stopDiaRejected(self, obj):
        obj.close()

    def saveCals(self, obj):
        obj.close()
        self.saveCalibrations()
        
    def keepCalsAccepted(self, obj):
        self.keepCals = True
        obj.close()

    def keepCalsRejected(self, obj):
        self.keepCals = False
        obj.close()

    def throwGraphInActiveException(self):
        startButtonExceptionDlg = Dialog(title="EXCEPTION!!", buttonCount=1, message="The plot is inactive. Please make sure the graph is actively plotting.\nPress Ok to continue.", parent=self)
        startButtonExceptionDlg.buttonBox.accepted.connect(lambda: self.buttonDialogAccepted(startButtonExceptionDlg))
        startButtonExceptionDlg.exec()

    def buttonDialogAccepted(self, obj):
        obj.close()



    def throwFolderNotSelectedException(self):
        startButtonExceptionDlg = Dialog(title="EXCEPTION!!", buttonCount=1, message="Select the data folder before pressing start button.\nPress Ok to continue.", parent=self)
        startButtonExceptionDlg.buttonBox.accepted.connect(lambda: self.startButtonDialogAccepted(startButtonExceptionDlg))
        startButtonExceptionDlg.exec()

    def startButtonDialogAccepted(self, dlg):
        dlg.close()


    def throwOutOfDataException(self):
        self.application_state = "Out_Of_Data"
        dataExceptionDlg = Dialog(title="EXCEPTION!!", buttonCount=1, message="Application is out of data. Wait for sometime and then press Start or check instrument\nPress Ok to close the message.", parent=self)
        dataExceptionDlg.buttonBox.accepted.connect(lambda: self.dataButtonDialogAccepted(dataExceptionDlg))
        dataExceptionDlg.exec()

    def outOfDataCondition(self):
        self.throwOutOfDataException()

    def dataButtonDialogAccepted(self, obj):
        obj.close()
        self.startButton.setEnabled(True)


    def throwFloatValueWarning(self):
        floatWarningDlg = Dialog(title="WARNING!", buttonCount=1, message="The entered value is not a numerical value!", parent=self)
        floatWarningDlg.buttonBox.accepted.connect(lambda: self.floatWarningAccepted(floatWarningDlg))
        floatWarningDlg.exec()
        


    def floatWarningAccepted(self, obj):
        obj.close()
        

    def purgeTablepButtonWarning(self):

        """
        Throws the purge table warning.
        :param -> None.
        :return -> None
        """

        purgeWarningDlg = Dialog(title="WARNING!!", buttonCount=2, message="Are you sure you want to Purge Table? The unsaved data will be deleted.\nPress Cancel to abort or OK to continue", parent=self)
        purgeWarningDlg.buttonBox.accepted.connect(lambda: self.purgeDiaAccepted(purgeWarningDlg))
        purgeWarningDlg.buttonBox.rejected.connect(lambda: self.purgeDiaRejected(purgeWarningDlg))
        purgeWarningDlg.exec()

    def purgeDiaAccepted(self, obj):
        
        """
        Closes the purge warning dialoge. Purges the table and clears O2 and Co2 velocity concentration data.
        Also clears concentration graphs.
        :param {obj: Dialog} -> Purge warning dialog object.
        :return -> None
        """

        obj.close()
        # clear table
        self.table.setRowCount(0)

        # clear data sets
        self.o2VelocityConcentrationData.clear()
        self.co2VelocityConcentrationData.clear()

        # clear plots
        self.concentrationGraph.clear()

        #autoscale other graphs
        self.assayBufferGraph.plotItem.getViewBox().autoRange()
        self.hclGraph.plotItem.getViewBox().autoRange()
        
        
    
    def purgeDiaRejected(self, obj):
        """
        Closes the purge warning dialoge.
        :param {obj: Dialog} -> Purge warning dialog object.
        :return -> None
        """
        obj.close()
        pass


    def throwUndefined(self, lineEdit):
        lineEdit.setText('undef')
    

################################################## End - Warning Dialog and ExceptionMethods #####################################
##################################################################################################################################



    def select_folder(self):
        # Open a file dialog to select a folder
        self.folder_path = QFileDialog.getExistingDirectory(self, 'Select a folder')
        if self.folder_path != '':
            self.setWindowTitle(f"LabView {os.path.basename(self.folder_path)}")
            self.dataObj.setDirectory(self.folder_path)
            self.application_state = "Folder_Selected"
            self.select_folder_action.setEnabled(False)

    def select_file(self):
        # Open a file dialog to select a file
        file_path = QFileDialog.getOpenFileName(self, 'Select a file', os.getcwd(), "CSV Files (*.csv)")

        # if file is selected
        if file_path[0] != '':
            # load calibration file
            self.loadCals(file_path)
        


    def graphConcentrationVsMean(self, mean, graph, concentration):
        """
        Creates a Save File Dialog for user to decide what to name file and where to save it.
        Saves all the data currently in the table to a file (.csv by default)
        """
        
        if (graph == 0):

            # if point already exists, delete point
            for key in dict(self.assayBufferData).keys():
                if key == concentration:
                    del self.assayBufferData[key]

            # if mean value is not undefined, create new point
            if (mean != None):    
                self.assayBufferData[concentration] = mean

            # clear graph before replot
            self.assayBufferGraph.clear()

            # plot all points on the assay buffer graph
            assayLine = self.assayBufferGraph.plot(list(self.assayBufferData.values()), list(self.assayBufferData.keys()), pen=None, symbol='o',
                                       symbolsize=1, symbolPen=pg.mkPen(color="#00fa9a", width=0), symbolBrush=pg.mkBrush("#00fa9a"))
            
            self.assayBufferGraph.plotItem.getViewBox().autoRange()
            
            
        else:

            # if point already exists, delete point
            for key in dict(self.hclData).keys():
                if key == concentration:
                    del self.hclData[key]

            # if mean value is not undefined, create new point
            if (mean != None):    
                self.hclData[concentration] = mean

            self.hclGraph.clear()
            
            # plot point on the hcl graph
            hclLine = self.hclGraph.plot(list(self.hclData.values()), list(self.hclData.keys()), pen=None, symbol='o',
                                       symbolsize=1, symbolPen=pg.mkPen(color="#00fa9a", width=0), symbolBrush=pg.mkBrush("#00fa9a"))
            
            self.hclGraph.plotItem.getViewBox().autoRange()
        




    def isFloat(self, string):
        """
        Checks if a string can be coverted to a float value
        :param {string : string}
        :return -> True or False
        """
        try:
            float(string)
            return True
        except ValueError:
            return False
                    


    def clearApplication(self, keepCals):
        """
            When the STOP button is pressed, the application resets. This methods reinitializes the initial
            parameters of the application and clears any saved data unless calibrations are asked to be retained by the user.
            Post this function execution, the application is ready to plot new data.
            :param { keepCals : list(QLineEdit)} -> List of calibration line edit that needs to be retained.
            :return -> None
        """

        # Reset all application global variables. These varibales are global to different components of the application.
        self.setWindowTitle("LabView")
        self.application_state = "Idle"
        self.pauseBit = False
        self.startBit = False
        self.delay = 200
        self.stopwatch = Stopwatch()
        self.firstPoint = False
        self.yAllMax = None
        self.yAllMin = None
        self.isYChanged = False
        self.fileCheckThreadStarted = False
        self.speedSlider.setSliderPosition(100)
        self.speedSlider.setValue(100)
        self.startButton.setEnabled(True)
        self.select_folder_action.setEnabled(True)


        # Dictionaries to hold data for graphs
        if not keepCals:
            self.assayBufferData = {}
            self.hclData = {}
        self.o2VelocityConcentrationData = {}
        self.co2VelocityConcentrationData = {}

        # Initialize O2 and CO2 Calibrations
        self.o2Calibration = 0
        self.co2BufferCalibration = 0
        self.co2HCLCalibration = 0
        self.biCarbCo2Ratio = 0

        # Initialize CO2 and O2 Blank values
        self.co2Blank = 0
        self.o2Blank = 0

        # Initialize CO2 and O2 Extract values
        self.co2Extract = 0
        self.o2Extract = 0

        #Initialize CO2 and O2 net rate of consumption
        self.co2ConsumptionRate = 0
        self.o2ConsumptionRate = 0

        # Initialize CO2 and O2 rate of consumption and concentrations
        self.vC = 0
        self.vO = 0
        self.co2Concentration = 0
        self.o2Concentration = 0

        self.co2Zero44Reading = 0
        

        # Reset shared data across different components of the application
        self.sharedData.fileList = []
        self.sharedData.dataPoints = {}
        self.sharedData.folderAccessed = False
        self.sharedData.xPoint = 0

        # Data Object for getting the points.
        self.dataObj = GetData()
        
        for lineEdit in self.lineEditList:
            if keepCals:
                if lineEdit.isReadOnly():
                    lineEdit.setText("")
            else:
                lineEdit.setText("")
                    

        self.startButton.setEnabled(True)

        self.curve1.clear()
        self.curve2.clear()

        self.curve3.clear()
        self.curve4.clear()
     

        # Uncheck all the graph boxes.
        self.graph1CheckBox.setChecked(False) 
        self.graph2CheckBox.setChecked(False) 

        
# Main function
app = QApplication([])
screen = app.primaryScreen()
size = screen.availableGeometry()
labView = LabView(size.width(), size.height(), app)
app.exec_()
