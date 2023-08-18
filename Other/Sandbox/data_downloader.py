import os.path
from re import S 
import webbrowser
import shutil
import pandas as pd
import numpy
import gzip
import time
import csv

# SET THE FOLLOWING:

# Filepath of your working folder
file_path = 'C:/devel/community-thermal-resilience/Paper 1'

# Filepath to your data folder
model_folder = file_path + "/Models/"
schedule_folder = file_path + "/Schedule Files/"

#Filepath of your downloads folder
download_folder = "C:/Users/govertsen.k/Downloads/"

#The City of Worcester's PUMA Code is G25000300. Change this if you are using another PUMA.(https://www2.census.gov/geo/pdfs/reference/puma/2010_PUMA_Names.pdf)
puma = 'G25000300'

########################################################################## DO NOT CHANGE FROM HERE DOWN.##########################################################################

# If metadata does not exist in your data folder, download it and move it to data folder. 
if not os.path.isfile(model_folder + 'Models_Worcester_Metadata.csv'):

    # Download metadata from OPEN EI (https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock%2Fend-use-load-profiles-for-us-building-stock%2F2021%2Fresstock_amy2018_release_1%2F)
    metadata_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/metadata/metadata.parquet'
    webbrowser.open(metadata_link)

    # Wait for file to download
    while not os.path.exists(download_folder + 'metadata.parquet'):
        time.sleep(1)

    if os.path.isfile(download_folder + 'metadata.parquet'):
    # Move from downloads to Data folder 
        for x in os.listdir(download_folder):
            if x.endswith(".parquet"):
                metadata_files = x
                shutil.copyfile(download_folder + metadata_files, model_folder + metadata_files)

        md = pd.read_parquet(model_folder + "metadata.parquet")

        # Reduce to just rows in the puma 
        md = md[md['in.puma'] == puma]

        # Save new metadata file to OG Models
        new_md = md.to_csv(model_folder + 'Models_Worcester_Metadata.csv')
    
        # Delete download files
        os.remove(download_folder + metadata_files)


# If/When metadata does exist in your data folder, retrieve osm files 

if os.path.isfile(model_folder + '/Models_Worcester_Metadata.csv'):
    md = pd.read_csv(model_folder +  '/Models_Worcester_Metadata.csv')
    # # Reset index so bldg_id can be accessed
    md.reset_index(inplace=True)

    # # set BLDG_ID to be 7 characters long
    md['bldg_id'] = md['bldg_id'].apply(str)
    md['bldg_id'] = md['bldg_id'].str.zfill(7)

    # # Download osms from website
    for iModel in range(md.shape[0]):
        model_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/building_energy_models/bldg' + str(md.loc[iModel,'bldg_id']) + '-up00.osm.gz'
        webbrowser.open(model_link)
        
    # Unzip and move the model
    for iModel in range(md.shape[0]):
        # Wait for file to download
        while not os.path.exists(download_folder + 'bldg' + str(md.loc[iModel,'bldg_id']) + '-up00.osm.gz' ):
            time.sleep(1)

        if os.path.isfile(download_folder + 'bldg' + str(md.loc[iModel,'bldg_id']) + '-up00.osm.gz'):
            with gzip.open(download_folder + 'bldg' + str(md.loc[iModel,'bldg_id'])  + '-up00.osm.gz', 'rb') as f_in:
                with open(model_folder + '/bldg' + str(md.loc[iModel,'bldg_id'])  + '.osm','wb') as f_out:
                    shutil.copyfileobj(f_in,f_out)
                    
    Download occupancy schedules from website
    for iModel in range(md.shape[0]):
        schedule_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/occupancy_schedules/bldg' + str(md.loc[iModel,'bldg_id']) + '-up00.csv.gz'
        webbrowser.open(schedule_link)
        
   # Unzip and move the schedule
    for iModel in range(md.shape[0]):
        # Wait for file to download
        while not os.path.exists(download_folder + 'bldg' + str(md.loc[iModel,'bldg_id']) + '-up00.csv.gz' ):
            time.sleep(1)

        if os.path.isfile(download_folder + 'bldg' + str(md.loc[iModel,'bldg_id']) + '-up00.csv.gz'):
            with gzip.open(download_folder + 'bldg' + str(md.loc[iModel,'bldg_id'])  + '-up00.csv.gz', 'rb') as f_in:
                with open(schedule_folder + '/bldg' + str(md.loc[iModel,'bldg_id'])  + '.csv','wb') as f_out:
                    shutil.copyfileobj(f_in,f_out)  
    
# Delete download files
downloaded_files = os.listdir(download_folder)
for file in downloaded_files:
    if file.endswith(".gz"):
        os.remove(os.path.join(download_folder+file))
    if file.endswith(".osm"):
        os.remove(os.path.join(download_folder+file))
    if file.endswith(".parquet"):
        os.remove(os.path.join(download_folder+file))