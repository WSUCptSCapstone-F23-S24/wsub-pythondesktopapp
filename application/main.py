import serial
import pandas as pd
import matplotlib.pyplot as plt
import struct
import numpy as np
from numpy.lib.function_base import blackman
import datetime
import os

ComPort = 'COM8'

def df_column_switch(df, column1, column2):
    i = list(df.columns)
    a, b = i.index(column1), i.index(column2)
    i[b], i[a] = i[a], i[b]
    df = df[i]
    return df

# Initialize dataframe
df = pd.DataFrame({'time': [], 
                        'channel1':    [],
                        'channel2':    [],
                        'channel3':    [],
                        'channel4':    [],
                        'channel5':    [],
                        'channel6':    [],
                        'channel7':    [],
                        'channel8':    [],
                        'channel9':    [],
                        'channel10':   [],
                        'channel11':   [],
                        'channel12':   [],
                        'gainSetting': []})

current = df.copy()

ser = serial.Serial(ComPort, timeout=4)
print("connected to: " + ser.name)

fileCount = 0 #counts amount of files created (for naming purposes)
ffBuff = 0
startTime = datetime.datetime.now()
chunkBuffer = bytes(50)

# make Acquisitions folder
if not os.path.exists("Acquisitions"):
    os.makedirs("Acquisitions")

# declare new Acquisition folder name
latest_file_index = len(os.listdir("Acquisitions"))
directoryName = "Acquisition" + str(latest_file_index)
if not os.path.exists("Acquisitions/" + directoryName):
    os.makedirs("Acquisitions/" + directoryName)

try:
    #raise Exception()
    while True:
        # find "ff ff ff ff"
        while True:
            hexByte = ser.read(1).hex() 
            #print(hexByte)
            if hexByte == 'ff':
                ffBuff += 1
            else:
                ffBuff = 0

            if ffBuff >= 4:
                #print("found fffffffff")
                ffBuff = 0
                break

        #read in a chunk (50) bytes (for compatibility with von's code)
        chunkBuffer = ser.read(50)
        #print("buff: ",chunkBuffer)

        hexString = chunkBuffer.hex()
        #print("hexString: ", hexString)

        time = datetime.datetime.now() - startTime
        time = round(time.total_seconds() * 1000, 0)
       
        # Store data in Pandas dataframe
        newCurrent = pd.DataFrame({ 'time':        time, 
                                    'channel1':    struct.unpack('!i', bytes.fromhex('0'+hexString[1:8]))[0] / 234800968 * 0.2,
                                    'channel2':    struct.unpack('!i', bytes.fromhex('0'+hexString[9:16]))[0] / 234800968 * 20.0,
                                    'channel3':    struct.unpack('!i', bytes.fromhex('0'+hexString[17:24]))[0] / 234800968 * 20.0,
                                    'channel4':    struct.unpack('!i', bytes.fromhex('0'+hexString[25:32]))[0] / 234800968 * 0.1,
                                    'channel5':    struct.unpack('!i', bytes.fromhex('0'+hexString[33:40]))[0] / 234800968 * 1.0,
                                    'channel6':    struct.unpack('!i', bytes.fromhex('0'+hexString[41:48]))[0] / 234800968 * 1.0,
                                    'channel7':    struct.unpack('!i', bytes.fromhex('0'+hexString[49:56]))[0] / 234800968 * 1.0,
                                    'channel8':    struct.unpack('!i', bytes.fromhex('0'+hexString[57:64]))[0] / 234800968 * 1.0,
                                    'channel9':    np.nan,
                                    'channel10':   np.nan,
                                    'channel11':   struct.unpack('!i', bytes.fromhex('0'+hexString[81:88]))[0] / 234800968 * 1.0,
                                    'channel12':   struct.unpack('!i', bytes.fromhex('0'+hexString[89:96]))[0] / 234800968 * 1.0,
                                    'gainSetting': '0'+hexString[97:]}, index=[0])


        newCurrent = newCurrent.round(3)
        current = pd.concat([current, newCurrent])
        
        

        if len(current.index) >= 8: # row count
            #write current to csv
            #directoryPath = r'C:/Users/brayden.groshong/Workspace/Acquisition/'
            filePath = "Acquisitions/" + directoryName + "/" + str(fileCount) + ".csv"
            print("writing csv: ", filePath)
            current = current.drop(current.columns[[9, 10, 13]], axis=1)  # df.columns is zero-based pd.Index

            # must reorder some columns
            #   channel 1 = mass 45
            #   channel 3 = mass 44

            #   in module 1, 
            #   curve 5 = mass 45
            #   curve 4 = mass 44

            #   must swap
            #   channel 1, channel 5
            #   channel 3, channel 4
            #print("before", current)
            current = df_column_switch(current, 'channel1', 'channel5')
            current = df_column_switch(current, 'channel3', 'channel4')
            #print("after", current)
            current.to_csv(filePath, header=False, index=False)
            current = df.copy()
            fileCount += 1

except Exception as e:
    print("closing port: " + ser.name)
    print(e)
    ser.close()

