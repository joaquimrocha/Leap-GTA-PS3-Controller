#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Leap Motion GTA 5 Controller
#  Copyright © 2013 Joaquim Rocha <me@joaquimrocha.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import Leap
import uinput
import sys, time
from Leap import CircleGesture, SwipeGesture, KeyTapGesture
import logging

class EventManager(object):

    FUNCTIONS_DEFAULT_DURATION = .1 # seconds
    ACCELERATE_COMBO = (uinput.KEY_A,)
    RUN_COMBO = (uinput.KEY_R,)
    WALK_COMBO = (uinput.KEY_UP,)
    WALK_BACK_COMBO = (uinput.KEY_DOWN,)
    BREAK_REVERSE_COMBO = (uinput.KEY_S,)
    LEFT_COMBO = (uinput.KEY_LEFT,)
    RIGHT_COMBO = (uinput.KEY_RIGHT,)
    UP_COMBO = (uinput.KEY_UP,)
    DOWN_COMBO = (uinput.KEY_DOWN,)
    CAR_ACTION_COMBO = (uinput.KEY_E,)
    JUMP_COMBO = (uinput.KEY_SPACE,)
    CONFIRM_COMBO = (uinput.KEY_ENTER,)

    RUNNING_RESET_TIMEOUT = .5 # seconds
    PRESS_RELEASE_TIMEOUT = .5 # seconds
    CAR_ENTER_LEAVE_TIMEOUT = 2 # seconds

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self._run_times = {}
        self._run_active_time = 0
        self._dev = uinput.Device(self.ACCELERATE_COMBO + self.WALK_COMBO +
                                  self.BREAK_REVERSE_COMBO + self.LEFT_COMBO +
                                  self.RIGHT_COMBO + self.UP_COMBO +
                                  self.DOWN_COMBO + self.CAR_ACTION_COMBO +
                                  self.JUMP_COMBO + self.CONFIRM_COMBO +
                                  self.RUN_COMBO,
                                  bustype=0x03)

    def accelerate(self):
        self._key_release(self.BREAK_REVERSE_COMBO)
        self._key_press(self.ACCELERATE_COMBO)

    def run(self):
        self._run_active_time = time.time()

    def _check_running_active(self, combo):
        if (time.time() - self._run_active_time) < self.RUNNING_RESET_TIMEOUT:
            combo = combo + self.RUN_COMBO
        else:
            self._key_release(self.RUN_COMBO)
        return combo

    def walk_forward(self):
        self.clear_movement()
        combo = self._check_running_active(self.WALK_COMBO)
        self._key_press(combo)

    def walk_back(self):
        self.clear_movement()
        combo = self._check_running_active(self.WALK_BACK_COMBO)
        self._key_press(combo)

    def break_reverse(self):
        self._key_release(self.ACCELERATE_COMBO)
        self._key_press(self.BREAK_REVERSE_COMBO)

    def clean_permanent_actions(self):
        for combo in [self.ACCELERATE_COMBO, self.WALK_COMBO, self.LEFT_COMBO,
                      self.RIGHT_COMBO, self.UP_COMBO,
                      self.BREAK_REVERSE_COMBO]:
            self._key_release(combo)

    def jump(self):
        self._run_function(self._press_and_release_key_combo,
                           self.FUNCTIONS_DEFAULT_DURATION,
                           self.JUMP_COMBO)

    def car_enter_leave(self):
        self.clean_permanent_actions()
        self._press_and_release_key_combo(self.CAR_ACTION_COMBO)
        time.sleep(self.CAR_ENTER_LEAVE_TIMEOUT)

    def _clear_movement(self):
        for combo in [self.LEFT_COMBO, self.RIGHT_COMBO,
                      self.UP_COMBO, self.DOWN_COMBO]:
            self._key_release(combo)

    def clear_movement(self):
        self._run_function(self._clear_movement,
                           self.FUNCTIONS_DEFAULT_DURATION)

    def left(self, press):
        self._key_action(self.LEFT_COMBO, press)

    def right(self, press):
        self._key_action(self.RIGHT_COMBO, press)

    def up_tap(self):
        self.clear_movement()
        self._run_function(self._press_and_release_key_combo,
                           self.PRESS_RELEASE_TIMEOUT,
                           self.UP_COMBO)

    def down_tap(self):
        self.clear_movement()
        self._run_function(self._press_and_release_key_combo,
                           self.PRESS_RELEASE_TIMEOUT,
                           self.DOWN_COMBO)

    def right_tap(self):
        self.clear_movement()
        self._run_function(self._press_and_release_key_combo,
                           self.PRESS_RELEASE_TIMEOUT,
                           self.RIGHT_COMBO)

    def left_tap(self):
        self.clear_movement()
        self._run_function(self._press_and_release_key_combo,
                           self.PRESS_RELEASE_TIMEOUT,
                           self.LEFT_COMBO)

    def confirm_action(self):
        self._run_function(self._press_and_release_key_combo,
                           self.FUNCTIONS_DEFAULT_DURATION,
                           self.CONFIRM_COMBO)

    def _press_and_release_key_combo(self, combo):
        for action in (1, 0):
            for key in combo:
                self._dev.emit(key, action, 0)
                self._dev.syn()
            time.sleep(0.1)

    def _syn(self):
        self._dev.syn()

    def _key_action(self, combo, action):
        for key in combo:
            self._dev.emit(key, action, 0)
            self._dev.syn()

    def _key_press(self, combo):
        self._key_action(combo, 1)

    def _key_release(self, combo):
        self._key_action(combo, 0)

    def _run_function(self, function, timeout, *args):
        '''
        Runs a function if it hasn't run for less than the
        specified timeout.
        '''
        last_run = self._run_times.get(function, 0)
        current_time = time.time()
        if current_time - last_run > timeout:
            function(*args)
        self._run_times[function] = current_time

class ControllerListener(Leap.Listener):

    MIN_CIRCLE_RADIUS = 100.0
    MIN_DIR_SWIPE = 100.0
    MIN_SWIPE_SPEED = 50.0
    MIN_WHEEL_DIFF = 50.0
    MIN_JUMP_DIST = 250.0
    ENABLED_GESTURES = [Leap.Gesture.TYPE_CIRCLE,
                        Leap.Gesture.TYPE_KEY_TAP,
                        Leap.Gesture.TYPE_SWIPE]

    def __init__(self):
        Leap.Listener.__init__(self)
        self._event_manager = EventManager()
        self._last_tap_time = 0
        self._keytap_gestures = []

    def on_connect(self, controller):
        for gesture in self.ENABLED_GESTURES:
            controller.enable_gesture(gesture)

    def handle_two_hands(self, frame):
        left = frame.hands.leftmost
        right = frame.hands.rightmost

        if len(left.pointables) > 2 or len(right.pointables) > 2:
            logging.debug('break/reverse')
            self._event_manager.break_reverse()

        # Steering wheel simulation
        angle_both_hands = left.palm_normal.angle_to(right.palm_normal) * 180.0 / Leap.PI
        if angle_both_hands > 70:
            if abs(left.sphere_center.y - right.sphere_center.y) > self.MIN_WHEEL_DIFF:
                if left.sphere_center.y > right.sphere_center.y:
                    logging.debug('right')
                    self._event_manager.right(1)
                else:
                    logging.debug('left')
                    self._event_manager.left(1)
            else:
                logging.debug('steady')
                self._event_manager.left(0)
                self._event_manager.right(0)
                self._event_manager.accelerate()

    def hand_is_facing_down(self, hand):
        return abs(Leap.Vector.y_axis.angle_to(hand.palm_normal) - Leap.PI) < Leap.PI / 4

    def hand_is_facing_up(self, hand):
        return Leap.Vector.y_axis.angle_to(hand.palm_normal) < Leap.PI / 4

    def handle_one_hand(self, frame):
        left_hand = frame.hands.leftmost

        if len(frame.fingers) < 3:
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                    keytap = KeyTapGesture(gesture)
                    if 0 < len(keytap.pointables) < 3 and \
                       self.hand_is_facing_down(keytap.pointable.hand):
                        logging.debug('click')
                        self._event_manager.confirm_action()
                elif gesture.type == Leap.Gesture.TYPE_SWIPE:
                    swipe = SwipeGesture(gesture)
                    if swipe.speed > self.MIN_SWIPE_SPEED and \
                       swipe.position.distance_to(swipe.start_position) > self.MIN_DIR_SWIPE:
                        angle_y = abs(Leap.Vector.y_axis.angle_to(swipe.direction))
                        angle_x = abs(Leap.Vector.x_axis.angle_to(swipe.direction))
                        if angle_y < Leap.PI / 4:
                            logging.debug('up')
                            self._event_manager.up_tap()
                        elif angle_y > Leap.PI - Leap.PI / 4:
                            logging.debug('down')
                            self._event_manager.down_tap()
                        elif angle_x < Leap.PI / 4:
                            logging.debug('right')
                            self._event_manager.right_tap()
                        elif angle_x > Leap.PI - Leap.PI / 4:
                            logging.debug('left')
                            self._event_manager.left_tap()
                    return

        if len(frame.fingers) >= 3:
            # checks rotation of the hand
            if abs(left_hand.direction.yaw) * 180 / Leap.PI > 10:
                if left_hand.direction.yaw > 0:
                    logging.debug('right')
                    self._event_manager.right(1)
                    self._event_manager.left(0)
                else:
                    logging.debug('left')
                    self._event_manager.left(1)
                    self._event_manager.right(0)
            else:
                self._event_manager.left(0)
                self._event_manager.right(0)
                if self.hand_is_facing_down(left_hand):
                    logging.debug('forward')
                    self._event_manager.walk_forward()
                elif self.hand_is_facing_up(left_hand):
                    logging.debug('back')
                    self._event_manager.walk_back()

            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_CIRCLE:
                    gesture = CircleGesture(gesture)
                    if gesture.radius > self.MIN_CIRCLE_RADIUS:
                        logging.debug('car enter/leave')
                        self._event_manager.car_enter_leave()
                elif gesture.type == Leap.Gesture.TYPE_SWIPE:
                    swipe = SwipeGesture(gesture)
                    if swipe.speed > 50 and \
                       swipe.position.distance_to(swipe.start_position) > self.MIN_JUMP_DIST and \
                       Leap.Vector.y_axis.angle_to(swipe.direction) < Leap.PI / 4 and \
                       self.hand_is_facing_down(swipe.pointable.hand):
                        logging.debug('jump')
                        self._event_manager.jump()
                elif gesture.type == Leap.Gesture.TYPE_KEY_TAP:
                    current_time = time.time()
                    if current_time - self._last_tap_time > 3:
                        self._keytap_gestures = []
                    keytap = KeyTapGesture(gesture)
                    if len(self._keytap_gestures) > 2:
                        self._keytap_gestures = []
                        logging.debug('run')
                        self._event_manager.run()
                    elif self._keytap_gestures:
                        tapping_hand = keytap.pointable.hand
                        if self.hand_is_facing_down(tapping_hand):
                            self._keytap_gestures.append(keytap)
                            self._last_tap_time = current_time
                    else:
                        self._keytap_gestures.append(keytap)
                        self._last_tap_time = current_time

    def on_frame(self, controller):
        frame = controller.frame()

        if frame.hands.is_empty:
            self._event_manager.clean_permanent_actions()
            return

        num_hands = len(frame.hands)
        if num_hands > 1:
            self.handle_two_hands(frame)
        elif num_hands == 1:
            self.handle_one_hand(frame)

def main():
    listener = ControllerListener()
    controller = Leap.Controller()

    controller.add_listener(listener)
    sys.stdin.readline()
    controller.remove_listener(listener)

if __name__ == "__main__":
    main()
