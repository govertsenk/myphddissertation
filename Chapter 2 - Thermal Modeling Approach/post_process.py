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
template_osw = data_file_path + "/run_model_template.osw"
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"
original_output_path = "output_path"
heat_index = pd.read_csv(data_file_path + "/Data/heatindex.csv")
heat_index = heat_index.set_index('RH')
# print(heat_index)
otg_start_diff = np.arange(0,13,1);
# otg_start_diff = [0]
# Conversion Functions 
def F_to_C(F):
    C = (F - 32)*5/9
    return C

def C_to_F(C):
    F = C*9/5 + 32
    return F

def calc_HI(T,RH):
# from https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    # T - temperature in F
    # RH - RH
    # HI is the apparent temperature
    
    # Simple is calculated first:
    HI = 0.5 * (T + 61.0 + ((T-68.0)*1.2) + (RH*0.094))
    avg_HI = (HI+T)/2
    
    if avg_HI >= 80: 
        HI = -42.379 + 2.04901523*T + 10.14333127*RH - .22475541*T*RH - .00683783*T*T - .05481717*RH*RH + .00122874*T*T*RH + .00085282*T*RH*RH - .00000199*T*T*RH*RH
        if (RH < 13) & (80 < T < 112):
            adj =  ((13-RH)/4)*np.sqrt((17-np.absolute(T-95))/17)
            HI = HI - adj
        if (RH > 85) & (80 < T < 87):
            adj = ((RH-85)/10) * ((87-T)/5)
            HI = HI + adj
    return HI 

# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model[:-4])
        
# TEST
# models = [models[5]]
extreme_heat = pd.read_csv(data_file_path +'/Data/extreme_heat_long.csv',index_col=0)
vers_id = sys.argv[1]
version = extreme_heat.index[int(vers_id)]

# def process_baseline(version):
version_datetime = pd.to_datetime(version)
version_string = str(version_datetime.strftime("%Y-%m-%d"))
version_otg_hr = str(version_datetime.hour)
version_year = str(version_datetime.year)
date_path = outputs_path + version_string

window_start = version_datetime - datetime.timedelta(days=1)
window_end = version_datetime + datetime.timedelta(days=2)

version_string = str(version_datetime.strftime("%Y-%m-%d"))
sample_dates = [[str(window_start.strftime("%m/%d %H:%M:%S"))],[str(window_end.strftime("%m/%d %H:%M:%S"))]]
index = ['start','end']
columns = ['Date/Time']
sample = pd.DataFrame(sample_dates,index,columns)
sample['Date/Time']= pd.to_datetime(sample['Date/Time'], format = '%m/%d %H:%M:%S')

# Make new summary folders
summary_path = date_path + "/" + "summary"
if not os.path.exists(summary_path):
    os.makedirs(summary_path)
# BASELINES
# - Temperature
baseline_temperature = pd.DataFrame(columns = models)

# - Humidity
baseline_humidity = pd.DataFrame(columns = models)

# - Heat Index
baseline_heatindex = pd.DataFrame(columns = models)

# - Electricity
baseline_electricity =pd.DataFrame(columns = models)

# - Gas 
baseline_gas = pd.DataFrame(columns = models)

for each_model in models:
    ## Baseline
    # Create empty dataframe
    baseline = pd.DataFrame()

    # Read the baseline output file
    data = pd.read_csv(date_path + '/baseline/' + each_model + '/eplusout.csv')
    data = data.loc[data['LIVING ZONE:Zone Air Temperature [C](Hourly)'].notnull()]
    baseline['Date/Time'] = data['Date/Time']
    baseline['Outdoor Temp'] = data['LIVING ZONE:Zone Outdoor Air Drybulb Temperature [C](Hourly)']
    baseline['RH'] = data['LIVING ZONE:Zone Air Relative Humidity [%](Hourly)']
    baseline['Indoor Temp'] = data['LIVING ZONE:Zone Air Temperature [C](Hourly)']
    baseline['Electricity'] = data['Electricity:Facility [J](Hourly)']
    if 'NaturalGas:Facility [J](TimeStep)' in data:
        baseline['Gas'] = data['NaturalGas:Facility [J](TimeStep)']
    # Change '24:00:00' to "00:00:00", set datetime, add one day to midnight values, reset index, and format
    baseline['Date/Time'] = baseline['Date/Time'].str.strip()
    baseline['Date/Time'] = baseline['Date/Time'].str.replace('24:00:00','00:00:00')
    baseline['Date/Time'] = pd.to_datetime(baseline['Date/Time'],format = '%m/%d  %H:%M:%S')
    baseline.loc[baseline['Date/Time'].dt.hour == 0,'Date/Time'] = baseline.loc[baseline['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')
    baseline = baseline.reset_index(drop=True)

    # Trim down just to sample dates
    baseline = baseline.loc[(baseline['Date/Time'] >= sample['Date/Time'][0]) & (baseline['Date/Time'] <= sample['Date/Time'][1])]
    baseline = baseline.reset_index(drop=True)
    
    # Transfer to consilidated list 
    baseline_temperature[each_model] = baseline["Indoor Temp"]
    baseline_humidity[each_model] = baseline["RH"]
    baseline_electricity[each_model] = baseline["Electricity"]
    if 'Gas' in baseline:
        baseline_gas[each_model] = baseline["Gas"]
        
    ## Heat Index
    hi_list = []
    for each_day in baseline_humidity.index:
        HI = 0
        raw_rh = baseline_humidity[each_model][each_day]
        rh = int(np.floor(raw_rh/5)*5)
        if rh >= 40: 
            raw_temp = C_to_F(baseline_temperature[each_model][each_day])
            temp = int(np.floor(raw_temp/2)*2)
            good = heat_index.loc[(heat_index.index == rh)]#
            if temp >= 80:
                HI = int(good[str(temp)])
        hi_list.append(HI)
    baseline_heatindex[each_model] = hi_list 
    if each_model == models[0]:
        # Save Outdoor Data
        outdoor = pd.DataFrame()
        data = pd.read_csv(date_path + '/baseline/' + each_model + '/eplusout.csv')
        data = data.loc[data['LIVING ZONE:Zone Air Temperature [C](Hourly)'].notnull()]
        outdoor['Date/Time'] = data['Date/Time']
        outdoor['Outdoor Temp'] = data['LIVING ZONE:Zone Outdoor Air Drybulb Temperature [C](Hourly)']
        outdoor

        # Change '24:00:00' to "00:00:00", set datetime, add one day to midnight values, reset index, and format
        outdoor['Date/Time'] = outdoor['Date/Time'].str.strip()
        outdoor['Date/Time'] = outdoor['Date/Time'].str.replace('24:00:00','00:00:00')
        outdoor['Date/Time'] = pd.to_datetime(outdoor['Date/Time'],format = '%m/%d  %H:%M:%S')
        outdoor.loc[outdoor['Date/Time'].dt.hour == 0,'Date/Time'] = outdoor.loc[outdoor['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')
        outdoor = outdoor.reset_index(drop=True)

        # Trim down just to sample dates
        outdoor = outdoor.loc[(outdoor['Date/Time'] >= sample['Date/Time'][0]) & (outdoor['Date/Time'] <= sample['Date/Time'][1])]
        outdoor = outdoor.reset_index(drop=True)

        outdoor.to_csv(summary_path + '/outdoor.csv',index=False)        
# Save as CSV
baseline_temperature = baseline_temperature.set_index(baseline['Date/Time'])
baseline_humidity = baseline_humidity.set_index(baseline['Date/Time'])
baseline_electricity = baseline_electricity.set_index(baseline['Date/Time'])
baseline_heatindex = baseline_heatindex.set_index(baseline['Date/Time'])
baseline_heatindex.to_csv(summary_path + "/baseline_heatindex.csv",index=True)
baseline_temperature.to_csv(summary_path + "/baseline_temperature.csv",index=True)
baseline_humidity.to_csv(summary_path + "/baseline_humidity.csv",index=True)
baseline_electricity.to_csv(summary_path + "/baseline_electricity.csv",index=True)
if not baseline_gas.empty:
    baseline_gas = baseline_gas.set_index(baseline['Date/Time'])
    baseline_gas.to_csv(summary_path + "/baseline_gas.csv",index=True)
baseline = baseline.reset_index(drop=True)
baseline_temperature = baseline_temperature.reset_index(drop=True)


# OUTAGE
def process(models,version,each_start):
    each_start_str = str(version_datetime.hour + each_start)
    start_summary_path = date_path + "/summary/" + each_start_str
    if not os.path.exists(start_summary_path):
        os.makedirs(start_summary_path)
    # - Temperature
    outage_temperature = pd.DataFrame(columns = models)
    
    # - Humidity
    outage_humidity = pd.DataFrame(columns = models)
    
     # - Humidity
    outage_heatindex = pd.DataFrame(columns = models)
    
    # - Temperature Difference
    outage_temp_diff = pd.DataFrame(columns = models)
    
    # - Electricity
    outage_electricity = pd.DataFrame(columns = models)
    
    # - Gas
    outage_gas = pd.DataFrame(columns = models)

    for each_model in models: 

        ## Outage
        # Create empty dataframe
        outage = pd.DataFrame()

        data = pd.read_csv(date_path + "/" + each_start_str + "/" + each_model + '/eplusout.csv')
        data = data.loc[data['LIVING ZONE:Zone Air Temperature [C](Hourly)'].notnull()]
        outage['Date/Time'] = data['Date/Time']
        outage['Outdoor Temp'] = data['LIVING ZONE:Zone Outdoor Air Drybulb Temperature [C](Hourly)']
        outage['Indoor Temp'] = data['LIVING ZONE:Zone Air Temperature [C](Hourly)']
        outage['RH'] = data['LIVING ZONE:Zone Air Relative Humidity [%](Hourly)']
        outage['Electricity'] = data['Electricity:Facility [J](Hourly)']
        if 'NaturalGas:Facility [J](TimeStep)' in data:
            outage['Gas'] = data['NaturalGas:Facility [J](TimeStep)']

        outage['Date/Time'] = outage['Date/Time'].str.strip()
        outage['Date/Time'] = outage['Date/Time'].str.replace('24:00:00','00:00:00')
        outage['Date/Time'] = pd.to_datetime(outage['Date/Time'],format = '%m/%d  %H:%M:%S')

        outage.loc[outage['Date/Time'].dt.hour == 0,'Date/Time'] = outage.loc[outage['Date/Time'].dt.hour == 0]['Date/Time'] + np.timedelta64(1,'D')

        outage=outage.reset_index(drop=True)

        # Reduce to near outage
        outage = outage.loc[(outage['Date/Time'] >= sample['Date/Time'][0]) & (outage['Date/Time'] <= sample['Date/Time'][1])]
        outage = outage.reset_index(drop=True)
        outage_temperature[each_model] = outage['Indoor Temp']
        outage_humidity[each_model] = outage['RH']
        outage_electricity[each_model] = outage["Electricity"]
        outage_temp_diff[each_model] = outage['Indoor Temp'] - baseline_temperature[each_model]

        if 'Gas' in outage.columns:
            outage_gas[each_model] = outage["Gas"]
        outage = outage.set_index(outage['Date/Time'])
        # heat index
        hi_list = []
        for each_day in outage_humidity.index:
            rh = outage_humidity[each_model][each_day]
            t = C_to_F(outage_temperature[each_model][each_day])
            HI = calc_HI(t,rh)
#             HI = 0
#             raw_rh = outage_humidity[each_model][each_day]
#             rh = int(np.floor(raw_rh/5)*5)
#             if rh >= 40: 
#                 raw_temp = C_to_F(outage_temperature[each_model][each_day])
#                 temp = int(np.floor(raw_temp/2)*2)
#                 good = heat_index.loc[(heat_index.index == rh)]#
#                 if temp >= 80:
#                     HI = int(good[str(temp)])
            hi_list.append(HI)
        outage_heatindex[each_model] = hi_list
        
    outage_temperature = outage_temperature.set_index(outage['Date/Time'])
    outage_temp_diff = outage_temp_diff.set_index(outage['Date/Time'])
    outage_humidity = outage_humidity.set_index(outage['Date/Time'])
    outage_electricity = outage_electricity.set_index(outage['Date/Time'])
    outage_heatindex = outage_heatindex.set_index(outage['Date/Time'])

    outage_temperature.to_csv(start_summary_path + "/outage_temperature.csv",index=True)
    outage_temp_diff.to_csv(start_summary_path + "/outage_temp_diff.csv",index=True)
    outage_humidity.to_csv(start_summary_path + "/outage_humidity.csv",index=True)
    outage_electricity.to_csv(start_summary_path + "/outage_electricity.csv",index=True)
    outage_heatindex.to_csv(start_summary_path + "/outage_heatindex.csv",index=True)

    if not outage_gas.empty:
        outage_gas =  outage_gas.set_index(outage['Date/Time'])
        outage_gas.to_csv(start_summary_path + "/outage_gas.csv",index=True)
        
     
        
async def process_outages(models,version,otg_start_diff):
    process_loop = asyncio.get_event_loop()
    futures = [process_loop.run_in_executor(None,process,models,version,each_start) for each_start in otg_start_diff]

process_loop = asyncio.new_event_loop()
process_loop.run_until_complete(process_outages(models,version,otg_start_diff))

