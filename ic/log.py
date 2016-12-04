import logging
import traceback

class NameFilter(object):
    """Filter out a logger name that is child of a given name.

    """
    def __init__(self, parent):
        self.parent = parent

    def filter(self, record):
        if record.name.startswith(self.parent):
            return 0
        else:
            return 1

class ANSIFormatter(logging.Formatter):
    """Format messages using ANSI escape codes.
    """
    COLORS = {
        "COLOR_EXCEPTION1" : "\033[31m",    # Red
        "COLOR_EXCEPTION2" : "\033[91m",    # Light Red
        "COLOR_INFO1"      : "\033[39m",    # Default
        "COLOR_INFO2"      : "\033[39m",    # Default
        "COLOR_WARNING1"   : "\033[33m",    # Yellow
        "COLOR_WARNING2"   : "\033[93m",    # Light Yellow
        "COLOR_DEBUG1"     : "\033[34m",    # Blue
        "COLOR_DEBUG2"     : "\033[94m",    # Light Blue
        "COLOR_DEFAULT"    : "\033[39m",    # Default color
        "BOLD"             : "\033[1m" ,
        "BOLD_RESET"       : "\033[21m",
    }
    COLOR_TAGS = {
        logging.INFO: "COLOR_INFO",
        logging.DEBUG: "COLOR_DEBUG",
        logging.ERROR: "COLOR_EXCEPTION",
        logging.CRITICAL: "COLOR_EXCEPTION",
        logging.WARNING: "COLOR_WARNING"
    }

    def __init__(self):
        super(ANSIFormatter, self).__init__()

    def format(self, record):
        C1 = self.COLORS[self.COLOR_TAGS[record.levelno]+"1"]
        C2 = self.COLORS[self.COLOR_TAGS[record.levelno]+"2"]
        B  = self.COLORS["BOLD"]
        B_ = self.COLORS["BOLD_RESET"]
        D  = self.COLORS["COLOR_DEFAULT"]

        self.C1 = C1
        self.C2 = C2

        name = D+B_+"%(name)s"
        path = D+B_+"%(pathname)s, line %(lineno)i"
        levelname = C1+B+"%(levelname)s"
        message   = C1+B+"%(message)s"

        if record.levelno == logging.DEBUG:
            fmt  = "from " + path + "\n"
            fmt  = fmt + name + D+B_+ "[" + levelname + D+B_+ "]" + D+B_+": " + message + B_+D
        else:
            fmt  = name + D+B_+ "[" + levelname + D+B_+ "]" + D+B_+": " + message + B_+D

        # Format exceptions if there is any
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text is not None:
            fmt = fmt + "\n\n" + record.exc_text
        else:
            fmt = fmt + "\n"

        # Computate message attribute
        record.message = record.getMessage()
        # Format time if needed
        if "(asctime)" in fmt:
            t = self.formatTime(record, self.datefmt)
            fmt = fmt % t

        # Format using record attributes
        return fmt % vars(record)

    def formatException(self, exc_inf):
        B  = self.COLORS["BOLD"]
        B_ = self.COLORS["BOLD_RESET"]
        C1 = self.C1
        C2 = self.C2
        D = self.COLORS["COLOR_DEFAULT"]
        exc_type, value, tb = exc_inf

        e_module = str(exc_type.__module__)
        e_module = e_module + "." if e_module != "" else ""

        e_type = B+C1+ e_module + str(exc_type.__name__)
        e_message = C1+B_+ str(value)
        fmt = "    " + e_type + D+B_+ ": " + e_message + D+B_+"\n" + D+B_
        fmt = fmt + B+"    Traceback (most recent calls last):\n"

        identation = "        "
        # Extract tracebacks
        tb_list = traceback.extract_tb(tb)

        for entry in tb_list:
            f, line, f_name, text = entry
            if f_name is not None:
                f_name = f_name + " in"
            entry_text = identation + C1+B+"%(f_name)s %(f)s[%(line)i]" + "\n"
            entry_text = entry_text +  identation + C1+B_ + "  %(text)s\n"
            fmt = fmt + entry_text % locals() + D+B_

        return fmt

class ColorlessFormatter(logging.Formatter):
    """Format messages without colors.

    """
    COLORS = {
        "COLOR_EXCEPTION1" : "",    # Red
        "COLOR_EXCEPTION2" : "",    # Light Red
        "COLOR_INFO1"      : "",    # Default
        "COLOR_INFO2"      : "",    # Default
        "COLOR_WARNING1"   : "",    # Yellow
        "COLOR_WARNING2"   : "",    # Light Yellow
        "COLOR_DEBUG1"     : "",    # Blue
        "COLOR_DEBUG2"     : "",    # Light Blue
        "COLOR_DEFAULT"    : "",    # Default color
        "BOLD"             : "" ,
        "BOLD_RESET"       : "",
    }
    COLOR_TAGS = {
        logging.INFO: "COLOR_INFO",
        logging.DEBUG: "COLOR_DEBUG",
        logging.ERROR: "COLOR_EXCEPTION",
        logging.CRITICAL: "COLOR_EXCEPTION",
        logging.WARNING: "COLOR_WARNING"
    }

    def __init__(self):
        super(ColorlessFormatter, self).__init__()

    def format(self, record):
        C1 = self.COLORS[self.COLOR_TAGS[record.levelno]+"1"]
        C2 = self.COLORS[self.COLOR_TAGS[record.levelno]+"2"]
        B  = self.COLORS["BOLD"]
        B_ = self.COLORS["BOLD_RESET"]
        D  = self.COLORS["COLOR_DEFAULT"]

        self.C1 = C1
        self.C2 = C2

        name = D+B_+"%(name)s"
        path = D+B_+"%(pathname)s, line %(lineno)i"
        levelname = C1+B+"%(levelname)s"
        message   = C1+B+"%(message)s"

        if record.levelno == logging.DEBUG:
            fmt  = "from " + path + "\n"
            fmt  = fmt + name + D+B_+ "[" + levelname + D+B_+ "]" + D+B_+": " + message + B_+D
        else:
            fmt  = name + D+B_+ "[" + levelname + D+B_+ "]" + D+B_+": " + message + B_+D

        # Format exceptions if there is any
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text is not None:
            fmt = fmt + "\n\n" + record.exc_text
        else:
            fmt = fmt + "\n"

        # Computate message attribute
        record.message = record.getMessage()
        # Format time if needed
        if "(asctime)" in fmt:
            t = self.formatTime(record, self.datefmt)
            fmt = fmt % t

        # Format using record attributes
        return fmt % vars(record)

    def formatException(self, exc_inf):
        B  = self.COLORS["BOLD"]
        B_ = self.COLORS["BOLD_RESET"]
        C1 = self.C1
        C2 = self.C2
        D = self.COLORS["COLOR_DEFAULT"]
        exc_type, value, tb = exc_inf

        e_module = str(exc_type.__module__)
        e_module = e_module + "." if e_module != "" else ""

        e_type = B+C1+ e_module + str(exc_type.__name__)
        e_message = C1+B_+ str(value)
        fmt = "    " + e_type + D+B_+ ": " + e_message + D+B_+"\n" + D+B_
        fmt = fmt + B+"    Traceback (most recent calls last):\n"

        identation = "        "
        # Extract tracebacks
        tb_list = traceback.extract_tb(tb)

        for entry in tb_list:
            f, line, f_name, text = entry
            if f_name is not None:
                f_name = f_name + " in"
            entry_text = identation + C1+B+"%(f_name)s %(f)s[%(line)i]" + "\n"
            entry_text = entry_text +  identation + C1+B_ + "  %(text)s\n"
            fmt = fmt + entry_text % locals() + D+B_

        return fmt
