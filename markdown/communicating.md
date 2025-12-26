# Communicating with the user

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
    QgsMessageLog,
    QgsGeometry,
)

from qgis.gui import (
    QgsMessageBar,
)

from qgis.PyQt.QtWidgets import (
    QSizePolicy,
    QPushButton,
    QDialog,
    QGridLayout,
    QDialogButtonBox,
)
```

This section shows some methods and elements that should be used to communicate
with the user, in order to keep consistency in the User Interface.

## Showing messages. The QgsMessageBar class

Using message boxes can be a bad idea from a user experience point of view. For
showing a small info line or a warning/error messages, the QGIS message bar is
usually a better option.

Using the reference to the QGIS interface object, you can show a message in the
message bar with the following code

```python
from qgis.core import Qgis
iface.messageBar().pushMessage("Error", "I'm sorry Dave, I'm afraid I can't do that", level=Qgis.Critical)
```

![QGIS Message bar](img/errorbar.png)
*QGIS Message bar*

You can set a duration to show it for a limited time

```python
iface.messageBar().pushMessage("Ooops", "The plugin is not working as it should", level=Qgis.Critical, duration=3)
```

![QGIS Message bar with timer](img/errorbar-timed.png)
*QGIS Message bar with timer*

The examples above show an error bar, but the `level` parameter can be used
to creating warning messages or info messages, using the
`Qgis.MessageLevel ` enumeration. You can use up to 4 different levels:

0. Info
1. Warning
2. Critical
3. Success

![QGIS Message bar (info)](img/infobar.png)
*QGIS Message bar (info)*

Widgets can be added to the message bar, like for instance a button to show
more info

```python
def showError():
    pass

widget = iface.messageBar().createMessage("Missing Layers", "Show Me")
button = QPushButton(widget)
button.setText("Show Me")
button.pressed.connect(showError)
widget.layout().addWidget(button)
iface.messageBar().pushWidget(widget, Qgis.Warning)
```

![QGIS Message bar with a button](img/bar-button.png)
*QGIS Message bar with a button*

You can even use a message bar in your own dialog so you don't have to show a
message box, or if it doesn't make sense to show it in the main QGIS window

```python
class MyDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.bar = QgsMessageBar()
        self.bar.setSizePolicy( QSizePolicy.Minimum, QSizePolicy.Fixed )
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.buttonbox.accepted.connect(self.run)
        self.layout().addWidget(self.buttonbox, 0, 0, 2, 1)
        self.layout().addWidget(self.bar, 0, 0, 1, 1)
    def run(self):
        self.bar.pushMessage("Hello", "World", level=Qgis.Info)

myDlg = MyDialog()
myDlg.show()
```

![QGIS Message bar in custom dialog](img/dialog-with-bar.png)
*QGIS Message bar in custom dialog*

## Showing progress

Progress bars can also be put in the QGIS message bar, since, as we have seen,
it accepts widgets. Here is an example that you can try in the console.

```python
import time
from qgis.PyQt.QtWidgets import QProgressBar
from qgis.PyQt.QtCore import *
progressMessageBar = iface.messageBar().createMessage("Doing something boring...")
progress = QProgressBar()
progress.setMaximum(10)
progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
progressMessageBar.layout().addWidget(progress)
iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

for i in range(10):
    time.sleep(1)
    progress.setValue(i + 1)

iface.messageBar().clearWidgets()
```

Also, you can use the built-in status bar to report progress, as in the next
example:

```python
vlayer = iface.activeLayer()

count = vlayer.featureCount()
features = vlayer.getFeatures()

for i, feature in enumerate(features):
    # do something time-consuming here
    print('.') # printing should give enough time to present the progress

    percent = i / float(count) * 100
    # iface.mainWindow().statusBar().showMessage("Processed {} %".format(int(percent)))
    iface.statusBarIface().showMessage("Processed {} %".format(int(percent)))

iface.statusBarIface().clearMessage()
```

## Logging

There are three different types of logging available in QGIS to log and save all
the information about the execution of your code. Each has its specific output
location. Please consider to use the correct way of logging for your purpose:

* `QgsMessageLog ` is for messages to communicate
  issues to the user.
  The output of the QgsMessageLog is shown in the Log Messages Panel.
* The python built in **logging** module is for debugging on the level of the QGIS
  Python API (PyQGIS). It is recommended for Python script developers that need to
  debug their python code, e.g. feature ids or geometries
* `QgsLogger ` is for messages for *QGIS internal*
  debugging / developers (i.e. you suspect something is triggered by some broken code).
  Messages are only visible with developer versions of QGIS.

Examples for the different logging types are shown in the following sections below.

**Warning:** e of the Python ``print`` statement is unsafe to do in any code which may be ltithreaded and **extremely slows down the algorithm**. This includes **expression nctions**, **renderers**, symbol layers** and **Processing algorithms** (amongst others). In these ses you should always use the python **logging** module or thread safe classes class:`QgsLogger <qgis.core.QgsLogger>`  :class:`QgsMessageLog <qgis.core.QgsMessageLog>`) instead.

### QgsMessageLog

```python
# You can optionally pass a 'tag' and a 'level' parameters
QgsMessageLog.logMessage("Your plugin code has been executed correctly", 'MyPlugin', level=Qgis.Info)
QgsMessageLog.logMessage("Your plugin code might have some problems", level=Qgis.Warning)
QgsMessageLog.logMessage("Your plugin code has crashed!", level=Qgis.Critical)
```

**Note:** You can see the output of the :class:`QgsMessageLog <qgis.core.QgsMessageLog>` in the :ref:`log_message_panel`

### The python built in logging module

```python
import logging
formatter = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfilename=r'c:\temp\example.log'
logging.basicConfig(filename=logfilename, level=logging.DEBUG, format=formatter)
logging.info("This logging info text goes into the file")
logging.debug("This logging debug text goes into the file as well")
```

The basicConfig method configures the basic setup of the logging.
In the above code the filename, logging level and the format are defined.
The filename refers to where to write the logfile to, the logging level defines what
levels to output and the format defines the format in which each message is output.

```python
2020-10-08 13:14:42,998 - root - INFO - This logging text goes into the file
2020-10-08 13:14:42,998 - root - DEBUG - This logging debug text goes into the file as well
```

If you want to erase the log file every time you execute your script you can do something like:

```python
if os.path.isfile(logfilename):
    with open(logfilename, 'w') as file:
        pass
```

Further resources on how to use the python logging facility are available at:

* https://docs.python.org/3/library/logging.html
* https://docs.python.org/3/howto/logging.html
* https://docs.python.org/3/howto/logging-cookbook.html

**Warning:** Please note that without logging to a file by setting a filename the logging may be multithreaded which heavily slows down the output.