import asyncio
import aiohttp
import csv
import datetime
import gzip
import numpy as np
import os
import pandas as pd
import requests
import shutil
import subprocess
import sys
import time
import webbrowser
from bs4 import BeautifulSoup
from concurrent.futures.thread import ThreadPoolExecutor
from re import S

# start_time = time.time()

# Filepath of your downloads folder (MAY NEED TO CHANGE THIS)
download_folder = "C:/Users/govertsen.k/Downloads/"

# Asynchronous:
## DOWNLOADING 
# Write function to download the NREL Model and Schedule
async def download_data(md, iModel, download_folder, puma_path):
    # Download Model and Move to Data/Models
    # link to model
    model_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/building_energy_models/bldg' + iModel + '-up00.osm.gz'
    
    # download model
    async with aiohttp.ClientSession() as session:
        async with session.get(model_link) as resp:
            with open(download_folder + 'bldg' + iModel + '-up00.osm.gz', 'wb') as f:
                f.write(await resp.read())

    # wait until downloaded
    await asyncio.sleep(1)
    # unzip and copy from downlaods to puma's model folder
    with gzip.open(download_folder + 'bldg' + iModel  + '-up00.osm.gz', 'rb') as f_in, open(puma_path + 'Models/bldg' + iModel  + '.osm','wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Download Schedule and Move to Data/Schedules
    # link to schedule
    schedule_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/occupancy_schedules/bldg' + iModel + '-up00.csv.gz'
    
    # download scheudle
    async with aiohttp.ClientSession() as session:
        async with session.get(schedule_link) as resp:
            with open(download_folder + 'bldg' + iModel + '-up00.csv.gz', 'wb') as f:
                f.write(await resp.read())
    # wait until downloaded
    await asyncio.sleep(1)

    # unzip and copy from downloads to puma's schedule folder 
    with gzip.open(download_folder + 'bldg' + iModel  + '-up00.csv.gz', 'rb') as f_in, open(puma_path + 'Schedules/bldg' + iModel  + '.csv','wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

# write function to download asynchronously 
async def download(md, download_folder, puma_path):
    tasks = []
    for iModel in md['bldg_id']:
        tasks.append(asyncio.create_task(download_data(md, iModel, download_folder, puma_path)))
    await asyncio.gather(*tasks)


## RUNNING:
# Asyncio Definitions:
async def process_model(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, each_model):
    # copy the osw template and paste into folder
    model_output_path = puma_output_path + "/" + each_model
    this_osw = model_output_path + "/" + each_model + ".osw"

    shutil.copyfile(template_osw,this_osw)

    # Move Schedule into folder as 'schedules.csv'
    schedule_path = schedules_path + each_model + '.csv'
    shutil.copyfile(schedule_path,model_output_path + "/schedules.csv")

    this_weather =  puma_path + '/Weather/' + puma + '_TMY3.epw'

    # open the osw file as a readable file
    with open(this_osw,'r') as file:
        data = file.read()

        this_osm = models_path + each_model + ".osm"

        #replace with new osm
        data = data.replace(original_osm, this_osm)

        # replace with new weather file (baseline)
        data = data.replace(original_weather,this_weather)

        # replace with new output path
        data = data.replace(original_output_path,model_output_path)

    with open(this_osw,'w') as file:
        file.write(data)

async def process_models(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, models):
    tasks = []
    for each_model in models:
        task = asyncio.create_task(process_model(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, each_model))
        tasks.append(task)
    await asyncio.gather(*tasks)

async def run_model(each_model_script):
    process = await asyncio.create_subprocess_shell(each_model_script)
    return process

async def run_model_with_executor(executor, each_model_script):
    loop = asyncio.get_running_loop()
    process = await loop.run_in_executor(executor, subprocess.run, each_model_script)
    return process

async def run_models_with_executor(executor, puma_output_path, these_models):
    tasks = []
    for each_model in these_models:
        model_output_path = puma_output_path + "/" + each_model
        this_osw = model_output_path + "/" + each_model + ".osw"
        shell_script = r'''C:\openstudio-3.2.1\bin\openstudio.exe run -w "{osw}"'''.format(osw=this_osw)
        task = asyncio.create_task(run_model_with_executor(executor, shell_script))
        tasks.append(task)
    await asyncio.gather(*tasks)

async def simulate():
    # Call the main function
    await process_models(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, models)

    # Create a thread pool executor
    max_workers = 6  # Set the maximum number of concurrent subprocesses (CHANGE FOR EC 2)
    executor = ThreadPoolExecutor(max_workers=max_workers)

    # Run models with thread pool executor
    await run_models_with_executor(executor, puma_output_path, models)

    # Shutdown the executor to release resources
    executor.shutdown()


## PROCESSING:
async def delete_folder(path_to_delete):
    shutil.rmtree(path_to_delete)

async def delete_all_folders(data_folder,output_folder_path,puma):
    tasks = []
    puma_path = os.path.join(output_folder_path, puma)
    models = os.listdir(puma_path)
    if 'summary' in models:
        models.remove('summary')
    # TEST
    # models = [models[0]]

    for each_model in models:
        path_to_delete = puma_path + '/' + each_model
        tasks.append(asyncio.create_task(delete_folder(path_to_delete)))
    
    # also Delete Models, Schedule, and Weather folders from /Data/
    models_path = os.path.join(data_folder, puma, 'Models')
    tasks.append(asyncio.create_task(delete_folder(models_path)))

    schedules_path = os.path.join(data_folder, puma, 'Schedules')
    tasks.append(asyncio.create_task(delete_folder(schedules_path)))

    weather_path = os.path.join(data_folder, puma, 'Weather')
    tasks.append(asyncio.create_task(delete_folder(weather_path)))

    await asyncio.gather(*tasks)


# SET THE FOLLOWING:

# Filepath of your working folder
og_wd = os.getcwd()
og_wd = str(og_wd).replace(os.sep, '/')
data_folder = og_wd + '/Data/'


# Constants 
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"
original_output_path = "output_path"
template_osw = og_wd + "/template.osw"
# kwh_conversion = 0.0000002778 # kwh conversion 1 J == 0.0000002778 kWh 
# btu_conversion =  0.000947817 #btu_conversion 1 J = 0.000947817 BTU

# Make Sure Data Folder is there
if not os.path.exists(data_folder):
    os.makedirs(data_folder)
    

if not os.path.isfile(data_folder + 'metadata.parquet'):
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


# Get All 2010 PUMAS -- this gives us the lat/lon of the controid of the puma for amy weather 
# Send a GET request to the website
# url = 'https://tigerweb.geo.census.gov/tigerwebmain/Files/tab20/tigerweb_tab20_puma_2010_us.html'
# response = requests.get(url)
# response.encoding = 'latin-1'  # Replace with the correct encoding

# Parse the HTML content using Beautiful Soup
# soup = BeautifulSoup(response.content.decode('latin-1'), 'html.parser')

# # Find the table element containing the data
# table = soup.find('table')
# all_pumas = pd.read_html(str(table))[0]
# all_pumas['PUMA'] = all_pumas['PUMA'].astype(str).str.zfill(5)

# SCE 2010 Pumas:
# sce_pumas = pd.read_csv(data_folder + "SCE_PUMA_2010.csv")
pumas = ['G25003306']#,'G25003400']

for puma in pumas:
    # Make a folder for each PUMA 
    # Subfolder Models is in Data
    puma_path = data_folder + puma + '/'

    ## DOWNLOADING
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

    md = pd.read_parquet(data_folder + "metadata.parquet")
    md = md.loc[md['in.puma']==puma]

    # TEST
    # md = md.reset_index()
    # md = md.loc[md.index == 0]

    # Reset index so bldg_id can be accessed
    md.reset_index(inplace=True)
    # set BLDG_ID to be 7 characters long
    md['bldg_id'] = md['bldg_id'].apply(str)
    md['bldg_id'] = md['bldg_id'].str.zfill(7)


    asyncio.run(download(md, download_folder, puma_path))

    # Save md 
    md = md.to_csv(puma_path + 'Models_Metadata_' + puma +'.csv')

    # Download Boston Logan TMY3
    if not os.path.isfile(puma_path + 'Weather/'+ puma + '_TMY3.epw'):
        weather_link = 'https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/USA/MA/USA_MA_Boston-Logan.Intl.AP.725090_TMY3/USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw'
        webbrowser.open(weather_link)
        new_weather_name = 'USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw'
        while not os.path.exists(download_folder + '/'+ new_weather_name):
            time.sleep(1)
        os.rename(download_folder + '/' + new_weather_name, download_folder + '/' + puma + '_TMY3.epw')
        shutil.move(download_folder + '/' + puma + '_TMY3.epw', puma_path + 'Weather/'+ puma + '_TMY3.epw')

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

    # # RUNNING
    # check if the current file is a directory
    puma_path = os.path.join(data_folder, puma)
    if os.path.isdir(puma_path):
        models_path = puma_path + '/Models/'
        schedules_path = puma_path + '/Schedules/'
        # Make output folder:
        output_folder = og_wd + '/Output/'
        if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                
        puma_output_path = output_folder + puma
        if not os.path.exists(puma_output_path):
                os.makedirs(puma_output_path)
                        
        # Identify all the models
        models = []
        # Iterate directory
        for model in os.listdir(models_path):
            # check only text files
            if model.endswith('.osm'):
                models.append(model[:-4])
            model_output_path = puma_output_path + '/' + model[:-4]
            if not os.path.exists(model_output_path):
                    os.makedirs(model_output_path)
        # Test
        # models = [models[0]]
        asyncio.run(simulate())

    ## PROCESSING : 
    # TEST
    # models = [models[0]]

    # Make new summary folders
    summary_path = puma_output_path + "/" + "summary"
    if not os.path.exists(summary_path):
        os.makedirs(summary_path)

    # OUTPUTS:
    # Electricity:  "Electricity:Facility"
    electricity_total =pd.DataFrame(columns = models)
    # # HVAC:       "Electricity:HVAC"
    electricity_hvac =pd.DataFrame(columns = models)
    # # Heating:    "Heating:Electricity"
    electricity_heat =pd.DataFrame(columns = models)
    # # Cooling:    "Cooling:Electricity"
    electricity_cool =pd.DataFrame(columns = models)
    # # Water:      "WaterSystems:Electricity"
    electricity_water =pd.DataFrame(columns = models)

    # Natural Gas:  "NaturalGas:Facility"
    gas_total = pd.DataFrame(columns = models)
    # # HVAC:       "NaturalGas:HVAC"
    gas_hvac = pd.DataFrame(columns = models)
    # # Heating:    "Heating:NaturalGas"
    gas_heat = pd.DataFrame(columns = models)
    # # Cooling:    "Cooling:NaturalGas"
    gas_cool = pd.DataFrame(columns = models)
    # # Water       "WaterSystems:NaturalGas"]
    gas_water = pd.DataFrame(columns = models)
    
    # Propane:      "Propane:Facility"
    propane_total = pd.DataFrame(columns = models)
    # # HVAC:       "Propane:HVAC"
    propane_hvac = pd.DataFrame(columns = models)
    # # Heating:    "Heating:Propane"
    propane_heat = pd.DataFrame(columns = models)
    
    # Fuel Oil:     "FuelOilNo1:Facility"
    oil_total = pd.DataFrame(columns = models)
    # # Heating:    "Heating:FuelOilNo1"
    oil_heat = pd.DataFrame(columns = models)
    # # Water:      "WaterSystems:FuelOilNo1"
    oil_water = pd.DataFrame(columns = models)

    
    for each_model in models:
        # Read the baseline output file
        data = pd.read_csv(puma_output_path + '/' + each_model + '/eplusout.csv')
        # Change '24:00:00' to "00:00:00", set datetime, add one day to midnight values, reset index, and format
        data['Date/Time'] = data['Date/Time'].str.strip()
        data['Date/Time'] = data['Date/Time'].str.replace('24:00:00','00:00:00')
        # set as datetime
        data['Date/Time'] = pd.to_datetime(data['Date/Time'],format = '%m/%d  %H:%M:%S')
        # Change to each Year
        data['Date/Time'] = data['Date/Time'].apply(lambda dt: dt.replace(year=int(2022)))
        # Where H == 24, change to 0 and add one day. 
        data.loc[data['Date/Time'].dt.hour == 0,'Date/Time'] = data.loc[data['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')
        # keep only hourly data instead of 15 min 
        data = data[data['Date/Time'].dt.minute == 0]
        data = data.reset_index(drop=True)

        # ASSIGN METER VALUES FOR EACH MODEL
        # Electricity:  "Electricity:Facility"
        if 'Electricity:Facility [J](Hourly)' in data:
            electricity_total[each_model] = data['Electricity:Facility [J](Hourly)']
        # # HVAC:       "Electricity:HVAC"
        if 'Electricity:HVAC [J](Hourly)' in data:
            electricity_hvac[each_model] = data['Electricity:HVAC [J](Hourly)']
        # # Heating:    "Heating:Electricity"
        if 'Heating:Electricity [J](Hourly)' in data:
            electricity_heat[each_model] = data['Heating:Electricity [J](Hourly)']
        # # Cooling:    "Cooling:Electricity"
        if 'Cooling:Electricity [J](Hourly)' in data:
            electricity_cool[each_model] = data['Cooling:Electricity [J](Hourly)']
        # # Water:      "WaterSystems:Electricity"
        if 'WaterSystems:Electricity [J](Hourly)' in data:
            electricity_water[each_model] = data['WaterSystems:Electricity [J](Hourly)']

        # Natural Gas:  "NaturalGas:Facility"
        if 'NaturalGas:Facility [J](Hourly)' in data:
            gas_total[each_model] = data['NaturalGas:Facility [J](Hourly)']
        # # HVAC:       "NaturalGas:HVAC"
        if 'NaturalGas:HVAC [J](Hourly)' in data:
            gas_hvac[each_model] = data['NaturalGas:HVAC [J](Hourly)']
        # # Heating:    "Heating:NaturalGas"
        if 'Heating:NaturalGas [J](Hourly)' in data:
            gas_heat[each_model] = data['Heating:NaturalGas [J](Hourly)']
        # # Cooling:    "Cooling:NaturalGas"
        if 'Cooling:NaturalGas [J](Hourly)' in data:
            gas_cool[each_model] = data['Cooling:NaturalGas [J](Hourly)']
        # # Water       "WaterSystems:NaturalGas"];
        if 'WaterSystems:NaturalGas [J](Hourly)' in data:
            gas_water[each_model] = data['WaterSystems:NaturalGas [J](Hourly)']
        
        # Propane:      "Propane:Facility"
        if 'Propane:Facility [J](Hourly)' in data:
            propane_total[each_model] = data['Propane:Facility [J](Hourly)']
        # # HVAC:       "Propane:HVAC"
        if 'Propane:HVAC [J](Hourly)' in data:
            propane_hvac[each_model] = data['Propane:HVAC [J](Hourly)']
        # # Heating:    "Heating:Propane"
        if 'Heating:Propane [J](Hourly)' in data:
            propane_heat[each_model] = data['Heating:Propane [J](Hourly)']
            
        # Fuel Oil:     "FuelOilNo1:Facility"
        if 'FuelOilNo1:Facility [J](Hourly)' in data:
            oil_total[each_model] = data['FuelOilNo1:Facility [J](Hourly)']
        # # Heating:    "Heating:FuelOilNo1"
        if 'Heating:FuelOilNo1 [J](Hourly)' in data:
            oil_heat[each_model] = data['Heating:FuelOilNo1 [J](Hourly)']
        # # Water:      "WaterSystems:FuelOilNo1"
        if 'WaterSystems:FuelOilNo1 [J](Hourly)' in data:
            oil_water[each_model] = data['WaterSystems:FuelOilNo1 [J](Hourly)']

    # EXPORT METER RESULTS
        # Electricity:  "Electricity:Facility"
    if not electricity_total.empty:
        electricity_total = electricity_total.set_index(data['Date/Time'])
        electricity_total.to_csv(summary_path + "/electricity_total.csv",index=True)
    # # HVAC:       "Electricity:HVAC"
    if not electricity_hvac.empty:
        electricity_hvac = electricity_hvac.set_index(data['Date/Time'])
        electricity_hvac.to_csv(summary_path + "/electricity_hvac.csv",index=True)
    # # Heating:    "Heating:Electricity"
    if not electricity_heat.empty:
        electricity_heat = electricity_heat.set_index(data['Date/Time'])
        electricity_heat.to_csv(summary_path + "/electricity_heat.csv",index=True)
    # # Cooling:    "Cooling:Electricity"
    if not electricity_cool.empty:
        electricity_cool = electricity_cool.set_index(data['Date/Time'])
        electricity_cool.to_csv(summary_path + "/electricity_cool.csv",index=True)
    # # Water:      "WaterSystems:Electricity"
    if not electricity_water.empty:
        electricity_water = electricity_water.set_index(data['Date/Time'])
        electricity_water.to_csv(summary_path + "/electricity_water.csv",index=True)

    # Natural Gas:  "NaturalGas:Facility"
    if not gas_total.empty:
        gas_total = gas_total.set_index(data['Date/Time'])
        gas_total.to_csv(summary_path + "/gas_total.csv",index=True)
    # # HVAC:       "NaturalGas:HVAC"
    if not gas_hvac.empty:
        gas_hvac = gas_hvac.set_index(data['Date/Time'])
        gas_hvac.to_csv(summary_path + "/gas_hvac.csv",index=True)
    # # Heating:    "Heating:NaturalGas"
    if not gas_heat.empty:
        gas_heat = gas_heat.set_index(data['Date/Time'])
        gas_heat.to_csv(summary_path + "/gas_heat.csv",index=True)
    # # Cooling:    "Cooling:NaturalGas"
    if not gas_cool.empty:
        gas_cool = gas_cool.set_index(data['Date/Time'])
        gas_cool.to_csv(summary_path + "/gas_cool.csv",index=True)
    # # Water       "WaterSystems:NaturalGas"];
    if not gas_water.empty:
        gas_water = gas_water.set_index(data['Date/Time'])
        gas_water.to_csv(summary_path + "/gas_water.csv",index=True)

    # Propane:      "Propane:Facility"
    if not propane_total.empty:
        propane_total = propane_total.set_index(data['Date/Time'])
        propane_total.to_csv(summary_path + "/propane_total.csv",index=True)
    # # HVAC:       "Propane:HVAC"
    if not propane_hvac.empty:
        propane_hvac = propane_hvac.set_index(data['Date/Time'])
        propane_hvac.to_csv(summary_path + "/propane_hvac.csv",index=True)
    # # Heating:    "Heating:Propane"
    if not propane_heat.empty:
        propane_heat = propane_heat.set_index(data['Date/Time'])
        propane_heat.to_csv(summary_path + "/propane_heat.csv",index=True)
    
    # Fuel Oil:     "FuelOilNo1:Facility"
    if not oil_total.empty:
        oil_total = oil_total.set_index(data['Date/Time'])
        oil_total.to_csv(summary_path + "/oil_total.csv",index=True)
    # # Heating:    "Heating:FuelOilNo1"
    if not oil_heat.empty:
        oil_heat = oil_heat.set_index(data['Date/Time'])
        oil_heat.to_csv(summary_path + "/oil_heat.csv",index=True)
    # # Water:      "WaterSystems:FuelOilNo1"
    if not oil_water.empty:
        oil_water = oil_water.set_index(data['Date/Time'])
        oil_water.to_csv(summary_path + "/oil_water.csv",index=True)
        
    # DELETE FOLDERS
    asyncio.run(delete_all_folders(data_folder,output_folder,puma))


            


