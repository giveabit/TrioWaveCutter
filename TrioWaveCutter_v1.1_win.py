# -*- coding: utf-8 -*-
#!/usr/bin/env python3


# ++++++++++++++++++++++++++++++++++++++++++++
# IMPORTS
# ++++++++++++++++++++++++++++++++++++++++++++
import sys
import time
import os
import statistics as s
from glob import glob
import re
import operator

# ++++++++++++++++++++++++++++++++++++++++++++
# GLOBALS
# ++++++++++++++++++++++++++++++++++++++++++++
offsetAudio = 44 # bytes - 0...43 = header
chunkSize = 32768 #bytes
wavDir = 'Trio_wav_export'
fileExtension = '.wav'
sampleRate = 44100 # Hz
resolution = 16 # bit
headerFile = wavDir+'/header.bin'
userArgs = sys.argv[1:] # everything but the script name
initialSilence = 2 #seconds
pauseBetween = 1 #seconds



# # ++++++++++++++++++++++++++++++++++++++++++++
# # DEBUG?
# # ++++++++++++++++++++++++++++++++++++++++++++
debug = False
debugDir = 'debug'

# ++++++++++++++++++++++++++++++++++++++++++++
# FUNCTIONS
# ++++++++++++++++++++++++++++++++++++++++++++

# int.from_bytes(item, byteorder='little')

# for i in range(1300, 1319, 4):
#     if not data[i:i + 4] == b'\x00' * 4:
#         parts.append(data[i:i + 4])

# if buffer == b'\x00'*chunkSize:

def intro():
    print('-----------------------------------------------------------------------------')
    print('|                                                                    @@     |')
    print('|                                                                    @@     |')
    print('|                                                                 @@@@@@@@  |')
    print('|                                                                    @@     |')
    print('| @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@     @@@      @@@@@@@@@@@@@       @@     |')
    print('|        @@@         @@@         @@@    @@@    @@@@          @@@            |')
    print('|        @@@         @@@          @@@   @@@   @@@             @@@@          |')
    print('|        @@@         @@@          @@@   @@@  @@@@              @@@          |')
    print('|        @@@         @@@        @@@@    @@@  @@@               @@@@         |')
    print('|        @@@         @@@@@@@@@@@@@      @@@  @@@                @@@         |')
    print('|        @@@         @@@    @@@@        @@@  @@@               @@@          |')
    print('|        @@@         @@@      @@@       @@@   @@@              @@@          |')
    print('|        @@@         @@@       @@@      @@@   @@@@            @@@           |')
    print('|        @@@         @@@        @@@@    @@@     @@@@       @@@@@            |')
    print('|        @@@         @@@          @@@   @@@        @@@@@@@@@@               |')
    print('-----------------------------------------------------------------------------')
    print('WAVE CUTTING TOOL - giveabit@mail.ru\n\n')
    time.sleep(0.5)


def init():
    if not os.path.isdir(wavDir):
        os.mkdir(wavDir)
    fileList = glob('*'+ fileExtension)

    if debug:
        if not os.path.isdir(debugDir):
            os.mkdir(debugDir)
    return fileList

def readBytes(fileName, offset):
    with open(fileName, 'rb') as f:
        f.seek(offset)
        buffer = f.read()
    return buffer

def outFile(fileName, writeBytes):
    with open(fileName,'ab') as f:
        f.write(writeBytes)
    return

def writeHeader(sizeAudio):
    data = []
    data.append('RIFF'.encode())
    fileSize = sizeAudio+44-8 #file-fileSize (equals file-fileSize - 8); wav header = 44 bytes
    sampleRate = 44100
    numberChannels = 1
    bitsPerSample = 16
    byteRate = int(sampleRate*bitsPerSample*numberChannels/8)
    blockAlign = int(numberChannels*bitsPerSample/8)
    subChunk2Size = fileSize-44

    data.append(fileSize.to_bytes(4,'little'))
    data.append('WAVEfmt '.encode())
    data.append((16).to_bytes(4,'little')) #Subchunk1Size    16 for PCM
    data.append((1).to_bytes(2,'little')) #Type of format (1 is PCM)
    data.append(numberChannels.to_bytes(2,'little')) #Number of Channels
    data.append(sampleRate.to_bytes(4,'little')) #sample rate
    data.append(byteRate.to_bytes(4,'little'))# byteRate = sample Rate * BitsPerSample * Channels/ 8
    data.append(blockAlign.to_bytes(2,'little'))#BlockAlign= NumChannels * BitsPerSample/8
    data.append(bitsPerSample.to_bytes(2,'little')) # BitsPerSample
    data.append('data'.encode())
    data.append(subChunk2Size.to_bytes(4,'little'))#data-block fileSize (equals file-fileSize - 44)

    with open(headerFile, 'wb') as f:
        for item in data:
            f.write(item)

def reportProgress(position, total):
    progress = float(position/total)*100
    sys.stdout.write("progress: %.2f%%   \r" % (progress))
    sys.stdout.flush()

def timeToBytes(timeSec):
    numBytes = int(round(timeSec*sampleRate*resolution/8, 0))
    if numBytes % 2:
        numBytes += 1
    return numBytes

def bytesToTime(positionBytes):
    timeMilliseconds = int(round(positionBytes*8/resolution/sampleRate*1000,0))
    return timeMilliseconds

def meanLoudness(data, startBytes, endBytes):
    step = int(resolution/8)
    values = []
    mean = 0
    std = 0
    for i in range(startBytes, endBytes, step):
        temp = data[i:i+step]
        val = int.from_bytes(temp, byteorder='little', signed=True)
        if val > 0:
            values.append(val)
        else:
            values.append(-1*val)
    if len(values) > 1:
        mean = int(s.mean(values))
        std = int(s.stdev(values, mean))
    # print(len(values))
    return mean, std

def scanAudio(data, start, end):
    lenghtPause = int(1000 * pauseBetween)
    partsCounter = 1
    start = end
    lenght = timeToBytes(0.001)
    end += lenght

    starts = []
    ends = []

    audio = False
    while not audio and not end > len(data):
        if start % 10 == 0:
            reportProgress(start, len(data))
        meanTest, foo = meanLoudness(data, start, end)
        if meanTest > cutOn:
            audio = True
            starts.append(start-lenght)
            out = '\t\t\t'+str(partsCounter)+': '+str(time.strftime("%H:%M:%S", time.gmtime(bytesToTime(start - lenght)/1000)))+'\r'
            sys.stdout.write(out)
            start += lenght
            end = start + lenght
        else:
            start += lenght
            end = start + lenght

        counter = 0
        startOld = None
        skipAhead = True
        firstRun = True
        while audio and not end > len(data):
            if start % 10 == 0:
                reportProgress(start, len(data))
            meanTest, foo = meanLoudness(data, start, end)
            if meanTest < cutOff:
                if startOld:
                    if startOld + (counter + 1) * lenght == start:
                        counter += 1
                        skipAhead = False
                    else:
                        counter = 0
                        startOld = None
                        lastWhileSkipping = start
                        if firstRun:
                            skipAhead = True
                else:
                    startOld = start
                    skipAhead = False

            if counter == lenghtPause:
                if firstRun:
                    firstRun = False
                    start = lastWhileSkipping
                    startOld = None
                    counter = 0
                else:
                    audio = False
                    ends.append(startOld)
                    out = '\t\t\t'+str(partsCounter)+': '+str(time.strftime("%H:%M:%S", time.gmtime(bytesToTime(starts[-1])/1000)))+'\t...\t'+str(time.strftime("%H:%M:%S", time.gmtime(bytesToTime(startOld)/1000)))+'\n'
                    sys.stdout.write(out)
                    partsCounter +=1
            if skipAhead:
                start += lenghtPause*lenght
                end = start + lenght
            else:
                start += lenght
                end = start + lenght
    reportProgress(1,1)
    return starts, ends

def writeRoutine(data, starts, ends, userInput):
    audio = zip(starts, ends)
    sequence = []
    instruments = {'g': 'guitar', 'b': 'bass', 'd': 'drums'}

    for char in userInput:
        sequence.append(instruments[char])

    counter = 0
    counter2 = 0
    for item in audio:
        start, end = item
        if counter + 1 > len(sequence):
            counter = 0
            counter2 += 1
        outFileName = wavDir + '/' + fileName.split('.')[0] + '_' + sequence[counter] + '_' + str(counter2) + '.tmp'
        outFile(outFileName, data[start:end + 2])
        headerHandling(outFileName)
        counter += 1

def headerHandling(outFileName):
    try:
        sizeAudio = os.path.getsize(outFileName)  # we need the size to write a correct wav header
        writeHeader(sizeAudio)  # do it!
        with open(headerFile, "ab") as f1, open(outFileName, "rb") as f2:
            f1.write(f2.read())  # now pump the data at the end of the header
        wavFile = outFileName[:-3] + 'wav'
        if os.path.isfile(wavFile):
            os.remove(wavFile)
        os.rename(headerFile, wavFile)  # rename nicely!
        os.remove(outFileName)  # and clean up ;-)
    except:
        print('\nWe encountered an error while processing: ' + outFileName)
        e = sys.exc_info()[0]
        print('The error message reads: ', e, '\n')
        if os.path.isfile(outFileName):
            os.remove(outFileName)

def userInputHandling():
    loop = True
    print('What instruments have you recorded?')
    print('You can input [g] for guitar, [b] for bass and [d] for drums.\n')
    print('Please input the instruments in the order that they were recorded.')
    print('If you enter nothing, \'gbd\' will be selected as default.')
    while loop:
        print('\n')
        instrumentsNew = ''
        instrDict = {'g': -1, 'b': -1, 'd': -1}
        instruments = input('Your instruments are: ')
        instruments = instruments.lower()
        ex = re.compile('g')
        result = ex.search(instruments)
        if result:
            pos, foo = result.span()
            instrDict['g'] = pos
        ex = re.compile('b')
        result = ex.search(instruments)
        if result:
            pos, foo = result.span()
            instrDict['b'] = pos
        ex = re.compile('d')
        result = ex.search(instruments)
        if result:
            pos, foo = result.span()
            instrDict['d'] = pos

        sorted_instruments = sorted(instrDict.items(), key=operator.itemgetter(1))
        for item, check in sorted_instruments:
            if not check == -1:
                instrumentsNew += item

        if not instrumentsNew:
            instrumentsNew = 'gbd'

        print('Your choice was: '+instrumentsNew)
        ok = input('correct? [y]/n: ')
        default = 'y'
        ok = ok or default
        if ok.lower() in ['y','yes','1']:
            loop = False
    return instrumentsNew

def parseUserArgs():
    initialSilence = 0
    instruments = 0
    pauseBetween = 0
    for item in userArgs:
        if item[:1] == 's':
            initialSilence = float(item[1:])
        elif item[:1] == 'i':
            instruments = str(item[1:])
        elif item[:1] == 'p':
            pauseBetween = float(item[1:])
    if not initialSilence:
        initialSilence = 2
    if not instruments:
        instruments = 'gbd'
    if not pauseBetween:
        pauseBetween = 1

    return initialSilence, pauseBetween, instruments

#  ++++++++++++++++++++++++++++++++++++++++++++
#              M    A    I    N
# ++++++++++++++++++++++++++++++++++++++++++++
intro()
fileList = init()
filesTotal = str(len(fileList))
nowTotal = time.time()

for fileName in fileList:
    if not userArgs:
        userInput = userInputHandling()
    else:
        initialSilence, pauseBetween, userInput = parseUserArgs()

    print('\nprocessing: ' + fileName + '\n')
    now = time.time()
    data = readBytes(fileName, offsetAudio)

    if debug:
        debugFile = debugDir+'/'+fileName+'.DBG.txt'
    else:
        debugFile = None

    sys.stdout.write('\n\t\t\t[x] gathering noise floor.')

    start = timeToBytes(0)
    end = timeToBytes(initialSilence)
    meanFloor, stdFloor = meanLoudness(data, start, end)
    cutOn = meanFloor + 4*stdFloor
    cutOff = meanFloor + 2*stdFloor # must not be negative !!!

    if debug:
        print('\n',meanFloor, stdFloor, cutOn, cutOff)


    sys.stdout.write('\n\t\t\t[x] scanning file.\n\n')
    starts, ends = scanAudio(data, start, end)
    if len(ends) < len(starts):
        ends.append(len(data))

    sys.stdout.write('\n\t\t\t[x] writing files.')
    writeRoutine(data, starts, ends, userInput)

    runningTime = str(round(time.time()-now,1))+' seconds.\n'
    sys.stdout.write('\n\t\t\t[x] finished in: '+runningTime)
runningTimeTotal = str(round(time.time()-nowTotal, 1))+' seconds.\n'
sys.stdout.write('\n'+filesTotal+' files overall processed in: '+runningTimeTotal)
input('<ENTER>')