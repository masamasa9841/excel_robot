#! /usr/bin/env python
# -*- coding: utf-8 -*-
#参考
#http://net.univ-q.com/archives/38

import tweepy
import datetime
import time
import sys
import math
import signal
import time
import rospy
from raspimouse_ros.srv import *
from raspimouse_ros.msg import *
from std_msgs.msg import UInt16

AT = ""
AS = ""
CK = ""
CS = ""


class Listener(tweepy.StreamListener):
    
    def on_status(self, status):
        #status.created_at += datetime.timedelta(hours=9)

        # リプライが来たら行動
        if str(status.in_reply_to_screen_name) == "cit_okawa_excel":
            text = status.text.replace("@cit_okawa_excel", "")
            text = text.split("#")
            text = text[0].replace(" ", "")
            print text
            lh = left_hand()
            lh.test(text)
        return True

    def on_error(self, status):
        print('Got an error with status code: ' + str(status))
        return False

    def on_timeout(self):
        print('Timeout...')
        return True

class left_hand(object):
    def __init__(self):
        rospy.init_node('left_hand')
        signal.signal(signal.SIGINT, self.handler)
        subls = rospy.Subscriber('/lightsensors', LightSensorValues, self.lightsensor_callback)
        subsw = rospy.Subscriber('/switches', Switches, self.switch_callback)
        self.sensor = [0, 0, 0, 0]
        self.switch = [0, 0, 0]
        time.sleep(1)

    def handler(self, signal, frame):
        if not self.switch_motors(False): 
            print "[check failed]: motors are not turned off"
        sys.exit(0)

    def switch_motors(self, onoff):
        rospy.wait_for_service('/switch_motors')
        try:
            p = rospy.ServiceProxy('/switch_motors', SwitchMotors)
            res = p(onoff)
            return res.accepted
        except rospy.ServiceException, e:
            print "Service call failed: %s"%e
        else:
            return False
    
    def lightsensor_callback(self, msg):
        self.left_side = msg.left_side
        self.right_side = msg.right_side
        if msg.right_forward > 700: self.sensor[2] = True
        else : self.sensor[2] = False
        if msg.right_side > 550: self.sensor[3] = True
        else : self.sensor[3] = False
        if msg.left_forward > 700: self.sensor[1] = True
        else : self.sensor[1] = False
        if msg.left_side > 550: self.sensor[0] = True
        else : self.sensor[0] = False

    def switch_callback(self, msg): 
        self.switch[0] = msg.front
        self.switch[1] = msg.center
        self.switch[2] = msg.rear
        #print self.switch

    def oneframe(self, left, right, p, dis):
        if left or right:
            dis = dis + 1
        t = ( 400 * dis ) / ( 2 * math.pi * 2.4 * p) 
        now = rospy.get_time()
        after = 0
        E = 0
        while not after - now >= t and not rospy.is_shutdown():
            after = rospy.get_time()
            if left and right:
                E = 0.2 * (self.left_side - self.right_side)
            elif left and not right:
                E = 0.35 * (self.left_side - 920)
            elif not left and right:
                E = -0.35 * (self.right_side - 920)
            else: pass
            self.raw_control(p+E,p-E)
            rospy.Rate(100)
            left , right = self.sensor[0], self.sensor[3]

    def turn(self,p, deg, rorl, rl=0):
        self.raw_control(0,0)
        rospy.sleep(0.15)
        t = (deg * 400 * 4.8) / (360 * 2.4 * p)
        if(0 > rorl):
            self.raw_control(p,-p)
            rospy.sleep(t)
        else:
            self.raw_control(-p,p)
            rospy.sleep(t)
        self.raw_control(0,0)
        rospy.sleep(0.15)

    def raw_control(self, left_hz, right_hz):
        pub = rospy.Publisher('/motor_raw', MotorFreqs, queue_size = 10)
        if not rospy.is_shutdown():
            d = MotorFreqs()
            d.left = left_hz
            d.right = right_hz
            pub.publish(d)

    def test(self, target):
        if not self.switch_motors(True):
            print "[check failed]: motors are not empowered"
        left, right = self.sensor[0], self.sensor[3]
        if (target == "forward"): self.oneframe(left, right, 500, 18.1)
        if (target == "right"): self.turn(500, 90, -1)
        if (target == "left"): self.turn(500, 90, 1)
        if (target == "back"): self.oneframe(left, right, -500, 18.1)
        self.raw_control(0,0)

    def main(self):
        if not self.switch_motors(True):
            print "[check failed]: motors are not empowered"
        while not rospy.is_shutdown():
            left, right = self.sensor[0], self.sensor[3]
            self.oneframe(left, right, 500, 18.1)
            front = self.sensor[1]
            if not left:
                self.turn(500, 90, 1)
            elif left and not front:
                pass
            elif left and right and front:
                self.turn(500, 180, 1)
            elif left and front:
                self.turn(500, 90, -1)

auth = tweepy.OAuthHandler(CK, CS)
auth.set_access_token(AT, AS)
api = tweepy.API(auth)

listener = Listener()
stream = tweepy.Stream(auth, listener)
stream.userstream()
