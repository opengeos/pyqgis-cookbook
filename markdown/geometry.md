# Geometry Handling

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
  QgsGeometry,
  QgsGeometryCollection,
  QgsPoint,
  QgsPointXY,
  QgsWkbTypes,
  QgsProject,
  QgsFeatureRequest,
  QgsVectorLayer,
  QgsDistanceArea,
  QgsUnitTypes,
  QgsCoordinateTransform,
  QgsCoordinateReferenceSystem
)
```

Points, linestrings and polygons that represent a spatial feature are commonly
referred to as geometries. In QGIS they are represented with the
`QgsGeometry ` class.

Sometimes one geometry is actually a collection of simple (single-part)
geometries. Such a geometry is called a multi-part geometry. If it contains
just one type of simple geometry, we call it multi-point, multi-linestring or
multi-polygon. For example, a country consisting of multiple islands can be
represented as a multi-polygon.

The coordinates of geometries can be in any coordinate reference system (CRS).
When fetching features from a layer, associated geometries will have
coordinates in CRS of the layer.

Description and specifications of all possible geometries construction and
relationships are available in the `OGC Simple Feature Access Standards
<https://www.ogc.org/publications/standard/sfa>`_ for advanced details.

## Geometry Construction

PyQGIS provides several options for creating a geometry:

* from coordinates

```python
gPnt = QgsGeometry.fromPointXY(QgsPointXY(1,1))
print(gPnt)
gLine = QgsGeometry.fromPolyline([QgsPoint(1, 1), QgsPoint(2, 2)])
print(gLine)
gPolygon = QgsGeometry.fromPolygonXY([[QgsPointXY(1, 1),
QgsPointXY(2, 2), QgsPointXY(2, 1)]])
print(gPolygon)
```

* from well-known text (WKT)

```python
geom = QgsGeometry.fromWkt("POINT(3 4)")
print(geom)
```

* from well-known binary (WKB)

```python
g = QgsGeometry()
wkb = bytes.fromhex("010100000000000000000045400000000000001440")
g.fromWkb(wkb)

# print WKT representation of the geometry
print(g.asWkt())
```

## Access to Geometry

First, you should find out the geometry type. The `wkbType() `
method is the one to use. It returns a value from the `QgsWkbTypes.Type `
enumeration.

```python
print(gPnt.wkbType())
# output: 1
print(gLine.wkbType())
# output: 2
print(gPolygon.wkbType())
# output: 3
```

As an alternative, one can use the `type() `
method which returns a value from the `QgsWkbTypes.GeometryType `
enumeration.

```python
print(gLine.type())
# output: 1
```

You can use the `displayString() `
function to get a human readable geometry type.

```python
print(QgsWkbTypes.displayString(gPnt.wkbType()))
# output: 'Point'
print(QgsWkbTypes.displayString(gLine.wkbType()))
# output: 'LineString'
print(QgsWkbTypes.displayString(gPolygon.wkbType()))
# output: 'Polygon'
```

There is also a helper function
`isMultipart() ` to find out whether a geometry is multipart or not.

To extract information from a geometry there are accessor functions for every
vector type. Here's an example on how to use these accessors:

```python
print(gPnt.asPoint())
# output: <QgsPointXY: POINT(1 1)>
print(gLine.asPolyline())
# output: [<QgsPointXY: POINT(1 1)>, <QgsPointXY: POINT(2 2)>]
print(gPolygon.asPolygon())
# output: [[<QgsPointXY: POINT(1 1)>, <QgsPointXY: POINT(2 2)>, <QgsPointXY: POINT(2 1)>, <QgsPointXY: POINT(1 1)>]]
```

**Note:** The tuples (x,y) are not real tuples, they are :class:`QgsPoint <qgis.core.QgsPoint>` objects, the values are accessible with :meth:`x() <qgis.core.QgsPoint.x>` and :meth:`y() <qgis.core.QgsPoint.y>` methods.

For multipart geometries there are similar accessor functions:
`asMultiPoint() `,
`asMultiPolyline() `
and `asMultiPolygon() `.

It is possible to iterate over all the parts of a geometry,
regardless of the geometry's type. E.g.

```python
geom = QgsGeometry.fromWkt( 'MultiPoint( 0 0, 1 1, 2 2)' )
for part in geom.parts():
  print(part.asWkt())
```

```python
geom = QgsGeometry.fromWkt( 'LineString( 0 0, 10 10 )' )
for part in geom.parts():
  print(part.asWkt())
```

```python
gc = QgsGeometryCollection()
gc.fromWkt('GeometryCollection( Point(1 2), Point(11 12), LineString(33 34, 44 45))')
print(gc[1].asWkt())
```

It's also possible to modify each part of the geometry using
`QgsGeometry.parts() ` method.

```python
geom = QgsGeometry.fromWkt( 'MultiPoint( 0 0, 1 1, 2 2)' )
for part in geom.parts():
  part.transform(QgsCoordinateTransform(
    QgsCoordinateReferenceSystem("EPSG:4326"),
    QgsCoordinateReferenceSystem("EPSG:3111"),
    QgsProject.instance())
  )

print(geom.asWkt())
```

## Geometry Predicates and Operations

QGIS uses GEOS library for advanced geometry operations such as geometry
predicates (`contains() `, `intersects() `, …) and set operations
(`combine() `, `difference() `, …). It can also compute geometric
properties of geometries, such as area (in the case of polygons) or lengths
(for polygons and lines).

Let's see an example that combines iterating over the features in a
given layer and performing some geometric computations based on their
geometries. The below code will compute and print the area and perimeter of
each country in the `countries` layer within our tutorial QGIS project.

The following code assumes `layer` is a `QgsVectorLayer ` object that has Polygon feature type.

```python
# let's access the 'countries' layer
layer = QgsProject.instance().mapLayersByName('countries')[0]

# let's filter for countries that begin with Z, then get their features
query = '"name" LIKE \'Z%\''
features = layer.getFeatures(QgsFeatureRequest().setFilterExpression(query))

# now loop through the features, perform geometry computation and print the results
for f in features:
  geom = f.geometry()
  name = f.attribute('NAME')
  print(name)
  print('Area: ', geom.area())
  print('Perimeter: ', geom.length())
```

Now you have calculated and printed the areas and perimeters of the geometries.
You may however quickly notice that the values are strange.
That is because areas and perimeters don't take CRS into account when computed
using the `area() ` and :meth:`length()
<qgis.core.QgsGeometry.length>`
methods from the `QgsGeometry ` class. For a more powerful area and
distance calculation, the `QgsDistanceArea `
class can be used, which can perform ellipsoid based calculations:

The following code assumes `layer` is a :class:`QgsVectorLayer
<qgis.core.QgsVectorLayer>` object that has Polygon feature type.

```python
d = QgsDistanceArea()
d.setEllipsoid('WGS84')

layer = QgsProject.instance().mapLayersByName('countries')[0]

# let's filter for countries that begin with Z, then get their features
query = '"name" LIKE \'Z%\''
features = layer.getFeatures(QgsFeatureRequest().setFilterExpression(query))

for f in features:
  geom = f.geometry()
  name = f.attribute('NAME')
  print(name)
  print("Perimeter (m):", d.measurePerimeter(geom))
  print("Area (m2):", d.measureArea(geom))

  # let's calculate and print the area again, but this time in square kilometers
  print("Area (km2):", d.convertAreaMeasurement(d.measureArea(geom), QgsUnitTypes.AreaSquareKilometers))
```

Alternatively, you may want to know the distance between two points.

```python
d = QgsDistanceArea()
d.setEllipsoid('WGS84')

# Let's create two points.
# Santa claus is a workaholic and needs a summer break,
# lets see how far is Tenerife from his home
santa = QgsPointXY(25.847899, 66.543456)
tenerife = QgsPointXY(-16.5735, 28.0443)

print("Distance in meters: ", d.measureLine(santa, tenerife))
```

You can find many example of algorithms that are included in QGIS and use these
methods to analyze and transform vector data. Here are some links to the code
of a few of them.

* Distance and area using the `QgsDistanceArea ` class:
  [Distance matrix algorithm ](python/plugins/processing/algs/qgis/PointDistance.py)
* [Lines to polygons algorithm ](python/plugins/processing/algs/qgis/LinesToPolygons.py)