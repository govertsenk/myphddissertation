# import pandas as pd
# import os
# import numpy as np

# og_wd = os.getcwd()
# og_wd = str(og_wd).replace(os.sep, '/')
# data_file_path = og_wd + '/Data/'
# output_file_path = og_wd + '/Output/'

# template_osw = og_wd + "/template.osw"
# puma = 'G25003400'


# puma_path = os.path.join(output_file_path, puma)
# # Identify all the models
# models = os.listdir(puma_path)
# # TEST
# # models = [models[5]]

# # Make new summary folders
# summary_path = puma_path + "/" + "summary"
# if not os.path.exists(summary_path):
#     os.makedirs(summary_path)

# # BASELINES
# # - Electricity
# baseline_electricity =pd.DataFrame(columns = models)

# # - Gas 
# baseline_gas = pd.DataFrame(columns = models)

# for each_model in models:
#     ## Baseline
#     # Create empty dataframe
#     baseline = pd.DataFrame()

#     # Read the baseline output file
#     data = pd.read_csv(puma_path + '/' + each_model + '/eplusout.csv')
#     baseline['Date/Time'] = data['Date/Time']
#     baseline['Electricity'] = data['Electricity:Facility [J](Hourly)']
#     if 'NaturalGas:Facility [J](TimeStep)' in data:
#         baseline['Gas'] = data['NaturalGas:Facility [J](TimeStep)']

#     # Change '24:00:00' to "00:00:00", set datetime, add one day to midnight values, reset index, and format
#     baseline['Date/Time'] = baseline['Date/Time'].str.strip()
#     baseline['Date/Time'] = baseline['Date/Time'].str.replace('24:00:00','00:00:00')
#     baseline['Date/Time'] = pd.to_datetime(baseline['Date/Time'],format = '%m/%d  %H:%M:%S')
#     baseline.loc[baseline['Date/Time'].dt.hour == 0,'Date/Time'] = baseline.loc[baseline['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')
#     # keep only hourly data instead of 15 min 
#     baseline = baseline[baseline['Date/Time'].dt.minute == 0]
#     baseline = baseline.reset_index(drop=True)

#     baseline_electricity[each_model] = baseline["Electricity"]
#     if 'Gas' in baseline:
#         baseline_gas[each_model] = baseline["Gas"]
    
# baseline_electricity = baseline_electricity.set_index(baseline['Date/Time'])
# baseline_electricity.to_csv(summary_path + "/electricity.csv",index=True)
# if not baseline_gas.empty:
#     baseline_gas = baseline_gas.set_index(baseline['Date/Time'])
#     baseline_gas.to_csv(summary_path + "/gas.csv",index=True)

#     # Delete all Files (needed for memory)
    
# # # Get a list of all directories in the specified directory
# # directories = [f for f in os.listdir(puma_path) if os.path.isdir(os.path.join(puma_path, f))]

# # # Loop through the directories and delete the ones that are not 'summary'
# # for folder in directories:
# #     if folder != 'summary':
# #         folder_path = os.path.join(puma_path, folder)
# #         shutil.rmtree(folder_path)

import shutil
import pandas as pd
import sys
import subprocess
import os
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
import numpy as np
import datetime

# Write function to download the NREL Model and Schedule
async def delete_folder(path_to_delete):
    shutil.rmtree(path_to_delete)

async def delete_all_folders(output_file_path,pumas):
    tasks = []
    for each_puma in pumas:
        puma_path = os.path.join(output_file_path, each_puma)

        models = os.listdir(puma_path)
        if 'summary' in models:
            models.remove('summary')
        # TEST
        # models = [models[0]]

        for each_model in models:
            path_to_delete = puma_path + '/' + each_model
            tasks.append(asyncio.create_task(delete_folder(path_to_delete)))
    await asyncio.gather(*tasks)

# kwh conversion 1 J == 0.0000002778 kWh 
kwh_conversion = 0.0000002778

#btu_conversion 1 J = 0.000947817 BTU
btu_conversion =  0.000947817

og_wd = os.getcwd()
og_wd = str(og_wd).replace(os.sep, '/')
data_file_path = og_wd + '/Data/'
output_file_path = og_wd + '/Output/'

template_osw = og_wd + "/template.osw"
pumas = [folder for folder in os.listdir(data_file_path) if os.path.isdir(os.path.join(data_file_path, folder))]
# TEST
pumas = [pumas[0]]

for each_puma in pumas: 
    puma_path = os.path.join(output_file_path, each_puma)
    # Identify all the models
    models = os.listdir(puma_path)
    if 'summary' in models:
        models.remove('summary')
    # TEST
    # models = [models[0]]

    # Make new summary folders
    summary_path = puma_path + "/" + "summary"
    if not os.path.exists(summary_path):
        os.makedirs(summary_path)

    # OUTPUTS:
    # Electricity:  "Electricity:Facility"
    electricity_total =pd.DataFrame(columns = models)
    
    # Natural Gas:  "NaturalGas:Facility"
    gas_total = pd.DataFrame(columns = models)
    # Natural Gas:  "NaturalGas:Facility"
    gas_cum_total = pd.DataFrame(columns = models)
    # # HVAC:       "NaturalGas:HVAC"
    gas_hvac = pd.DataFrame(columns = models)
    # # Heating:    "Heating:NaturalGas"
    gas_heat = pd.DataFrame(columns = models)
    # # Cooling:    "Cooling:NaturalGas"
    gas_cool = pd.DataFrame(columns = models)
    # # Water       "WaterSystems:NaturalGas"]
    gas_water = pd.DataFrame(columns = models)


    for each_model in models:
        # Read the baseline output file
        data = pd.read_csv(puma_path + '/' + each_model + '/eplusout.csv')
        # Change '24:00:00' to "00:00:00", set datetime, add one day to midnight values, reset index, and format
        data['Date/Time'] = data['Date/Time'].str.strip()
        data['Date/Time'] = data['Date/Time'].str.replace('24:00:00','00:00:00')
        # set as datetime
        data['Date/Time'] = pd.to_datetime(data['Date/Time'],format = '%m/%d  %H:%M:%S')
        # Change to each Year
        data['Date/Time'] = data['Date/Time'].apply(lambda dt: dt.replace(year=2022))
        # Where H == 24, change to 0 and add one day. 
        data.loc[data['Date/Time'].dt.hour == 0,'Date/Time'] = data.loc[data['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')
        # keep only hourly data instead of 15 min 
        data = data[data['Date/Time'].dt.minute == 0]
        data = data.reset_index(drop=True)

        # ASSIGN METER VALUES FOR EACH MODEL
        # Electricity:  "Electricity:Facility"
        if 'Electricity:Facility [J](Hourly)' in data:
            electricity_total[each_model] = data['Electricity:Facility [J](Hourly)']*kwh_conversion
        
        # Natural Gas:  "NaturalGas:Facility"
        if 'NaturalGas:Facility [J](Hourly)' in data:
            gas_total[each_model] = data['NaturalGas:Facility [J](Hourly)']*btu_conversion
        # Natural Gas:  "NaturalGas:Facility"
        if 'Cumulative,NaturalGas:Facility [J](Hourly)' in data:
            gas_cum_total[each_model] = data['Cumulative,NaturalGas:Facility [J](Hourly)']*btu_conversion
        # # HVAC:       "NaturalGas:HVAC"
        if 'NaturalGas:HVAC [J](Hourly)' in data:
            gas_hvac[each_model] = data['NaturalGas:HVAC [J](Hourly)']*btu_conversion
        # # Heating:    "Heating:NaturalGas"
        if 'Heating:NaturalGas [J](Hourly)' in data:
            gas_heat[each_model] = data['Heating:NaturalGas [J](Hourly)']*btu_conversion
        # # Cooling:    "Cooling:NaturalGas"
        if 'Cooling:NaturalGas [J](Hourly)' in data:
            gas_cool[each_model] = data['Cooling:NaturalGas [J](Hourly)']*btu_conversion
        # # Water       "WaterSystems:NaturalGas"];
        if 'WaterSystems:NaturalGas [J](Hourly)' in data:
            gas_water[each_model] = data['WaterSystems:NaturalGas [J](Hourly)']*btu_conversion
        
    
    # EXPORT METER RESULTS
        # Electricity:  "Electricity:Facility"
    if not electricity_total.empty:
        electricity_total = electricity_total.set_index(data['Date/Time'])
        electricity_total.to_csv(summary_path + "/electricity_total_kwh.csv",index=True)
    
    # Natural Gas:  "NaturalGas:Facility"
    if not gas_total.empty:
        gas_total = gas_total.set_index(data['Date/Time'])
        gas_total.to_csv(summary_path + "/gas_total_btu.csv",index=True)
    # Natural Gas:  "Cumulative,NaturalGas:Facility"
    if not gas_cum_total.empty:
        gas_cum_total = gas_cum_total.set_index(data['Date/Time'])
        gas_cum_total.to_csv(summary_path + "/gas_cum_total_btu.csv",index=True)
    
    # # HVAC:       "NaturalGas:HVAC"
    if not gas_hvac.empty:
        gas_hvac = gas_hvac.set_index(data['Date/Time'])
        gas_hvac.to_csv(summary_path + "/gas_hvac_btu.csv",index=True)
    # # Heating:    "Heating:NaturalGas"
    if not gas_heat.empty:
        gas_heat = gas_heat.set_index(data['Date/Time'])
        gas_heat.to_csv(summary_path + "/gas_heat_btu.csv",index=True)
    # # Cooling:    "Cooling:NaturalGas"
    if not gas_cool.empty:
        gas_cool = gas_cool.set_index(data['Date/Time'])
        gas_cool.to_csv(summary_path + "/gas_cool_btu.csv",index=True)
    # # Water       "WaterSystems:NaturalGas"];
    if not gas_water.empty:
        gas_water = gas_water.set_index(data['Date/Time'])
        gas_water.to_csv(summary_path + "/gas_water_btu.csv",index=True)
        

# DELETE FOLDERS
asyncio.run(delete_all_folders(output_file_path,pumas))

       
            