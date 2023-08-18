import shutil
import pandas as pd
import subprocess
import os
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor

# Constants 
original_osm = "bldg#######.osm"
original_weather = "weather.epw"
original_schedule_name = "schedules.csv"
original_output_path = "output_path"

og_wd = os.getcwd()
og_wd = str(og_wd).replace(os.sep, '/')
data_file_path = og_wd + '/Data/'
weather_file_path = data_file_path + 'Weather/'
template_osw = og_wd + "/template.osw"
puma = 'G25003400'


# Asyncio Definitions:
async def process_model(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, md,each_model):
    # copy the osw template and paste into folder
    model_output_path = puma_output_path + "/" + each_model
    this_osw = model_output_path + "/" + each_model + ".osw"

    shutil.copyfile(template_osw,this_osw)

    # Move Schedule into folder as 'schedules.csv'
    schedule_path = schedules_path + each_model + '.csv'
    shutil.copyfile(schedule_path,model_output_path + "/schedules.csv")
    
    this_weather = weather_file_path + str(md['in.nhgis_county_gisjoin'].loc[md['bldg_id']==each_model].item()) + '.epw'

    # open the osw file as a readable file
    with open(this_osw,'r') as file:
        data = file.read()

        this_osm = models_path + each_model + ".osm"

        #replace with new osm
        data = data.replace(original_osm, this_osm)

        # replace with new weather file (baseline)
        data = data.replace(original_weather,this_weather)

        # replace with new output path
        data = data.replace(original_output_path,model_output_path)

    with open(this_osw,'w') as file:
        file.write(data)

async def process_models(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, md,models):
    tasks = []
    for each_model in models:
        task = asyncio.create_task(process_model(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path,md, each_model))
        tasks.append(task)
    await asyncio.gather(*tasks)

async def run_model(each_model_script):
    process = await asyncio.create_subprocess_shell(each_model_script)
    return process

async def run_model_with_executor(executor, each_model_script):
    loop = asyncio.get_running_loop()
    process = await loop.run_in_executor(executor, subprocess.run, each_model_script)
    return process

async def run_models_with_executor(executor, puma_output_path, these_models):
    tasks = []
    for each_model in these_models:
        model_output_path = puma_output_path + "/" + each_model
        this_osw = model_output_path + "/" + each_model + ".osw"
        shell_script = r'''C:\openstudio-3.2.1\bin\openstudio.exe run -w "{osw}"'''.format(osw=this_osw)
        task = asyncio.create_task(run_model_with_executor(executor, shell_script))
        tasks.append(task)
    await asyncio.gather(*tasks)

async def main():
    # Call the main function
    await process_models(template_osw, schedules_path, models_path, original_osm, original_weather, original_output_path, puma_output_path, md, models)

    # Create a thread pool executor
    max_workers = 6  # Set the maximum number of concurrent subprocesses
    executor = ThreadPoolExecutor(max_workers=max_workers)

    # Run models with thread pool executor
    await run_models_with_executor(executor, puma_output_path, models)

    # Shutdown the executor to release resources
    executor.shutdown()

puma_path = os.path.join(data_file_path, puma)
if os.path.isdir(puma_path):
    models_path = puma_path + '/Models/'
    schedules_path = puma_path + '/Schedules/'
    # for each_folder in /Weather/
        # if each_folder == 'AMY:
            # for each_folder in /Weather/AMY
                #this_weather = puma_path + '/Weather/TMY3/' + str(os.listdir(puma_path + '/Weather/TMY3/')[0])
                #outputs_path = og_wd + '/Output/' + 
        # Else: 
    md = pd.read_csv(puma_path + '/Models_Metadata_' + puma + '.csv')
    md['bldg_id'] = md['bldg_id'].astype(str).str.zfill(7)
    md['bldg_id'] = 'bldg' + md['bldg_id']

    # Make output folder:
    outputs_path = og_wd + '/Output/'
    if not os.path.exists(outputs_path):
            os.makedirs(outputs_path)
    
    # outputs_path = og_wd + '/Output/AMY/'

    # if not os.path.exists:
    #        os.makedirs(outputs_path)
    # outputs_path = og_wd + '/Output/TMY3'

    # if not os.path.exists
    #        os.makedirs(outputs_path)      
    puma_output_path = outputs_path + puma
    if not os.path.exists(puma_output_path):
            os.makedirs(puma_output_path)

    # Identify all the models
    models = []
    # Iterate directory
    for model in os.listdir(models_path):
        # check only text files
        if model.endswith('.osm'):
            model_name = model[:-4]
            models.append(model_name)
        model_output_path = puma_output_path + '/' + model_name
        if not os.path.exists(model_output_path):
                os.makedirs(model_output_path)
    # models = [models[0]] # test on one first 
    asyncio.run(main())

