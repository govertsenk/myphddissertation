## Import things:
import pandas as pd 
import os
import shutil
import datetime 
import glob
import subprocess

## Constants 
study = ["baseline","outage"] #
og_wd = os.getcwd()
data_file_path  =  str(og_wd)
data_file_path = data_file_path.replace(os.sep, '/')
models_path = data_file_path + '/Models/'
schedules_path = data_file_path + '/Schedule Files/'
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"

# Path the ReadVarsESO.exe
read_var_file_path = "C:/devel/community-thermal-resilience/ReadVarsESO.exe"

# Modfiy weather file name here:
new_weather = "USA_MA_Worcester.Rgnl.AP.725095_TMY3.epw"

# Modify Power Outage Here: 
otg_date = "July 24" # start outage on this day
otg_hour = "12" # start outage just after this hour
otg_len = ["2","4","6","8","12","24","48"] # approximate hours

# example: Simulate outage from 12:01 PM to 1:59 PM on 7/24: 

# otg_date = "July 24" # start outage on this day
# otg_hour = "12" # start outage just after this hour
# otg_len = ["2"] # approximate hours

# Clear Output Folder
output_path = data_file_path + '/Outputs/'
if os.path.exists(output_path):
    shutil.rmtree(output_path)

# Identify all the models
models = []
# Iterate directory
for model in os.listdir(models_path):
    # check only text files
    if model.endswith('.osm'):
        models.append(model)

# Create new output folders for each scenario 
for each_study in study:
    new_path = data_file_path + "/Outputs/" + each_study
    if not os.path.exists(new_path):
        os.makedirs(new_path)
    if each_study == 'baseline':
        new_path = data_file_path + "/Outputs/" + each_study 
        if not os.path.exists(new_path):
            os.makedirs(new_path)  
        for each_model in models:
            new_path = data_file_path + "/Outputs/" + each_study + "/" + each_model[:-4]
            if not os.path.exists(new_path):
                    os.makedirs(new_path)
    if each_study == 'outage':
        new_path = data_file_path + "/Outputs/" + each_study 
        if not os.path.exists(new_path):
            os.makedirs(new_path)  
        for each_otg in otg_len:
            new_path = data_file_path + "/Outputs/" + each_study + "/" + each_otg 
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            for each_model in models:
                new_path = data_file_path + "/Outputs/" + each_study + "/" + each_otg + "/" + each_model[:-4]
                if not os.path.exists(new_path):
                    os.makedirs(new_path)

# Create Schedules for each scenario         
schedules = []
# check that schedule for model exists 
for schedule in os.listdir(schedules_path):
    for each_model in models: 
        if not schedule.endswith(each_model[:-4] + '.csv'):
            print('Schedule File for ' + each_model[:-4] + 'does not exist. please find and add to Schedule Files folder',"\n")
            break 
        for each_study in study:
            if each_study == 'baseline':
                #SAVE BASELINE SCHEDULES WITHOUT HEADERS 
                schedule_path = schedules_path + schedule
                baseline_schedule_path = data_file_path + "/Outputs/" + each_study + "/" + each_model[:-4] + "/" + each_model[:-4] + '_baseline.csv'
                shutil.copyfile(schedule_path,baseline_schedule_path)
                baseline_schedule = pd.read_csv(baseline_schedule_path)
                baseline_schedule.to_csv(baseline_schedule_path,index = False,header=False) 
            if each_study == 'outage':
                # Create Schedules for Outages (# SAVE WITHOUT HEADERS)
                for each_otg in otg_len:
                    new_path = data_file_path + "/Outputs/" + each_study +"/" + each_otg + "/" + each_model[:-4]
                    original_schedule_path = schedules_path + schedule
                    outage_schedule_path = new_path + '/' + each_model[:-4] + '_outage_' + each_otg + '.csv'
                    shutil.copyfile(original_schedule_path,outage_schedule_path)
                    outage_schedule = pd.read_csv(outage_schedule_path)
                    otg_start = pd.to_datetime(otg_date + " " + otg_hour + ":00:00",format = "%B %d %H:%M:%S")
                    otg_hr_end = int(otg_hour) + int(each_otg)
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
                    #print(otg_end)
                                                       
                    time = pd.DataFrame(pd.date_range('1900-01-01 00:00:00', '1900-12-31 23:45:00', freq='15T'),columns=['Datetime'])
                    otg_start = otg_start + datetime.timedelta(minutes=75)
                    #otg_end = otg_end + datetime.timedelta(minutes=30)
                    # print(otg_start)
                    # print(otg_end)
                    change = time.loc[(time['Datetime'] >= otg_start) & (time['Datetime'] <= otg_end)].index.array
                    outage_schedule.loc[change,:]=0
                    #print(change)
                    outage_schedule.to_csv(outage_schedule_path,index = False,header=False)  
                

                
# # Start Simulating
for each_study in study:
    if each_study == 'baseline':
       for each_model in models:
            new_path = data_file_path + "/Outputs/" + each_study + "/" + each_model[:-4]
            this_schedules_path = new_path + "/" + each_model[:-4] + '_baseline.csv'

            # Save schedule in main folder as 'schedules.csv' (IF YOU DO NOT DO THIS, IT WILL NOT RUN)
            shutil.copyfile(this_schedules_path,original_schedule_name)

            # this_schedules = each_model[:-4] + '_baseline.csv'
            # this_schedules_path = new_path + "/" + this_schedules_name
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

            # run 
            file_to_run = data_file_path + "/run_this_model.bat"
            os.system(file_to_run)
            
            #save baseline osm in output folder
            destination = new_path + "/" + each_model[:-4] + "_baseline.osm"
            shutil.copyfile(new_osm,destination)
            
            # change output filename and save in data_folder
            source = data_file_path + "/run/eplusout.sql"
            destination = new_path + "/eplusout.sql"
            shutil.copyfile(source,destination)
            
            # change output filename and save in data_folder
            source = data_file_path + "/run/eplusout.eso"
            destination = new_path + "/eplusout.eso"
            shutil.copyfile(source,destination)
            
            # Add and Run ReadVarsESO
            destination = new_path + "/eplusout.eso"
            shutil.copyfile(read_var_file_path,new_path + "/ReadVarsESO.exe")
            
            os.chdir(os.path.abspath(new_path))
            old_name = new_path + "/eplusout.csv"
            new_name = new_path + "/" + each_model[:-4] + "_" + each_study + "_eplusout.csv"

            cwd = os.getcwd()

            subprocess.run(["ReadVarsESO"], shell=True)

            # Renaming the file
            os.rename(old_name, new_name)

            os.chdir(cwd)
            os.chdir(og_wd)
        
    if each_study == 'outage': 
        for each_otg in otg_len:
            for each_model in models:
                new_path = data_file_path + "/Outputs/" + each_study + "/" + each_otg + "/" + each_model[:-4]
                this_schedules_path = new_path + "/" + each_model[:-4] + '_' + each_study + '_' + each_otg + '.csv'
                
                # Save schedule in main folder as 'schedules.csv'
                shutil.copyfile(this_schedules_path,original_schedule_name)
                
                # copy and paste
                shutil.copyfile(data_file_path + "/run_all_models_" + each_study + ".osw",data_file_path + "/run_this_model.osw")
                
                # open the file as a readable file
                with open(data_file_path + "/run_this_model.osw",'r') as file:
                    data = file.read()
                    
                    new_osm = data_file_path + "/Models/" + each_model 

                    #replace with new osm
                    data = data.replace(original_osm, new_osm)

                    # replace with new weather file (baseline)
                    data = data.replace(original_weather,new_weather)
                                       
                    # replace the 
                    data = data.replace("variable_otg_date",otg_date)
                    data = data.replace("variable_otg_hour",otg_hour)
                    data = data.replace("variable_otg_len",each_otg)
                    
                with open(data_file_path + "/run_this_model.osw",'w') as file:
                    file.write(data)
                    
                # run 
                file_to_run = data_file_path + "/run_this_model.bat"
                os.system(file_to_run)

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
                
                # change output osm and save in data_folder
                source = data_file_path + "/measures/PowerOutage/new_model.osm"
                destination = new_path + "/" + each_model[:-4] + "_outage_" + each_otg + "hr.osm"
                shutil.copyfile(source,destination)
                
                # Add and Run ReadVarsESO
                destination = new_path + "/eplusout.eso"
                shutil.copyfile(read_var_file_path,new_path + "/ReadVarsESO.exe")
                
                os.chdir(os.path.abspath(new_path))
                old_name = new_path + "/eplusout.csv"
                new_name = new_path + "/" + each_model[:-4] + "_" + each_study + "_" + each_otg + "_eplusout.csv"

                cwd = os.getcwd()

                subprocess.run(["ReadVarsESO"], shell=True)

                # Renaming the file
                os.rename(old_name, new_name)

                os.chdir(cwd)
                os.chdir(og_wd)