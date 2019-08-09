
# Keras Spatial
Keras Spatial includes data generators and utilities designed to simplify 
working with spatial data.

Keras Spatial provides a data generator based on a raster file. The 
generator reads directly from this source and eliminates the need to
create small raster files in heirarchical directory structure. The
raster file may reside locally or remotely. Any necessary reprojections
and scaling is handled automatically.

Additional gridding utilties are available to assist in the creation of a dataframes 
based on the spatial extent of a raster and number of desired samples.

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

1. Create a SpatialDataGen that will create 200, 200 pixel samples from TIF
1. Create a 10,000 element geodataframe covering the spatial extent of the raster
1. Create the generator
1. Fit model

```Python
from keras_spatial.datagen import SpatialDataGenerator

sdg = SpatialDataGenerator(200,200, source='/path/to/file.tif')
geodataframe = sdg.regular_grid(.01, .01)
generator = sdg.flow_from_dataframe(geodataframe)
model.fit_generator(generator, ...)
```

## Usage

Keras Spatial provides a SpatialDataGenerator (SDG) modeled on the Keras 
ImageDataGenerator. The SDG allows user to work in spatial coorindates rather
than pixels and easily integrate data from different coordinates systems. Reprojection
and resampling is handled automatically as needed. Because Keras Spatial is based
on the rasterio package, raster data source may either local files or remote 
resources referenced by URL.

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

- width (int): sample width in pixels 
- height (int): sample height in pixels
- source (path or url): raster source
- indexes (int or sequence of ints): one or more raster bands to sampled
- crs (CRS): the desired coordinate reference system if different from source
- interleave (str): type of interleave 'band' or 'pixel'
- resampling (int): One of the values from rasterio.enums.Resampling 
(default=Resampling.nearest)
- preprocess (function): callback function invoked on the numpy array prior
to returning it to the model

Raises RasterioIOError when the source is set if the file or resource is not 
available.

###### Examples

```Python
from keras_spatial import SpatialDataGenerator
sdg = SpatialDataGenerator()
sdg.height, sdg.width = 200,200
sdg.source = '/path/to/file.tif'
```
The height, width, and source arguments are required prior calling 
flow_from_dataframe. This can be done in several equivalent ways as shown below.

```Python
sdg1 = SpatialDataGenerator(200,200)
sdg1.source = '/path/to/file.tif'
sdg2 = SpatialDataGenerator(200,200, source='/path/to/file.tif')
```

The _indexes_ argument selects bands in a multiband raster. By default all bands
are read and the _indexes_ argument is updated when the raster _source_ is set.

If _interleave_ is set to 'pixel' and more than one band is read (based on _indexes_),
the numpy array axes are moved. This can lead to incompatible shapes when using
multiple SDG generators -- use with care.

```Python
sdg = SpatialDataGenerator(200,200, '/path/to/file.tif')
gen = sdg.flow_from_dataframe(df, batch_size=1)
print(next(gen).shape)
> [1, 5, 200, 200]
sdg.interleave = 'pixel'
gen = sdg.flow_from_dataframe(df, batch_size=1)
print(next(gen.shape))
> [1, 200, 200, 5]
```

Because more than one SDG is expected to be used simultaneously and SDGs are expected
to having matching spatial requirements, the SDG class provides a profile attribute
that can be easily share arguments across instances as shown below. Note: source is not
part of the profile.

```Python
sdg = SpatialDataGenerator(200,200, source='/path/to/file.tif')
sdg2 = SpatialDataGenerator()
sdg2.profile = sdg.profile
sdg2.source = '/path/to/file2.tif'
```

### SpatialDataGenerator methods

#### flow_from_dataframe
```Python
flow_from_dataframe(geodataframe, batch_size)
```

Creates a generator that returns a numpy ndarray of samples read from the SDG source.

##### Arguments
- geodataframe (GeoDataFrame): a geodataframe with sample boundaries
- batch_size (int): number of samples to returned by generator

##### Returns

A generator of numpy ndarrays

##### Example
```Python
sdg = SpatialDataGenerator(200, 200, source='/path/to/file.tif')
gen = sdg.flow_from_dataframe(df)
```

#### random_grid
```Python
random_grid(pct_width, pct_height, count)
```

Creates a geodataframe suitable to passing to the flow_from_dataframe method. The
sample module provides a similar function using passed using spatial extents.

##### Arguments
- pct_width (float): percentage of raster width
- pct_height (float): percentage of raster height
- count (int): number of samples

##### Returns
A GeoDataFrame defining a polygon around each sample.

##### Example
```Python
sdg = SpatialDataGenerator(source='/path/to/file.tif')
df = sdg.random_grid(0.01, 0.01, 1000)
```

#### regular_grid
```Python
regular_grid(pct_width, pct_height, overlap)
```

Creates a geodataframe suitable to passing to the flow_from_dataframe method. The
sample module provides a similar function using passed using spatial extents.

##### Arguments
- pct_width (float): percentage of raster width
- pct_height (float): percentage of raster height
- overlap (float): percentage of overlap (default=0.0)

##### Returns
A GeoDataFrame defining a polygon around each sample.

##### Example
```Python
sdg = SpatialDataGenerator(source='/path/to/file.tif')
df = sdg.regular_grid(0.01, 0.01)
```

## Full Example


```python
from keras_spatial import SpatialDataGenerator
labels = SpatialDataGenerator(200,200)
labels.source = '/path/to/labels.tif'
df = labels.regular_grid(0.01, 0.01)

patches = SpatialDataGenerator(200,200)
patches.source = 'https://server.com/files/data.tif'
patches.crs = labels.crs

train_gen = zip(labels.flow_from_dataframe(df), patches.flow_from_dataframe(df))
model(train_gen)


```
