from subprocess import Popen, PIPE

p0 = Popen(['python', 'demo-slave.py', "/dev/ttyACM0"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
p1 = Popen(['python', 'demo-slave.py', "/dev/ttyACM1"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
p2 = Popen(['python', 'demo-slave.py', "/dev/ttyACM2"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
p3 = Popen(['python', 'demo-slave.py', "/dev/ttyACM3"], stdin=PIPE, stdout=PIPE, stderr=PIPE)

while True:
    out0 = p0.stdout.readline().decode('utf-8').split(" ")
    (anchor0,pulse0,syncT0) = (out0[1],out0[3],out0[5])
    out1 = p1.stdout.readline().decode('utf-8').split(" ")
    (anchor1,pulse1,syncT1) = (out1[1],out1[3],out1[5])
    out2 = p2.stdout.readline().decode('utf-8').split(" ")
    (anchor2,pulse2,syncT2) = (out2[1],out2[3],out2[5])
    out3 = p3.stdout.readline().decode('utf-8').split(" ")
    (anchor3,pulse3,syncT3) = (out3[1],out3[3],out3[5])
    print("out0:{}\nout1:{}\nout2: {}\nout3: {}\n\n"
        .format((anchor0,pulse0,syncT0), (anchor1,pulse1,syncT1), (anchor2,pulse2,syncT2),(anchor3,pulse3,syncT3)))