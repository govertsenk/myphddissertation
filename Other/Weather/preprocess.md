## Import things:
import pandas as pd 
import os
import shutil
import datetime 

## Constants 
scenario = ["SSP119"]#,"SSP126","SSP245","SSP370","SSP585"]
years = ["2025"]#,"2050"."2075","2075"]
percent = ["5%"]#,"50%","95%"]
run = ["0"] # range 0 -99
og_wd = os.getcwd()
data_file_path  =  str(og_wd)
data_file_path = data_file_path.replace(os.sep, '/')
models_path = data_file_path + '/Models/'
schedules_path = data_file_path + '/Schedule Files/'
weather_path = data_file_path + '/Weather Files/'
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"
original_output_path = "output_path"

# TODO:
# Identify Weather/Folder Names
weather_names = []
for each_file in os.listdir(weather_path):
    # check only text files
    if each_file.endswith('.epw'):
        weather_names.append(each_file)

# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model)

# break for loops into functions                 
# - check that weather files exist (error and return)
# - create output folders (/scenario_year_#%_r##/(6000) ... /bldg### (315))
# - copy schedule into output folder as 'schedules.csv'
# - copy weather into output folder as 'weather.epw'
# - save openstudio run folder to output folder in .osw 
# - create and save run_this_model.osw file into output folder

# have function with multiple inputs to eliminate 

for each_scenario in scenario:
    for each_year in years:
        for each_percent in percent:
            for each_run in run:
                new_weather = "USA_MA_Worcester.Rgnl.AP.725095_TMY3" + each_scenario + "_" + each_year + "_" + each_percent + "_r" + each_run + ".epw"
                
                # Check that the weather file exists 
                if not os.path.exists(data_file_path + "/Weather Files/" + new_weather)
                    print(new_weather + " Does Not Exist")
                    return
                
                # Create Ouptut folder as scenario_year_percent%_r###
                new_path = data_file_path + "Output/" + each_scenario + "_" + each_year + "_" + each_percent + "%_r" + each_run 
                if not os.path.exists(new_path)
                    os.makedirs(new_path)
                
                for each_model in models:
                    newer_path = new_path + "/" + each_model[:-4]
                    if not os.path.exists(newer_path)
                        os.makedirs(newer_path) 
                    
                    # Copy and Paste Weather as "weather.epw" into the output folder     
                    shutil.copyfile(data_file_path + "/Weather Files/" + new_weather,original_weather)
                    
                    this_schedules_path = schedules_path + each_model[:-4] + '.csv'
        
                    # Save schedule in main folder as 'schedules.csv' (IF YOU DO NOT DO THIS, IT WILL NOT RUN)
                    shutil.copyfile(this_schedules_path,original_schedule_name)
        
                    # copy the baseline template and paste
                    shutil.copyfile(data_file_path + "/run_all_models.osw",data_file_path + "/run_this_model.osw")
                    # open the file as a readable file
                    with open(data_file_path + "/run_this_model.osw",'r') as file:
                        data = file.read()
                        
                        new_osm = data_file_path  + "/Models/" + each_model
        
                        #replace with new osm
                        data = data.replace(original_osm, new_osm)
                    
                    with open(data_file_path + "/run_this_model.osw",'w') as file:
                        file.write(data)
                
                    # run simulation from shell script
                    file_to_run = data_file_path + "/run_this_model.sh"
                    os.system(file_to_run)
        
                    #save baseline osm in output folder
                    destination = new_path + "/" + each_model[:-4] + ".osm"
                    shutil.copyfile(new_osm,destination)
        
                    # change output filename and save in data_folder
                    source = data_file_path + "/run/eplusout.sql"
                    destination = new_path + "/eplusout.sql"
                    shutil.copyfile(source,destination)
                    
                    # change output filename and save in data_folder
                    source = data_file_path + "/run/eplusout.eso"
                    destination = new_path + "/eplusout.eso"
                    shutil.copyfile(source,destination)
                    
                    # change output filename and save in data_folder
                    source = data_file_path + "/run/eplusout.err"
                    destination = new_path + "/eplusout.err"
                    shutil.copyfile(source,destination)
            
