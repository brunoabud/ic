#coding: utf-8
import traceback

import cv2

class ICDilateFilter(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters = {
            "kernel_size" : (3, 99, 3, "Kernel size"),
            "kernel_steps": (3, 99, 4, "Dilatation Steps")
        }
        self.v            = {}
        self.v["kernel_size"]  = 3
        self.v["kernel_steps"] = 4

    def parameter_change(self, param_name, value):
        if param_name == "kernel_size":
            self.v["kernel_size"] = value | 1
            return self.v["kernel_size"]
        else:
            return value

    def apply_filter(self, frame):
        kernel     = np.ones((self.v["kernel_size"],)*2, np.uint8)
        frame.data = cv2.dilate(frame.data, kernel, iterations=self.v["kernel_steps"])
        return frame

    def release(self):
        pass

def main(plugin_path):
    return ICDilateFilter(plugin_path)
