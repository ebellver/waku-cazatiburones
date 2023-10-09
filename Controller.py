import socket
import sys
from struct import *

import numpy as np

from Fps import Fps
from TelemetryDictionary import telemetrydirs as td
from prediction import predict

# TANK SELECTION
TANK = 1

# This is the port where the simulator is waiting for commands
# The structure is given in ../commandorder.h/CommandOrder
ctrlsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ip = '127.0.0.1'
controlport = 4501 if TANK == 1 else 4502

ctrl_server_address = (ip, controlport)

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
server_address = ('127.0.0.1', 4601 if TANK == 1 else 4602)
print('Starting up on %s port %s' % server_address)

sock.bind(server_address)


def gimmesomething(ser):
    while True:
        line = ser.readline()
        if (len(line) > 0):
            break
    return line


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
b = np.array([])
x = np.array([])
z = np.array([])

b_o = np.array([])
x_o = np.array([])
z_o = np.array([])

fps = Fps()
fps.tic()

# Which tank I AM.
tank = TANK
pitch = 1
yaw = 1
bank = 1
precesion = 1
roll = 1

g = -9.81
dx = 0
vec2d = [0, 0]


def pol_ang(dx):
    return (46444912318939 / 39968822186453183063040000000000000000000) * dx ** 9 - (
            7781440178087 / 483182086393292832000000000000000000) * dx ** 8 + (
            316129964218830149 / 3330735182204431921920000000000000000) * dx ** 7 - (
            551924899814085793 / 1784322419038088529600000000000000) * dx ** 6 + (
            173388917298542880161 / 285491587046094164736000000000000) * dx ** 5 - (
            87408225930600458011 / 118954827935872568640000000000) * dx ** 4 + (
            1588299317143465375357 / 2938883984298028166400000000) * dx ** 3 - (
            7279883547186637908271 / 31225642333166549268000000) * dx ** 2 + (
            768588293075311340843 / 13010684305486062195000) * dx - (152727869843707009 / 17330248825156260)


def pol_t(dx):
    return (455792489252083847 / 2278222864627831434593280000000000000000000000) * dx ** 10 - (
            297281476762729189 / 110165515697670765696000000000000000000000) * dx ** 9 + (
            2928326376497740380661 / 189851905385652619549440000000000000000000) * dx ** 8 - (
            19760538752467831532327 / 406825511540684184748800000000000000000) * dx ** 7 + (
            1493121066314119876737973 / 16273020461627367389952000000000000000) * dx ** 6 - (
            2877174774499713591626117 / 27121700769378945649920000000000000) * dx ** 5 + (
            12294838591773623965364723 / 167516387104987605484800000000000) * dx ** 4 - (
            402963480717060484668713503 / 14238892903923946466208000000000) * dx ** 3 + (
            63917385703876927998265279 / 11865744086603288721840000000) * dx ** 2 + (
            4137764182556694717803 / 10866066013372975020000) * dx


def calculate_roll(bearing, target_angle):
    angle_diff = target_angle - bearing

    if angle_diff > 180:
        angle_diff -= 360
    elif angle_diff < -180:
        angle_diff += 360

    roll = angle_diff * 0.25
    # if roll > 100:
    #     roll = 100
    # elif roll < -100:
    #     roll = -100

    return roll


def prob_fire(dx):
    return np.cbrt(dx / -3600) + 1


swerve = False
ot_pos = None
ot_pred = None
bullets = 1000
timer = 0
thrust = 0
allowed_fire = True

while True:
    fps.steptoc()
    data, address = sock.recvfrom(length)

    # print(f"Fps: {fps.fps}")

    if len(data) > 0 and len(data) == length:
        new_values = unpack(unpackcode, data)

        if int(new_values[td['number']]) != tank:
            b_o = np.append(b_o, [float(new_values[td['bearing']])])
            x_o = np.append(x_o, [float(new_values[td['x']])])
            z_o = np.append(z_o, [float(new_values[td['z']])])
            ot_pos = np.array([x_o[-1], z_o[-1]])
            dx_aux = np.sqrt((vec2d[0] - ot_pos[0]) ** 2 + (vec2d[1] - ot_pos[1]) ** 2)
            if len(b_o) >= 10 and new_values[td['timer']] >= 50:
                ot_pred = predict(b_o[-10:], x_o[-10:], z_o[-10:], pol_t(dx_aux))
            allowed_fire = True
            if new_values[td['y']] > 11:
                allowed_fire = False

        if int(new_values[td['number']]) == tank:
            b = np.append(b, [float(new_values[td['bearing']])])
            x = np.append(x, [float(new_values[td['x']])])
            z = np.append(z, [float(new_values[td['z']])])

            vec2d = (float(x[-1]), float(z[-1]))

            # if new_values[td['timer']] % 10 == 0:
            #     thrust = np.random.uniform(-40, 40)

            ang = 0
            target = ot_pos
            if ot_pred is not None:
                target = ot_pred

            bearing = new_values[td["bearing"]]
            if target is not None:
                dist = np.sqrt((vec2d[0] - target[0]) ** 2 + (vec2d[1] - target[1]) ** 2)
                dx = np.sqrt((vec2d[0] - target[0]) ** 2 + (vec2d[1] - target[1]) ** 2)
                ang = (180 * np.arctan2(target[1] - vec2d[1], target[0] - vec2d[0]) / np.pi) - 90
                # print(f"ayuda {(-180 * np.arctan2(1, 0) / np.pi) + 90}")
                # print(f"ang: {ang}", f"[x, z]: {[target[0] - vec2d[0], target[1] - vec2d[1]]}", f"atan2: {180 * np.arctan2(target[1] - vec2d[1], target[0] - vec2d[0]) / np.pi}")
                if ang < 0:
                    ang += 360
                if np.abs(bearing - ang) < 30 or np.abs(bearing - ang) > 330:
                    dx -= thrust
                elif np.abs(bearing - ang) > 150 and np.abs(bearing - ang) < 210:
                    dx += thrust

            if np.random.rand() <= 0.01:
                swerve = not swerve

            if np.abs(x[-1]) >= 1300:
                to = 270 if x[-1] < 1300 else 90
                roll = calculate_roll(bearing, to)
            elif np.abs(z[-1]) >= 1300:
                to = 180 if z[-1] > 1300 else 0
                roll = calculate_roll(bearing, to)
            else:
                if dx < 400:
                    change = np.random.normal(100, 5)
                else:
                    change = np.random.normal(90, 5)
                # roll = calculate_roll(bearing, ang + 90 if swerve else ang - 90)
                roll = calculate_roll(bearing, ang + change if swerve else ang - change)
                # roll = calculate_roll(bearing, ang + 90)
                # print(f"swerve: {swerve}", f"roll: {roll}", f"bearing: {bearing}", f"ang: {(ang + 90 if swerve else ang - 90) % 360}")

            precesion = (ang - bearing) % 360
            # precesion = ((ang - bearing) - roll * 0.05 * (np.abs(ang - bearing)/180)) % 360

            if dx > 0:
                pitch = pol_ang(dx)
            else:
                pitch = 0

            yaw = 0
            bank = 0

            fire = 0

            if new_values[td['timer']] > 40:
                thrust = 50

            if new_values[td['timer']] > 100:
                if timer > 0:
                    timer -= 1
                elif np.random.rand() <= 0.025:
                    timer = 5
                    thrust = -thrust
                else:
                    thrust = 20
            # if new_values[td["timer"]] % 250 <= 50:
            #     thrust = 0
            #     if new_values[td["timer"]] % 250 > 40:
            #         fire = 11

            if np.abs(roll) < 5 and allowed_fire:
                if bullets > 400:
                    fire = 11
                    bullets -= 1
                elif np.random.rand() <= prob_fire(dx):
                    fire = 11
                    bullets -= 1
            elif np.random.rand() <= prob_fire(dx) and allowed_fire:
                fire = 11
                bullets -= 1

            if 25 < new_values[td["timer"]] <= 30 + 170 * prob_fire(dx):
                fire = 11
                bullets -= 1

            send_command(new_values[td["timer"]], tank, thrust, roll, pitch, yaw, precesion, bank, 1, fire)

print('Everything successfully closed.')
