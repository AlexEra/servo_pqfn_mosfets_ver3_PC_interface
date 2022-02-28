import serial
import threading
from time import time


def read_from_port():
    global prt, thread_is_con
    while thread_is_con:
        if prt is not None:
            from_prt = prt.readline()
            if 2 <= len(from_prt) <= 5:
                print('\n', f'{adc_to_grad(from_prt)} grad', '\n')
            elif from_prt != b'':
                print('\n', from_prt, '\n')


def grad_to_adc(val: int):
    return int(val * 4095 / 360)


def adc_to_grad(adc_bytes: bytes) -> float:
    return round(int(adc_bytes) * 360 / 4095, 2)


def return_value_from_str(in_str: str) -> (int, int):
    low_byte = int(in_str) & 0x00FF
    high_byte = (int(in_str) & 0xFF00) >> 8
    return low_byte, high_byte


if __name__ == '__main__':
    kp, ki, kd = '', '', ''
    log_file = open('log_' + str(time()) + '.txt', 'w')

    thread_is_con = True

    prt = None
    try:
        prt = serial.Serial(port='COM6', baudrate=115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                            stopbits=serial.STOPBITS_ONE, timeout=1, write_timeout=20)
    except Exception as e:
        exit(e)

    thread_prt = threading.Thread(target=read_from_port)
    thread_prt.start()

    to_send = bytearray(8)
    value = 0

    while True:
        input_str = input('Command: ')

        try:
            value = grad_to_adc(int(input_str))
            number_feature = True
        except ValueError:
            number_feature = False

        if number_feature:
            to_send[0] = 97
            to_send[7] = 0
            to_send[1] = value & 0x00FF
            to_send[2] = (value & 0xFF00) >> 8
            if value > 4095:
                print('Angle should be less 360!')
                continue
            print(f'ADC: {value}\n')
            log_file.write(input_str + '\n')
            # print(to_send, '\n')
            prt.write(to_send)
        else:
            if len(input_str) == 1:
                if input_str == 'q':
                    print('Bye-bye!')
                    thread_is_con = False
                    log_file.close()
                    exit()
                elif input_str == 'c':
                    print(f'kp = {kp}, ki = {ki}, kd = {kd}')
                elif input_str in ['a', 't', 'e']:
                    for i in range(len(to_send) - 1):
                        to_send[i] = 0
                    to_send[7] = ord(input_str)

                elif input_str in ['b', 'f', 's']:
                    for i in range(1, len(to_send) - 1):
                        to_send[i] = 0
                    to_send[0] = ord(input_str)
                    to_send[7] = 0

                else:
                    print('Error: unknown command')
                    continue

                log_file.write(input_str + '\n')
                # print(to_send, '\n')
                prt.write(to_send)

            elif len(input_str) > 1 and input_str[1:].isdigit():
                if input_str[0] not in ['p', 'i', 'd']:
                    print('Error: unknown command')
                    continue
                else:
                    to_send[0] = ord(input_str[0])
                    to_send[7] = 0
                    to_send[1], to_send[2] = return_value_from_str(input_str[1:])
                    log_file.write(input_str + '\n')
                    # print(to_send, '\n')
                    prt.write(to_send)

                    if input_str[0] == 'p':
                        kp = input_str[1:]
                    elif input_str[0] == 'i':
                        ki = input_str[1:]
                    elif input_str[0] == 'd':
                        kd = input_str[1:]
            else:
                print('Error: unknown command')
                continue
