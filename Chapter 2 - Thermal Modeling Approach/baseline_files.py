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
def move(each_model,version):
    version_datetime = pd.to_datetime(version)
    version_string = str(version_datetime.strftime("%Y-%m-%d"))
    version_otg_hr = str(version_datetime.hour)
    version_year = str(version_datetime.year)
    version_datetime = str(version_datetime)
 
    output_path = outputs_path + version_string + "/baseline/" + each_model + "/"
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        
    # Move Files
    # Move Model into folder 
    model_path = models_path +  "/" + each_model + '.osm'
    shutil.copyfile(model_path,output_path + each_model + '.osm')

    # Move Schedule into folder as 'schedules.csv'
    schedule_path = schedules_path + each_model + '.csv'
    shutil.copyfile(schedule_path,output_path + "schedules.csv")

    # Get full weather path
    this_weather = weathers_path + "POWER_Point_Hourly_" + version_year + '0101_' + version_year + '1231_042d2631N_071d8022W_LST.epw'

    # copy the osw template and paste into folder
    this_osw = output_path + "run_this_model.osw"
    shutil.copyfile(template_osw,this_osw)

    # open the osw file as a readable file
    with open(output_path + "run_this_model.osw",'r') as file:
        data = file.read()

        this_osm = models_path + each_model + ".osm"

        #replace with new osm
        data = data.replace(original_osm, this_osm)

        # replace with new weather file (baseline)
        data = data.replace(original_weather,this_weather)

        # replace with new output path
        data = data.replace(original_output_path,output_path + "run/")

    with open(output_path + "run_this_model.osw",'w') as file:
        file.write(data)
        
    shell_script = str("#!/bin/bash\nsingularity exec --bind \"" + data_file_path + "/:" + data_file_path + "/\" /shared/container_repository/OpenStudio/openstudio-3_2_1.sif openstudio run -w \"" + output_path + "run_this_model.osw\"") 

    with open (output_path + '/run_this_model.sh', 'w') as rsh:
                rsh.write(shell_script)

async def move_all_files(models,version):
    move_loop = asyncio.get_event_loop()
    futures = [move_loop.run_in_executor(None,move,each_model,version) for each_model in models]

move_loop = asyncio.new_event_loop()
move_loop.run_until_complete(move_all_files(models,version))

