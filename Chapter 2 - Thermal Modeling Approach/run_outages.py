import shutil
import pandas as pd
import sys
import subprocess
import os
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
import numpy as np

og_wd = os.getcwd()
data_file_path  =  str(og_wd)
data_file_path = data_file_path.replace(os.sep, '/')
models_path = data_file_path + '/Models/'
schedules_path = data_file_path + '/Schedules/'
weathers_path = data_file_path + '/Weather/'
outputs_path = data_file_path + '/Output/'
template_osw = data_file_path + "/run_model_template.osw"
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"
original_output_path = "output_path"
otg_start_diff = np.arange(0,13,1);
# otg_start_diff = [0]

# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model[:-4])
        
# models = [models[3]]
extreme_heat = pd.read_csv(data_file_path +'/Data/extreme_heat_long.csv',index_col=0)
vers_id = sys.argv[1]
version = extreme_heat.index[int(vers_id)]

def run_simulation(each_model,each_version,otg_start):
    version_datetime = pd.to_datetime(each_version)
    version_string = str(version_datetime.strftime("%Y-%m-%d"))
    version_otg_hr = str(version_datetime.hour)
    version_year = str(version_datetime.year)
    date_path = outputs_path + version_string
    # Get full weather path
    this_weather = weathers_path + "POWER_Point_Hourly_" + version_year + '0101_' + version_year + '1231_042d2631N_071d8022W_LST.epw'
    # Make outage folders within each date    
    otg_date = str(version_datetime.strftime("%B %d"))
    otg_len = "12" # approximate hours
    otg_hour = str(version_datetime.hour + otg_start)
    output_path = date_path + "/" + otg_hour + "/" + each_model + "/"

    # run simultations
    file_to_run = output_path + "run_this_model.sh"
    subprocess.run(['chmod', '770', file_to_run])
    subprocess.run(file_to_run)
    
async def run_all_simulations(models,version,otg_start_diff):
    model_loop = asyncio.get_event_loop()
    futures = [model_loop.run_in_executor(None,run_simulation,each_model,version,otg_start) for each_model in models for otg_start in otg_start_diff]

model_loop = asyncio.new_event_loop()
model_loop.run_until_complete(run_all_simulations(models,version,otg_start_diff))


