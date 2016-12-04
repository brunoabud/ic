#coding: utf-8
import traceback

import cv2

class ICAdaptiveThreshold(object):
    def __init__(self, plugin_path):
        self.plugin_path = plugin_path
        self.parameters = {
            "max_value"  : (0, 255, 255, "Max Pixel Value"),
            "kernel_size": (1, 31, 3, "Kernel size"),
            "threshold_c": (0, 10, 2, "Threshold Constant")}

        self.v                = {}
        self.v["max_value"]   = 255
        self.v["kernel_size"] = 3
        self.v["threshold_c"] = 2

    def parameter_change(self, param_name, value):
        if param_name == "kernel_size":
            self.v["kernel_size"] = value | 1
            return self.v["kernel_size"]
        else:
            self.v[param_name] = value
            return value

    def apply_filter(self, frame):
        frame.data = cv2.adaptiveThreshold(frame.data, self.v["max_value"],
    		              cv2.ADAPTIVE_THRESH_MEAN_C,
                          cv2.THRESH_BINARY_INV,  self.v["kernel_size"],
                         self.v["threshold_c"])
        return frame

    def release(self):
        pass

def main(plugin_path):
    return ICAdaptiveThreshold(plugin_path)
