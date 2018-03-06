import random
import sys
import subprocess
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'build'))
import psmove



class Scornhole:
    def __init__(self):
        self.move = psmove.PSMove()
        self.timeout = 3.0
        self.curr_time = 0.0
        self.sleep_time = 0.1
        self.extents = {
            'a': (-4000, 4000),
            'g': (-6000, 6000),
            'm': (-360, 360),
        }
        self.raw_values = {
            'a': (0),
            'g': (0),
            'm': (0),
        }
        self.translated_values = {
            'a': (0),
            'g': (0),
            'm': (0),
        }

        if self.move.connection_type == psmove.Conn_Bluetooth:
            print('bluetooth')
        elif self.move.connection_type == psmove.Conn_USB:
            print('usb')
        else:
            print('unknown')

        if self.move.connection_type != psmove.Conn_Bluetooth:
            print('Please connect controller via Bluetooth')
            sys.exit(1)

        self.specs = self.load_specs()

    def translate(self, value, inputMin, inputMax, outputMin, outputMax):
        # clip extents
        if value < inputMin:
            return outputMin
        if value > inputMax:
            return outputMax
        # Figure out how 'wide' each range is
        inputSpan = inputMax - inputMin
        outputSpan = outputMax - outputMin
        # Convert the input range into a 0-1 range (float)
        valueScaled = float(value - inputMin) / float(inputSpan)
        # Convert the 0-1 range into a value in the output range.
        ret = outputMin + (valueScaled * outputSpan)
        # print('Translated: {} => {} - {} to {} - {} => {}'.format(value, inputMin, inputMax, outputMin, outputMax, int(ret)))
        return ret

    def load_specs(self):
        lines = [line.rstrip('\n').split(' ') for line in open('specs.txt', 'r')]
        self.specs = lines
        print(lines)

    def play_video(self, filename, start_x, start_y, end_x, end_y):
        command = 'omxplayer --win="{} {} {} {}" /home/pi/videos/{}'.format(start_x, start_y, end_x, end_y, filename)
        subprocess.Popen(command, shell=True)


    def print_values(self):
        os.system('clear')
        # print('accel:       ', (str(self.move.ax).rjust(6), str(self.move.ay).rjust(6), str(self.move.az).rjust(6)))
        # print('gyro:        ', (str(self.move.gx).rjust(6), str(self.move.gy).rjust(6), str(self.move.gz).rjust(6)))
        # print('magnetometer:', (str(self.move.mx).rjust(6), str(self.move.my).rjust(6), str(self.move.mz).rjust(6)))
        for sensor in ('a', 'g', 'm'):
            self.print_sensor(sensor)

        print()
        print(self.raw_values)
        print(self.translated_values)

    def print_sensor(self, sensor):
        bar_size = 255
        lo, hi = self.extents[sensor]
        print('Sensor: {}'.format(sensor))
        for attr in [sensor + 'x', sensor + 'y', sensor + 'z']:
            value = getattr(self.move, attr)
            self.raw_values[attr] = value
            translated = int(self.translate(value, lo, hi, 0, bar_size))
            self.translated_values[attr] = translated
            print('{}: {} ({}) - {}'.format(attr, str(value).rjust(6), str(translated).rjust(4), '#' * translated)) 
        print()

    def sleep(self):
        time.sleep(self.sleep_time)
        prev_time = self.curr_time
        self.curr_time = max(0, self.curr_time - self.sleep_time)
        if self.curr_time == 0 and prev_time > 0:
            print ('Ready.')

    def main(self):
        lowest_value = 0
        highest_value = 4000

        while True:
            # Get the latest input report from the controller
            while self.move.poll(): pass

            self.print_values()

            trigger_value = self.move.get_trigger()

            triggered = trigger_value > 0 
            # print(trigger_value)

            min_value = -180
            max_value = 180

            value = self.move.gx

            if value == -32768:
                self.sleep()
                continue

            lowest_value = min(lowest_value, value)
            highest_value = max(highest_value, value)

            if value < min_value or value > max_value:
                self.sleep()
                continue

            # print('Lowest: {}, Highest: {}'.format(lowest_value, highest_value))

            min_led = 1
            max_led = 255
                                                                                                                                                                                                                                                                      
            on_timeout = self.curr_time > 0 
            buttons = self.move.get_buttons()

            self.move_pressed = buttons & psmove.Btn_MOVE

            if not triggered:
                self.move.set_leds(0 if on_timeout else 255, 255 if on_timeout else 0, 0)
                self.move.update_leds()

            # self.move.ay -4400 - 4400

            if triggered:
                if self.curr_time == 0:
                    self.load_specs()
                    print('Showing vid')
                    self.play_video(*random.choice(self.specs))
                    self.curr_time = self.timeout
                else:
                    self.move.set_leds(0, 0, 255)
                    self.move.update_leds()
                # print('triangle pressed')
                # self.move.set_rumble(trigger_value)
            else:
                self.move.set_rumble(0)

            
            # print (self.move.get_buttons())
            # print (trigger_value)

            self.sleep()

if __name__ == '__main__':
    if psmove.count_connected() < 1:
        print('No controller connected')
        sys.exit(1)
    scornhole = Scornhole()
    scornhole.main()
