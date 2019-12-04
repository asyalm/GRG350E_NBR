#  grg350e_project_code.py
#  this program calculates a burn ratio and image difference for tif files of an area
#
#  Francisco Gavan
#  Bran Heidon
#  Asya Mazmanyan
#
#  GRG 350E Fall 2019
#  Last Mod : 2019/12/3
#
#  sources : https://learn.arcgis.com/en/projects/assess-burn-scars-with-satellite-imagery/lessons/calculate-the-burn-index.htm



import os
import numpy as np
from __future__ import division
import arcpy
from arcpy import env
import csv
import matplotlib.pyplot as plt


#-------------------------------------------------
#  set up env and workspace, return list of targetted files
def Init_Env() : 
    path = 'D:\grg350e_burn\project_code_files'.replace('/', '\\')
    env.workspace = path
    arcpy.CheckOutExtension("Spatial")
    os.chdir(path)
    os.listdir(path)

    file_list = [ f for f in os.listdir(path) if f.endswith(".tif")
                  or f.endswith(".shp") or f.endswith(".csv") ]
    return file_list

#-------------------------------------------------
#  sets the extent with raster input 
def Init_Extent(input_raster) :
    env.extent = input_raster
    env.cellSize = input_raster
    env.outputCoordinateSystem = input_raster
    env.overwriteOutput = True
    
#-------------------------------------------------
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  minor alts-- heading and param finialization
#  initialize csv file
def Init_Csv(csv_out, header) :
    header = ["PATH", "ROW" , "YEAR", "HIGH"]
    with open(csv_out, mode = "wb") as csvfile :
        tabwriter = csv.writer(csvfile, delimiter = ',')
        tabwriter.writerow(header)
        
#-------------------------------------------------
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  minor alts-- param finialization
#  add a row to the csv
def Append_Csv(ba_csv, path, row, year, high, modhigh, modlow) :
    with open(csv_out, mode = "a") as csvfile :
        tabwriter = csv.writer(csvfile, delimiter = ',')
        outRow = ['testyeah', year]
        tabwriter.writerow(outRow)

#-------------------------------------------------
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  minor alts-- x and y labels and param
#  reads csv file into chart
def Csv_Chart(csv_out, title, xlabel, ylabel) :
    x_coor = []
    y_coor = []
    with open(csv_out, mode = "r") as csvfile :
        tabreader = csv.reader(csvfile, delimiter = ',')
        for row in tabreader :
            if not row[1].isalpha() :
                x_coor.append(int(row[1]))
                y_coor.append(float(row[2])) 
    plt.plot(x_coor,y_coor, marker='o')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()

#-------------------------------------------------
#  convert raster to arr; input- raster list , output- array list
def RastArr_Conv(inrast_list) :
    outarr_list = []
    for rast in inrast_list :
        Init_Extent(rast)
        outarr_list.append( arcpy.RasterToNumPyArray(rast, nodata_to_value = -99 ) )
    return outarr_list

#-------------------------------------------------
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  Convert array to a geodatabase raster
def ArrRast_Conv(inarr):
    return arcpy.NumPyArrayToRaster(inarr)

#-------------------------------------------------
#  converts polygon to raster
#  input- polygone shapefile and linking field ,  output - tif raster
def PolyRast_Conv(inpoly, field) : #  maybe outrast name as input
    outrast = 'something.tif'
    arcpy.PolygonToRaster_conversion(inpoly, field, outrast)

#-------------------------------------------------
#  normalized burn ratio 
#  NBR = (Band 5 - Band 7)/(Band 5 + Band 7)
#  input- bands 5 and 7 array files
#  near infrared and shortwave infrared 
#  output- array file
def BurnRatio(b5, b7) :
    b5 = np.add(b5, 1)
    b7 = np.add(b7, 1)
    num = np.subtract(b5,b7)
    den = np.add(b5, b7)
    div = np.true_divide(num, den)
    return div

#-------------------------------------------------
#  image difference / delta NBR
def BurnCompare(yr1, yr2) :
    return np.subtract(yr1, yr2)

#-------------------------------------------------
#  saves a file to the dir
#  should primarily be a tif raster
def SaveFile(outdata, outname) :
    outdata.save(outname)
    print( '{} save completed'.format(outname))

#-------------------------------------------------
    

def main() :
#  get list of desired files
    files = Init_Env()
    print(files)


#  list containing bands for Burn Ratio calc
    bands = [ f for f in files if f.endswith('5.tif')
                   or f.endswith('7.tif') ]
    print(bands)
    print(" bands list length:", len(bands))
    band_name = [f[9:20] for f in bands]
    print(band_name)

    
#  convert tif files to arrays
    bands_arr = RastArr_Conv(bands)
    print(" bands_arr list length:", len(bands_arr))

    
#  calc total area 
    tot_area = float(np.count_nonzero( bands_arr[0] > -1 ) * 900)


#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  initiate csv for individual burn area
    ba_csv = 'burn_area.csv'
    ba_header = ''

#  calculate burn index / individual burned area 
    burn_ind = []
    for r in range(0, len(bands_arr)-1, 2) :
        barr = BurnRatio(bands_arr[r], bands_arr[r+1])
        
        name = band_name[r + 1]
        path = name[0:3]
        row = name[3:6]
        year = name[-4:]
        high = ( np.count_nonzero( 1 >= barr > .6) * 900 ) / tot_area  
        modhigh = ( np.count_nonzero( .6 >= barr > .5) * 900 ) / tot_area
        modlow = ( np.count_nonzero( .5 >= barr > .4) * 900 ) / tot_area
        Append_Csv(ba_csv, path, row, year, high, modhigh, modlow)

        burn_ind.append(barr)
        print(" burn ratio of {} completed:".format(name)) 


    print(" burn ratio len:", len(burn_ind)) 

#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  initiate csv for individual burn area
    bc_csv = 'burncomp_area.csv'
    bc_header = ''
     
#  compare burned areas between years
    burn_comp = []
    for r in range(0, len(burn_ind)-1) :
        bcomp = BurnCompare(burn_ind[r], burn_ind[r+1])
#  could be optimized but nah
        name = band_name[r + 3]
        path = name[0:3]
        row = name[3:6]
        year = '201819' 
        high = ( np.count_nonzero( 1.5 >= barr > .6) * 900 ) / tot_area  
        modhigh = ( np.count_nonzero( .6 >= barr > .3) * 900 ) / tot_area
        modlow = ( np.count_nonzero( .3 >= barr > .4) * 900 ) / tot_area
        Append_Csv(bc_csv, path, row, year, high, modhigh, modlow)

        burn_comp.append(bcomp)
        print(" burn comparison of {} completed:".format(name + '19')) 



#  need to reconvert back to a raster
    ind = 0
    for r in burn_comp :
        arrast = ArrRast_Conv(r)
        comp_name = 'burnchange_{}{}.tif'.format(band_name[ind],band_name[ind+2] )
        SaveFile(arrast, comp_name )
        ind += 1

        
#&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  csv stuff
#  reading in precip data and outputting into chart
    csv_files = [ f for f in files if f.endswith('.csv') ]
    for c in csv_files :
        Csv_Chart(c , )


#  do shapefile cut/clip?

main()


