import os.path
from re import S 
import webbrowser
import shutil
import pandas as pd
import numpy
import gzip
import time
import csv

# SET THE FOLLOWING:

# Filepath of your working folder
file_path = 'C:/devel/community-thermal-resilience'

# Filepath to your data folder
data_folder = file_path + "/Data/"

#Filepath of your downloads folder
download_folder = "C:/Users/govertsen.k/Downloads/"

#The City of Worcester's PUMA Code is G25000300. Change this if you are using another PUMA.(https://www2.census.gov/geo/pdfs/reference/puma/2010_PUMA_Names.pdf)
puma = 'G25000300'

########################################################################## DO NOT CHANGE FROM HERE DOWN.##########################################################################

# If metadata does not exist in your data folder, download it and move it to data folder. 
if not os.path.isfile(data_folder + 'Models_Metadata.csv'):

    # Download metadata from OPEN EI
    metadata_link = 'https://oedi-data-lake.s3.amazonaws.com/nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2021/resstock_amy2018_release_1/metadata/metadata.parquet'
    webbrowser.open(metadata_link)

    # Wait for file to download
    while not os.path.exists(download_folder + 'metadata.parquet'):
        time.sleep(1)

    if os.path.isfile(download_folder + 'metadata.parquet'):
    # Move from downloads to Data folder 
        for x in os.listdir(download_folder):
            if x.endswith(".parquet"):
                metadata_files = x
                shutil.copyfile(download_folder + metadata_files, data_folder + metadata_files)

        md = pd.read_parquet(data_folder + "metadata.parquet")

        # Reduce to just rows in the puma 
        md = md[md['in.puma'] == puma]

        # Save new metadata file (HELP)
        new_md = md.to_csv(data_folder + 'Models_Metadata.csv')

        # Delete download files
        os.remove(download_folder + metadata_files)

