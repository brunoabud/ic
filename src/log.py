import time as tm
import traceback

log_file = None
tics = {}
output = set()


def tic(label):
    tics[label] = tm.clock()


def tac(label, retic = False):
    if label not in tics.keys(): raise KeyError("No tic for label '{}'".format(label))
    elapsed = tm.clock() - tics[label]
    if retic: tics[label] = tm.clock()
    return elapsed


def add_output(out):
    global output
    output.add(out)


def remove_output(out):
    output.discard(out)


def dump_traceback():
    e = traceback.format_exc()
    write(e, 'traceback')


def write(text, tag=''):
    global output
    tag = tag.strip()
    ftm = tm.strftime("%H:%M:%S", tm.localtime())
    prefix = "[{}] ".format(tag) if tag != "" else ""
    for o in output:
        try:
            o.write("{}{}::{}\n".format(prefix, ftm, str(text).replace("\n", "\\n")))
        except Exception as e:
            pass
