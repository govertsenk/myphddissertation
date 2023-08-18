## Import things:
import pandas as pd 
import os
import shutil
import datetime 
import numpy as np
import asyncio
import sys

## Constants 
og_wd = os.getcwd()
data_file_path  =  str(og_wd)
data_file_path = data_file_path.replace(os.sep, '/')
models_path = data_file_path + '/Models/'
outputs_path = data_file_path + '/Output/'
if not os.path.exists(outputs_path):
    os.makedirs(outputs_path)
otg_start_diff = np.arange(0,13,1)
# otg_start_diff = [0]


extreme_heat = pd.read_csv(data_file_path +'/Data/extreme_heat_long.csv',index_col=0)
vers_id = sys.argv[1]
version = extreme_heat.index[int(vers_id)]

# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model[:-4])
# TEST
# models = [models[3]]

version_datetime = pd.to_datetime(version)
version_string = str(version_datetime.strftime("%Y-%m-%d"))
date_path = outputs_path + version_string
# Make folders for each event date
if not os.path.exists(date_path):
    os.makedirs(date_path)
# Make baseline folders within each date
baseline_path = date_path + "/baseline"
if not os.path.exists(baseline_path):
        os.makedirs(baseline_path)
# Make model folders within each baseline 
for each_model in models:
        model_path = baseline_path + "/" + each_model
        if not os.path.exists(model_path):
            os.makedirs(model_path)
        run_path = model_path + "/run"
        if not os.path.exists(run_path):
            os.makedirs(run_path)
# Make outage folders within each date    
otg_date = str(version_datetime.strftime("%B %d"))
otg_len = "12" # approximate hours
for each_hr in otg_start_diff:
    otg_hour = version_datetime.hour + each_hr
    time_path = date_path + "/" + str(otg_hour)
    if not os.path.exists(time_path):
        os.makedirs(time_path)
    # Make model folders within each outage
    for each_model in models:
        model_path = time_path + "/" + each_model
        if not os.path.exists(model_path):
            os.makedirs(model_path)
        run_path = model_path + "/run"
        if not os.path.exists(run_path):
            os.makedirs(run_path)