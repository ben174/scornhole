import random
import sys
import subprocess
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'build'))

import psmove
import time




class Scornhole:
    def __init__(self):
        self.move = psmove.PSMove()

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

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.

        ret = rightMin + (valueScaled * rightSpan)
        
        return ret


    def load_specs(self):
        lines = [line.rstrip('\n').split(' ') for line in open('specs.txt', 'r')]
        self.specs = lines
        print(lines)

    def play_video(self, filename, start_x, start_y, end_x, end_y):
        command = 'omxplayer --win="{} {} {} {}" /home/pi/videos/{}'.format(start_x, start_y, end_x, end_y, filename)
        #command = 'omxplayer --win="0 0 800 1100" /home/pi/videos/dapper.mp4'
        subprocess.Popen(command, shell=True)


    def print_value(self):
        pass

    def main(self):
        lowest_value = 0
        highest_value = 4000
        timeout = 3.0
        curr_time = 0.0
        command = 'omxplayer', '--win="-825 0 1600 1024"', '/home/pi/videos/explosion.mp4'
        command = 'omxplayer', '--win="0 0 1000 1800"', '/home/pi/videos/dapper.mp4'
        sleep_time = 0.01

        while True:
            # Get the latest input report from the controller
            while self.move.poll(): pass

            trigger_value = self.move.get_trigger()

            triggered = trigger_value > 0 
            # print(trigger_value)

            min_value = -180
            max_value = 180

            value = self.move.gx

            if value == -32768:
                continue

            lowest_value = min(lowest_value, value)
            highest_value = max(highest_value, value)

            if value < min_value or value > max_value:
                continue

            # print('Lowest: {}, Highest: {}'.format(lowest_value, highest_value))

            min_led = 1
            max_led = 255
                                                                                                                                                                                                                                                                      
            red = int(self.translate(value, min_value, max_value, min_led, max_led))
            # print ('# * {} + <sp> * {}'.format(red, 255-red))
            # print (('#' * red) + ' ' * (max_led-red), end='' + str(red).rjust(5))

            # print ('\b' * (max_led + 5), end='')

            # print(red)
            on_timeout = curr_time > 0 
            buttons = self.move.get_buttons()

            self.move_pressed = buttons & psmove.Btn_MOVE

            if not triggered:
                self.move.set_leds(0 if on_timeout else 255, 255 if on_timeout else 0, 0)
                self.move.update_leds()

            # self.move.ay -4400 - 4400

            if triggered:
                if curr_time == 0:
                    self.load_specs()
                    print('Showing vid')
                    self.play_video(*random.choice(self.specs))
                    curr_time = timeout
                else:
                    self.move.set_leds(0, 0, 255)
                    self.move.update_leds()
                # print('triangle pressed')
                # self.move.set_rumble(trigger_value)
            else:
                self.move.set_rumble(0)

            
            '''
            print('accel:', (self.move.ax, self.move.ay, self.move.az))
            print('gyro:', (self.move.gx, self.move.gy, self.move.gz))
            print('magnetometer:', (self.move.mx, self.move.my, self.move.mz))
            '''
            #print('accel:', (str(self.move.ax).rjust(5), str(self.move.ay).rjust(5), str(self.move.az).rjust(5)))
            # print (self.move.get_buttons())
            # print (trigger_value)
            prev_time = curr_time
            curr_time = max(0, curr_time - sleep_time)
            if curr_time == 0 and prev_time > 0:
                print ('Ready.')
            time.sleep(sleep_time)

if __name__ == '__main__':
    if psmove.count_connected() < 1:
        print('No controller connected')
        sys.exit(1)
    scornhole = Scornhole()
    scornhole.main()
