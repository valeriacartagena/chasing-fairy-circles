import ee
import pandas as pd

ee.Authenticate()
ee.Initialize(project='project id here') # I will not share my project ID publicly!

def extract_gee_data(lat, lon, loc_name,start_date, end_date,size_km=20):
    center = ee.Geometry.Point([lon, lat])
    region = center.buffer(size_km * 500).bounds()

    # Dataset 1: Harmonized Sentinel-2 MSI: MultiSpectral Instrument, Level-2A (SR) #########################################
    spectral = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(region)
                .filterDate(start_date, end_date)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .median())
    
    # Bands (colors) for FCs: Red, NIR, SWOIR1, SWIR2
    spectral_bands = ['B2','B8', 'B11', 'B12']

    # Calculations
    ndvi = spectral.normalizedDifference(['B8', 'B4']).rename('current_NDVI') # NDVI = Normalized Difference Vegetation Index
    brightness = spectral.expression('(B4 + B8) / 2',
        {'B4': spectral.select('B4'), 'B8': spectral.select('B8')}
    ).rename('brightness')

    # Dataset 2: NASA SRTM Digital Elevation 30m #########################################
    elevation = (ee.Image("USGS/SRTMGL1_003")
                 .select('elevation')
                 .clip(region))
    slope = ee.Terrain.slope(elevation).rename('slope')
    aspect = ee.Terrain.aspect(elevation).rename('aspect')

    # Topograhic Position Index (TPI)
    mean_elevation = elevation.reduceNeighborhood(
        reducer=ee.Reducer.mean(),
        kernel=ee.Kernel.circle(radius=500, units='meters')
    )
    tpi = elevation.subtract(mean_elevation).rename('TPI')

    # Dataset 3: USGS Landsat 8 Level 2, Collection 2, Tier 1 #########################################
    def add_ndvi_landsat(image):
        ndvi_landsat = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI_Landsat')
        return image.addBands(ndvi_landsat)
    
    temporal = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                .filterBounds(region)
                .filterDate('2015-01-01', '2024-12-31')
                .filter(ee.Filter.lt('CLOUD_COVER', 20))
                .map(add_ndvi_landsat))
    ndvi_landsat_mean = temporal.select('NDVI_Landsat').mean().rename('NDVI_Landsat_mean')
    ndvi_landsat_std = temporal.select('NDVI_Landsat').reduce(ee.Reducer.stdDev()).rename('NDVI_Landsat_std')

    # Edge detection
    ndvi_texture = ndvi.reduceNeighborhood(
        reducer=ee.Reducer.stdDev(),
        kernel=ee.Kernel.square(3)
    ).rename('NDVI_texture')

    # Combine all features into a single image
    feature_image = ee.Image.cat([
        spectral.select('B4').rename('Red'),
        spectral.select('B8').rename('NIR'),
        spectral.select('B11').rename('SWOIR1'),
        spectral.select('B12').rename('SWOIR2'),
        ndvi,
        brightness,
        ndvi_texture,
        elevation,
        slope,
        aspect,
        tpi,
        ndvi_landsat_mean,
        ndvi_landsat_std
    ])

    scale = 2000
    samples = feature_image.sample(
        region=region,
        scale=scale,
        geometries=True,
        seed=42
    )

    features_list = samples.getInfo()['features']
    features_array = []
    for feature in features_list:
        coords = feature['geometry']['coordinates']
        props = feature['properties']
        features_array.append({
            'location': loc_name,
            'longitude': coords[0],
            'latitude': coords[1],
            **props
        })
    df = pd.DataFrame(features_array)
    return df


# Time range for data extraction
start_date = '2023-05-01'
end_date = '2024-09-30'

# Extracting data
locations = [
    # Namibia
    (-24.953, 15.978, 'namibia'),
    
    # Australia
    (-23.38, 119.89, 'australia'),
    
    # Mali
    (13.194, -6.242, 'mali'),
]

all_data = []
for lat, lon, loc_name in locations:
    df = extract_gee_data(lat, lon, loc_name, size_km=20, start_date=start_date, end_date=end_date)
    all_data.append(df)

if all_data:
    df_final = pd.concat(all_data, ignore_index=True)
    df_final.to_csv('gee_extracted_data.csv', index=False)