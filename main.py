'''

UDP Telemetry Receiver and controller.

This script receives the information from the simulator (the telemetry)
picks only the data that corresponds to one of the tanks, and sends
a command to the simulator to control the tank.

'''

import numpy as np

import time
import datetime
from struct import *

import sys, select

import socket

from TelemetryDictionary import telemetrydirs as td

import math

from Fps import Fps

# This is the port where the simulator is waiting for commands
# The structure is given in ../commandorder.h/CommandOrder
ctrlsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ip = '127.0.0.1'
controlport = 4501

ctrl_server_address = (ip, controlport)


def send_command(timer, controllingid, thrust, roll, pitch, yaw, precesion, bank, faction, command):
    #    controllingid=1
    #    thrust=10.0
    #    roll=1.0
    #    pitch=0.0
    #    yaw=0.0
    #    precesion=0.0
    #    bank=0.0
    #    faction=1
    #    #timer=1

    spawnid = 0
    typeofisland = 0
    x = 0.0
    y = 0.0
    z = 0.0
    target = 0
    bit = 0
    weapon = 0

    # This is the structure fron CommandOrder
    data = pack("iffffffiLiiifffi?i",
                controllingid,
                thrust,
                roll,
                pitch,
                yaw,
                precesion,
                bank,
                faction,
                timer,
                command,  # 0 or 11
                spawnid,
                typeofisland,
                x, y, z,
                target,
                bit,
                weapon)

    sent = ctrlsock.sendto(data, ctrl_server_address)

    return


data1 = 4
data2 = 2
data3 = 3

min = -400
max = 400

# Telemetry length and package form.
length = 84
unpackcode = 'Liiiffffffffffffffff'

if (len(sys.argv) >= 2):
    print("Reading which data to shown")
    try:
        data1 = int(sys.argv[1])
        data2 = int(sys.argv[2])
        data3 = int(sys.argv[3])
    except:
        data1 = telemetrydirs[sys.argv[1]]
        data2 = telemetrydirs[sys.argv[2]]
        data3 = telemetrydirs[sys.argv[3]]
        pass

if (len(sys.argv) >= 5):
    min = int(sys.argv[4])
    max = int(sys.argv[5])

if (len(sys.argv) >= 7):
    length = int(sys.argv[6])
    unpackcode = sys.argv[7]

# UDP Telemetry port on port 4500
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 4601)
print('Starting up on %s port %s' % server_address)

sock.bind(server_address)


def gimmesomething(ser):
    while True:
        line = ser.readline()
        if (len(line) > 0):
            break
    return line


# Sensor Recording
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S')
f = open('./data/sensor.' + st + '.dat', 'w')
out = open("./scripts/pitch2.csv", 'w')
out.write("health,power,bearing,x,y,z,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,r12\n")

x = []
y = []
z = []

fps = Fps()
fps.tic()

# Which tank I AM.
tank = 1
pitch = 1

while True:
    # read
    fps.steptoc()
    data, address = sock.recvfrom(length)

    #    print(f"data: {data}")

    print(f"Fps: {fps.fps}")

    # Take care of the latency
    if len(data) > 0 and len(data) == length:
        # is  a valid message struct
        new_values = unpack(unpackcode, data)
        if int(new_values[td['number']]) == tank:
            out.write(
                f"{new_values[2]},{new_values[3]},{new_values[4]},{new_values[5]},{new_values[6]},{new_values[7]},{new_values[8]},{new_values[9]},{new_values[10]},{new_values[11]},{new_values[12]},{new_values[13]},{new_values[14]},{new_values[15]},{new_values[16]},{new_values[17]},{new_values[18]},{new_values[19]}\n")
        # out.flush()

        # The
        if int(new_values[td['number']]) == tank:

            f.write(str(new_values[0]) + ',' + str(new_values[1]) + ',' + str(new_values[2]) + ',' + str(
                new_values[3]) + ',' + str(new_values[4]) + ',' + str(new_values[6]) + '\n')
            f.flush();

            x.append(float(new_values[td['bearing']]))
            y.append(float(new_values[td['x']]))
            z.append(float(new_values[td['z']]))

            vec2d = (float(new_values[td['x']]), float(new_values[td['z']]))

            polardistance = math.sqrt(vec2d[0] ** 2 + vec2d[1] ** 2)

            print(polardistance);

            if polardistance < 1700:
                thrust = 0.0
            else:
                thrust = 0.0

            roll = 0.0
            pitch = pitch + 90
            yaw = 0
            precesion = 0
            bank = 0.0

            # Analyze the data to determine what to do.
            # Do something
            send_command(new_values[td["timer"]], tank, thrust, roll, pitch, yaw, precesion, bank, 1, 0)

f.close()
out.close()

print('Everything successfully closed.')
