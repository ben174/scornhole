import random
import sys
import subprocess
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'build'))
import psmove


class Scornhole:
    FNULL = open(os.devnull, 'w')

    def __init__(self):
        self.move = psmove.PSMove()
        self.timeout = 3.0
        self.curr_time = 0.0
        self.sleep_time = 0.1
        self.sensors = {'a': 'Accelerometer', 'g': 'Gyroscope', 'm': 'Magnetometer'}
        self.axes = ['x', 'y', 'z']
        self.bar_size = 255
        self.extents = {
            'a': (-4000, 4000),
            'g': (-6000, 6000),
            'm': (-360, 360),
        }
        self.debug = False
        self.raw_values = {sensor: {axis: 0 for axis in self.axes} for sensor in self.sensors.keys()}
        self.translated_values = dict(self.raw_values)
        self.selected_sensor = 'a'
        self.show_sensors = True
        self.move_pressed = False
        self.trigger_pressed = False
        self.trigger_value = 0
        self.button_mappings = {
            'Move': psmove.Btn_MOVE,
            'Triangle': psmove.Btn_TRIANGLE,
            'Circle': psmove.Btn_CIRCLE,
            'Cross': psmove.Btn_CROSS,
            'Square': psmove.Btn_SQUARE,
            'Select': psmove.Btn_SELECT,
            'Start': psmove.Btn_START,
        }
        self.button_values = {b: False for b in self.button_mappings.keys()}
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
        lines = [line.rstrip('\n').split(' ') for line in open('specs.txt', 'r') if not line.startswith('#')]
        self.specs = lines
        print('Loaded {} videos.'.format(len(lines)))

    def play_video(self, filename, *args):
        if (len(args) > 0):
            start_x, start_y, end_x, end_y = args
            command = 'omxplayer --win="{} {} {} {}" /home/pi/videos/{}'.format(start_x, start_y, end_x, end_y, filename)
        else:
            command = 'omxplayer /home/pi/videos/{}'.format(filename)
        print('Running command: {}'.format(command))
        subprocess.Popen(command, shell=True, stdout=self.FNULL)

    def print_values(self):
        os.system('clear')
        for sensor in self.extents.keys():
            self.print_sensor(sensor)

        print()
        # print(self.raw_values)
        # print(self.translated_values)

        rgb = [self.translated_values[self.selected_sensor][axis] for axis in self.axes]
        print('RGB: {}, {}, {}'.format(*rgb))
        print('Show sensors: {}'.format(self.show_sensors))
        print('On timeout: {}'.format(self.on_timeout()))
        print()
        print('Buttons:')
        for button, value in self.button_values.items():
            print('   {}: {}'.format(button.ljust(10), value))
        print()

    def read_sensors(self):
        for sensor in ('a', 'g', 'm'):
            self.read_sensor(sensor)

    def read_sensor(self, sensor):
        lo, hi = self.extents[sensor]
        for attr in ['x', 'y', 'z']:
            value = getattr(self.move, sensor + attr)
            self.raw_values[sensor][attr] = value
            translated = int(self.translate(value, lo, hi, 0, self.bar_size))
            self.translated_values[sensor][attr] = translated

    def print_sensor(self, sensor):
        label = '{}{}'.format(self.sensors[sensor], ' (*)' if self.selected_sensor == sensor else '')
        print(label)
        print('-' * len(label))
        for attr in self.axes:
            value = self.raw_values[sensor][attr]
            translated = self.translated_values[sensor][attr]
            print('{}: {} ({}) - {}'.format(attr, str(value).rjust(6), str(translated).rjust(4), '#' * translated)) 
        print()

    def sleep(self):
        time.sleep(self.sleep_time)
        prev_time = self.curr_time
        self.curr_time = max(0, self.curr_time - self.sleep_time)
        if self.curr_time == 0 and prev_time > 0:
            if not self.debug:
                print ('You are off timeout.')

    def on_timeout(self):
        return self.curr_time > 0 

    def switch_sensor(self):
        index = list(self.sensors.keys()).index(self.selected_sensor)
        if index == 2:
            index = 0
        else:
            index += 1
        self.selected_sensor = list(self.sensors.keys())[index]
        if not self.debug:
            print ('Switch sensor to: {}'.format(self.sensors[self.selected_sensor]))

    def read_buttons(self):
        self.trigger_value = self.move.get_trigger()
        buttons = self.move.get_buttons()
        self.button_values = {label: bool(buttons & button) for label, button in self.button_mappings.items()}

    def put_on_timeout(self):
        if not self.debug:
            print ('You are on timeout.')
        self.curr_time = self.timeout


    def main(self):
        while True:
            while self.move.poll(): pass

            self.read_sensors()
            if self.show_sensors:
                rgb = [self.translated_values[self.selected_sensor][axis] for axis in self.axes]
                self.move.set_leds(*rgb)
                self.move.update_leds()
            if self.debug:
                self.print_values()

            triggered = self.trigger_value > 0 
            self.read_buttons()

            if triggered:
                self.show_sensors = False
                if self.curr_time == 0:
                    self.put_on_timeout()
                    self.load_specs()
                    self.play_video(*random.choice(self.specs))
                    # do blue
                    # self.move.set_leds(0, 0, 255)
                    self.move.update_leds()
                else:
                    if self.on_timeout():
                        self.move.set_leds(255, 0, 0)
                        self.move.update_leds()
            else:
                self.show_sensors = not self.on_timeout()
                if not self.show_sensors:
                    self.move.set_leds(0, 255, 0)
                    self.move.update_leds()
            if self.button_values['Triangle'] and not self.on_timeout():
                self.put_on_timeout()
                self.switch_sensor()


            self.sleep()

if __name__ == '__main__':
    if psmove.count_connected() < 1:
        print('No controller connected')
        sys.exit(1)
    scornhole = Scornhole()
    scornhole.main()
