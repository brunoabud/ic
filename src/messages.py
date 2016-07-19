from Queue import Queue

from PyQt4.QtCore import QTimer


messages  = None
listeners = None
timer     = None


def init_message_system():
    global messages, listeners, timer
    messages  = Queue()
    listeners = set()
    timer     = QTimer()

    timer.timeout.connect(dispatch_messages)
    timer.start()


def add_message_listener(listener):
    global listeners
    listeners.add(listener)


def remove_message_listener(listener):
    global listeners
    listeners.discard(listener)


def post_message(message_type, message_data, sender):
    global messages
    messages.put((message_type, message_data, sender))


def dispatch_messages():
    global messages, listeners
    while not messages.empty():
        message_type, message_data, sender = messages.get(False)
        for l in [listener for listener in listeners]:
            try:
                if sender is not l:
                    l.receive_message(message_type, message_data, sender)
            except:
                listeners.discard(l)
