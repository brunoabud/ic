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

        if record.levelno != logging.INFO:
            fmt  = D+"@ %(name)s at %(pathname)s[%(lineno)i]" + " @@ " + B+C1+"%(message)s"+D+B_
        else:
            fmt  = D+"@ %(name)s" + " @@ " + B+C1+"%(message)s"+D+B_
        # Format exceptions if there is any
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text is not None:
            fmt = C1 +B+"\n%(levelname)8s"+B_ + " @ Exception"+  "\n%(exc_text)s\n" + "         " + fmt
        else:
            fmt = C1+B+"\n%(levelname)8s "+D+B_ + fmt
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
        exc_type, value, tb = exc_inf

        fmt = B+"             type : "+B_ + exc_type.__module__ + "." + exc_type.__name__  + "\n"
        fmt = fmt + B+"             value: "+B_ + str(value) + "\n"
        fmt = fmt + "         @ Traceback\n"
        # Extract tracebacks
        tb_list = traceback.extract_tb(tb)

        for entry in tb_list:
            f, line, f_name, text = entry
            if f_name is not None:
                f_name = f_name + " in"
            entry_text = B+"             %(f_name)s %(f)s[%(line)i]"+B_ + "\n                %(text)s\n"
            fmt = fmt + entry_text % locals()

        return fmt
