import pandas as pd
import os
import numpy as np

og_wd = os.getcwd()
og_wd = str(og_wd).replace(os.sep, '/')
data_file_path = og_wd + '/Data/'
output_file_path = og_wd + '/Output/'

template_osw = og_wd + "/template.osw"
puma = 'G25003400'


puma_path = os.path.join(output_file_path, puma)
# Identify all the models
models = os.listdir(puma_path)
# TEST
# models = [models[5]]

# Make new summary folders
summary_path = puma_path + "/" + "summary"
if not os.path.exists(summary_path):
    os.makedirs(summary_path)

# BASELINES
# - Electricity
baseline_electricity =pd.DataFrame(columns = models)

# - Gas 
baseline_gas = pd.DataFrame(columns = models)

for each_model in models:
    ## Baseline
    # Create empty dataframe
    baseline = pd.DataFrame()

    # Read the baseline output file
    data = pd.read_csv(puma_path + '/' + each_model + '/eplusout.csv')
    baseline['Date/Time'] = data['Date/Time']
    baseline['Electricity'] = data['Electricity:Facility [J](Hourly)']
    if 'NaturalGas:Facility [J](TimeStep)' in data:
        baseline['Gas'] = data['NaturalGas:Facility [J](TimeStep)']

    # Change '24:00:00' to "00:00:00", set datetime, add one day to midnight values, reset index, and format
    baseline['Date/Time'] = baseline['Date/Time'].str.strip()
    baseline['Date/Time'] = baseline['Date/Time'].str.replace('24:00:00','00:00:00')
    baseline['Date/Time'] = pd.to_datetime(baseline['Date/Time'],format = '%m/%d  %H:%M:%S')
    baseline.loc[baseline['Date/Time'].dt.hour == 0,'Date/Time'] = baseline.loc[baseline['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')
    # keep only hourly data instead of 15 min 
    baseline = baseline[baseline['Date/Time'].dt.minute == 0]
    baseline = baseline.reset_index(drop=True)

    baseline_electricity[each_model] = baseline["Electricity"]
    if 'Gas' in baseline:
        baseline_gas[each_model] = baseline["Gas"]
    
baseline_electricity = baseline_electricity.set_index(baseline['Date/Time'])
baseline_electricity.to_csv(summary_path + "/electricity.csv",index=True)
if not baseline_gas.empty:
    baseline_gas = baseline_gas.set_index(baseline['Date/Time'])
    baseline_gas.to_csv(summary_path + "/gas.csv",index=True)

    # Delete all Files (needed for memory)
    
# # Get a list of all directories in the specified directory
# directories = [f for f in os.listdir(puma_path) if os.path.isdir(os.path.join(puma_path, f))]

# # Loop through the directories and delete the ones that are not 'summary'
# for folder in directories:
#     if folder != 'summary':
#         folder_path = os.path.join(puma_path, folder)
#         shutil.rmtree(folder_path)
