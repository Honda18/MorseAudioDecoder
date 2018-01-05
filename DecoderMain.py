from sys import byteorder
from array import array
from struct import pack

import pyaudio
import wave
import struct
import numpy as np

THRESHOLD = 300
#Chunks of data
chunk=480
FORMAT = pyaudio.paInt16
#Frames per second
RATE = 48000
window = np.blackman(chunk)
FREQ = 700
HzVARIANCE = 20
ALLOWANCE = 3
WINDOW = 160

letter_to_morse = {
	"a" : ".-",	"b" : "-...",	"c" : "-.-.",
	"d" : "-..",	"e" : ".",	"f" : "..-.",
	"g" : "--.",	"h" : "....",	"i" : "..",
	"j" : ".---",	"k" : "-.-",	"l" : ".-..",
	"m" : "--",	"n" : "-.",	"o" : "---",
	"p" : ".--.",	"q" : "--.-",	"r" : ".-.",
	"s" : "...",	"t" : "-",	"u" : "..-",
	"v" : "...-",	"w" : ".--",	"x" : "-..-",
	"y" : "-.--",	"z" : "--..",	"1" : ".----",
	"2" : "..---",	"3" : "...--",	"4" : "....-",
	"5" : ".....", 	"6" : "-....",	"7" : "--...",
	"8" : "---..",	"9" : "----.",	"0" : "-----",
	" " : "/"}


def is_silent(snd_data):
    "Returns 'True' if below the 'silent' threshold"
    return max(snd_data) < THRESHOLD

def normalize(snd_data):
    "Average the volume out"
    #32768 maximum /2
    MAXIMUM = 16384
    times = float(MAXIMUM)/max(abs(i) for i in snd_data)

    r = array('h')
    for i in snd_data:
        r.append(int(i*times))
    return r

def decode(list1):

    list1=list1.split("0")
    listascii=""
    counter=0


    for i in range(len(list1)):
        if len(list1[i])==0: #blank character adds 1
            counter+=1
        else:
            if counter<ALLOWANCE:
                list1[i]+=list1[i-counter-1]
                list1[i-counter-1]=""
            counter=0


    for i in range(len(list1)):
        if len(list1[i])>=20 and len(list1[i])<50:#200-490 ms dah, throws values >50
            listascii+="-"
            counter=0
        elif len(list1[i])<20 and len(list1[i])>5: #50-190ms is dit
            listascii+="."
            counter=0
        elif len(list1[i])==0: #blank character adds 1
            counter+=1
            if 40<counter<50 and len(list1[i+1])!=0: #370 ms blanks is letter space
                listascii+=" "
                counter=0
            elif counter==80: #80 ms blanks is word space
                listascii+="  "
                counter=0

    listascii=listascii.split(" ")


    stringout=""

    for i in range(len(listascii)):
        for letter,morse in letter_to_morse.items():
            if listascii[i]==morse:
                stringout+=letter
        if listascii[i]=="":
            stringout+=" "

    if(stringout!= " "):
        print(stringout)


def record():
    num_silent = 0
    snd_started = False
    oncount = 0
    offcount = 0
    status = 0
    timelist = ""

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
			channels=1,
			rate=RATE,
        		input=True,
			input_device_index=2,
			frames_per_buffer=chunk)


    #r = array('h')
    print("started")
    while True:

		#Reads audio data from stream
        snd_data = stream.read(chunk, exception_on_overflow = False)
		#Big endian to little endian byte sequence
        if byteorder == 'big':
            snd_data.byteswap()

        #Gets size of sample format
        sample_width = p.get_sample_size(FORMAT)

        #find frequency of each chunk
        indata = np.array(wave.struct.unpack("%dh"%(chunk), snd_data))*window

        #take fft and square absolute of each value
        fftData = abs(np.fft.rfft(indata))**2

        # find the index of the maximum
        which = fftData[1:].argmax() + 1

        silent = is_silent(indata)

        if silent:
            thefreq = 0
        elif which != len(fftData)-1:
			#Quadratic interpolation
            y0,y1,y2 = np.log(fftData[which-1:which+2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency
            thefreq = (which+x1)*RATE/chunk
        else:
            thefreq = which*RATE/chunk

        if thefreq > (FREQ-HzVARIANCE) and thefreq < (FREQ+HzVARIANCE):
            status = 1
        else:
            status = 0

        if status == 1:
            timelist+="1"
            num_silent = 0

        else:
            timelist+="0"
            num_silent += 1

        if num_silent > WINDOW and "1" in timelist:

            decode(timelist)
            timelist=""

        if num_silent > 1000:
            print("reset")
            num_silent =0

    print("ended")
    print(num_silent)
    p.terminate()

record()
