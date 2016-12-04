#coding: utf-8
import traceback

import cv2

class ICBlurFilter(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters = {"kernel_size": (1, 15, 3, "Kernel size")}

        self.kernel_size = 3

    def parameter_change(self, param_name, value):
        if param_name == "kernel_size":
            self.kernel_size = value | 1
            return self.kernel_size
        else:
            return None

    def apply_filter(self, frame):
        frame.data = cv2.blur(frame.data, (self.kernel_size,)*2)
        return frame

    def release(self):
        pass

def main(plugin_path):
    return ICBlurFilter(plugin_path)
