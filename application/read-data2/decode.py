# %%
import pandas as pd
import matplotlib.pyplot as plt

# %%
def head_amp_capture(fn):
    """head_amp_capture(fn)

    Args:
        fn (string): Name of Head Amp Capture file to decode

    Returns:
        current (dataframe): Pandas dataframe that contains current for Head Amp channels as a function of time
    
    Written by: Von P. Walden, Washington State University, 6 February 2024
    """
    import struct
    import numpy as np
    from numpy.lib.function_base import blackman

    # Initialize dataframe
    current = pd.DataFrame({'time': [], 
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
    
    # Open head amp capture file
    fp = open(fn, 'rt')
    
    # Skip header line.
    fp.readline()
    
    # Set up for first 50-byte group
    bites = ""
    line = fp.readline()
    # Skip DCE line.
    if(line[46:49]=='   '): line = fp.readline()

    while len(line)>0:
        # 1) Find the start of the next group of 50 bytes; search for ' ff ff ff ff'
        while True:
            bites = bites + line[47:].replace(" ", "").strip()
            #print(line, bites)
            if('ffffffff' in bites):
                offset = len(bites) - bites.find('ffffffff') - 8
                break
            line = fp.readline()
            if(len(line)<=0): break

        # 2) Store 50-byte group of current measurements
        time = pd.to_datetime(line[21:38]) + pd.Timedelta(float(line[39:46]), unit='milliseconds')
        hexString = line[47:].replace(" ", "").strip()[-offset:]
        while(len(hexString)<100):
            line = fp.readline()
            # Skip DCE line.
            if(line[46:49]=='   '): line = fp.readline()
            hexString = hexString + line[47:].replace(" ", "").strip()
            if(len(line)<=0): break
        hexString = hexString[:100]

        # 3) Store data in Pandas dataframe
        try:
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
        except:
            break

        current = pd.concat([current, newCurrent])
        
        # 4) Reset for next iteration.
        bites = line[47:].replace(" ", "").strip()
    
    fp.close()
    current.index = current.time
    return current


# %%
fn = '../data/Head Amp Capture[28].txt'
current = head_amp_capture(fn)

#%%
#current[['channel1', 'channel2', 'channel3', 'channel4']].plot()
current[['channel1', 'channel4']].plot()

plt.show()
# %%
