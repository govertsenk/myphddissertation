import shutil
import pandas as pd
import sys
import subprocess
import os
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
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

# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model[:-4])
# TEST
# models = [models[3]]

extreme_heat = pd.read_csv(data_file_path +'/Data/extreme_heat_long.csv',index_col=0)
vers_id = sys.argv[1]
version = extreme_heat.index[int(vers_id)]

# Move Baseline files
def run_simulation(each_model,each_version):
    version_datetime = pd.to_datetime(version)
    version_string = str(version_datetime.strftime("%Y-%m-%d"))
    version_otg_hr = str(version_datetime.hour)
    version_year = str(version_datetime.year)
    version_datetime = str(version_datetime)
 
    output_path = outputs_path + version_string + "/baseline/" + each_model + "/"

    # run simultations
    file_to_run = output_path + "run_this_model.sh"
    subprocess.run(['chmod', '770', file_to_run])
    subprocess.run(file_to_run)
    
async def run_all_simulations(models,version):
    model_loop = asyncio.get_event_loop()
    futures = [model_loop.run_in_executor(None,run_simulation,each_model,version) for each_model in models]

model_loop = asyncio.new_event_loop()
model_loop.run_until_complete(run_all_simulations(models,version))


