# <center>ICGUI_Interface</center>
The `ICGUI_Interface` object is responsible for providing access to the software
*Graphical User Interface*. It is created by the application and passed to a
Plugin at the moment of its initialization(see [Video Input Model](Video Input Mode.md)).

The `ICGUI_Interface` provides methods for adding and removing tabs to the
MainWindow **Tools Tab Widget** and **Main Tab Widget**. It also provides
methods for creating `Parameter` objects. More about `Parameter` objects can
be found in the next sections.

## Adding and Removing Tab Pages
The interface provides methods that can be called by the plugin in order
to add it's own widgets to tab widgets of the Main Window. The widgets will be
added inside `QScrollArea` objects and will be resized when the user moves
the other widgets around, so it must be prepared to react to these resize events(e.g. using layouts).

```
addToolTab(widget, tab_title) -> bool

Add a new tab to the Main Window's Tools Tab Widget with tab_title as it's
title.

- widget    : a QWidget (or child) instance to be added as a page.
- tab_title : a str or QString containing the title of the tab
- return    : True if the tab was added or was already added and False if it fails


addMainTab(widget, tab_title) -> bool

Add a new tab to the Main Window's **Main Tab Widget** with tab_title as it's
title.

- widget    : a QWidget (or child) instance to be added as a page.
- tab_title : a str or QString containing the title of the tab
- return    : True if the tab was added or was already added and False if it fails


removeToolTab(widget) -> bool

Remove a previously added widget from the Main Window's **Tools Tab Widget**.
title.

- widget    : a QWidget (or child) instance to be removed from the tab widget.
- return    : True if the tab was removed or False if it fails


removeMainTab(widget) -> bool

Remove a previously added widget from the Main Window's **Main Tab Widget**.
title.

- widget    : a QWidget (or child) instance to be removed from the tab widget.
- return    : True if the tab was removed or False if it fails
```

## Parameters
The `ICGUI_Interface` also provides methods for creating widgets like sliders,
buttons etc. that can be bound to variables. All the methods here will return
an `Parameter` object. Each parameter can have different types but they all
expose the members `value`, `default` and `title`. When each one of these
members are assigned (by using the `=` operator) they will automatically update
the widgets, and when the user interacts with them, their values will also be updated.

When a new parameter is created it will be added to a tool tab called **Plugin Parameters**.

```
intParameter(title, value_range, default_value[, slider_type, adjust_func]) -> IntParameter

Create and return a integer parameter.

- title          : a str or QString containing the title that will be
                 : shown to the user
- value_range    : a `tuple` containing the max and min values of the parameter
- default_value  : the default value of the parameter
- slider_type    : an `GUIInterface.SliderType` enum containing the type
                 : of slider to be created. default is `HSlider`
- adjust_func    : a function that can be used to adjust the value of the
                 : parameter. the default function just sets the value of
                 : the parameter to the same as the slider's value. if the
                 : parameter needs some form of correction (like making sure)
                 : its an odd number) this function should receive the original
                 : value and return the adjusted one.
```
