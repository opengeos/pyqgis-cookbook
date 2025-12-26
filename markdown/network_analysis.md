# Network analysis library

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
  QgsVectorLayer,
  QgsPointXY,
)
```

The network analysis library can be used to:

* create mathematical graph from geographical data (polyline vector layers)
* implement basic methods from graph theory (currently only Dijkstra's algorithm)

Briefly, a typical use case can be described as:

#. create graph from geodata (usually polyline vector layer)
#. run graph analysis
#. use analysis results (for example, visualize them)

## Building a graph

The first thing you need to do --- is to prepare input data,
that is to convert a vector layer into a graph.
All further actions will use this graph, not the layer.

As a source we can use any polyline vector layer. Nodes of the polylines
become graph vertexes, and segments of the polylines are graph edges.
If several nodes have the same coordinates then they are the same graph vertex.
So two lines that have a common node become connected to each other.

Additionally, during graph creation it is possible to "fix" ("tie") to the
input vector layer any number of additional points. For each additional
point a match will be found --- the closest graph vertex or closest graph edge.
In the latter case the edge will be split and a new vertex added.

Vector layer attributes and length of an edge can be used as the properties
of an edge.

Converting from a vector layer to the graph is done using the
[Builder ](https://en.wikipedia.org/wiki/Builder_pattern) programming pattern.
A graph is constructed using a so-called Director.
There is only one Director for now: :class:`QgsVectorLayerDirector
<qgis.analysis.QgsVectorLayerDirector>`.
The director sets the basic settings that will be used to construct a graph
from a line vector layer, used by the builder to create the graph.
Currently, as in the case with the director, only one builder exists:
`QgsGraphBuilder `,
that creates `QgsGraph ` objects.
You may want to implement your own builders that will build a graph compatible
with such libraries as [BGL ](https://www.boost.org/doc/libs/1_48_0/libs/graph/doc/index.html)
or [NetworkX ](https://networkx.org/).

To calculate edge properties the programming pattern
[strategy ](https://en.wikipedia.org/wiki/Strategy_pattern) is used.
For now only `QgsNetworkDistanceStrategy `
strategy (that takes into account the length of the route)
and `QgsNetworkSpeedStrategy `
(that also considers the speed) are available.
You can implement your own strategy that will use all necessary parameters.

It's time to dive into the process.

#. First of all, to use this library we should import the analysis module:

```python
from qgis.analysis import *
```

#. Then some examples for creating a director:

```python
# Don't use information about road direction from layer attributes,
# all roads are treated as two-way
director = QgsVectorLayerDirector(
    vectorLayer, -1, "", "", "", QgsVectorLayerDirector.DirectionBoth
)
```

```python
# Use field with index 5 as source of information about road direction.
# one-way roads with direct direction have attribute value "yes",
# one-way roads with reverse direction have the value "1", and accordingly
# bidirectional roads have "no". By default roads are treated as two-way.
# This scheme can be used with OpenStreetMap data
director = QgsVectorLayerDirector(
    vectorLayer, 5, "yes", "1", "no", QgsVectorLayerDirector.DirectionBoth
)
```

   To construct a director, we should pass a vector layer that will be used
   as the source for the graph structure and information about allowed movement on
   each road segment (one-way or bidirectional movement, direct or reverse direction).
   The call looks like this
   (find more details on the parameters at `qgis.analysis.QgsVectorLayerDirector`):

```python
director = QgsVectorLayerDirector(
    vectorLayer,
    directionFieldId,
    directDirectionValue,
    reverseDirectionValue,
    bothDirectionValue,
    defaultDirection,
)
```

#. It is necessary then to create a strategy for calculating edge properties

```python
# The index of the field that contains information about the edge speed
attributeId = 1
# Default speed value
defaultValue = 50
# Conversion from speed to metric units ('1' means no conversion)
toMetricFactor = 1
strategy = QgsNetworkSpeedStrategy(attributeId, defaultValue, toMetricFactor)
```

#. And tell the director about this strategy

```python
director = QgsVectorLayerDirector(vectorLayer, -1, "", "", "", 3)
director.addStrategy(strategy)
```

#. Now we can use the builder, which will create the graph,
   using the `QgsGraphBuilder ` class constructor.

```python
# only CRS is set, all other values are defaults
builder = QgsGraphBuilder(vectorLayer.crs())
```

#. Also we can define several points, which will be used in the analysis.
   For example:

```python
startPoint = QgsPointXY(1179720.1871, 5419067.3507)
endPoint = QgsPointXY(1180616.0205, 5419745.7839)
```

#. Now all is in place so we can build the graph and "tie" these points to it:

```python
tiedPoints = director.makeGraph(builder, [startPoint, endPoint])
```

   Building the graph can take some time
   (which depends on the number of features in a layer and layer size).
   `tiedPoints` is a list with coordinates of "tied" points.
#. When the build operation is finished we can get the graph and use it for the analysis:

```python
graph = builder.graph()
```

#. With the next code we can get the vertex indexes of our points:

```python
startId = graph.findVertex(tiedPoints[0])
endId = graph.findVertex(tiedPoints[1])
```

## Graph analysis

Networks analysis is used to find answers to two questions: which vertexes
are connected and how to find a shortest path. To solve these problems the
network analysis library provides Dijkstra's algorithm.

Dijkstra's algorithm finds the shortest route from one of the vertexes of the
graph to all the others and the values of the optimization parameters.
The results can be represented as a shortest path tree.

The shortest path tree is a directed weighted graph (or more precisely a tree)
with the following properties:

* only one vertex has no incoming edges — the root of the tree
* all other vertexes have only one incoming edge
* if vertex B is reachable from vertex A, then the path from A to B is the
  single available path and it is optimal (shortest) on this graph

To get the shortest path tree use the methods
`shortestTree() `
and `dijkstra() `
of the `QgsGraphAnalyzer ` class.
It is recommended to use the `dijkstra() ` method
because it works faster and uses memory more efficiently.

The `shortestTree() ` method
is useful when you want to walk around the shortest path tree.
It always creates a new graph object (`QgsGraph `)
and accepts three variables:

* `source` --- input graph
* `startVertexIdx` --- index of the point on the tree (the root of the tree)
* `criterionNum` --- number of edge property to use (started from 0).

```python
tree = QgsGraphAnalyzer.shortestTree(graph, startId, 0)
```

The `dijkstra() ` method has the
same arguments, but returns a tuple of arrays:

* In the first array, element `n` contains index of the incoming edge or -1 if there
  are no incoming edges.
* In the second array, element `n` contains the distance from the root of the tree
  to vertex `n` or DOUBLE_MAX if vertex `n` is unreachable from the root.

```python
(tree, cost) = QgsGraphAnalyzer.dijkstra(graph, startId, 0)
```

Here is some very simple code to display the shortest path tree using the graph created
with the `shortestTree() `
or the `dijkstra() ` method
(select linestring layer in **Layers** panel and replace coordinates with your own).

**Warning:** Use this code only as an example, it creates a lot of class:`QgsRubberBand <qgis.gui.QgsRubberBand>` objects and may be slow on large datasets.

### Finding shortest paths

To find the optimal path between two points the following approach is used.
Both points (start A and end B) are "tied" to the graph when it is built.
Then using the `shortestTree() `
or `dijkstra() ` method
we build the shortest path tree with root in the start point A.
In the same tree we also find the end point B and start to walk through the tree
from point B to point A.
The whole algorithm can be written as:

```python
assign T = B
while T != B
    add point T to path
    get incoming edge for point T
    look for point TT, that is start point of this edge
    assign T = TT
add point A to path
```

At this point we have the path, in the form of the inverted list of vertexes
(vertexes are listed in reversed order from end point to start point) that will
be visited during traveling by this path.

Here is the sample code for QGIS Python Console (you may need to load and
select a linestring layer in TOC and replace coordinates in the code with yours) that
uses the `shortestTree() `
or `dijkstra() ` method:

### Areas of availability

The area of availability for vertex A is the subset of graph vertexes that are
accessible from vertex A and the cost of the paths from A to these vertexes are
not greater that some value.

More clearly this can be shown with the following example: "There is a fire
station. Which parts of city can a fire truck reach in 5 minutes? 10 minutes?
15 minutes?". Answers to these questions are fire station's areas of availability.

To find the areas of availability we can use
the `dijkstra() ` method
of the `QgsGraphAnalyzer ` class.
It is enough to compare the elements of the cost array with a predefined value.
If cost[i] is less than or equal to a predefined value,
then vertex i is inside the area of availability, otherwise it is outside.

A more difficult problem is to get the borders of the area of availability.
The bottom border is the set of vertexes that are still accessible,
and the top border is the set of vertexes that are not accessible.
In fact this is simple:
it is the availability border based on the edges of the shortest path tree
for which the source vertex of the edge is accessible
and the target vertex of the edge is not.

Here is an example:

```python
director = QgsVectorLayerDirector(
  vectorLayer, -1, "", "", "", QgsVectorLayerDirector.DirectionBoth
)
strategy = QgsNetworkDistanceStrategy()
director.addStrategy(strategy)
builder = QgsGraphBuilder(vectorLayer.crs())

pStart = QgsPointXY(1179661.925139, 5419188.074362)
delta = iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 1

rb = QgsRubberBand(iface.mapCanvas())
rb.setColor(Qt.green)
rb.addPoint(QgsPointXY(pStart.x() - delta, pStart.y() - delta))
rb.addPoint(QgsPointXY(pStart.x() + delta, pStart.y() - delta))
rb.addPoint(QgsPointXY(pStart.x() + delta, pStart.y() + delta))
rb.addPoint(QgsPointXY(pStart.x() - delta, pStart.y() + delta))

tiedPoints = director.makeGraph(builder, [pStart])
graph = builder.graph()
tStart = tiedPoints[0]

idStart = graph.findVertex(tStart)

(tree, cost) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0)

upperBound = []
r = 1500.0
i = 0
tree.reverse()

while i < len(cost):
    if cost[i] > r and tree[i] != -1:
        outVertexId = graph.edge(tree [i]).toVertex()
        if cost[outVertexId] < r:
            upperBound.append(i)
    i = i + 1

for i in upperBound:
    centerPoint = graph.vertex(i).point()
    rb = QgsRubberBand(iface.mapCanvas())
    rb.setColor(Qt.red)
    rb.addPoint(QgsPointXY(centerPoint.x() - delta, centerPoint.y() - delta))
    rb.addPoint(QgsPointXY(centerPoint.x() + delta, centerPoint.y() - delta))
    rb.addPoint(QgsPointXY(centerPoint.x() + delta, centerPoint.y() + delta))
    rb.addPoint(QgsPointXY(centerPoint.x() - delta, centerPoint.y() + delta))
```