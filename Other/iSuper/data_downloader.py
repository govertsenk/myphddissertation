import os
from re import S 
import webbrowser
import shutil
import pandas as pd
import numpy as np
import gzip
import time
import csv
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp


# Asynchronous:

async def download_data(md, iModel, download_folder, puma_path):
    # Download Model and Move to Data/Models
    model_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/building_energy_models/bldg' + iModel + '-up00.osm.gz'
    async with aiohttp.ClientSession() as session:
        async with session.get(model_link) as resp:
            with open(download_folder + 'bldg' + iModel + '-up00.osm.gz', 'wb') as f:
                f.write(await resp.read())
    await asyncio.sleep(1)
    with gzip.open(download_folder + 'bldg' + iModel  + '-up00.osm.gz', 'rb') as f_in, open(puma_path + 'Models/bldg' + iModel  + '.osm','wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Download Schedule and Move to Data/Schedules
    schedule_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/occupancy_schedules/bldg' + iModel + '-up00.csv.gz'
    async with aiohttp.ClientSession() as session:
        async with session.get(schedule_link) as resp:
            with open(download_folder + 'bldg' + iModel + '-up00.csv.gz', 'wb') as f:
                f.write(await resp.read())

    await asyncio.sleep(1)
    with gzip.open(download_folder + 'bldg' + iModel  + '-up00.csv.gz', 'rb') as f_in, open(puma_path + 'Schedules/bldg' + iModel  + '.csv','wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

async def download(md, download_folder, puma_path):
    tasks = []
    for iModel in md['bldg_id']:
        tasks.append(asyncio.create_task(download_data(md, iModel, download_folder, puma_path)))
    await asyncio.gather(*tasks)

# SET THE FOLLOWING:

# Filepath of your working folder
file_path = os.getcwd()
file_path = str(file_path).replace(os.sep, '/')
# Filepath to your data folder
data_folder = file_path + "/Data/"

# Make Sure Data Folder is there
if not os.path.exists(data_folder):
    os.makedirs(data_folder)
    
#Filepath of your downloads folder
download_folder = "C:/Users/govertsen.k/Downloads/"
if not os.path.isfile(download_folder + 'metadata.parquet'):
    # Download metadata from OPEN EI (https://data.openei.org/s3_viewer?bucket=oedi-data-lake&prefix=nrel-pds-building-stock%2Fend-use-load-profiles-for-us-building-stock%2F2021%2Fresstock_amy2018_release_1%2F)
    metadata_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/metadata/metadata.parquet'
    webbrowser.open(metadata_link)

    # Wait for file to download
    while not os.path.exists(download_folder + 'metadata.parquet'):
        time.sleep(2)

    # Wait for the file to have a non-zero size
    while os.path.getsize(download_folder + 'metadata.parquet') == 0:
        time.sleep(1)  # wait for 1 second before checking again

    if os.path.isfile(download_folder + 'metadata.parquet'):
    # Move from downloads to Data folder 
        for x in os.listdir(download_folder):
            if x.endswith(".parquet"):
                metadata_files = x
                shutil.copyfile(download_folder + metadata_files, data_folder + metadata_files)


# # Get PUMAs 
# url = 'https://tigerweb.geo.census.gov/tigerwebmain/Files/tab20/tigerweb_tab20_puma_2010_us.html'
# response = requests.get(url)
# response.encoding = 'latin-1'  # Replace with the correct encoding

# # Parse the HTML content using Beautiful Soup
# soup = BeautifulSoup(response.content.decode('latin-1'), 'html.parser')

# # Find the table element containing the data
# table = soup.find('table')
            
# all_pumas = pd.read_html(str(table))[0]

# retrieve a list of all PUMA's in MA
# pumas = all_pumas['PUMA'].loc[all_pumas['STATE']==25].unique()

#  Brookline PUMA and Chelsea PUMA via 'https://tigerweb.geo.census.gov/tigerwebmain/Files/tab20/tigerweb_tab20_puma_2010_us.html'
pumas = ['G25003400','G25003306']

for each_puma in pumas: 
    # Make a folder for  PUMA 
    # Subfolder Models is in Data
    puma_path = data_folder + each_puma + '/'

    if not os.path.exists(puma_path):
        os.makedirs(puma_path)

    if not os.path.exists(puma_path + 'Models'):
        os.makedirs(puma_path + 'Models')

    # Subfolder Schedules is in Data
    if not os.path.exists(puma_path + 'Schedules'):
        os.makedirs(puma_path + 'Schedules')    

    # Subfolder Weather is in Data
    if not os.path.exists(puma_path + 'Weather'):
        os.makedirs(puma_path + 'Weather')    
    if not os.path.exists(puma_path + 'Weather/TMY3/'):
        os.makedirs(puma_path + 'Weather/TMY3/') 

    md = pd.read_parquet(data_folder + "metadata.parquet")
    md = md.loc[md['in.puma']==each_puma]

    # Reset index so bldg_id can be accessed
    md.reset_index(inplace=True)

    # set BLDG_ID to be 7 characters long
    md['bldg_id'] = md['bldg_id'].apply(str)
    md['bldg_id'] = md['bldg_id'].str.zfill(7)

    asyncio.run(download(md, download_folder, puma_path))

    # Save md 
    md = md.to_csv(puma_path + 'Models_Metadata_' + each_puma +'.csv')

    puma_int = each_puma[:-4]
    
# # Download AMY
# lat = all_pumas['CENTLAT'].loc[all_pumas['PUMA'] == puma_int].values[0]
# lat_str = str(round(lat, 2))
# lat_before = lat_str.split(".")[0].zfill(3)
# lat_after = lat_str.split(".")[1]
# lat_name = lat_before +'d'+lat_after +'N'

# lon = all_pumas['CENTLON'].loc[all_pumas['PUMA'] == puma_int].values[0]
# lon_str = str(round(abs(lon), 2))
# lon_before = lon_str.split(".")[0].zfill(3)
# lon_after = lon_str.split(".")[1]

# if lon < 0:
#     dir = "W"
# else:
#     dir = "E"
# lon_name = lon_before + 'd' + lon_after + dir
# for each_year in np.arange(2001,2023,1):
#     each_year = str(each_year)
#     weather_link = 'https://power.larc.nasa.gov/api/temporal/hourly/point?Time=LST&parameters=WS10M,WD10M,T2MDEW,T2M,RH2M,PS,PRECTOT&community=SB&longitude=' + str(lon) +'&latitude='+str(lat)+'&start='+each_year+'0101&end='+each_year+'1231&format=EPW'
#     webbrowser.open(weather_link)
#     new_weather_name = 'POWER_Point_Hourly_' + each_year + '0101_' + each_year + '1231_' + lat_name + '_' + lon_name + '_LT.epw'
#     while not os.path.exists(download_folder + '/'+ new_weather_name):
#         time.sleep(1)
#     os.rename(download_folder + '/' + new_weather_name, download_folder + '/' + each_puma + '_' + str(each_year) + '.epw')

# # Download Boston Logan TMY3
# weather_link = 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/USA/MA/USA_MA_Boston-Logan.Intl.AP.725090_TMY3/USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw'
# webbrowser.open(weather_link)
# new_weather_name = 'USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw'
# while not os.path.exists(download_folder + '/'+ new_weather_name):
#     time.sleep(1)
# os.rename(download_folder + '/' + new_weather_name, download_folder + '/' + each_puma + '_TMY3.epw')

# # Move each Weather file from Downloads to /Data/Weather
# # Get a list of all files in directory A
# files = os.listdir(download_folder)

# # Loop through each file and move it to directory B if it has a .epw extension
# for file in files:
#     if file.endswith('.epw'):
#         file_path = os.path.join(download_folder, file)
#         if 'TMY3' in file_path:
#             shutil.move(file_path, puma_path + '/Weather/TMY3/')
#         else:
#             shutil.move(file_path, puma_path + '/Weather/AMY/')

# Delete download files
downloaded_files = os.listdir(download_folder)
for file in downloaded_files:
    if file.endswith(".gz"):
        os.remove(os.path.join(download_folder+file))
    if file.endswith(".osm"):
        os.remove(os.path.join(download_folder+file))
    if file.endswith(".parquet"):
        os.remove(os.path.join(download_folder+file))
    if file.endswith(".epw"):
        os.remove(os.path.join(download_folder+file))
   

