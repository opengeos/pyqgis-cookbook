# Developing Python Plugins

It is possible to create plugins in the Python programming language.
In comparison with classical plugins written in C++ these should be easier to
write, understand, maintain and distribute due to the dynamic nature of the
Python language.

Python plugins are listed together with C++ plugins in QGIS plugin manager.
They are searched for in `~/(UserProfile)/python/plugins` and these paths:

* UNIX/Mac: `(qgis_prefix)/share/qgis/python/plugins`
* Windows: `(qgis_prefix)/python/plugins`

For definitions of `~` and `(UserProfile)` see *core_and_external_plugins*.

**Note:**  By setting `QGIS_PLUGINPATH` to an existing directory path, you can add this  path to the list of paths that are searched for plugins.