import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
data_file_path = "Data/"

metadata = pd.read_csv(data_file_path + 'Models_Worcester_Metadata.csv')
metadata_cols = ['bldg_id','in.geometry_floor_area','in.geometry_wall_exterior_finish','in.roof_material','in.geometry_building_type_acs','in.vintage','in.hvac_heating_type_and_fuel','in.hvac_cooling_type']
metadata=metadata[metadata_cols]
num_models = len(metadata)
hvi_p = pd.read_csv(data_file_path + 'hvi_p.csv')

actual_parcels = pd.read_csv(data_file_path + 'Worcester_Tax_Parcels.csv')
properties = pd.read_csv(data_file_path + 'scraped_properties.csv')
properties['mblu'] = properties['mblu'].str.replace("-","_")
# Drop where roof & wall & heat == NONE
properties=properties.loc[properties['roof']!='NONE']
properties = properties.loc[properties['wall']!='NONE']
properties =properties.loc[properties['heat']!='NONE']

# Drop where area = 0
properties =properties.loc[properties['area']!=0]

# drop where area == F, Yes, Typical, 3, \xa0
properties.loc[(properties['ac'] != '\xa0') |
      (properties['ac'] != 'F') |
       (properties['ac'] != 'Yes') |
       (properties['ac'] != 'Typical') |
        (properties['ac'] != '3')]

# drop where wall = metal
properties = properties.loc[properties['wall']!='Metal']
properties = properties.reset_index(drop=True)

properties=properties.loc[(properties['units'] != '\xa0')]
properties['units'] = properties['units'].astype(float)

merged_parcels = pd.merge(actual_parcels, properties, how='left',left_on='PROP_ID',right_on='mblu')
merged_parcels = merged_parcels.set_index(merged_parcels['LOC_ID'])
/tmp/ipykernel_5951/3499341497.py:16: DtypeWarning: Columns (23) have mixed types. Specify dtype option on import or set low_memory=False.
 actual_parcels = pd.read_csv(data_file_path + 'Worcester_Tax_Parcels.csv')
parcels = pd.DataFrame(index=merged_parcels['LOC_ID'].unique(),columns=['year', 'style', 'units', 'tot_units', 'heat', 'ac',
    'wall', 'roof', 'area'])
for each_loc in merged_parcels['LOC_ID'].unique():
  matches = merged_parcels.loc[merged_parcels['LOC_ID']==each_loc]
  matches = matches.reset_index(drop=True)
  if (len(matches) == 1):
    parcels['year'][each_loc] = matches['year'][0]
    parcels['style'][each_loc] = matches['style'][0]
    parcels['units'][each_loc] = matches['units'][0]
    parcels['tot_units'][each_loc] = matches['tot_units'][0]
    parcels['heat'][each_loc] = matches['heat'][0]
    parcels['ac'][each_loc] = matches['ac'][0]
    parcels['wall'][each_loc] = matches['wall'][0]
    parcels['roof'][each_loc] = matches['roof'][0]
    parcels['area'][each_loc] = matches['area'][0]
  if len(matches) > 1:
    matches = matches.loc[matches['mblu'].notnull()]
    matches = matches.reset_index(drop=True)
    if len(matches) == 1: 
      parcels['year'][each_loc] = matches['year'][0]
      parcels['style'][each_loc] = matches['style'][0]
      parcels['units'][each_loc] = matches['units'][0]
      parcels['tot_units'][each_loc] = matches['tot_units'][0]
      parcels['heat'][each_loc] = matches['heat'][0]
      parcels['ac'][each_loc] = matches['ac'][0]
      parcels['wall'][each_loc] = matches['wall'][0]
      parcels['roof'][each_loc] = matches['roof'][0]
      parcels['area'][each_loc] = matches['area'][0]
    if len(matches) > 1:
      submatches = matches[['year', 'style', 'units', 'tot_units', 'heat', 'ac',
  'wall', 'roof','area']]  
      if len(submatches.loc[submatches.duplicated()==False]) == 1:
        submatches = submatches.loc[submatches.duplicated()==False]
        submatches = submatches.reset_index(drop=True)
        parcels['year'][each_loc] = submatches['year'][0]
        parcels['style'][each_loc] = submatches['style'][0]
        parcels['units'][each_loc] = submatches['units'][0]
        parcels['tot_units'][each_loc] = submatches['tot_units'][0]
        parcels['heat'][each_loc] = submatches['heat'][0]
        parcels['ac'][each_loc] = submatches['ac'][0]
        parcels['wall'][each_loc] = submatches['wall'][0]
        parcels['roof'][each_loc] = submatches['roof'][0]
        parcels['area'][each_loc] = submatches['area'][0]
      if len(submatches.loc[submatches.duplicated()==False]) > 1:
        parcels['year'][each_loc] = submatches['year'].mode()[0]
        parcels['style'][each_loc] = submatches['style'].mode()[0]
        parcels['units'][each_loc] = submatches['units'].mode()[0]
        parcels['tot_units'][each_loc] = submatches['tot_units'].mode()[0]
        parcels['heat'][each_loc] = submatches['heat'].mode()[0]
        parcels['ac'][each_loc] = submatches['ac'].mode()[0]
        parcels['wall'][each_loc] = submatches['wall'].mode()[0]
        parcels['roof'][each_loc] = submatches['roof'].mode()[0]
        parcels['area'][each_loc] = submatches['area'].mean()
# Drop NA
parcels=parcels.dropna()
# Change to integers
parcels['units']=parcels['units'].astype('int')
parcels['tot_units']= parcels['tot_units'].astype('int')

# Initialize Column
parcels['num_units']=0
# Where total units > units, set num_units as total units
parcels.loc[parcels['units']<parcels['tot_units'],'num_units'] = parcels['tot_units'].loc[parcels['units']<parcels['tot_units']]
# Where units > total units, set num_units as units
parcels.loc[parcels['tot_units'] < parcels['units'],'num_units'] = parcels['units'].loc[parcels['tot_units'] < parcels['units']]
# Where total units == units, set num_units as units
parcels.loc[parcels['num_units'] == 0,'num_units'] = parcels['units'].loc[parcels['num_units'] == 0]
# Reduce to just the cols we need
parcels[['year', 'style', 'num_units', 'heat', 'ac',
    'wall', 'roof', 'area']]

num_parcels = len(parcels)
# Vintage
parcels['vintage'] = ""
parcels.loc[parcels['year'] < 1940, 'vintage'] = "<1940"
parcels.loc[(parcels['year'] >= 1940) & (parcels['year'] < 1950), 'vintage'] = "1940s"
parcels.loc[(parcels['year'] >= 1950) & (parcels['year'] < 1960), 'vintage'] = "1950s"
parcels.loc[(parcels['year'] >= 1960) & (parcels['year'] < 1970), 'vintage'] = "1960s"
parcels.loc[(parcels['year'] >= 1970) & (parcels['year'] < 1980), 'vintage'] = "1970s"
parcels.loc[(parcels['year'] >= 1980) & (parcels['year'] < 1990), 'vintage'] = "1980s"
parcels.loc[(parcels['year'] >= 1990) & (parcels['year'] < 2000), 'vintage'] = "1990s"
parcels.loc[(parcels['year'] >= 2000) & (parcels['year'] < 2010), 'vintage'] = "2000s"
parcels.loc[(parcels['year'] >= 2010), 'vintage'] = "2010s"
## Vintage Type Bar Chart
parcels['vintage_ix']=0
parcels.loc[parcels['vintage'] == '<1940','vintage_ix'] = 0 
parcels.loc[parcels['vintage'] == '1940s','vintage_ix'] = 1 
parcels.loc[parcels['vintage'] == '1950s','vintage_ix'] = 2 
parcels.loc[parcels['vintage'] == '1960s','vintage_ix'] = 3 
parcels.loc[parcels['vintage'] == '1970s','vintage_ix'] = 4 
parcels.loc[parcels['vintage'] == '1980s','vintage_ix'] = 5 
parcels.loc[parcels['vintage'] == '1990s','vintage_ix'] = 6 
parcels.loc[parcels['vintage'] == '2000s','vintage_ix'] = 7 
parcels.loc[parcels['vintage'] == '2010s','vintage_ix'] = 8 
metadata['vintage_ix']=0
metadata.loc[metadata['in.vintage'] == '<1940','vintage_ix'] = 0 
metadata.loc[metadata['in.vintage'] == '1940s','vintage_ix'] = 1 
metadata.loc[metadata['in.vintage'] == '1950s','vintage_ix'] = 2 
metadata.loc[metadata['in.vintage'] == '1960s','vintage_ix'] = 3 
metadata.loc[metadata['in.vintage'] == '1970s','vintage_ix'] = 4 
metadata.loc[metadata['in.vintage'] == '1980s','vintage_ix'] = 5 
metadata.loc[metadata['in.vintage'] == '1990s','vintage_ix'] = 6 
metadata.loc[metadata['in.vintage'] == '2000s','vintage_ix'] = 7 
metadata.loc[metadata['in.vintage'] == '2010s','vintage_ix'] = 8
v_ids = metadata['vintage_ix'].unique()
v_ids.sort()
vintage = ['<1940','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s']

parcels=parcels.sort_values(by='vintage_ix', ascending=True)
# Vintage as Dwelling Units: 
num_dwellings = parcels['num_units'].sum()
vintage_stats = pd.DataFrame(index =v_ids,columns = ['Properties','Models'])
for each_index in v_ids:
  vintage_stats.loc[vintage_stats.index == each_index,'Properties'] = 100*parcels['num_units'].loc[parcels['vintage_ix'] == each_index].sum()/num_dwellings
  vintage_stats.loc[vintage_stats.index == each_index,'Models'] = 100*len(metadata.loc[metadata['vintage_ix'] == each_index])/num_models
fig = plt.figure(figsize=(5,2.5),dpi=360)
vintage_stats.plot(kind='bar',stacked=False,color = {'Properties':'blue',"Models":'green'},ax=plt.gca())
plt.xlabel('Vintage')
plt.ylabel('Percent(%) of Units\nin Housing Stock')
plt.xticks(ticks = vintage_stats.index,labels=vintage)
plt.yticks(ticks=np.arange(0,80,10))
plt.ylim([0,70])
plt.title('Vintage Distribution of Housing Stock\nby Percent of Units')
plt.savefig("Figures/Final/vintage_bar.png",bbox_inches = "tight")

# USE UNIT TO DOUBLE CHECK: 
parcels['style_type']= ""
# Assign Style First By Num Units:
parcels.loc[(parcels['num_units'] == 2), 'style_type'] = '2 Unit'
parcels.loc[((parcels['num_units'] >= 3) & (parcels['num_units']<= 4)), 'style_type'] = '3 or 4 Unit'
parcels.loc[((parcels['num_units'] >= 5) & (parcels['num_units'] <=9)) , 'style_type'] = '5 to 9 Unit'
parcels.loc[((parcels['num_units'] >= 10) & (parcels['num_units'] <=19)) , 'style_type'] = '10 to 19 Unit'
parcels.loc[((parcels['num_units'] >= 20) & (parcels['num_units'] <=49)) , 'style_type'] = '20 to 49 Unit'
parcels.loc[(parcels['num_units'] >= 50), 'style_type'] = '50 or more Unit'

# Consider Style Next
parcels.loc[((parcels['units'] == 1) & (parcels['style'] == "Conventional")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Raised Ranch")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Ranch")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Colonial")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Bungalow")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Cape Cod")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Tudor")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Modern")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Split Level")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Victorian")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Raised Cape")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Two Family")), 'style_type'] = "2 Unit"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Two Family Conversio")), 'style_type'] = "2 Unit"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Duplex")), 'style_type'] = "2 Unit"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Three Fam Conversion")), 'style_type'] = "3 or 4 Unit"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Three Family")), 'style_type'] = "3 or 4 Unit"
parcels.loc[((parcels['units'] == 1) &(parcels['style'] == "Multi Res 4-8 Units")), 'style_type'] = "5 to 9 Unit"
parcels.loc[((parcels['units'] == 1) & (parcels['style'] == "Half Duplex")), 'style_type'] = "Single-Family Attached"
parcels.loc[((parcels['units'] == 1) & (parcels['style'] == "Converted small apt")), 'style_type'] = "Single-Family Detached"
parcels.loc[((parcels['units'] == 0) & (parcels['style'] == "Converted small apt")), 'style_type'] = "Single-Family Detached"
# NEW STYLE
parcels['type_ix']=0
parcels.loc[parcels['style_type'] == 'Single-Family Detached','type_ix'] = 1 
parcels.loc[parcels['style_type'] == 'Single-Family Attached','type_ix'] = 2
parcels.loc[parcels['style_type'] == '2 Unit','type_ix'] = 3
parcels.loc[parcels['style_type'] == '3 or 4 Unit','type_ix'] = 4 
parcels.loc[parcels['style_type'] == '5 to 9 Unit','type_ix'] = 5 
parcels.loc[parcels['style_type'] == '10 to 19 Unit','type_ix'] = 6
parcels.loc[parcels['style_type'] == '20 to 49 Unit','type_ix'] = 7 
parcels.loc[parcels['style_type'] == '50 or more Unit','type_ix'] = 8 
parcels=parcels.sort_values(by='style_type', ascending=True)
print(parcels['type_ix'].unique())
metadata['type_ix']=0
metadata.loc[metadata['in.geometry_building_type_acs'] == 'Mobile Home','type_ix'] = 0 
metadata.loc[metadata['in.geometry_building_type_acs'] == 'Single-Family Detached','type_ix'] = 1 
metadata.loc[metadata['in.geometry_building_type_acs'] == 'Single-Family Attached','type_ix'] = 2 
metadata.loc[metadata['in.geometry_building_type_acs'] == '2 Unit','type_ix'] = 3 
metadata.loc[metadata['in.geometry_building_type_acs'] == '3 or 4 Unit','type_ix'] = 4 
metadata.loc[metadata['in.geometry_building_type_acs'] == '5 to 9 Unit','type_ix'] = 5 
metadata.loc[metadata['in.geometry_building_type_acs'] == '10 to 19 Unit','type_ix'] = 6 
metadata.loc[metadata['in.geometry_building_type_acs'] == '20 to 49 Unit','type_ix'] = 7 
metadata.loc[metadata['in.geometry_building_type_acs'] == '50 or more Unit','type_ix'] = 8 
metadata=metadata.sort_values(by='type_ix', ascending=True)
ids = metadata['type_ix'].unique()
ids.sort()

style_stats = pd.DataFrame(index = metadata['type_ix'].unique(),columns = ['Properties','Models'])
for each_index in style_stats.index:
  style_stats.loc[style_stats.index == each_index,'Properties'] = 100*len(parcels.loc[parcels['type_ix'] == each_index])/num_parcels
  style_stats.loc[style_stats.index == each_index,'Models'] = 100*len(metadata.loc[metadata['type_ix'] == each_index])/num_models

# Type as Dwelling Units: 
num_dwellings = parcels['num_units'].sum()
style_stats = pd.DataFrame(index = metadata['type_ix'].unique(),columns = ['Properties','Models'])
for each_index in style_stats.index:
  style_stats.loc[style_stats.index == each_index,'Properties'] = 100*parcels['num_units'].loc[parcels['type_ix'] == each_index].sum()/num_dwellings
  style_stats.loc[style_stats.index == each_index,'Models'] = 100*len(metadata.loc[metadata['type_ix'] == each_index])/num_models
fig = plt.figure(figsize=(5,2.5),dpi=360)
style_stats.plot(kind='bar',stacked=False,color = {'Properties':'blue',"Models":'green'},ax=plt.gca())
styles = ['Mobile Home','S.F. Detached','S.F. Attached','2 Unit','3 or 4 Unit','5 to 9 Unit','10 to 19 Unit','20 to 49 Unit','50 + Unit']
plt.xlabel('Type')
plt.ylabel('Percent(%) of Units\nin Housing Stock')
plt.xticks(ticks = style_stats.index,labels=styles)
plt.yticks(ticks=np.arange(0,80,10))
plt.ylim([0,45])
plt.title('Type Distribution of Housing Stock\nby Percent of Units')
plt.savefig("Figures/Final/type_bar.png",bbox_inches = "tight")
[6 3 7 4 5 8 2 1]

# AC
parcels['ac_type']=""
parcels.loc[(parcels['ac']== "None"),'ac_type'] = "None"
parcels.loc[(parcels['ac']== "Heat Pump"),'ac_type'] = "Heat Pump"
parcels.loc[(parcels['ac']== "Central"),'ac_type'] = "Central AC"
parcels.loc[(parcels['ac']== "Par Central"),'ac_type'] = "Central AC"
parcels.loc[(parcels['ac']== "Partial Wall"),'ac_type'] = "Room AC"
parcels.loc[(parcels['ac']== "Wall Units"),'ac_type'] = "Room AC"
parcels.loc[(parcels['ac']== "AC"),'ac_type'] = "Room AC"

# Style Type Bar Chart
parcels['ac_ix']=0
parcels.loc[parcels['ac_type'] == 'None','ac_ix'] = 0 
parcels.loc[parcels['ac_type'] == 'Central AC','ac_ix'] = 1
parcels.loc[parcels['ac_type'] == 'Room AC','ac_ix'] = 2
parcels.loc[parcels['ac_type'] == 'Heat Pump','ac_ix'] = 3 

# Style Type Bar Chart
metadata['ac_ix']=0
metadata.loc[metadata['in.hvac_cooling_type'] == 'None','ac_ix'] = 0 
metadata.loc[metadata['in.hvac_cooling_type'] == 'Central AC','ac_ix'] = 1
metadata.loc[metadata['in.hvac_cooling_type'] == 'Room AC','ac_ix'] = 2
metadata.loc[metadata['in.hvac_cooling_type'] == 'Heat Pump','ac_ix'] = 3 
metadata=metadata.sort_values(by='ac_ix', ascending=True)
a_ids = metadata['ac_ix'].unique()
a_ids.sort()
ac =['None','Central AC','Room AC','Heat Pump']

ac_stats = pd.DataFrame(index = a_ids,columns = ['Properties','Models'])
for each_index in a_ids:
  ac_stats.loc[ac_stats.index == each_index,'Properties'] = 100*len(parcels.loc[parcels['ac_ix'] == each_index])/num_parcels
  ac_stats.loc[ac_stats.index == each_index,'Models'] = 100*len(metadata.loc[metadata['ac_ix'] == each_index])/num_models

# Vintage as Dwelling Units: 
num_dwellings = parcels['num_units'].sum()
ac_stats = pd.DataFrame(index =a_ids,columns = ['Properties','Models'])
for each_index in a_ids:
  ac_stats.loc[ac_stats.index == each_index,'Properties'] = 100*parcels['num_units'].loc[parcels['ac_ix'] == each_index].sum()/num_dwellings
  ac_stats.loc[ac_stats.index == each_index,'Models'] = 100*len(metadata.loc[metadata['ac_ix'] == each_index])/num_models
fig = plt.figure(figsize=(5,2.5),dpi=360)
ac_stats.plot(kind='bar',stacked=False,color = {'Properties':'blue',"Models":'green'},ax=plt.gca())
plt.xlabel('AC Type')
plt.ylabel('Percent(%) of Units\nin Housing Stock')
plt.xticks(ticks = ac_stats.index,labels=ac)
plt.yticks(ticks=np.arange(0,100,10))
plt.ylim([0,90])
plt.title('Air Conditioning Distribution of Housing Stock\nby Percent of Units')
plt.savefig("Figures/Final/ac_bar.png",bbox_inches = "tight")

# Rename Types to Shorter Styles
parcels.loc[parcels['style_type'] == 'Single-Family Detached','style_type'] = 'S.F. Detached'
parcels.loc[parcels['style_type'] == 'Single-Family Attached','style_type'] = 'S.F. Attached'
parcels.loc[parcels['style_type'] == '50 or more Unit','style_type'] = '50 + Unit'

# Keep only LOC_ID, Vintage, Type, and AC 
matched_parcels=parcels[['vintage','style_type','ac_type','num_units']]
v_ids = matched_parcels['vintage'].unique()
v_ids.sort()

t_ids = matched_parcels['style_type'].unique()
t_ids.sort()
matched_parcels
each_vintage = v_ids[0]
each_type = t_ids[0]
subset = matched_parcels.loc[(matched_parcels['vintage']==each_vintage) & (matched_parcels['style_type'] == each_type) & (matched_parcels['ac_type']== 'None')]
subset.empty
True
no_ac_plot = pd.DataFrame(index=styles,columns=vintage)

for each_type in t_ids:
  for each_vintage in v_ids: 
    subset = matched_parcels.loc[(matched_parcels['vintage']==each_vintage) & (matched_parcels['style_type'] == each_type) & (matched_parcels['ac_type']== 'None')]
    if subset.empty is False:
      no_ac_plot[each_vintage][each_type]=len(subset)
    else:
      no_ac_plot[each_vintage][each_type]=0
ac_plot = pd.DataFrame(index=styles,columns=vintage)
for each_type in t_ids:
  for each_vintage in v_ids: 
    subset = matched_parcels.loc[(matched_parcels['vintage']==each_vintage) & (matched_parcels['style_type'] == each_type) & (matched_parcels['ac_type']!= 'None')]
    if subset.empty is False:
      ac_plot[each_vintage][each_type]=len(subset)
    else:
      ac_plot[each_vintage][each_type]=0
no_ac_plot.loc[no_ac_plot.index=='Mobile Home'] = 0
ac_plot.loc[ac_plot.index=='Mobile Home'] = 0
num_no = no_ac_plot.sum().sum()
num_ac = ac_plot.sum().sum()

# add total to columns and index
no_ac_plot['Type Total'] = no_ac_plot.sum(axis=1)
ac_plot['Type Total'] = ac_plot.sum(axis=1)
no_ac_plot.loc['Vintage Total'] = no_ac_plot.sum()
ac_plot.loc['Vintage Total'] = ac_plot.sum()
ac_plot = ac_plot.apply(pd.to_numeric, errors='coerce',downcast='integer')
no_ac_plot = no_ac_plot.apply(pd.to_numeric, errors='coerce',downcast='integer')
/tmp/ipykernel_5951/2466234503.py:10: FutureWarning: The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.
 no_ac_plot=no_ac_plot.append(no_series)
/tmp/ipykernel_5951/2466234503.py:12: FutureWarning: The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.
 ac_plot=ac_plot.append(ac_series)
colors = sns.color_palette('Greys', 7)
levels = [0, 1, 10, 100, 1000,10000,20000]
cmap, norm = mpl.colors.from_levels_and_colors(levels, colors, extend="max")
f,(ax1,ax2) = plt.subplots(ncols=2,figsize=(10, 5),dpi=360)
sns.heatmap(no_ac_plot,ax=ax1,cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
sns.heatmap(ac_plot,ax=ax2,cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
ax1.title.set_text('Without AC (n='+str(num_no)+')')
ax2.title.set_text('With AC (n='+str(num_ac)+')')
f.subplots_adjust(wspace = .5)
plt.suptitle('Tax Assessed Properties in Worcester',y=1)
f.text(0.5, -0.07, 'Vintage', ha='center')
f.text(-0.01, 0.5, 'Type', va='center', rotation='vertical')
plt.savefig("Figures/Final/properties_heat.png",bbox_inches = "tight")

# Rename Types to Shorter Styles
metadata.loc[metadata['in.geometry_building_type_acs'] == 'Single-Family Detached','in.geometry_building_type_acs'] = 'S.F. Detached'
metadata.loc[metadata['in.geometry_building_type_acs'] == 'Single-Family Attached','in.geometry_building_type_acs'] = 'S.F. Attached'
metadata.loc[metadata['in.geometry_building_type_acs'] == '50 or more Unit','in.geometry_building_type_acs'] = '50 + Unit'
metadata=metadata.sort_values(by='vintage_ix', ascending=True)
v_ids = metadata['in.vintage'].unique()
metadata=metadata.sort_values(by='type_ix', ascending=True)
t_ids = metadata['in.geometry_building_type_acs'].unique()
nrel_no_ac_plot = pd.DataFrame(index=t_ids,columns=v_ids)
for each_type in t_ids:
  for each_vintage in v_ids: 
    subset = metadata.loc[(metadata['in.vintage']== each_vintage) & (metadata['in.geometry_building_type_acs']== each_type) & (metadata['ac_ix']==0)]
    if len(subset) > 0:
      nrel_no_ac_plot[each_vintage][each_type]=len(subset)
    else:
      nrel_no_ac_plot[each_vintage][each_type]=0

nrel_ac_plot = pd.DataFrame(index=t_ids,columns=v_ids)
for each_type in t_ids:
  for each_vintage in v_ids: 
    subset = metadata.loc[(metadata['in.vintage']== each_vintage) & (metadata['in.geometry_building_type_acs']== each_type) & (metadata['ac_ix']!=0)]
    if len(subset) > 0:
      nrel_ac_plot[each_vintage][each_type]=len(subset)
    else:
      nrel_ac_plot[each_vintage][each_type]=0
# no_ac_plot = no_ac_plot.apply(pd.to_numeric, errors='coerce')
num_no_nrel = nrel_no_ac_plot.sum().sum()
num_ac_nrel = nrel_ac_plot.sum().sum()

# add total to columns and index
nrel_no_ac_plot['Type Total'] = nrel_no_ac_plot.sum(axis=1)
nrel_ac_plot['Type Total'] = nrel_ac_plot.sum(axis=1)
nrel_no_ac_plot.loc['Vintage Total'] = nrel_no_ac_plot.sum()
nrel_ac_plot.loc['Vintage Total'] = nrel_ac_plot.sum()
nrel_ac_plot = nrel_ac_plot.apply(pd.to_numeric, errors='coerce',downcast='integer')
nrel_no_ac_plot = nrel_no_ac_plot.apply(pd.to_numeric, errors='coerce',downcast='integer')
/tmp/ipykernel_5951/3702315702.py:34: FutureWarning: The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.
 nrel_no_ac_plot=nrel_no_ac_plot.append(no_series)
/tmp/ipykernel_5951/3702315702.py:36: FutureWarning: The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.
 nrel_ac_plot=nrel_ac_plot.append(ac_series)
f,(ax1,ax2) = plt.subplots(ncols=2,figsize=(10, 5),dpi=360)
sns.heatmap(nrel_no_ac_plot,ax=ax1,cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
sns.heatmap(nrel_ac_plot,ax=ax2,cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
ax1.title.set_text('Without AC (n='+str(num_no_nrel)+')')
ax2.title.set_text('With AC (n='+str(num_ac_nrel)+')')
f.subplots_adjust(wspace = .5)
plt.suptitle('Data Availability in NREL EULP',y=1)
f.text(0.5, -0.07, 'Vintage', ha='center')
f.text(-0.01, 0.5, 'Type', va='center', rotation='vertical')
plt.savefig("Figures/Final/nrel_heat.png",bbox_inches = "tight")

f,axs = plt.subplots(nrows=2,ncols=2,figsize=(8, 5),dpi=360)#,sharex=True,sharey=True)
sns.heatmap(no_ac_plot,ax=axs[0,0],cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
sns.heatmap(ac_plot,cbar=False, ax=axs[0,1],annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
sns.heatmap(nrel_no_ac_plot,ax=axs[1,0],cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
sns.heatmap(nrel_ac_plot,ax=axs[1,1],cbar=False, annot=True,fmt='.0f',annot_kws={"fontsize":8},cmap = cmap, norm=norm)
axs[0,0].title.set_text('Properties Without AC (n='+str(num_no)+')')
axs[0,1].title.set_text('Properties With AC (n='+str(num_ac)+')')
axs[1,0].title.set_text('Models Without AC (n='+str(num_no_nrel)+')')
axs[1,1].title.set_text('Models With AC (n='+str(num_ac_nrel)+')')
f.subplots_adjust(wspace = .5,hspace=.75)
f.suptitle('Data Availability',y=1)
f.text(0.5, -0.05, 'Vintage', ha='center')
f.text(-0.01, 0.5, 'Type', va='center', rotation='vertical')

plt.savefig("Figures/Final/both_heat.png",bbox_inches = "tight")

for each_v in v_ids:
  for each_t in t_ids:
    if len(matched_parcels.loc[(matched_parcels['vintage'] == each_v) & (matched_parcels['style_type'] == each_t)]) > 0:
      for each_hr in range(13):
        matched_parcels.loc[(matched_parcels['vintage'] == each_v) & (matched_parcels['style_type'] == each_t), str(each_hr)] = hvi_p.loc[(hvi_p['vintage'] == each_v) & (hvi_p['type'] == each_t), str(each_hr)].values[0]
matched_parcels.to_csv(data_file_path + 'matched_parcels.csv',index=False)

 
