
"""
__author__ = "Ritik Agarwal, Zoe Parker"
__credits__ = ["Ritik Agarwal", "Zoe Parker"]
__version__ = "1.0.0"
__maintainer__ = ""
__email__ = ["agarwal.ritik1101@gmail.com", "zoeparker@comcast.net"]
__status__ = "Completed"
"""
import pandas as pd
import time as time
from sharedSingleton import SharedSingleton



class File:

    def __init__(self, fileName):
        
        self.fileName = fileName
        self.data = self.__openFile()
        self.sharedData = SharedSingleton()
        self.fileType = 0 # 0 == normal, 1 == new


    def __openFile(self):
        
        d = pd.read_csv(self.fileName, header=None)
        print("printing opened file")
        print(d)
        return d

    def __iter__(self):
        pass

    def __next__(self):
        if self.fileType == 0:
            x_len = len(list(self.data.iloc[:,0]))
            x_first = list(self.data.iloc[:,0])[0]/1000
            x_last = list(self.data.iloc[:,0])[x_len-1]/1000
            x = self.sharedData.xPoint + (x_last - x_first)
            self.sharedData.xPoint = x


            y_mean_data = list(self.data.astype('float64').mean(axis=0))
            y_mean_data.pop(0)
            
            print(x, y_mean_data)
            return x,y_mean_data