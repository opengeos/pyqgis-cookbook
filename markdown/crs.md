# Projections Support

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsPointXY,
)
```

## Coordinate reference systems

Coordinate reference systems (CRS) are encapsulated by the
`QgsCoordinateReferenceSystem `
class. Instances of this class can be created in several different ways:

* specify CRS by its ID

```python
# EPSG 4326 is allocated for WGS84
crs = QgsCoordinateReferenceSystem("EPSG:4326")
print(crs.isValid())
```

If no prefix is specified, WKT definition is assumed.

* specify CRS by its well-known text (WKT)

```python
wkt = 'GEOGCS["WGS84", DATUM["WGS84", SPHEROID["WGS84", 6378137.0, 298.257223563]],' \
      'PRIMEM["Greenwich", 0.0], UNIT["degree",0.017453292519943295],' \
      'AXIS["Longitude",EAST], AXIS["Latitude",NORTH]]'
crs = QgsCoordinateReferenceSystem(wkt)
print(crs.isValid())
```

* create an invalid CRS and then use one of the `create*` functions to
  initialize it. In the following example we use a Proj string to initialize the
  projection.

```python
crs = QgsCoordinateReferenceSystem()
crs.createFromProj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
print(crs.isValid())
```

It's wise to check whether creation (i.e. lookup in the database) of the CRS
has been successful: `isValid() `
must return `True`.

Note that for initialization of spatial reference systems QGIS needs to look up
appropriate values in its internal database `srs.db`. Thus in case you
create an independent application you need to set paths correctly with
`QgsApplication.setPrefixPath() `,
otherwise it will fail to find the
database. If you are running the commands from the QGIS Python console or
developing a plugin you do not care: everything is already set up for you.

Accessing spatial reference system information:

```python
crs = QgsCoordinateReferenceSystem("EPSG:4326")

print("QGIS CRS ID:", crs.srsid())
print("PostGIS SRID:", crs.postgisSrid())
print("Description:", crs.description())
print("Projection Acronym:", crs.projectionAcronym())
print("Ellipsoid Acronym:", crs.ellipsoidAcronym())
print("Proj String:", crs.toProj())
# check whether it's geographic or projected coordinate system
print("Is geographic:", crs.isGeographic())
# check type of map units in this CRS (values defined in QGis::units enum)
print("Map units:", crs.mapUnits())
```

Output:

## CRS Transformation

You can do transformation between different spatial reference systems by using
the `QgsCoordinateTransform ` class.
The easiest way to use it is to create a source and destination CRS and
construct a `QgsCoordinateTransform `
instance with them and the current project. Then just repeatedly call
`transform() ` function to do
the transformation. By default it does forward transformation, but it is capable
to do also inverse transformation.

```python
crsSrc = QgsCoordinateReferenceSystem("EPSG:4326")    # WGS 84
crsDest = QgsCoordinateReferenceSystem("EPSG:32633")  # WGS 84 / UTM zone 33N
transformContext = QgsProject.instance().transformContext()
xform = QgsCoordinateTransform(crsSrc, crsDest, transformContext)

# forward transformation: src -> dest
pt1 = xform.transform(QgsPointXY(18,5))
print("Transformed point:", pt1)

# inverse transformation: dest -> src
pt2 = xform.transform(pt1, QgsCoordinateTransform.ReverseTransform)
print("Transformed back:", pt2)
```

Output: