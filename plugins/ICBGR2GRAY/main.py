#coding: utf-8
import traceback

import cv2

class ICBGR2GRAY(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters = {}

    def parameter_change(self, param_name, value):
        return None

    def apply_filter(self, frame):
        frame.data = cv2.cvtColor(frame.data, cv2.COLOR_BGR2GRAY)
        frame.color_space = "GRAY"
        return frame

    def release(self):
        pass

def main(plugin_path):
    return ICBGR2GRAY(plugin_path)
