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
controlport = 4502

ctrl_server_address = (ip, controlport)

def send_command(timer, controllingid, thrust, roll, pitch, yaw, precesion, bank, faction, command):
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
server_address = ('127.0.0.1', 4602)
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
f = open('./data/random.' + st + '.dat', 'w')

b = []
x = []
z = []

b_o = []
x_o = []
z_o = []

fps = Fps()
fps.tic()

# Which tank I AM.
tank = 2

pitch = 1
yaw = 1
bank = 1
precesion = 1
roll = 1
thrust = 1

g = -9.81
dx = 0

swerve = False
ot_pos = None

while True:
    # read
    fps.steptoc()
    data, address = sock.recvfrom(length)

    print(f"Fps: {fps.fps}")

    # Take care of the latency
    if len(data) > 0 and len(data) == length:
        # is a valid message struct
        new_values = unpack(unpackcode, data)
        # The
        if int(new_values[td['number']]) == tank:
            f.write(str(new_values[td['timer']]) + ', ' + str(new_values[td['bearing']]) + ', ' + str(new_values[td['x']]) + ', ' + str(new_values[td['z']]) + '\n')
            f.flush()

            if new_values[td['timer']] % 30 == 0:
                thrust = np.random.uniform(-40, 40)

            if new_values[td['timer']] % 15 == 0:
                roll = np.random.uniform(-70, 70)

            send_command(new_values[td["timer"]], tank, thrust, roll, pitch, yaw, precesion, bank, 1, 0)

f.close()

print('Everything successfully closed.')
