
# Keras Spatial
Keras Spatial includes data generators and tools designed to simplify 
the preprocessing of spatial data for deep learning applications.

Keras Spatial provides a data generator that reads samples directly
from a raster data source and eliminates the need to create small, 
individual raster files prior to model execution. The raster data 
source may be local or remote service. Any necessary reprojections 
and scaling is handled automatically.

Central to the use of Keras Spatial is a GeoPandas GeoDataFrame which
defines a virtual sample set, a list of samples that drives the data
generator. The dataframe can also be used to filter samples based
on different aspects such as the existance of nodata, handling 
imbalanced label distributions, and storing sample attributes used
in normalization amoung other data augmentation functions.

Features include:
* Sample extraction from local or remote data sources -- no intermediate files
* Automatic reprojection and resampling as needed
* Sample augmentation using user-defined callback system
* Flexible structure improves organization and data management

## Installation
To install the package from PyPi repository you can execute the following command:

```
pip install keras-spatial
```

or directly from GitHub

```
$ pip install git+https://github.com/IllinoisStateGeologicalSurvey/keras-spatial#egg=keras-spatial --process-dependency-links
```

## Quickstart

1. Create a SpatialDataGen and set the source raster
1. Create a geodataframe with 200x200 (in projection units) samples covering the spatial extent of the raster
1. Create the generator producing arrays with shape [32, 128, 128, 1]
1. Fit model

```Python
from keras_spatial.datagen import SpatialDataGenerator

sdg = SpatialDataGenerator(source='/path/to/file.tif')
geodataframe = sdg.regular_grid(200, 200)
generator = sdg.flow_from_dataframe(geodataframe, 128, 128, batch_size=32)
model(generator, ...)
```

## Usage

Keras Spatial provides a SpatialDataGenerator (SDG) modeled on the Keras 
ImageDataGenerator. The SDG allows user to work in spatial coorindates rather
than pixels and easily integrate data from different coordinates systems. 
Reprojection and resampling is handled automatically as needed. Because 
Keras Spatial is based on the rasterio package, raster data source may 
either local files or remote resources referenced by URL.

Because the SDG reads directly from larger raster data sources rather than
small, preprocessed images files, SDG makes use of a GeoDataFrame to identify
each sample area. The geometry associated with the datafame is expected to be
a polygon but extraction is done using a windowed read based on the bounds.
As with the ImageDataGenerator, the flow_from_dataframe method returns the 
generator that can be passed to the Keras model.

### SpatialDataGenerator class

The SDG is similar to the ImageDataGenerator albeit missing the .flow and
the .flow_from_directory methods. SDG also moves more configutation
and setting to the instance and with the .flow_from_dataframe having
few arguments.

##### Arguments

- source (path or url): raster source
- width (int): array size produced by generator
- height (int): array size produced by generator
- indexes (int or tuple of ints): one or more raster bands to sampled
- interleave (str): type of interleave 'band' or 'pixel' (default='pixel')
- resampling (int): One of the values from rasterio.enums.Resampling 
(default=Resampling.nearest)

Raises RasterioIOError when the source is set if the file or remote 
resource is not available.

###### Examples

```Python
from keras_spatial import SpatialDataGenerator

sdg = SpatialDataGenerator(source='/path/to/file.tif')
sdg.width, sdg.height = 128,128
```
The source must be set prior to calling flow_from_dataframe.  Width and 
height are also required but maybe passed as arguments to flow_from_dataframe.

The _indexes_ argument selects bands in a multiband raster. By default 
all bands are read and the _indexes_ argument is updated when the raster 
_source_ is set.

In multiband situations, if _interleave_ is set to 'band' the numpy array axes
are moved to the following order [batch_size, bands, height, width].  This 
can lead to incompatible shapes when using multiple SDG generators -- 
use with care. The default interleave is 'pixel' which is compatible with
Tensorflow.

```Python
# file.tif is a 5 band raster
sdg = SpatialDataGenerator('/path/to/file.tif')
gen = sdg.flow_from_dataframe(df, 128, 128, batch_size=1)
print(next(gen).shape)
> [1, 128, 128, 5]
sdg.interleave = 'band'
gen = sdg.flow_from_dataframe(df, 128, 128, batch_size=1)
print(next(gen.shape))
> [1, 5, 200, 200]
```

Because more than one SDG is expected to be used simultaneously and SDGs 
are expected to having matching spatial requirements, the SDG class 
provides a profile attribute that can be easily share arguments across 
instances as shown below. Note: source is not part of the profile.

```Python
sdg = SpatialDataGenerator(source='/path/to/file.tif')
sdg2 = SpatialDataGenerator()
sdg2.profile = sdg.profile
sdg2.source = '/path/to/file2.tif'
```

### SpatialDataGenerator methods

#### flow_from_dataframe
```Python
flow_from_dataframe(geodataframe, width, height, batch_size)
```

Creates a generator that returns a numpy ndarray of samples read from 
the SDG source.

##### Arguments
- geodataframe (GeoDataFrame): a geodataframe with sample boundaries
- width (int): width of array
- height (int): height of array
- batch_size (int): number of samples to returned by generator

##### Returns

A generator of numpy ndarrays of the shape [batch_size, height, width, bands].

##### Example
```Python
sdg = SpatialDataGenerator(source='/path/to/file.tif')
gen = sdg.flow_from_dataframe(df, 128, 128)
arr = next(gen)
```

#### random_grid
```Python
random_grid(width, height, count, units='native')
```

Creates a geodataframe suitable to passing to the flow_from_dataframe 
method. The grid module provides a similar function using passed using 
spatial extents.

##### Arguments
- width (int): width in pixels
- height (int): height in pixels
- count (int): number of samples
- units (str): units for width and height, either native or in pixels

##### Returns
A GeoDataFrame defining the polygon boundary of each sample.

##### Example
```Python
sdg = SpatialDataGenerator(source='/path/to/file.tif')
df = sdg.random_grid(200, 200, 1000)
```

#### regular_grid
```Python
regular_grid(width, height, overlap=0.0, units='native')
```

Creates a geodataframe suitable to passing to the flow_from_dataframe 
method. The sample module provides a similar function using passed using 
spatial extents.

##### Arguments
- width (int): width in pixels
- height (int): width in pixels
- overlap (float): percentage of overlap (default=0.0)
- units (str): units for width and height, either native or in pixels

##### Returns
A GeoDataFrame defining the polygon boundary of each sample.

##### Example
```Python
sdg = SpatialDataGenerator(source='/path/to/file.tif')
df = sdg.regular_grid(200, 200)
```

## Full Example

```python
from keras_spatial import SpatialDataGenerator
labels = SpatialDataGenerator()
labels.source = '/path/to/labels.tif'
labels.width, labels.height = 128, 128
df = labels.regular_grid(200,200)

samples = SpatialDataGenerator()
samples.source = 'https://server.com/files/data.tif'
samples.width, samples.height = labels.width, label.height

train_gen = zip(labels.flow_from_dataframe(df), patches.flow_from_dataframe(df))
model(train_gen)
```
