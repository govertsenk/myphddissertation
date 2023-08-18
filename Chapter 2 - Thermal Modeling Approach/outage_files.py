import shutil
import pandas as pd
import sys
import subprocess
import os
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
import numpy as np
import datetime
og_wd = os.getcwd()
data_file_path  =  str(og_wd)
data_file_path = data_file_path.replace(os.sep, '/')
models_path = data_file_path + '/Models/'
schedules_path = data_file_path + '/Schedules/'
weathers_path = data_file_path + '/Weather/'
outputs_path = data_file_path + '/Output/'
template_osw = data_file_path + "/run_outage_template.osw"
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
# TEST
# models = [models[3]]
extreme_heat = pd.read_csv(data_file_path +'/Data/extreme_heat_long.csv',index_col=0)
vers_id = sys.argv[1]
version = extreme_heat.index[int(vers_id)]
# Move Outage files
def move(each_model,version,otg_start):
    version_datetime = pd.to_datetime(version)
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
    otg_hour = otg_hour.zfill(2)
    # Move Files
    # Move Model into folder 
    model_path = models_path +  "/" + each_model + '.osm'
    shutil.copyfile(model_path,output_path + each_model + '.osm')

    # Move Schedule into folder as 'schedules.csv'
    schedule_path = schedules_path + each_model + '.csv'
    this_schedule = output_path + "schedules.csv"
    shutil.copyfile(schedule_path,this_schedule)
    # Modify Schedule for Power Outage
    outage_schedule = pd.read_csv(schedule_path)
    time = pd.DataFrame(pd.date_range('1900-01-01 00:00:00', '1900-12-31 23:45:00', freq='15T'),columns=['Datetime'])

    otg_start = pd.to_datetime(otg_date + " " + otg_hour + ":00:00",format = "%B %d %H:%M:%S")
    
    otg_hr_end = int(otg_hour) + int(otg_len) + int(1)
    if otg_hr_end < 24:
        otg_end = pd.to_datetime(otg_date + " " + str(otg_hr_end) + ":00:00",format = "%B %d %H:%M:%S")
    elif otg_hr_end == 24:
        otg_end = pd.to_datetime(otg_date + " 00:00:00", format = "%B %d %H:%M:%S")
        otg_end = otg_end + datetime.timedelta(days=1)
        otg_hr_end = otg_end.hour 
    else: 
        otg_end = pd.to_datetime(otg_date + " 00:00:00", format = "%B %d %H:%M:%S")
        otg_end = otg_end + datetime.timedelta(days=1) 
        otg_end = otg_end + datetime.timedelta(hours = (otg_hr_end - 24))
        otg_hr_end = otg_end.hour
    # TURNED THIS ON 
    otg_start = otg_start + datetime.timedelta(minutes=45)
    change = time.loc[(time['Datetime'] >= otg_start) & (time['Datetime'] <= otg_end)].index.array
    outage_schedule.loc[change,:]=0
    outage_schedule.to_csv(this_schedule,index = False)#,header=False)  

    # copy the osw template and paste into folder
    this_osw = output_path + "run_this_model.osw"
    shutil.copyfile(template_osw,this_osw)
    # open the osw file as a readable file
    with open(this_osw,'r') as file:
        data = file.read()
        this_osm = models_path + each_model + ".osm"
        #replace with new osm
        data = data.replace(original_osm, this_osm)
        # replace with new weather file (baseline)
        data = data.replace(original_weather,this_weather)
        # replace with new output path
        data = data.replace(original_output_path,output_path + "run/")

        # replace the 
        data = data.replace("variable_otg_date",otg_date)
        data = data.replace("variable_otg_hour",otg_hour)
        data = data.replace("variable_otg_len",otg_len)

    with open(output_path + "run_this_model.osw",'w') as file:
        file.write(data)

    shell_script = str("#!/bin/bash\nsingularity exec --bind \"" + data_file_path + "/:" + data_file_path + "/\" /shared/container_repository/OpenStudio/openstudio-3_2_1.sif openstudio run -w \"" + output_path + "run_this_model.osw\"") 

    with open (output_path + '/run_this_model.sh', 'w') as rsh:
                rsh.write(shell_script)

async def move_all_files(models,version,otg_start_diff):
    move_loop = asyncio.get_event_loop()
    futures = [move_loop.run_in_executor(None,move,each_model,version,otg_start) for each_model in models for otg_start in otg_start_diff]

move_loop = asyncio.new_event_loop()
move_loop.run_until_complete(move_all_files(models,version,otg_start_diff))

