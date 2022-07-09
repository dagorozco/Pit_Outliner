# **Pit Outliner**

This repository containt the code used for delineating a the footprint of an open pit based on strip ratio and
a given pit slope.

## Background

The code was written in Python, and the workflow takes the advantage of using processing algoriths from QGIS.
SQLite was also used for creating the drillhole database.

Moreover, the script produces a shapefile that can be imported into mining software for DTM creation and to
prepare volumetrics reports.

## Rationale

Objective is to create, in a relatively quick manner, an open pit footprint using a threshold based on strip ratio (SR)
and an user defined pit slope. The ultimate pit would result in a SR higher than the chosen threshold because it would
consider that the pit needs to be projected above the highest collar elevation.

The code defines the crest and toe of the entire pit, however no benches are included in the design. The reason for no
adding benches is that those are not neccesary for the particular deposit the data comes from (clay deposit), which
usually is a shallow operation.

## How the code works

1. It assumess drilling data is in csv format
2. Digest csv into SQLite DB, creates a lenght column in the lithology table. 
3. Using the lenght column create new tables of aggregate data, one for the overburden unit and the second for the ore unit. 
4. The tables created in step 3 are exported as csv in order to be read in QGIS as point files.
5. Create rasters for overburden and ore unit using point files.
6. Create a SR raster by overbruden and clay rasters.
7. Create contours from the SR raster,
8. Extract the contour that correspond to the desired SR.
9. Expand the extracted contour based on slope and maximum elevation from the drillholes.
10. Calculate the elevations for the crest and toe and update attribute tables.

## Lesson Learned

This script can be improved by creating some functions for repetitive lines. Additionally, no try, except statements
to deal with potential errors was included in the code.

Another improvement is to use a spatial database instead of exporting csv files from the SQLite database to be used
in QGIS.

## Future use of the code

Some mining companies (aggregates, industrial minerals) usually deal with the challenge of mining several pits at once in
a distric scale. If the drilling data is stored in a single database, and by adding some loops into the code, the ultimate
pit footprints could be generated relatively quick and assess how the pit interacts with property lines, environmental
polygons, infrastructure, etc. The last assumes the user have this information on hand and in a format that can be open
in QGIS.

The code has the potential to create two pits, one that sticks to the chosen strip ratio or a less conservative that would
yield more ore but also more overburden.
