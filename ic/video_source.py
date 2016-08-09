import traceback
import types

from gui.application import get_app, Application
from gui.gui_interface import GUI_Interface

def get_vs():
    """Return the singleston instance of the VideoSource class."""
    return VideoSource._INSTANCE

# Raised when attempting to access a closed Video Source
class SourceClosedError(object):
    pass

# Exception raised when a plugin could not be initialized
class PluginInitError(Exception):
    pass


# Class that exposes the _open and _close methods of the VideoSource instance.
# The input plugins will receive this bridge to signal that a video source is
# available or not
class InputBridge(object):
    def __init__(self, VS):
        self.VS = VS

    def open(self, *args, **kwargs):
        self.VS._open(*args, **kwargs)

    def close(self, *args, **kwargs):
        self.VS._close(*args, **kwargs)

class VideoSource(object):
    """Class responsible for communicating with the VideoInput.

    This class exposes methods to the VideoInput plugin to communicate when
    video sources are avaible. It is also responsible for signaling to the main
    application when a video source is or is not available.

    A Bridge to some of the Video Input Plugin methods is provided. It makes
    possible to call functions like `seek`, `tell`, `get_fps`, etc.

    :singleton
    """
    _INSTANCE = None

    def __init__(self):
        assert VideoSource._INSTANCE is None
        VideoSource._INSTANCE = self

        #Is the video source open?
        self._source_open = False

        #List of bridged methods (Since they have the same behaviour, they will
        #be dynamically generated when the bridge is initialized)
        self._bridge_methods = ["seek", "tell", "get_length", "get_fps",
            "get_size", "next"]

        #Create the bridge object that will be provided to the VideoInput
        self._input_bridge = InputBridge(self)

        #The current bridge plugin instance
        self._plugin_instance = None

        self.mid = get_app().register_message_listener(self)

    #The method that should be called by the Video Input Plugin to make a Video
    #Source avaible to the application. The Video Input Plugin will have access
    #to it by a bridge object, that will be provided to it when the init_plugin
    #method of the plugin is called.
    #This will be done by the Application object when the plugin is loaded
    #The bridge used can be obtained by calling VideoSource.get_input_bridge
    def _open(self, *args, **kwargs):
        self._source_open = True
        get_app().post_message("video_source_opened", {}, self.mid)
        return True

    #The method that should be called by the Video Input Plugin to make the VS
    #unavailable
    def _close(self, *args, **kwargs):
        if self._source_open:
            self._source_open = False
            get_app().post_message("video_source_closed", {}, self.mid)
            return True
    #Return the bridge object that exposes the _open and _close methods of the
    #VS instance
    def get_input_bridge(self):
        return self._input_bridge

    #This is the main method of the class. When a new Video Input Plugin is ini-
    #tialized, this function should be called. It will be responsible for:
    # - Creating the bridge methods
    # - Starting the state handling for the video input plugin
    #When the Plugin is unloaded, the method `close_bridge` should be called
    def init_bridge(self, plugin_instance):
        #Generate the bridge methods
        for m in self._bridge_methods:
            #Check if the plugin instance has the method
            if not hasattr(plugin_instance,  m):
                raise NameError("The plugin does not have a '{}' method".format(m))

            #Create a method that checks if the video source is open before
            #calling the bridge method. This is a bound method so the "self"
            #argument needs to be here.
            def create_method(name):
                def method(*args, **kwargs):
                    if not self._source_open:
                        raise SourceClosedError()
                    return getattr(plugin_instance, name).__call__(*args, **kwargs)
                return method

            #Add the bridged method to this object
            setattr(self, m, create_method(m))

        #Reset the states
        self._source_open = False
        #Set the current plugin instance
        self._plugin_instance = plugin_instance

    #Reset all the states and remove the generated bridge methods
    def close_bridge(self):
        #Remove the bridge methods
        for m in self._bridge_methods:
            if hasattr(self, m):
                delattr(self, m)

        #Reset the states
        self._source_open = False
        #Tell the plugin to close the video source
        self._plugin_instance.close_source()
        self._plugin_instance = None

    def receive_message(self, mtype, mdata, sender):
        pass

    def is_open(self):
        return self._source_open

    def set_video_input(self, plugin_id):
        """Sets the current Video Input Plugin.

        This methods close any previously loaded Plugin and initialize the new
        one. It does not load or unload the plugins, just init and close them.

        """
        app = get_app()
        #Check if the plugin_id is valid
        new_plugin = app.get_plugin(plugin_id)
        if not new_plugin.plugin_type == Application.PLUGIN_TYPE_VIDEO_INPUT:
            raise TypeError("Wrong Plugin Type {}".format(new_plugin.plugin_type))

        if app.video_input_info:
            current_id = app.video_input_info["plugin_id"]
            current_plugin = app.get_plugin(current_id)

            #Call the plugin close method
            try:
                current_plugin.instance.close_plugin()
            except:
                traceback.print_exc()
            #Release the gui interface
            try:
                current_plugin.gui_interface.release()
                current_plugin.gui_interface = None
            except:
                traceback.print_exc()
            #Clean the input plugin info
            del app.video_input_info
            #Close the VideoSource bridge
            self.close_bridge()
            #Post the message signaling that the video input was closed
            app.post_message("video_input_closed", {"plugin_id": current_id}, -1)

        #Get a input bridge to the video source object
        video_source_bridge = self.get_input_bridge()
        #Object that provides gui access to the plugin
        interface = GUI_Interface(plugin_id)
        #Init the plugin
        try:
            ret = new_plugin.instance.init_plugin(gui_interface=interface, video_source_bridge=video_source_bridge)
            if ret:
                #Init the VideoSource bridge
                self.init_bridge(new_plugin.instance)
                new_plugin.gui_interface = interface
                app.video_input_info =  {"plugin_id": plugin_id}
                app.post_message("video_input_changed", {"plugin_id": plugin_id}, -1)
            else:
                interface.release()
                raise PluginInitError("init_plugin returned False")
        except:
            print "_-----------------------------------------------------------"
            traceback.print_exc()
            print "------------------------------------------------------------"
            raise PluginInitError("Plugin init. raised exception")
            interface.release()
            self.close_bridge()
