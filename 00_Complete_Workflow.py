# Import all libraries needed
import csv
import math
import os
import processing
import sqlite3 as sql
from processing.core.Processing import Processing
from qgis.core import (QgsApplication, QgsProcessingFeedback, QgsVectorLayer)


# Create functions for clean code
def add_layer(lyrName, name_to_display):
	"""Function to add the layer into Map Canvas"""
	layer_name = lyrName
	name_on_screen = name_to_display
	layer = QgsVectorLayer(layer_name, name_on_screen, "ogr")
	if not layer.isValid():
		print("Layer failed to load")
	else:
		QgsProject.instance().addMapLayer(layer)

# CSV Preparation before raster creation
# Path to files
db_path = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/ddh.db"
collar_path = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/collar.csv"
lithology_path = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/lithology.csv"
ob_csv = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/ob_thickness.csv"
clay_csv = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/clay_thickness.csv"

# Create database in folder
con = sql.connect(db_path)

# Create collar and lithology tables in database
con = sql.connect(db_path)
cur = con.cursor()
table_collar = "CREATE TABLE collar(hole_id, drillcode, drilldate, x, y, z, max_depth, holetype, result)"
cur.execute(table_collar)
table_litho = "CREATE TABLE lithology(drillcode, hole_id, depth_from, depth_to, stratigraphy,lithology, drop1, drop2, drop3, drop4, drop5)"
cur.execute(table_litho)
con.commit()
con.close()

# Import csvs into database
con = sql.connect(db_path)
cur = con.cursor()
collar = open(collar_path)
contents_collar = csv.reader(collar)
insert_collar = "INSERT INTO collar(hole_id, drillcode, drilldate, x, y, z, max_depth, holetype, result) VALUES(?,?,?,?,?,?,?,?,?)"
cur.executemany(insert_collar, contents_collar)
con.commit()
con.close()

con = sql.connect(db_path)
cur = con.cursor()
litho = open(lithology_path)
contents_litho = csv.reader(litho)
insert_litho = "INSERT INTO lithology(drillcode, hole_id, depth_from, depth_to, stratigraphy, lithology, drop1, drop2, drop3, drop4, drop5) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
cur.executemany(insert_litho, contents_litho)
con.commit()
con.close()

# Delete first row for collar and litho tables which contains the headers
con = sql.connect(db_path)
cur = con.cursor()
cur.execute("DELETE FROM collar WHERE hole_id LIKE 'hole_id'")
cur.execute("DELETE FROM lithology WHERE hole_id LIKE 'hole_id'")
con.commit()
con.close()

# Add a column called lenght in the lithology table which is going to the be the difference between depth_to - depth_from
con = sql.connect(db_path)
cur = con.cursor()
cur.execute("ALTER TABLE lithology ADD COLUMN lenght REAL")
cur.execute("UPDATE lithology SET lenght = depth_to - depth_from")
con.commit()
con.close()


# Create a table of aggregate ob thickness per drillhole
con = sql.connect(db_path)
cur = con.cursor()
ob_table = "CREATE TABLE ob_thick AS SELECT hole_id, SUM(lenght) AS ob_thick FROM lithology WHERE stratigraphy LIKE '%ov%' GROUP BY hole_id "
cur.execute(ob_table)
con.commit()
con.close()

# Add coordinates to ob_thick table
con = sql.connect(db_path)
cur = con.cursor()
cur.execute("ALTER TABLE ob_thick ADD COLUMN x REAL")
cur.execute("ALTER TABLE ob_thick ADD COLUMN y REAL")
con.commit()
con.close()

con = sql.connect(db_path)
cur = con.cursor()
cur.execute("UPDATE ob_thick SET x = (SELECT x FROM collar WHERE hole_id = ob_thick.hole_id)")
cur.execute("UPDATE ob_thick SET y = (SELECT y FROM collar WHERE hole_id = ob_thick.hole_id)")
con.commit()
con.close()

# Create table of aggregate clay thickness per drillhole
con = sql.connect(db_path)
cur = con.cursor()
ob_table = "CREATE TABLE clay_thick AS SELECT hole_id, SUM(lenght) AS clay_thick FROM lithology WHERE stratigraphy LIKE '%cl%' GROUP BY hole_id "
cur.execute(ob_table)
con.commit()
con.close()


# Add columns and update accordingly
con = sql.connect(db_path)
cur = con.cursor()
cur.execute("ALTER TABLE clay_thick ADD COLUMN x REAL")
cur.execute("ALTER TABLE clay_thick ADD COLUMN y REAL")
cur.execute("UPDATE clay_thick SET x = (SELECT x FROM collar WHERE hole_id = clay_thick.hole_id)")
cur.execute("UPDATE clay_thick SET y = (SELECT y FROM collar WHERE hole_id = clay_thick.hole_id)")
con.commit()
con.close()

# Export data to csv
con = sql.connect(db_path)
cur = con.cursor()
ob_data = cur.execute("SELECT * FROM ob_thick")
with open(ob_csv, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['hole_id', 'ob_thick', 'x', 'y'])
    writer.writerows(ob_data)
con.close()

con = sql.connect(db_path)
cur = con.cursor()
clay_data = cur.execute("SELECT * FROM clay_thick")
with open(clay_csv, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['hole_id', 'clay_thick', 'x', 'y'])
    writer.writerows(clay_data)
con.close()

# Commences QGIS steps by setting the files
ob = "file:///Users/dagoorozcoquintana/Documents/Pit_Outliner/ob_thickness.csv?delimiter={}&xField={}&yField={}&crs=esri:103262".format(",", "x", "y")
ob_shp = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/ob_points.shp"
ob_shp_for_int = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/ob_points.shp::~::0::~::1::~::0"
ob_thickness_int = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/ob_idw.tif"
clay = clay = "file:///Users/dagoorozcoquintana/Documents/Pit_Outliner/clay_thickness.csv?delimiter={}&xField={}&yField={}&crs=esri:103262".format(",", "x", "y")
clay_shp = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/clay_points.shp"
clay_shp_for_int = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/clay_points.shp::~::0::~::1::~::0"
clay_thickness_int = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/clay_idw.tif"

# create ob raster
ob_import = QgsVectorLayer(ob, 'ob_thickness', 'delimitedtext')
# Convert from csv to shp
QgsVectorFileWriter.writeAsVectorFormat(ob_import, ob_shp, "UTF-8", ob_import.crs(), "ESRI Shapefile")
ob_points_lyr = QgsVectorLayer(ob_shp, 'ob points', 'ogr')
QgsProject.instance().addMapLayer(ob_points_lyr)
# Create raster from previously imported shp
layer = iface.activeLayer()
ext = layer.extent()
# This can be improvied by getting the extend from the drill data using the example in the post I saved at GIS Stack Exchange
# or by running the interpolator and understanding how to properly set the extend.
# Actually the extent next to come from SQLite because I want to add some feet but I will improve that portion later
processing.run("qgis:idwinterpolation", {'INTERPOLATION_DATA':ob_shp_for_int,'DISTANCE_COEFFICIENT':2, 'EXTENT': ext, 'PIXEL_SIZE':1.3, 'OUTPUT':ob_thickness_int} )
ob_raster = iface.addRasterLayer(ob_thickness_int, "OB IDW INTERPOLATED")

# Create clay raster
clay_import = QgsVectorLayer(clay, 'clay_thickness', 'delimitedtext')
QgsVectorFileWriter.writeAsVectorFormat(clay_import, clay_shp, "UTF-8", clay_import.crs(), "ESRI Shapefile")
clay_points_lyr = QgsVectorLayer(clay_shp, 'clay points', 'ogr')
QgsProject.instance().addMapLayer(clay_points_lyr)
processing.run("qgis:idwinterpolation", {'INTERPOLATION_DATA':clay_shp_for_int,'DISTANCE_COEFFICIENT':2, 'EXTENT': ext, 'PIXEL_SIZE':1.3, 'OUTPUT':clay_thickness_int} )
clay_raster = iface.addRasterLayer(clay_thickness_int, "Clay IDW INTERPOLATED")

# Create the SR raster by using the raster calculator and dividing the OB and Clay rasters
ob_lyr = QgsRasterLayer("/Users/dagoorozcoquintana/Documents/Pit_Outliner/ob_idw.tif")
clay_lyr = QgsRasterLayer("/Users/dagoorozcoquintana/Documents/Pit_Outliner/clay_idw.tif")
sr_output = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/strip_ratio.tif"
sr_countours = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/strip_ratio.shp"
entries = []
ob_ras = QgsRasterCalculatorEntry()
ob_ras.ref = 'ob_thickness@1'
ob_ras.raster = ob_lyr
ob_ras.bandNumber = 1
entries.append(ob_ras)
clay_ras = QgsRasterCalculatorEntry()
clay_ras.ref = 'clay_thickness@1'
clay_ras.raster = clay_lyr
clay_ras.bandNumber = 1
entries.append(clay_ras)
calc = QgsRasterCalculator('ob_thickness@1 / clay_thickness@1', sr_output, 'GTiff', \
							ob_lyr.extent(), ob_lyr.width(), ob_lyr.height(), entries)
calc.processCalculation()

# Add raster into Project window and change color
sr_lyr = iface.addRasterLayer(sr_output, 'strip ratio')
stats = sr_lyr.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
min_val = stats.minimumValue
max_val = stats.maximumValue
rnge = max_val-min_val
add = rnge//2
interval = min_val + add
colDic = {'red':'#ff0000', 'yellow':'#ffff00', 'blue':'#0000ff'}
fnc = QgsColorRampShader()
fnc.setColorRampType(QgsColorRampShader.Interpolated)
lst = [QgsColorRampShader.ColorRampItem(min_val, QColor(colDic['blue']), f"{min_val}"), \
		QgsColorRampShader.ColorRampItem(interval, QColor(colDic['yellow'])), \
		QgsColorRampShader.ColorRampItem(max_val, QColor(colDic['red']), f"{max_val}")]
fnc.setColorRampItemList(lst)
shader = QgsRasterShader()
shader.setRasterShaderFunction(fnc)
renderer = QgsSingleBandPseudoColorRenderer(sr_lyr.dataProvider(), 1, shader)
sr_lyr.setRenderer(renderer)
sr_lyr.triggerRepaint()


# Creating contours for strip ratio raster
processing.run("gdal:contour", {'INPUT':sr_output, 'BAND': 1, 'INTERVAL':1, 'FIELD_NAME':"sr", 'OUTPUT': sr_countours})
add_layer(sr_countours, "strip ratio contours")

# Extract SR value 4
optimal_sr = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/strip_ratio_equals_4.shp"
processing.run("qgis:extractbyattribute", {'INPUT':sr_countours, 'FIELD':'sr', 'OPERATOR':0, 'VALUE':4, 'OUTPUT':optimal_sr})
add_layer(optimal_sr, "optimal strip ratio")

# Creating buffer
# In order to create a 3D shp that can be imported into Surpac I need to
# 1. Extract the polyline/perimeter of the buffer using processing.run(native:polygonstolines, {parameters})
# 2. Add a field to the perimeter with z value
# 3. Copy the SR shp/line into the perimeter defined in 3 and add the z value
# 4. Repeat for pit option 2.

# Calculate distance for the buffer from the database
# Get max elevation from collar
con = sql.connect(db_path)
cur = con.cursor()
cur.execute("SELECT max(z) FROM collar")
max_z = cur.fetchone()[0]
con.commit()
con.close()
print(max_z)
max_z_collar = float(max_z)
# Modify database to extract the minimum z value for any clay intercept
con = sql.connect(db_path)
cur = con.cursor()
cur.execute("ALTER TABLE lithology ADD COLUMN z REAL")
cur.execute("ALTER TABLE lithology ADD COLUMN clay_base_elevation REAL")
cur.execute("UPDATE lithology SET z = (SELECT z FROM collar WHERE hole_id = lithology.hole_id)")
cur.execute("UPDATE lithology SET clay_base_elevation = z - depth_to - lenght")
cur.execute("SELECT min(z) FROM lithology WHERE stratigraphy LIKE '%cl%' ")
min_z = cur.fetchone()[0]
con.commit()
con.close()
print(min_z)
z_clay = float(min_z)
# formula for buffer assuming a pit angle of 35 degrees
pit_angle = 35
angle = math.radians(pit_angle)
elevation_difference = max_z_collar - z_clay
buffer = elevation_difference/math.tan(angle)
negative_buffer = buffer * -1
print(buffer)
print(negative_buffer)

pit_option1 = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/pit_option1.shp"
pit_option2 = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/pit_option2.shp"
processing.run("native:buffer", {'INPUT':optimal_sr, "DISTANCE":buffer, "DISSOLVE":"TRUE", "OUTPUT":pit_option1})
processing.run("native:buffer", {'INPUT':optimal_sr, "DISTANCE":negative_buffer, "DISSOLVE":"TRUE", "OUTPUT":pit_option2})
pit_option1_layer = QgsVectorLayer(pit_option1, "pit_option1", "ogr")

# Add layers to map canvas
add_layer(pit_option1, "pit option 1")
add_layer(pit_option2, "pit option 2")

# Extract outline of buffer and add new field
pit1_cleaned = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/pit_option1_cleaned.shp"
pit1_outline = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/pit_option1_outline.shp"
pit1_crest = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/pit_option1_crest.shp"
optimal_sr_with_elevation = "/Users/dagoorozcoquintana/Documents/Pit_Outliner/strip_ratio_with_z_value.shp"

# Clean holes in the buffer
processing.run("native:deleteholes", {'INPUT':pit_option1, 'OUTPUT':pit1_cleaned})
# Extract perimeter line
processing.run("native:polygonstolines", {'INPUT':pit1_cleaned, 'OUTPUT': pit1_outline})
# Add field to pit1 outline
processing.run("native:addfieldtoattributestable", {'INPUT':pit1_outline, 'FIELD_NAME':'z', 'FIELD_TYPE':1, 'OUTPUT':pit1_crest})
# Add layer to map view
add_layer(pit1_crest, "pit option 1 design")
# Update z value for the crest
lyr_to_update = QgsVectorLayer(pit1_crest, "pit option 1 crest", "ogr")
attr_value = {2:max_z_collar}
lyr_to_update.dataProvider().changeAttributeValues({0:attr_value})

# Add z field to optimal SR and update z value
processing.run("native:addfieldtoattributestable", {'INPUT':optimal_sr, 'FIELD_NAME':'z', 'FIELD_TYPE':1, 'OUTPUT': optimal_sr_with_elevation })
# Update z value for the sr
sr_lyr_z_update = QgsVectorLayer(optimal_sr_with_elevation, 'sr with elevation', 'ogr')
features = sr_lyr_z_update.getFeatures()
for f in features:
	id = f.id()
	z_value = {2:z_clay} 
	sr_lyr_z_update.dataProvider().changeAttributeValues({id:z_value})
add_layer(optimal_sr_with_elevation, "optimal sr with elevation")

# Copy features from optimal sr with elevation to pit option 1 design
polylines = []
for poly in sr_lyr_z_update.getFeatures():
	polylines.append(poly)
lyr_to_update.startEditing()
lyr_to_update.dataProvider().addFeatures(polylines)
lyr_to_update.commitChanges()

# Extract points for pit option 1 design in order to have a shpfile that can be imported
# with 3D features (z) into Surpac and create a proper dtm
pit1_points =  "/Users/dagoorozcoquintana/Documents/Pit_Outliner/pit_option1_points.shp"
# Get the points from the pit
processing.run("native:extractvertices", {'INPUT':pit1_crest, 'OUTPUT':pit1_points})
add_layer(pit1_points, "Pit 1 Design Points")


# delete ddh database
os.remove(db_path)
