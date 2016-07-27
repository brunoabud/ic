#coding: utf-8
"""This module contains the ICAnalysis class and the PreviewOption enum.

"""
__all__     = ["PreviewOption", "ICAnalysis"]
__author__  = "Bruno Abude Cardoso"
__version__ = "0.4.0"

import os

from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QTimer
from enum import Enum

import filter_rack
import plugin
import log
import media
import messages
import main


class PreviewOption(Enum):
    """Enum that holds the preview source options."""
    #No preview is defined
    NoPreview = 1
    #Right after the VIMO has read the video
    Raw = 2
    #Right after all the filters were applied
    PostFiltering = 3
    #Right after the VideoAnalysisModule has processed the video
    PostProcessing = 4


class ICAnalysis(object):
    """Class that holds loaded plugins and the media object.

    The ICAnalysis class holds the FilterRack, currently loaded VideoInput Plugin instance,
    currently loaded VideoAnalysis Plugin instance, ICMedia instance and the preview source option.
    """
    def __init__(self):
        super(ICAnalysis, self).__init__()
        self._filter_rack  = filter_rack.ICFilterRack()
        self._VIMO         = None
        self._VAMO         = None
        self._preview      = PreviewOption.Raw
        self._media        = media.ICMedia()
        messages.add_message_listener(self)

    def getpreview(self):    return self._preview
    def getvimo(self):       return self._VIMO
    def getvamo(self):       return self._VAMO
    def getfilter_rack(self): return self._filter_rack
    def getmedia(self):      return self._media
    def getpreview(self):    return self._preview

    def setpreview(self, preview):
        if not isinstance(preview, PreviewOption):
            raise TypeError("Not an PreviewOption enum")
        self._preview = preview
        messages.post_message('preview_source_changed', self.preview, self)

    def empty(self):
        """Clear all objects of the analysis."""
        self._filter_rack.release()
        self.close_VIMO()
        self.close_VAMO()
        self._media._close()
        self.preview = PreviewOption.Raw
        messages.post_message('analysis_emptied', None, self)

    def release(self):
        """Release all objects of the analysis."""
        if self._filter_rack   is not None: self._filter_rack.release()
        if self._VIMO         is not None: self.close_VIMO()
        if self._VAMO         is not None: self.close_VAMO()
        if self._media        is not None: self._media._close()
        self.preview = PreviewOption.Raw
        messages.post_message('analysis_released', None, self)

    def receive_message(self, message_type, message_data, sender):
        """Handle a message.

        This function is not supposed to be called directly. The messaging system will be
        responsible for calling it when a message is posted.

        Messages Handled
        ----------------
        media_opened
        media_closed

        """
        if message_type == "media_opened":
            if self._VAMO:
                try:
                    self._VAMO.on_media_opened(self._media._state.clone(), self._media._lhint, self._media._fhint)
                except:
                    log.dump_traceback()
                    self.close_VAMO()
        elif message_type == "media_closed":
            if self._VAMO:
                try:
                    self._VAMO.on_media_closed(self._media._state.clone())
                except:
                    log.dump_traceback()
                    self.close_VAMO()
        elif message_type == "media_sought":
            if self._VAMO:
                try:
                    self._VAMO.on_media_sought(self._media._state.clone())
                except:
                    log.dump_traceback()
                    self.close_VAMO()

    def open_VIMO(self, gui_proxy, plugin_name):
        """Open a new Video Input Model Object plugin.

        Parameters
        ----------
        gui_proxy : GUI_Interface
        """
        if self._VIMO:
            self.close_VIMO()
        try:
            video_dir   = main.settings['video_dir']
            media_proxy = media.create_VIM_proxy(self._media)
            p           = plugin.load_plugin(video_dir, plugin_name)
            if not p.init_plugin(gui_proxy = gui_proxy, media_proxy = media_proxy):
                p.release()
                gui_proxy.release()
                return False
            else:
                self._VIMO    = p
                self._VIMOgui = gui_proxy
                messages.post_message('input_plugin_loaded', {'plugin_name' : plugin_name}, self)
                return True
        except:
            gui_proxy.release()
            log.dump_traceback()
            return False

    def close_VIMO(self):
        """Close and release the Video Input Model Object plugin"""
        if self._VIMO is not None:
            try:
                self._VIMO.release()
            except:
                log.dump_traceback()
            finally:
                self._VIMOgui.release()
                self._VIMO    = None
                self._VIMOgui = None
                messages.post_message('input_plugin_closed', None, self)

    def open_VAMO(self, gui_proxy, plugin_name):
        """Open a new Video Analysis Model Object Plugin."""
        self.close_VAMO()
        try:
            analysis_dir = main.settings['analysis_dir']
            p            = plugin.load_plugin(analysis_dir, plugin_name)
            if not p.init_plugin(gui_proxy = gui_proxy):
                p.release()
                gui_proxy.release()
                return False
            else:
                self._VAMO  = p
                self._VAMOgui = gui_proxy
                if self._media._state.is_open:
                    self._VAMO.on_media_opened(self._media.state.clone(), self._media.lhint, self._media.fhint)
                messages.post_message('analysis_plugin_loaded', {'plugin_name' : plugin_name}, self)
                return True
        except:
            gui_proxy.release()
            log.dump_traceback()
            return False

    def close_VAMO(self):
        """Close and release the current opened Video Analysis Model Object Plugin"""

        if self._VAMO is not None:
            try:
                self._VAMO.release()
            except:
                log.dump_traceback()
            finally:
                self._VAMOgui.release()
                self._VAMO = None
                self._VAMOgui = None
                messages.post_message('analysis_plugin_closed', None, self)

    filter_rack   = property(getfilter_rack,    None)
    VIMO         = property(getvimo,          None)
    VAMO         = property(getvamo,          None)
    preview      = property(getpreview, setpreview)
    media        = property(getmedia,         None)
