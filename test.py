import serial, time

ser = serial.Serial("COM10", 115200, timeout=1)
time.sleep(2)
ser.reset_input_buffer()

ser.write(b"led 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0\n")

while True:
    line = ser.readline().decode(errors='ignore').strip()
    if line:
        print(f"Received: {line!r}")
        if line == "OK":
            break