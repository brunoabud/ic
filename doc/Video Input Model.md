# <center>Video Input</center>

This page covers the methods, exceptions and members that must be implemented by
a *VideoInput* Plugin Object. It also shows how a new *VideoInput* Plugin can be
 installed.

## <center> Installing a Plugin </center>

To install a *VideoInput* Plugin, one should copy a `py` file and a `xml` file containing the structure showed below.
The file must have the same name.

```xml
<VideoInput>
    <Title>Title of the plugin</Title>
    <Author>Author of the plugin</Author>
    <Description>A short description of what the plugin implements.</Description>
    <Version>major.minor1.minor2...</Version>
</VideoInput>
```

The information in the `xml` file will be shown to the user when him needs to load a new plugin.

## <center> The Python module or "Plugin Model" </center>
A Video Input plugin instance is called **VIMO** (short for *Video Input Model Object*).
A **VIMO** is responsible for implementing a interface that provides video frames
when requested. The communication of the **VIMO** and the software is supposed to be as simples as possible.

Having a instance of a **VIMO** doesn't mean that a video source is available
since a single implementation can get data from different sources. To signal
that a `media` (thats how a video source is called) is available or not, the
**VIMO** should use the [`ICMedia`](ICMedia.md) object that will passed as a keyword argument
 when `initplugin` is called.

#### Module
The module containing the code must have a function `main(*args, **kwargs)`.
This function will be called when a new plugin needs to be created, so it must
return a new plugin object when called.

#### VIMO Plugin Object
The following methods must be exposed:

```
init_plugin(*args, **kwargs) -> bool

Method that will be called at the initialization of the plugin, after its instantiation. The keyword args for the current version are:  

- gui_proxy    : a ICGUI_Interface instance. this interface object should be
               : used to access the software GUI.
- media_proxy  : an ICMedia_VIMOProxy instance. this object should be used to inform
               : the analysis object that a video source has been opened or closed
- return       : the value returned should be True if the plugin was
               : initialized or False if something went wrong. if False is
               : returned, the plugin's release() method will be called right
               : after this. information about the error can be written used the
               : Log module to display user-friendly information.


release() -> None

Method that will be called at the end of an VIMO's life. It needs to
release any resources used by the plugin.

```
