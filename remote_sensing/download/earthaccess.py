""" Methods related to EarthAccess API for remote sensing data access """

import earthaccess
import numpy as np

import pandas

from shapely.geometry import Polygon, Point
from shapely.ops import orient

def fix_antimeridian_polygon(coords):
    """Fix polygon that crosses the antimeridian by adjusting longitudes"""
    fixed_coords = []
    
    for i, (lon, lat) in enumerate(coords):
        if i > 0:
            prev_lon = fixed_coords[-1][0]
            
            # If longitude jump > 180°, we likely crossed antimeridian
            if abs(lon - prev_lon) > 180:
                if lon > 0 and prev_lon < 0:
                    # Crossing from negative to positive - subtract 360 from positive
                    lon = lon - 360
                elif lon < 0 and prev_lon > 0:
                    # Crossing from positive to negative - add 360 to negative
                    lon = lon + 360
                    
        fixed_coords.append((lon, lat))
    
    return fixed_coords


def extract_spatial_extent(granule:earthaccess.results.DataGranule|dict):
    """
    Extract spatial extent information from an earthaccess DataGranule object.
    
    Parameters:
    -----------
    granule : earthaccess.results.DataGranule or dict
        The granule object to extract spatial extent from
        
    Returns:
    --------
    dict : Dictionary containing extracted spatial information
    """
    spatial_info = {
        'bounding_rectangles': [],
        'gpolygons': [],
        'points': [],
        'lines': []
    }
    
    # Check if spatial extent exists
    if 'SpatialExtent' not in granule.get('umm', {}):
        print("No spatial extent found in granule metadata")
        return spatial_info
    
    spatial_extent = granule['umm']['SpatialExtent']
    
    # Extract horizontal spatial domain
    if 'HorizontalSpatialDomain' in spatial_extent:
        horizontal_domain = spatial_extent['HorizontalSpatialDomain']
        
        if 'Geometry' in horizontal_domain:
            geometry = horizontal_domain['Geometry']
            
            # Extract GPolygons
            if 'GPolygons' in geometry:
                for gpolygon in geometry['GPolygons']:
                    polygon_info = {
                        'boundary_points': [],
                        'exclusive_zones': []
                    }
                    
                    # Extract boundary points
                    if 'Boundary' in gpolygon:
                        boundary = gpolygon['Boundary']
                        if 'Points' in boundary:
                            points = [(point['Longitude'], point['Latitude']) 
                                    for point in boundary['Points']]
                            polygon_info['boundary_points'] = points
                    
                    # Extract exclusive zones (holes)
                    if 'ExclusiveZone' in gpolygon:
                        if 'Boundaries' in gpolygon['ExclusiveZone']:
                            for boundary in gpolygon['ExclusiveZone']['Boundaries']:
                                if 'Points' in boundary:
                                    hole_points = [(point['Longitude'], point['Latitude']) 
                                                 for point in boundary['Points']]
                                    polygon_info['exclusive_zones'].append(hole_points)
                    
                    spatial_info['gpolygons'].append(polygon_info)
            
            # Extract BoundingRectangles
            if 'BoundingRectangles' in geometry:
                for rect in geometry['BoundingRectangles']:
                    spatial_info['bounding_rectangles'].append({
                        'west': rect.get('WestBoundingCoordinate'),
                        'east': rect.get('EastBoundingCoordinate'), 
                        'north': rect.get('NorthBoundingCoordinate'),
                        'south': rect.get('SouthBoundingCoordinate')
                    })
            
            # Extract Points
            if 'Points' in geometry:
                for point in geometry['Points']:
                    spatial_info['points'].append((
                        point['Longitude'], 
                        point['Latitude']
                    ))
            
            # Extract Lines
            if 'Lines' in geometry:
                for line in geometry['Lines']:
                    if 'Points' in line:
                        line_points = [(point['Longitude'], point['Latitude']) 
                                     for point in line['Points']]
                        spatial_info['lines'].append(line_points)
    
    return spatial_info

def create_shapely_geometries(spatial_info, fix_antimeridian:bool=False):
    """
    Convert spatial extent information to Shapely geometry objects.
    
    Parameters:
    -----------
    spatial_info : dict
        Spatial information dictionary from extract_spatial_extent
        
    Returns:
    --------
    dict : Dictionary containing Shapely geometry objects
    """
    geometries = {
        'polygons': [],
        'rectangles': [],
        'points': [],
        'lines': []
    }
    
    # Convert GPolygons to Shapely Polygons
    for gpolygon in spatial_info['gpolygons']:
        if gpolygon['boundary_points']:
            # Create exterior ring
            exterior = gpolygon['boundary_points']

            # Fix antimeridian crossing if required
            if fix_antimeridian:
                exterior = fix_antimeridian_polygon(exterior)
            
            # Create holes (exclusive zones)
            holes = gpolygon['exclusive_zones'] if gpolygon['exclusive_zones'] else None
            
            try:
                # Ensure proper orientation (counter-clockwise for exterior)
                polygon = Polygon(exterior, holes=holes)
                # Orient exterior counter-clockwise, holes clockwise
                oriented_polygon = orient(polygon)
                geometries['polygons'].append(oriented_polygon)
            except Exception as e:
                print(f"Error creating polygon: {e}")
    
    # Convert BoundingRectangles to Shapely Polygons
    for rect in spatial_info['bounding_rectangles']:
        if all(coord is not None for coord in [rect['west'], rect['east'], 
                                              rect['north'], rect['south']]):
            # Create rectangle coordinates (counter-clockwise)
            rect_coords = [
                (rect['west'], rect['south']),   # SW
                (rect['east'], rect['south']),   # SE  
                (rect['east'], rect['north']),   # NE
                (rect['west'], rect['north']),   # NW
                (rect['west'], rect['south'])    # Close
            ]
            geometries['rectangles'].append(Polygon(rect_coords))
    
    # Convert Points to Shapely Points
    for point in spatial_info['points']:
        geometries['points'].append(Point(point))
    
    # Convert Lines to Shapely LineStrings
    from shapely.geometry import LineString
    for line in spatial_info['lines']:
        if len(line) >= 2:
            geometries['lines'].append(LineString(line))
    
    return geometries

def extract_temporal_extent(granule:earthaccess.results.DataGranule|dict):
    tstart = granule['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime']
    tend = granule['umm']['TemporalExtent']['RangeDateTime']['EndingDateTime']
#
    # Return
    return tstart, tend

def granules_to_dict(granules:list):

    # Generate a dict
    full_dict = {}
    for iresult in granules:
        key = iresult['meta']['native-id']
        #
        full_dict[key] = {}
        for ikey in ['meta', 'umm']:
            full_dict[key][ikey] = iresult[ikey]

    # Return
    return full_dict

def build_granule_table(granules:dict, fix_antimeridian:bool=False):

    # Generate a table of interesting bits and pieces
    df = pandas.DataFrame()
    df['id'] = list(granules.keys())

    polygons = []
    tstarts, tends = [], []
    urls, ccs = [], []
    # Loop on granules
    for key in granules.keys():
        granule = granules[key]
        # Polygon
        spt = extract_spatial_extent(granule)
        dshap = create_shapely_geometries(spt, fix_antimeridian=fix_antimeridian)
        polygons.append(dshap['polygons'][0] if dshap['polygons'] else None)

        # Time
        tstart, tend = extract_temporal_extent(granule)
        tstarts.append(tstart)
        tends.append(tend)

        # Cloud cover
        cc = granule['umm']['CloudCover']
        ccs.append(cc)

        # Data file URL
        assert granule['umm']['RelatedUrls'][1]['Type'] == 'GET DATA'
        url = granule['umm']['RelatedUrls'][1]['URL']
        urls.append(url)

    # Add polygons to DataFrame
    df['polygon'] = polygons
    #df['polygon'] = df['polygon'].apply(lambda x: x.wkt if x else None)

    # Time
    tstart = pandas.to_datetime(tstarts)
    tend = pandas.to_datetime(tends)
    tmid = tstart + (tend-tstart) / 2
    df['time'] = tmid

    # Cloud cover
    df['CC'] = ccs

    # URL
    df['url'] = urls

    return df
