  ## Import things:
import pandas as pd 
import os
import shutil

## Constants 
study = ["baseline"]
og_wd = os.getcwd()
data_file_path  =  str(og_wd)
data_file_path = data_file_path.replace(os.sep, '/')
models_path = data_file_path + '/Models/'
schedules_path = data_file_path + '/Schedule Files/'
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"
version = "trial_1" # this is good to keep track of your versions

# Modfiy weather file name here:
new_weather = "USA_MA_Worcester.Rgnl.AP.725095_TMY3.epw"
        
# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model)


#Create new output folders for each scenario 
for each_study in study:
    new_path = data_file_path + "/Outputs/" + version
    if not os.path.exists(new_path):
        os.makedirs(new_path)
    new_path = data_file_path + "/Outputs/" + version + "/" + each_study 
    if not os.path.exists(new_path):
        os.makedirs(new_path)  
    for each_model in models:
        new_path = data_file_path + "/Outputs/" + version + "/" + each_study + "/" + each_model[:-4]
        if not os.path.exists(new_path):
                os.makedirs(new_path)
                    
# Check that Schedule for Model Exists 
for each_model in models:
    schedule = each_model[:-4] + '.csv'
    if not os.path.exists(schedules_path + schedule):
        print('Schedule File for ' + each_model[:-4] + 'does not exist. please find and add to Schedule Files folder',"\n")
        break
    
# Modify and Move Schedules         
for each_model in models: 
    for each_study in study:
        if each_study == 'baseline':
            #SAVE BASELINE SCHEDULES WITHOUT HEADERS 
            schedule_path = schedules_path + each_model[:-4] + '.csv'
            baseline_schedule_path = data_file_path + "/Outputs/" + version + "/"  + each_study + "/" + each_model[:-4] + "/" + each_model[:-4] + '_baseline.csv'
            shutil.copyfile(schedule_path,baseline_schedule_path)
            baseline_schedule = pd.read_csv(baseline_schedule_path)
            baseline_schedule.to_csv(baseline_schedule_path,index = False,header=False) 
        
# Start Simulating
for each_study in study:
    for each_model in models:
        new_path = data_file_path + "/Outputs/" + version + "/"  + each_study + "/" + each_model[:-4]
        this_schedules_path = new_path + "/" + each_model[:-4] + "_" + each_study + ".csv"

        # Save schedule in main folder as 'schedules.csv' (IF YOU DO NOT DO THIS, IT WILL NOT RUN)
        shutil.copyfile(this_schedules_path,original_schedule_name)

        # copy the baseline template and paste
        shutil.copyfile(data_file_path + "/run_all_models_" + each_study + ".osw",data_file_path + "/run_this_model.osw")
        
        # open the file as a readable file
        with open(data_file_path + "/run_this_model.osw",'r') as file:
            data = file.read()
            
            new_osm = data_file_path  + "/Models/" + each_model

            #replace with new osm
            data = data.replace(original_osm, new_osm)

            # replace with new weather file (baseline)
            data = data.replace(original_weather,new_weather)
        
        with open(data_file_path + "/run_this_model.osw",'w') as file:
            file.write(data)

        # Create .sh file
        osw_name = og_wd.replace(os.sep, '/') + "/run_this_model.osw"
        shell_script = "#!/bin/bash\nsingularity exec /shared/container_repository/OpenStudio/openstudio-3_2_1.sif openstudio run -w " + """'""" + osw_name + """'"""
        with open ('run_this_model.sh', 'w') as rsh:
            rsh.write(shell_script)

        # Run .sh file aka call openstudio container to read your file
        file_to_run = data_file_path + "/run_this_model.sh"
        os.system(file_to_run)

        #save baseline osm in output folder
        destination = new_path + "/" + each_model[:-4] + "_" + each_study + ".osm"
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
            
        