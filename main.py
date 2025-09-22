import threading
import queue
import time
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import csv
import os
import datetime
from tkinter import *
from pylablib.devices import Thorlabs #Thorlabs library
import statistics

import sys
import clr
sys.path.append(r"C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_2.3.1.0__9a267756cf640dcf")
clr.AddReference(r"C:\Windows\Microsoft.NET\assembly\GAC_64\Newport.XPS.CommandInterface\v4.0_2.3.1.0__9a267756cf640dcf\Newport.XPS.CommandInterface")
from CommandInterfaceXPS import XPS



# Create abort_event
abort_event = threading.Event()

#Class for holding the limit information, and performing the software limit checking
class Limits:
    def __init__(self, LowerLimit: float, UpperLimit: float):
        self.LL = LowerLimit
        self.UL = UpperLimit

    def CheckLimit(self, Position: float):
        if Position > self.LL and Position < self.UL:
            return True
        else:
            return False

# Struct for Queue messages
@dataclass
class LabelUpdate:
    label: int
    message: any

# Define what to do when the abort Button is pressed
def abort() -> None:
    abort_event.set()

#TODO set the correct limits

XAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)
YAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)
ZAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)
RotAxisLimit = Limits(LowerLimit=-100, UpperLimit=100)

LimitList = [XAxisLimit, YAxisLimit, ZAxisLimit, RotAxisLimit]

#Scale for the Thorlabs actuators, translating microsteps to mm
KCubestepsPerMM = 34554.88  # Magic Number from datasheet
KCubeScale = (KCubestepsPerMM, KCubestepsPerMM * 53.68, KCubestepsPerMM / 90.9 / 2)
ZAxisStepsPerMM = 819200  # Magic Number from datasheet
ZAxisScale = (ZAxisStepsPerMM, ZAxisStepsPerMM * 53.68, ZAxisStepsPerMM / 90.9 / 2)


#Stage and actuator defining
XPSStage = XPS()
#KCube = Thorlabs.KinesisMotor(str(27262610), scale=KCubeScale)
#ZAxis = Thorlabs.KinesisMotor(str(70292334), is_rack_system=True, scale=ZAxisScale, default_channel=1)

#Keeping track of where the stages are
global PositionList
PositionList = [0.0, 0.0, 0.0, 0.0]

#Save the optimum position
OptimumList = [0.0, 0.0, 0.0, 0.0]
ReachedOptimum = False


# TODO Remove after debugging
NumberOfPoints = 35
CouplingEfficiencyRatio = 0.5

NumberOfDataPoints = 35
MaxNumberOfItteration = 20
MinNumberOfItteration = 5
ImprovementLimit = 0.02

global Debugging
Debugging = True

now = datetime.datetime.now()
global dt_string
dt_string = now.strftime("%Y_%m_%d_%H_%M")
if not os.path.exists(dt_string):
    os.makedirs(dt_string)

#PlotLists
XPlotList = []
YPlotList = []

def save_to_csv(directory, filename, listOne, listTwo):

    if not os.path.exists(directory):
        os.makedirs(directory)

    length = len(listOne)
    csvfile = open(directory + "/" + filename + ".csv", 'w', newline='')
    for i in range(length):
        csvfile.write(str(listOne[i]) + ", " + str(listTwo[i]) + "\n")

    csvfile.close()



# Event handler to update the label
def on_update_label(event) -> None:

    try:
        # Retrieve the next message from the queue
        message = q.get_nowait()

        match message.label:
            case 1:
                testLabelVar.set(message.message)
            case 2:
                voltageLabelVar.set(message.message)
            case 3:
                referencePowerLabelVar.set(message.message)
            case 4:
                xPosLabelVar.set(message.message)
            case 5:
                yPosLabelVar.set(message.message)
            case 6:
                zPosLabelVar.set(message.message)
            case 7:
                rotPosLabelVar.set(message.message)
            case 8:
                unitLabelPosVar.set(message.message)
            case 9:
                unitLabelLLVar.set(message.message)
            case 10:
                unitLabelULVar.set(message.message)
            case _:
                testLabelVar.set("WeirdIndex")

    except queue.Empty:
        pass


# Function to create and embed the matplotlib plot
def create_plot(frame, x, y):
    # Create a matplotlib figure and plot
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    # Sample plot (a simple sine wave)


    ax.plot(x, y)
    ax.set_title("Coupling Efficiency")

    # Create a canvas to embed the matplotlib figure into Tkinter
    canvas = FigureCanvasTkAgg(fig, master=frame)  # A tk.DrawingArea
    canvas.draw()

    # Pack the canvas in the frame (or use .grid(), .place())
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

def add_to_plot(XValue, YValue):
    global XPlotList, YPlotList
    if len(XPlotList) == 0:
        XPlotList = [XValue]
        YPlotList = [YValue]
    else:
        XPlotList.append(XValue)  # Increment the x-axis value
        YPlotList.append(YValue)  # Get the input value for the y-axis

    # Clear the previous plot and update the frame
    for widget in plot_frame.winfo_children():
        widget.destroy()  # Remove previous plot

    # Create the updated plot
    create_plot(plot_frame, XPlotList, YPlotList)

def clearPlotData():
    global XPlotList, YPlotList
    XPlotList = []
    YPlotList = []

def manualVoltageMesurement():

    voltage = XPS_VoltageGet(XPSStage)



def startPeakFinding():

    ImprovementList = [0.0] * MaxNumberOfItteration
    LimitReached = False
    global ReferencePower
    ReferencePower = float(referencePowerEntry.get())

    XBounaries = [-1, 1]
    XBounaries = [x + PositionList[0] for x in XBounaries]

    YBounaries = [-1, 1]
    YBounaries = [x + PositionList[1] for x in YBounaries]

    ZBounaries = [-3, 3]
    ZBounaries = [x + PositionList[2] for x in ZBounaries]

    RotBounaries = [-3, 1]
    RotBounaries = [x + PositionList[3] for x in RotBounaries]

    BoundaryTable = [XBounaries, YBounaries, ZBounaries, RotBounaries]
    MaximumCoupEff = 0.0

    posFile = open(dt_string + "/PosFile.txt", "w")
    posFile.write("Itteration, AxisIndex, XPos, YPos, ZPos, RotPos")
    for ItterationIndex in range(MaxNumberOfItteration):
        if Debugging:
            print("Starting Itteration Nr:" + str(ItterationIndex))
        if ItterationIndex >= MaxNumberOfItteration or LimitReached:
            break

        for Axis in range(4):
            [MaximumCoupEff, BoundaryTable[Axis][0], BoundaryTable[Axis][1]] = measurementRun(lowerLimit=BoundaryTable[Axis][0], upperLimit=BoundaryTable[Axis][1], numberOfPoints=NumberOfPoints, axisIndex=Axis,referencePower=ReferencePower, runNumber=ItterationIndex)

            posFile.write(str(ItterationIndex) + ", " + str(Axis) + ", " + str(PositionList[0]) + ", " + str(PositionList[1]) + ", " + str(PositionList[2]) + ", " + str(lengthToAngle(PositionList[3])) + "\n")

            if Debugging:
                print("Axis:" + str(Axis) + "between " + str(BoundaryTable[Axis][0]) + " and " + str(BoundaryTable[Axis][1]) + " at " + str(MaximumCoupEff) + "% Coupling Efficiency.")

        if ItterationIndex > MinNumberOfItteration:
            LimitReached = checkImprovement(MaximumCoupEff, ImprovementList[ItterationIndex - 1])



        ImprovementList[ItterationIndex] = MaximumCoupEff
    posFile.close()
    global OptimumList, ReachedOptimum
    OptimumList = PositionList
    ReachedOptimum = True

    messageObject = LabelUpdate(label=1, message="FoundOptimum")
    q.put(messageObject)
    root.event_generate('<<UpdateLabel>>')


def returnToOptimum():
    if ReachedOptimum:
        for i in range(4):
            moveActuators(i, OptimumList[i])

    return 3

def goToPosition():

    index = getSelectorIndex()
    position = float(positionEntry.get())

    if index == 3:
        position = angleToLength(position)

    moveActuators(index, position)
    return 3

def manualMeasurementRun():
    global ReferencePower
    ReferencePower = float(referencePowerEntry.get())
    lowerLimit = float(lowerLimitEntry.get())
    upperLimit = float(upperLimitEntry.get())
    axisIndex = getSelectorIndex()

    if axisIndex == 3:
        lowerLimit = angleToLength(lowerLimit)
        upperLimit = angleToLength(upperLimit)
    measurementRun(lowerLimit, upperLimit, NumberOfPoints, axisIndex, ReferencePower, "manual")



def moveActuators(AxisIndex: int, Position: float):
    XPos = PositionList[0]
    YPos = PositionList[1]

    PositionList[AxisIndex] = Position


    if not LimitList[AxisIndex].CheckLimit(Position=Position):
        abort()
        return False
    if Debugging:
        print("Moving Actuator Index:" + str(AxisIndex) + "to: " + str(Position))

    match AxisIndex:
        case 0:

            messageUpdate = LabelUpdate(message="XPos = " + "{:.2f}".format(Position) + "mm", label=AxisIndex + 4)
            q.put(messageUpdate)
            root.event_generate('<<UpdateLabel>>')

            XPSStage.GroupMoveAbsolute("XYGroup", [Position, YPos], 2, str())

            time.sleep(1)
            return True

        case 1:

            messageUpdate = LabelUpdate(message="YPos = " + "{:.2f}".format(Position) + "mm", label=AxisIndex + 4)
            q.put(messageUpdate)
            root.event_generate('<<UpdateLabel>>')

            XPSStage.GroupMoveAbsolute("XYGroup", [XPos, Position], 2, str())

            time.sleep(1)
            return True

        case 2:

            messageUpdate = LabelUpdate(message="ZPos = " + "{:.2f}".format(Position) + "mm", label=AxisIndex + 4)
            q.put(messageUpdate)
            root.event_generate('<<UpdateLabel>>')

            ZAxis.move_to(position=Position)
            ZAxis.wait_move(timeout=10)

            return True

        case 3:

            messageUpdate = LabelUpdate(message="Rot = " + "{:.2f}".format(lengthToAngle(Position)) + "°", label=AxisIndex + 4)
            q.put(messageUpdate)
            root.event_generate('<<UpdateLabel>>')

            #TODO Implement Angle to Position and vice versa conversion
            KCube.move_to(position=Position)
            KCube.wait_move(timeout=10)

            return True



def angleToLength(angle: float):

    length = 0.661641 * angle + 0.0986658

    return length

def lengthToAngle(length: float):

    angle = 1.51053 * length - 0.149123

    return angle


def connectToStages():

    #Connect to XPS Stage
    if not connectToXPSStage(XPSStage):
        abort()

    #Connect to Thorlabs
    ZAxis.open()
    KCube.open()
    ZAxis.set_supported_channels(3)
    ZAxis._enable_channel(enabled=True, channel=1)

    if ZAxis.is_opened() and KCube.is_opened():
        return True
    else:
        return False

def homeActuators():

    #Home XPS Stage
    XPSStage.GroupHomeSearch("XYGroup", str())

    #Home Z and Rot Axes
    KCube.setup_homing(velocity=0.75, offset_distance=7.55) #TODO Find correct offsets
    ZAxis.setup_homing(velocity=0.75, offset_distance=2)

    ZAxis.home(force=True, sync=False)
    KCube.home(force=True, sync=False)

    ZAxis.wait_for_home(timeout=40)
    KCube.wait_for_home(timeout=40)

    #TODO establish correct limit switches, maybe contact thorlabs, or trial and error
    KCube.setup_limit_switch(hw_kind_cw='ignore', hw_kind_ccw='ignore')
    ZAxis.setup_limit_switch(hw_kind_cw='ignore', hw_kind_ccw='ignore')

    KCube.setup_velocity(min_velocity=0.0, acceleration=1.0, max_velocity=2.0)
    ZAxis.setup_velocity(min_velocity=0.0, acceleration=1.0, max_velocity=2.0)

    if KCube.is_opened() and KCube.is_opened():
        return True
    else:
        return False


def convertVoltageToCoupEff(voltage: [float], referenceP: float):

    coupEff = (convertVoltageToPower(voltage) / referenceP) * 100

    return coupEff


def convertVoltageToPower(voltageV: float):

    powermW = voltageV * 0.0341 + 0.3435

    return powermW


def detectPeak(coupEff: [float]):

    length = len(coupEff)
    maximum = max(coupEff)
    lowerBoundary = 0
    upperBoundary = 0

    for id, ce in enumerate(coupEff):
        if (ce / maximum) > CouplingEfficiencyRatio:
            lowerBoundary = id
            break

    for id, ce in enumerate(reversed(coupEff)):
        if (ce / maximum) > CouplingEfficiencyRatio:
            upperBoundary = length - 1 - id
            break

    result = [lowerBoundary, upperBoundary]
    return result

def checkImprovement(currentCoupEff: float, oldCoupEff: float):

    if abs(1 - (currentCoupEff / oldCoupEff)) < ImprovementLimit:
        return True
    else:
        return False

def measurementRun(lowerLimit: float, upperLimit: float, numberOfPoints: int, axisIndex: int, referencePower: float, runNumber: any):
    clearPlotData()

    positions = linspace(lowerLimit, upperLimit, numberOfPoints)
    voltages = [0.0] * numberOfPoints
    coupEff = [0.0] * numberOfPoints
    for id, pos in enumerate(positions):
        if not moveActuators(axisIndex, pos):
            abort()
            break
        voltages[id] = XPS_VoltageGet(XPSStage)
        coupEff[id] = convertVoltageToCoupEff(voltages[id], referencePower)

        if Debugging:
            print("Voltage: " + str(coupEff[id]))

        add_to_plot(positions[id], coupEff[id])

    maximum = max(coupEff)
    maxIndex = coupEff.index(maximum)
    maxPosition = positions[maxIndex]
    AxisNames = ["XAxis", "YAxis", "ZAxis", "RotAxis"]

    if axisIndex == 3:
        temp = positions
        for id, pos in enumerate(positions):
            temp[id] = lengthToAngle(pos)
        positions = temp

    save_to_csv(dt_string + "/Run" + runNumber + "/", AxisNames[axisIndex] + ".txt", positions, voltages)
    # TODO maybe also write the fixed coordinates to file for better data analysis
    [LL, UL] = detectPeak(coupEff)

    moveActuators(axisIndex, maxPosition)
    return [maximum, LL, UL]


# Move the XY Stage to a position
def XPS_GroupMoveAbsolute(myXPS, TargetPosition, nbItems=2):

    GroupName = "XYGroup"
    result = myXPS.GroupMoveAbsolute(GroupName, TargetPosition, nbItems, str())
    if result == 0:
        return True
    else:
        return False




#Get Voltage applied to pin XPS RDL Controller
def XPS_VoltageGet(myXPS):
    voltageList = [0.0] * 1000
    voltage = [1]
    for i in range(1000):
        result = myXPS.GPIOAnalogGet(["GPIO2.ADC1"], voltage, str())
        if (result[1])[0] > 10**10:
            voltageList[i] = -10
        else:
            voltageList[i] = (result[1])[0]

    messageUpdate = LabelUpdate(message="Measured: " + "{:.2f}".format(statistics.mean(voltageList)) + "V", label=2)
    q.put(messageUpdate)
    root.event_generate('<<UpdateLabel>>')

    return statistics.mean(voltageList)



def linspace(lower_limit, upper_limit, num_points):
    if num_points <= 0:
        return []
    points = [lower_limit + i * (upper_limit - lower_limit) / (num_points - 1) for i in range(num_points)]
    return points



def create_gui(root):
    # Create a frame to hold the plot
    global plot_frame
    plot_frame = tk.Frame(root)
    plot_frame.grid(row=0, column=0, rowspan=12)

    # Call the function to create the plot in the frame
    global t, y
    t = [0]
    y = [0]
    create_plot(plot_frame, t, y)

    # Create Label and LabelVars
    global testLabelVar, voltageLabelVar, referencePowerLabelVar, xPosLabelVar, yPosLabelVar, zPosLabelVar, rotPosLabelVar, unitLabelPosVar, unitLabelLLVar, unitLabelULVar
    global testLabel, voltageLabel, referencePowerLabel, xPosLabel, yPosLabel, zPosLabel, rotPosLabel, unitLabelPos, unitLabelLL, unitLabelUL

    # Assign standard values
    testLabelVar = tk.StringVar(root, "TestLabel")
    voltageLabelVar = tk.StringVar(root, "Measured: 0 mW")
    referencePowerLabelVar = tk.StringVar(root, "Reference:")
    xPosLabelVar = tk.StringVar(root, "XPos = 0 mm")
    yPosLabelVar = tk.StringVar(root, "YPos = 0 mm")
    zPosLabelVar = tk.StringVar(root, "ZPos = 0 mm")
    rotPosLabelVar = tk.StringVar(root, "Rot = 0 °")
    unitLabelPosVar = tk.StringVar(root, "mm")
    unitLabelLLVar = tk.StringVar(root, "mm")
    unitLabelULVar = tk.StringVar(root, "mm")

    #Create Label elements and place them on the grid
    testLabel = tk.Label(root, textvariable=testLabelVar, font=("Arial", 14))
    testLabel.grid(row=16, column=3, padx=5)

    voltageLabel = tk.Label(root, textvariable=voltageLabelVar, font=("Arial", 14))
    voltageLabel.grid(row=0, column=2, padx=5)

    referencePowerLabel = tk.Label(root, textvariable=referencePowerLabelVar, font=("Arial", 14))
    referencePowerLabel.grid(row=1, column=2, padx=5)

    xPosLabel = tk.Label(root, textvariable=xPosLabelVar, font=("Arial", 14))
    xPosLabel.grid(row=5, column=1, padx=5)

    yPosLabel = tk.Label(root, textvariable=yPosLabelVar, font=("Arial", 14))
    yPosLabel.grid(row=5, column=2, padx=5)

    zPosLabel = tk.Label(root, textvariable=zPosLabelVar, font=("Arial", 14))
    zPosLabel.grid(row=6, column=1, padx=5)

    rotPosLabel = tk.Label(root, textvariable=rotPosLabelVar, font=("Arial", 14))
    rotPosLabel.grid(row=6, column=2, padx=5)

    unitLabelPos = tk.Label(root, textvariable=unitLabelPosVar, font=("Arial", 14))
    unitLabelPos.grid(row=15, column=3, padx=5)

    unitLabelLL = tk.Label(root, textvariable=unitLabelLLVar, font=("Arial", 14))
    unitLabelLL.grid(row=10, column=3, padx=5)

    unitLabelUL = tk.Label(root, textvariable=unitLabelULVar, font=("Arial", 14))
    unitLabelUL.grid(row=11, column=3, padx=5)

    upperLimitTextLabel = tk.Label(root, text="Upper Limit:", font=("Arial", 14))
    upperLimitTextLabel.grid(row=11, column=1, padx=5)

    lowerLimitTextLabel = tk.Label(root, text="Lower Limit:", font=("Arial", 14))
    lowerLimitTextLabel.grid(row=10, column=1, padx=5)

    numberOfPointsTextLabel = tk.Label(root, text="Number of points:", font=("Arial", 14))
    numberOfPointsTextLabel.grid(row=12, column=1, padx=5)

    global abortButton, manualVoltageButton, homeActuatorsButton, peakFindingButton, returnToOptimumButton, goToPosButton, startMeasurementRunButton, inputButton, startWorkerThreadButton, disconnectStagesButton
    abortButton = tk.Button(root, text="ABORT!", command=abort)
    abortButton.grid(row=0, column=3)

    manualVoltageButton = tk.Button(root, text="Manual Voltage Measurement", command=manualVoltageMesurement)
    manualVoltageButton.grid(row=0, column=1)

    connectToStagesButton = tk.Button(root, text="Connect to Stages", command=connectToStages)
    connectToStagesButton.grid(row=2, column=1)

    homeActuatorsButton = tk.Button(root, text="Home Actuators", command=homeActuators)
    homeActuatorsButton.grid(row=5, column=3)

    peakFindingButton = tk.Button(root, text="Start peak finding", command=workThread)
    peakFindingButton.grid(row=2, column=3)

    returnToOptimumButton = tk.Button(root, text="Return to optimum", command=returnToOptimum)
    returnToOptimumButton.grid(row=6, column=3)

    goToPosButton = tk.Button(root, text="Go to position", command=goToPosition)
    goToPosButton.grid(row=15, column=1)

    startMeasurementRunButton = tk.Button(root, text="Start measurement run", command=manualMeasurementRun)
    startMeasurementRunButton.grid(row=9, column=1)

    inputButton = tk.Button(root, text="INPUT!", command=lambda: add_to_plot())
    inputButton.grid(row=15)

    startWorkerThreadButton = tk.Button(root, text="Start Worker Thread", command=workThread)
    startWorkerThreadButton.grid(row=16)

    testButton = tk.Button(root, text="Test Button", command=testFunction)
    testButton.grid(row=17)

    disconnectStagesButton = tk.Button(root, text="Exit", command=disconnectStage)
    disconnectStagesButton.grid(row=17, column=3)

    global addToPlotEntry, referencePowerEntry, lowerLimitEntry, upperLimitEntry, positionEntry, numberOfPointsEntry
    addToPlotEntry = tk.Entry(root, width=20)
    addToPlotEntry.grid(row=14)

    referencePowerEntry = tk.Entry(root, width=20)
    referencePowerEntry.grid(row=1, column=3)

    lowerLimitEntry = tk.Entry(root, width=20)
    lowerLimitEntry.grid(row=10, column=2)

    upperLimitEntry = tk.Entry(root, width=20)
    upperLimitEntry.grid(row=11, column=2)

    numberOfPointsEntry = tk.Entry(root, width=20)
    numberOfPointsEntry.grid(row=12, column=2)

    positionEntry = tk.Entry(root, width=20)
    positionEntry.grid(row=15, column=2)

    separatorOne = ttk.Separator(root, orient='horizontal')
    separatorOne.grid(row=4, column=1, columnspan=3, sticky="ew")

    separatorTwo = ttk.Separator(root, orient='horizontal')
    separatorTwo.grid(row=7, column=1, columnspan=3, sticky="ew")

    separatorThree = ttk.Separator(root, orient='horizontal')
    separatorThree.grid(row=13, column=1, columnspan=3, sticky="ew")
    
    
    global AxisSelectorMenue, clicked
    global options
    options = ["X axis", "Y axis", "Z axis", "Rot axis"]
    clicked = StringVar()
    clicked.set("X axis")
    AxisSelectorMenue = OptionMenu(root, clicked, *options)
    AxisSelectorMenue.grid(row=9, column=2)

    # TODO
    # Find a change option event, to change unit to degree when Rotation axis is selected, or just rename unit to mm/deg

    root.bind('<<UpdateLabel>>', on_update_label)


def disconnectStage():
    XPSStage.GroupKill("XYGroup", str())
    XPSStage.CloseInstrument()
    ZAxis.close()
    KCube.close()
    root.destroy()


def getSelectorIndex():
    text = clicked.get()
    index = options.index(text)
    return index


def testFunction():

    if not connectToStages():
        abort()
        return 0
    now = time.time()

    voltageList = [0.0] * 1000
    for i in range(1000):
        voltageList[i] = XPS_VoltageGet(XPSStage)
    elapsed = time.time() - now
    save_to_csv("testFolder", "testVoltages", range(100), voltageList)
    print("average: " + str(statistics.mean(voltageList)))
    print("time: " + str(elapsed))

def workThread():
    # Start the worker thread
    abort_event.clear()
    thread = threading.Thread(target=startPeakFinding())
    thread.daemon = True  # Daemonize thread to exit with the program
    thread.start()


def connectToXPSStage(myXPS):

    # Connecting to XPS RDL controller for X and Y axis
    address = "192.168.0.254"
    port = 5001
    timeout = 1000

    result = myXPS.OpenInstrument(address, port, timeout)
    if result != 0:
        return False

    result = myXPS.GroupInitialize("XYGroup", str())
    if result != 0:
        return False
    return True



"""
main
"""

# TODO
# Create a close button, that also properly disconnects from the stages. The thorlabs one was funny if I remember correctly


# TODO
# Maybe include a relative or absolute selector, for the measurement run option to be around the optimum


# TODO
# make a error checking function, just a simple number check and throw error and suicide

# TODO
# disable other buttons when something is happening, maybe make a seperate function for it. using button.config(state="disabled")


global root
root = tk.Tk()
root.title("Fiber Coupling Project")
root.geometry("10000x60000")  # set starting size of window
root.maxsize(1000, 600)  # width x height

create_gui(root)

# Create a queue to communicate between threads
global q
q = queue.Queue()
# Run the Tkinter main loop
root.mainloop()


