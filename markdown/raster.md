# Using Raster Layers

**Hint:** The code snippets on this page need the following imports if you're outside the pyqgis console:

```python
from qgis.core import (
    QgsRasterLayer,
    QgsProject,
    QgsPointXY,
    QgsRaster,
    QgsRasterShader,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
    QgsSingleBandColorDataRenderer,
    QgsSingleBandGrayRenderer,
)

from qgis.PyQt.QtGui import (
    QColor,
)
```

## Layer Details

A raster layer consists of one or more raster bands --- referred to as
single band and multi band rasters. One band represents a matrix of
values. A color image (e.g. aerial photo) is a raster consisting of red,
blue and green bands. Single band rasters typically represent either continuous
variables (e.g. elevation) or discrete variables (e.g. land use). In some
cases, a raster layer comes with a palette and the raster values refer to
the colors stored in the palette.

The following code assumes `rlayer` is a
`QgsRasterLayer ` object.

```python
rlayer = QgsProject.instance().mapLayersByName('srtm')[0]
# get the resolution of the raster in layer unit
print(rlayer.width(), rlayer.height())
```

```python
# get the extent of the layer as QgsRectangle
print(rlayer.extent())
```

```python
# get the extent of the layer as Strings
print(rlayer.extent().toString())
```

```python
# get the raster type: 0 = GrayOrUndefined (single band), 1 = Palette (single band), 2 = Multiband
print(rlayer.rasterType())
```

```python
# get the total band count of the raster
```

    print(rlayer.bandCount())

```python
# get the first band name of the raster
print(rlayer.bandName(1))
```

```python
# get all the available metadata as a QgsLayerMetadata object
print(rlayer.metadata())
```

## Renderer

When a raster layer is loaded, it gets a default renderer based on its
type. It can be altered either in the layer properties or programmatically.

To query the current renderer:

```python
print(rlayer.renderer())
```

```python
print(rlayer.renderer().type())
```

To set a renderer, use the `setRenderer() `
method of `QgsRasterLayer `. There are a
number of renderer classes (derived from :class:`QgsRasterRenderer
<qgis.core.QgsRasterRenderer>`):

* `QgsHillshadeRenderer `
* `QgsMultiBandColorRenderer `
* `QgsPalettedRasterRenderer `
* `QgsRasterContourRenderer `
* `QgsSingleBandColorDataRenderer `
* `QgsSingleBandGrayRenderer `
* `QgsSingleBandPseudoColorRenderer `

Single band raster layers can be drawn either in gray colors (low values =
black, high values = white) or with a pseudocolor algorithm that assigns colors
to the values.
Single band rasters with a palette can also be drawn using the palette.
Multiband layers are typically drawn by mapping the bands to RGB colors.
Another possibility is to use just one band for drawing.

### Single Band Rasters

Let's say we want a render single band raster layer with colors ranging from
green to yellow (corresponding to pixel values from 0 to 255).
In the first stage we will prepare a
`QgsRasterShader ` object and configure
its shader function:

```python
fcn = QgsColorRampShader()
fcn.setColorRampType(QgsColorRampShader.Interpolated)
lst = [ QgsColorRampShader.ColorRampItem(0, QColor(0,255,0)),
      QgsColorRampShader.ColorRampItem(255, QColor(255,255,0)) ]
fcn.setColorRampItemList(lst)
shader = QgsRasterShader()
shader.setRasterShaderFunction(fcn)
```

The shader maps the colors as specified by its color map. The color map is
provided as a list of pixel values with associated colors.
There are three modes of interpolation:

* linear (`Interpolated`): the color is linearly interpolated
  from the color map entries above and below the pixel value
* discrete (`Discrete`): the color is taken from the closest color
  map entry with equal or higher value
* exact (`Exact`): the color is not interpolated, only pixels with
  values equal to color map entries will be drawn

In the second step we will associate this shader with the raster layer:

```python
renderer = QgsSingleBandPseudoColorRenderer(rlayer.dataProvider(), 1, shader)
rlayer.setRenderer(renderer)
```

The number `1` in the code above is the band number (raster bands are
indexed from one).

Finally we have to use the
`triggerRepaint() ` method
to see the results:

```python
rlayer.triggerRepaint()
```

### Multi Band Rasters

By default, QGIS maps the first three bands to red, green and blue to
create a color image (this is the `MultiBandColor` drawing style).
In some cases you might want to override these setting.
The following code interchanges red band (1) and green band (2):

```python
rlayer_multi = QgsProject.instance().mapLayersByName('multiband')[0]
rlayer_multi.renderer().setGreenBand(1)
rlayer_multi.renderer().setRedBand(2)
```

In case only one band is necessary for visualization of the raster,
single band drawing can be chosen, either gray levels or pseudocolor.

We have to use `triggerRepaint() `
to update the map and see the result:

```python
rlayer_multi.triggerRepaint()
```

## Query Values

Raster values can be queried using the
`sample() ` method of
the `QgsRasterDataProvider ` class.
You have to specify a `QgsPointXY `
and the band number of the raster layer you want to query. The method returns a
tuple with the value and `True` or `False` depending on the results:

```python
val, res = rlayer.dataProvider().sample(QgsPointXY(20.50, -34), 1)
```

Another method to query raster values is using the :meth:`identify()
<qgis.core.QgsRasterDataProvider.identify>` method that returns a
`QgsRasterIdentifyResult ` object.

```python
ident = rlayer.dataProvider().identify(QgsPointXY(20.5, -34), QgsRaster.IdentifyFormatValue)

if ident.isValid():
  print(ident.results())
```

In this case, the `results() `
method returns a dictionary, with band indices as keys, and band values as
values.
For instance, something like `{1: 323.0}`

## Editing raster data

You can create a raster layer using the `QgsRasterBlock `
class. For example, to create a 2x2 raster block with one byte per pixel:

```python
block = QgsRasterBlock(Qgis.Byte, 2, 2)
block.setData(b'\xaa\xbb\xcc\xdd')
```

Raster pixels can be overwritten thanks to the :meth:`writeBlock()
<qgis.core.QgsRasterDataProvider.writeBlock>` method.
To overwrite existing raster data at position 0,0 by the 2x2 block:

```python
provider = rlayer.dataProvider()
provider.setEditable(True)
provider.writeBlock(block, 1, 0, 0)
provider.setEditable(False)
```