## Folder Structure
	• ProjectName (in this case it's Template
		○ Measures
			§ AddHoulyMeters
			§ AddOutputVariable
			§ Plus any others you get from bcl.org/make
		○ Models
			§ .osm files of every bldg you want to model
		○ Outputs
			§ Blank to start… but will fill with folders, .err and .out files as necessary
		○ Schedules
			§ .csv named same as .osm files in /MODELS/
## Files
#Environment(.yml)
	• create custom environment from this .yml file
		○ follow guidance on how to here: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file
		○ Add this environment to the batch_simulate.sh file instead of kg_env_310

# Weather File (.epw)
	• USA_MA_Worcester.Rgnl.AP.725095_TMY3.epw 
		○ This can be changed. Just be sure the change the file name in run_simulations.py
		
# Python(.py): 
	• run_simulation.py
		○ MODIFY THESE:
			§ new_weather : Be sure to edit the weather file to right name 
			§ study: you can keep as baseline if you'd like. But then also change name of run_this_model_baseline.osw 
			§ version: this is to name/number trials if you need to
		○ IF YOU RUN A SECOND STUDY… you'll need to
			§ Add it to study =[]
			§ Make output folders for it 
			§ Make schedules for it (maybe)
			§ Make a run_this_model_OTHERSTUDY.osw file (see below)
	
# Open Studio Workflow (.osw - JSON)
	• Run_this_model_baseline.osw
		○ In this file you change the measure_dir_name, variable_name, and frequency to what you need. 
	• Run_this_model_OTHER.osw
		○ If you want to run another study to compare to the baseline, copy this .osw file, rename it, and add your own measure names and inputs. 
		
# Shell Scripts
- Run_this_model.sh (is written during run_simulations.py) 
- Batch_simulate.sh (EDIT TO FIT YOUR NEEDS)
		○ Change output file paths 
		○ Change environment if you need too
		○ Add python folders if you need to
		○ Change partitions as needed (express for fast jobs <1 hr, short for < 24 hr )
		○ Change nodes as needed
		○ Change time as needed