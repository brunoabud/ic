from enum import Enum
import messages
import log


class LengthHint(Enum):
    Fixed   = 1
    Growing = 2


class FPSHint(Enum):
    Fixed   = 1
    Dynamic = 2


class CursorPosition(Enum):
    Begin = 1
    End   = 2
    EOF   = 3


class MediaState(object):
    def __init__(self, media = None):
        self._is_open  = media and media._is_open
        self._pos      = media and media._pos
        self._length   = media and media._length
        self._fps      = media and media._fps
        self._size     = media and media._size
        self._seekable = media and media._seekable

    def clone(self):
        return MediaState(self)

    def copy(self, media):
        self._is_open  = media and media._opened
        self._pos      = media and media._pos
        self._length   = media and media._length
        self._fps      = media and media._fps
        self._size     = media and media._size
        self._seekable = media and media._seekable

    def __eq__(self, other):
        return True if (self._is_open  == other._is_open and
                        self._pos      == other._pos     and
                        self._length   == other._length  and
                        self._fps      == other._fps     and
                        self._size     == other._size    and
                        self._seekable == other._seekable)   else False


    def __ne__(self, other):
        return not self.__eq__(other)

    def _check(self):
        if not self._is_open:
            raise MediaClosedError()

    def is_open(self):
        return self._is_open

    def get_pos(self):
        self._check()
        return self._pos

    def get_length(self):
        self._check()
        return self._length

    def get_fps(self):
        self._check()
        return self._fps

    def get_size(self):
        self._check()
        return self._size

    def get_seekable(self):
        self._check()
        return self._seekable

    is_open  = property(fget = is_open)
    fps      = property(fget = get_fps)
    length   = property(fget = get_length)
    size     = property(fget = get_size)
    pos      = property(fget = get_pos)
    seekable = property(fget = get_seekable)


class NotSeekableError(Exception):
    pass


class MediaClosedError(Exception):
    pass


class FrameError (Exception):
    pass


class ICMedia(object):
    def __init__(self):
        self._state     = MediaState()
        self._lhint     = None               #One of the LengthHint enum value.
        self._fhint     = None               #One of the FPSHint enum value.
        self._next      = None               #Reference to the VIMO's 'next' method
        self._seek      = None               #Reference to the VIMO's 'seek' method
        self.loop       = False

    def get_state(self):
        return self._state

    def get_length_hint(self):
        self._state._check()
        return self._lhint

    def get_fps_hint(self):
        self._state._check()
        return self._fhint

    lhint    = property(fget = get_length_hint)
    fhint    = property(fget = get_fps_hint)
    state    = property(fget = get_state)

    def notify_state_change(self, old_state, new_state):
        if old_state != new_state:
            messages.post_message('media_state_changed', {'old': old_state, 'new': new_state}, self)

    def next(self):
        self._state._check()
        try:
            old_state = self._state.clone()
            frame     = self._next()
            new_state = self._state.clone()
            self.notify_state_change(old_state, new_state)
            return (old_state, frame)
        except EOFError:
            raise
        except:
            Log.dumptraceback()
            self._close()


    def seek(self, pos):
        self._state._check()
        if not self._state._seekable:
            raise NotSeekableError()
        try:
            pos = 0                if pos is CursorPosition.Begin else pos
            pos = self._length - 1 if pos is CursorPosition.End   else pos

            old_state = self._state.clone()
            ret       = self._seek(pos)
            new_state = self._state.clone()

            if ret:
                self.notify_state_change(old_state, new_state)
                messages.post_message("media_seeked", {'pos': pos}, self)
            return ret
        except IndexError:
            raise
        except:
            log.dump_traceback()
            self._close()

    def _open(self, size, length, pos, fps, seekable, l_hint, f_hint, next_func, seek_func):
        self._close()
        self._state._length   = length
        self._state._pos      = pos
        self._state._size     = size
        self._state._fps      = fps
        self._state._seekable = seekable
        self._state._is_open  = True
        self._lhint           = l_hint
        self._fhint           = f_hint
        self._next            = next_func
        self._seek            = seek_func

        messages.post_message('media_opened', None, self)
        return True

    def _set_fps(self, fps):
        self._state._fps = fps

    def _set_length(self, length):
        self._state._length = length

    def _set_pos(self, pos):
        self._state._pos = pos

    def _set_size(self, size):
        self._state._size = size

    def _get_fps(self):
        return self._state._fps

    def _get_length(self):
        return self._state._length

    def _get_pos(self):
        return self._state._pos

    def _get_size(self):
        return self._state._size

    def _close(self):
        if self._state._is_open:
            self._state     = MediaState()
            self._lhint     = None               #One of the LengthHint enum value.
            self._fhint     = None               #One of the FPSHint enum value.
            self._next      = None               #Reference to the VIMO's 'next' method
            self._seek      = None               #Reference to the VIMO's 'seek' method
            messages.post_message('media_closed', None, self)
        return True


class proxy_property(object):
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget()

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel()


def create_VIM_proxy(media):
    fps    = proxy_property(media._get_fps, media._set_fps)
    length = proxy_property(media._get_length, media._set_length)
    pos    = proxy_property(media._get_pos, media._set_pos)
    size   = proxy_property(media._get_size, media._set_size)

    d      = {'fps' : fps, 'length' : length, 'pos' : pos, 'size' : size, 'open' : media._open,
    'close' : media._close}
    proxy  = type("ICMedia_Proxy", (), d)
    return proxy()
