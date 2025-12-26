# Accessing the Table Of Contents (TOC)

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
)
```

You can use different classes to access all the loaded layers in the TOC and
use them to retrieve information:

* `QgsProject `
* `QgsLayerTreeGroup `

## The QgsProject class

You can use `QgsProject ` to retrieve information
about the TOC and all the layers loaded.

You have to create an `instance` of `QgsProject `
and use its methods to get the loaded layers.

The main method is `mapLayers() `. It will
return a dictionary of the loaded layers:

```python
layers = QgsProject.instance().mapLayers()
print(layers)
```

The dictionary `keys` are the unique layer ids while the `values` are the
related objects.

It is now straightforward to obtain any other information about the layers:

```python
# list of layer names using list comprehension
l = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
# dictionary with key = layer name and value = layer object
layers_list = {}
for l in QgsProject.instance().mapLayers().values():
  layers_list[l.name()] = l

print(layers_list)
```

You can also query the TOC using the name of the layer:

```python
country_layer = QgsProject.instance().mapLayersByName("countries")[0]
```

**Note:** A list with all the matching layers is returned, so we index with `[0]`` to get the first layer with this name.

## QgsLayerTreeGroup class

The layer tree is a classical tree structure built of nodes. There are currently
two types of nodes: group nodes (`QgsLayerTreeGroup `)
and layer nodes (`QgsLayerTreeLayer `).

**Note:** for more information you can read these blog posts of Martin Dobias: Part 1 <https://www.lutraconsulting.co.uk/blogs/qgis-layer-tree-api-part-1/>`_ Part 2 <https://www.lutraconsulting.co.uk/blogs/qgis-layer-tree-api-part-2/>`_ Part 3 <https://www.lutraconsulting.co.uk/blogs/qgis-layer-tree-api-part-3/>`_

The project layer tree can be accessed easily with the method
`layerTreeRoot() `
of the `QgsProject ` class:

```python
root = QgsProject.instance().layerTreeRoot()
```

`root` is a group node and has *children*:

```python
root.children()
```

A list of direct children is returned. Sub group children should be accessed
from their own direct parent.

We can retrieve one of the children:

```python
child0 = root.children()[0]
print(child0)
```

Layers can also be retrieved using their (unique) `id`:

```python
ids = root.findLayerIds()
# access the first layer of the ids list
root.findLayer(ids[0])
```

And groups can also be searched using their names:

```python
root.findGroup('Group Name')
```

`QgsLayerTreeGroup ` has many other useful
methods that can be used to obtain more information about the TOC:

```python
# list of all the checked layers in the TOC
checked_layers = root.checkedLayers()
print(checked_layers)
```

Now let’s add some layers to the project’s layer tree. There are two ways of doing
that:

#. **Explicit addition** using the `addLayer() `
   or `insertLayer() `
   functions:

```python
# create a temporary layer
layer1 = QgsVectorLayer("path_to_layer", "Layer 1", "memory")
# add the layer to the legend, last position
root.addLayer(layer1)
# add the layer at given position
root.insertLayer(5, layer1)
```

#. **Implicit addition**: since the project's layer tree is connected to the
   layer registry it is enough to add a layer to the map layer registry:

```python
QgsProject.instance().addMapLayer(layer1)
```

You can switch between `QgsVectorLayer ` and
`QgsLayerTreeLayer ` easily:

```python
node_layer = root.findLayer(country_layer.id())
print("Layer node:", node_layer)
print("Map layer:", node_layer.layer())
```

Groups can be added with the `addGroup() `
method. In the example below, the former will add a group to the end of the TOC
while for the latter you can add another group within an existing one:

```python
node_group1 = root.addGroup('Simple Group')
# add a sub-group to Simple Group
node_subgroup1 = node_group1.addGroup("I'm a sub group")
```

To moving nodes and groups there are many useful methods.

Moving an existing node is done in three steps:

#. cloning the existing node
#. moving the cloned node to the desired position
#. deleting the original node

```python
# clone the group
cloned_group1 = node_group1.clone()
# move the node (along with sub-groups and layers) to the top
root.insertChildNode(0, cloned_group1)
# remove the original node
root.removeChildNode(node_group1)
```

It is a little bit more *complicated* to move a layer around in the legend:

```python
# get a QgsVectorLayer
vl = QgsProject.instance().mapLayersByName("countries")[0]
# create a QgsLayerTreeLayer object from vl by its id
myvl = root.findLayer(vl.id())
# clone the myvl QgsLayerTreeLayer object
myvlclone = myvl.clone()
# get the parent. If None (layer is not in group) returns ''
parent = myvl.parent()
# move the cloned layer to the top (0)
parent.insertChildNode(0, myvlclone)
# remove the original myvl
root.removeChildNode(myvl)
```

or moving it to an existing group:

```python
# get a QgsVectorLayer
vl = QgsProject.instance().mapLayersByName("countries")[0]
# create a QgsLayerTreeLayer object from vl by its id
myvl = root.findLayer(vl.id())
# clone the myvl QgsLayerTreeLayer object
myvlclone = myvl.clone()
# create a new group
group1 = root.addGroup("Group1")
# get the parent. If None (layer is not in group) returns ''
parent = myvl.parent()
# move the cloned layer to the top (0)
group1.insertChildNode(0, myvlclone)
# remove the QgsLayerTreeLayer from its parent
parent.removeChildNode(myvl)
```

Some other methods that can be used to modify the groups and layers:

```python
node_group1 = root.findGroup("Group1")
# change the name of the group
node_group1.setName("Group X")
node_layer2 = root.findLayer(country_layer.id())
# change the name of the layer
node_layer2.setName("Layer X")
# change the visibility of a layer
node_group1.setItemVisibilityChecked(True)
node_layer2.setItemVisibilityChecked(False)
# expand/collapse the group view
node_group1.setExpanded(True)
node_group1.setExpanded(False)
```