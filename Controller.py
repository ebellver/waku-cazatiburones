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


def newton_raphson(f, df, x0, tol=1e-6, max_iter=1000, e=1e-6):
    x = x0
    for i in range(max_iter):
        fx = f(x)
        dfx = df(x)
        if np.abs(fx) < tol:
            return x
        x = x - fx / (dfx + e)
    return x

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
f = open('../wakuseibokan/data/sensor.' + st + '.dat', 'w')

x = []
y = []
z = []

fps = Fps()
fps.tic()

# Which tank I AM.
tank = 1
pitch = 1
yaw = 1
bank = 1
precesion = 1
roll = 1

g = -9.81
dx = 0

def f_p(x):
    global dx, g
    return 2 + np.tan(x) * dx - 9.81 / 2 * (dx / (600 * np.cos(x)))**2

def df_p(x):
    global dx, g
    return dx * (1 / np.cos(x)**2) + 2 * (g) * (dx / 600)**2 * (np.tan(x) / np.cos(x)**2)

def f_damp_o(x):
    global dx, b, g
    print(f"f: {dx * b / (600 * np.sqrt(1 - np.sin(x)**2) - 1)}")
    return np.sin(x) - dx * g / (2600 * b) * np.log(dx * b / (600 * np.sqrt(np.cos(x)**2) - 1)) + (2 * b + g) / 2600

def df_damp_o(x):
    global dx, g
    return np.cos(x) - (dx * g * np.sin(2 * x)) / (26 * b * np.cos(x) * (600 * np.cos(x) - 1))

def f_damp(x):
    global dx, b, g
    return 2 + 1 / b * (g / b + 600 * np.sin(x)) * (2 - dx * b / (600 * np.cos(x) + 1)) + (g / b**2) * (np.log(dx * b / (600 * np.cos(x) - 1)))

def df_damp(x):
    global dx, g
    return -(600 * dx * np.sin(x) * (g / b + 600 * np.sin(x))) / ((600 * np.cos(x) + 1)**2) + (600 * np.cos(x) * (2 - (dx * b) / (600 * np.cos(x) + 1))) / b + (600 * g * np.sin(x)) / (b**2 * (600 * np.cos(x) - 1))

def pol_ang(dx):
    return (46444912318939 / 39968822186453183063040000000000000000000) * dx**9 - (7781440178087 / 483182086393292832000000000000000000) * dx**8 + (316129964218830149 / 3330735182204431921920000000000000000) * dx**7 - (551924899814085793 / 1784322419038088529600000000000000) * dx**6 + (173388917298542880161 / 285491587046094164736000000000000) * dx**5 - (87408225930600458011 / 118954827935872568640000000000) * dx**4 + (1588299317143465375357 / 2938883984298028166400000000) * dx**3 - (7279883547186637908271 / 31225642333166549268000000) * dx**2 + (768588293075311340843 / 13010684305486062195000) * dx - (152727869843707009 / 17330248825156260)

def calculate_roll(bearing, target_angle):
    angle_diff = target_angle - bearing
    
    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360
    
    roll = angle_diff * 0.5
    
    return roll


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

        if int(new_values[td['number']]) != tank:
            ot_pos = (float(new_values[td['x']]), float(new_values[td['z']]))

        # The
        if int(new_values[td['number']]) == tank:

            f.write(str(new_values[0]) + ',' + str(new_values[1]) + ',' + str(new_values[2]) + ',' + str(
                new_values[3]) + ',' + str(new_values[4]) + ',' + str(new_values[6]) + '\n')
            f.flush()

            x.append(float(new_values[td['bearing']]))
            y.append(float(new_values[td['x']]))
            z.append(float(new_values[td['z']]))

            vec2d = (float(new_values[td['x']]), float(new_values[td['z']]))

            ang = 0
            polardistance = np.sqrt(vec2d[0] ** 2 + vec2d[1] ** 2)
            if ot_pos:
                dist = np.sqrt((vec2d[0] - ot_pos[0])**2 + (vec2d[1] - ot_pos[1])**2)
                dx = np.sqrt((vec2d[0]-ot_pos[0])**2 + (vec2d[1]-ot_pos[1])**2)
                ang = (180 * np.arctan2(ot_pos[1] - vec2d[1], ot_pos[0] - vec2d[0]) / np.pi) - 90
                if ang < 0:
                    ang += 360

            print(f"({vec2d[0]}, {vec2d[1]})")

            bearing = new_values[td["bearing"]]

            print(polardistance)

            if np.random.rand() <= 0.005:
                swerve = not swerve

            if np.abs(new_values[td["x"]]) >= 1300:
                mu = 270  # Mean
                sigma = 30  # Standard deviation (adjust as needed)
                to = 270 if new_values[td["x"]] < 1300 else 90 #np.random.normal(mu, sigma)
                roll = calculate_roll(bearing, to)
            elif np.abs(new_values[td["z"]]) >= 1300:
                mu = 180 if new_values[td["z"]] < 1300 else 0
                sigma = 30
                to = 180 if new_values[td["z"]] > 1300 else 0 # np.random.normal(mu, sigma)
                roll = calculate_roll(bearing, to)
            else:
                roll = calculate_roll(bearing, ang + 90 if swerve else ang - 90)


            precesion = (ang - bearing) % 360
            thrust = 50.0

            if dx > 0:
                pitch = pol_ang(dx)
            else:
                pitch = 0

            print(f"pitch = {pitch}")
            print(f"vec2d = {vec2d}")
            print(f"ot_pos = {ot_pos}")
            print(f"ang = {ang}")

            yaw = 0
            bank = 0

            send_command(new_values[td["timer"]], tank, thrust, roll, pitch, yaw, precesion, bank, 1, 0)

f.close()

print('Everything successfully closed.')
