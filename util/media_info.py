import os
import sys
from xml.dom import Node, minidom

# Check for ffmpy library
try:
    import ffmpy
    # Check for ffprobe binary
    probe = ffmpy.FFprobe(global_options="-version")
    probe.run()
except ImportError:
    print "Library ffmpy not installed."
    sys.exit(-1)

except ffmpy.FFExecutableNotFoundError:
    print "ffprobe binary must be installed."
    sys.exit(-1)


def get_info(path):
    # Check if the file exists
    if not os.path.isfile(path):
        raise OSError("file {} not found".format(path))
    # Execute the ffprobe and get the xml data
    probe = ffmpy.FFprobe(inputs={path:"-print_format xml -show_streams -select_streams v:0"})
    xml_data = probe.run()
    # Parse from string
    doc = minidom.parseString(xml_data)
    # Collect the stream node
    stream_element = doc.getElementsByTagName("stream")[0]

    attr = stream_element.attributes
    info = {}

    # Collect all attributes from the stream node
    for i in range(0, attr.length):
        a = attr.item(i)
        try:
            # Convert from unicode if possible
            name = str(a.localName)
            value = str(a.value)
            # If it has a / convert to float
            if "/" in value:
                a, b = value.split("/")
                value = float(a) / float(b)
            # Check if it contains only numbers (integer)
            elif all(map(lambda c: c in "1234567890", value)):
                value = int(value)
            info[name] = value
        except:
            # Ignore attribute
            pass

    return info
