# Loading Projects

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
    Qgis,
    QgsProject,
    QgsPathResolver
)

from qgis.gui import (
    QgsLayerTreeMapCanvasBridge,
)
```

Sometimes you need to load an existing project from a plugin or (more often)
when developing a standalone QGIS Python application (see: *pythonapplications*).

To load a project into the current QGIS application you need to create
an instance of the `QgsProject ` class.
This is a singleton class, so you must use its `instance() ` method to do it.
You can call its `read() ` method, passing the path of the project to be loaded:

```python
# If you are not inside a QGIS console you first need to import
# qgis and PyQt classes you will use in this script as shown below:
from qgis.core import QgsProject
# Get the project instance
project = QgsProject.instance()
# Print the current project file name (might be empty in case no projects have been loaded)
# print(project.fileName())

# Load another project
project.read('testdata/01_project.qgs')
print(project.fileName())
```

If you need to make modifications to the project (for example to add or remove some layers)
and save your changes, call the `write() ` method of your project instance.
The `write() ` method also accepts an optional
path for saving the project to a new location:

```python
# Save the project to the same
project.write()
# ... or to a new file
project.write('testdata/my_new_qgis_project.qgs')
```

Both `read() ` and
`write() ` functions
return a boolean value that you can use to check if the operation was successful.

**Note:** If you are writing a QGIS standalone application, in order to synchronise the loaded project with the canvas you need to instantiate a :class:`QgsLayerTreeMapCanvasBridge <qgis.gui.QgsLayerTreeMapCanvasBridge>` as in the example below:

```python
bridge = QgsLayerTreeMapCanvasBridge( \
         QgsProject.instance().layerTreeRoot(), canvas)
# Now you can safely load your project and see it in the canvas
project.read('testdata/my_new_qgis_project.qgs')
```

## Resolving bad paths

It can happen that layers loaded in the project are moved to another location.
When the project is loaded again all the layer paths are broken.
The `QgsPathResolver ` class helps you rewrite
layers path within the project.

Its `setPathPreprocessor() `
method allows setting a custom path pre-processor function to
manipulate paths and data sources prior to resolving them to file references
or layer sources.

The processor function must accept a single string argument (representing the
original file path or data source) and return a processed version of this path.
The path pre-processor function is called **before** any bad layer handler.
If multiple preprocessors are set, they will be called in sequence based
on the order in which they were originally set.

Some use cases:

#. replace an outdated path:

```python
def my_processor(path):
    return path.replace('c:/Users/ClintBarton/Documents/Projects', 'x:/Projects/')

QgsPathResolver.setPathPreprocessor(my_processor)
```

#. replace a database host address with a new one:

```python
def my_processor(path):
    return path.replace('host=10.1.1.115', 'host=10.1.1.116')

QgsPathResolver.setPathPreprocessor(my_processor)
```

#. replace stored database credentials with new ones:

```python
def my_processor(path):
    path= path.replace("user='gis_team'", "user='team_awesome'")
    path = path.replace("password='cats'", "password='g7as!m*'")
    return path

QgsPathResolver.setPathPreprocessor(my_processor)
```

Likewise, a `setPathWriter() `
method is available for a path writer function.

An example to replace the path with a variable:

```python
def my_processor(path):
  return path.replace('c:/Users/ClintBarton/Documents/Projects', '$projectdir$')

QgsPathResolver.setPathWriter(my_processor)
```

Both methods return an `id` that can be used to remove the pre-processor
or writer they added.
See `removePathPreprocessor() `
and `removePathWriter() `.

## Using flags to speed up things

In some instances where you may not need to use a fully functional project, but only
want to access it for a specific reason, flags may be helpful. A full list of flags is available under
`ProjectReadFlag `. Multiple flags can be added together.

As an example, if we do not care about actual layers and data and simply want to
access a project (e.g. for layout or 3D view settings), we can use `DontResolveLayers` flag
to bypass the data validation step and prevent the bad layer dialog from appearing.
The following can be done:

```python
readflags = Qgis.ProjectReadFlags()
readflags |= Qgis.ProjectReadFlag.DontResolveLayers
project = QgsProject.instance()
project.read('C:/Users/ClintBarton/Documents/Projects/mysweetproject.qgs', readflags)
```

To add more flags the python Bitwise OR operator (`|`) must be used.