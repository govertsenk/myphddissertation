library(rgdal)
library("data.table")
library(sf)
library(ggplot2)
library(raster)
library(geomerge)
library(ggthemes)
library(RColorBrewer)
library(ggmap)
library(ggpubr)
library(ggspatial)
library(tidyr)
library(spdep)

H = 7
W = 6
D = 360
M = 20
Font= 24

# Get the "RdYlBu" color palette with 9 colors
color_palette <- brewer.pal(n = 9, name = "RdYlBu")
color_palette2 <- brewer.pal(n = 4, name = "RdYlBu")
# Extract the individual colors from the palette
color1 <- color_palette[1]
color2 <- color_palette[2]
color3 <- color_palette[3]
color4 <- color_palette[4]
color5 <- color_palette[5]
color6 <- color_palette[6]
color7 <- color_palette[7]
color8 <- color_palette[8]
color9 <- color_palette[9]

# Extract the individual colors from the palette
colorA <- color_palette2[1]
colorB <- color_palette2[2]
colorC <- color_palette2[3]
colorD <- color_palette2[4]

# Load data
working_path <-'C:/Users/govertsen.k/Northeastern University/ABLE_Lab - U_2018 Govertsen - U_2018 Govertsen/Research/Dissertation/'
file_path <- paste(working_path,'Data/',sep = '')
figure_path <- paste(working_path,'August/figures/Maps/',sep = '')

# Tree Projects
tree_path <- paste(file_path,'Workshops/Tree_Projects/TreeProjects.shp',sep = '')
tree_shapefile <- read_sf(tree_path)

# Vulnerable Areas 
vulnerable_path <- paste(file_path,'Workshops/Vulnerable_Areas/Vulnerable Areas.shp',sep = '')
areas_shapefile <- read_sf(vulnerable_path)

## Worcester Shapefile
city_path <- paste(file_path,'Worcester_boundary/Worcester_boundary.shp',sep = '')
city_shapefile <- read_sf(city_path)

# Plot greyed out city:
city_map <- ggplot(city_shapefile) + 
  geom_sf(fill = "grey75", color = NA) + 
  theme_map()


## Census Shapefiles
census_path <- paste(file_path,'Census_Tracts/Census_Tracts_2020.shp',sep = '')
census_shapefile <- read_sf(census_path)

census_shapefile$Description <- ifelse(census_shapefile$NAME20 %in% c(7312.02,7329.02), "University", "Other")
bbox <- st_bbox(census_shapefile)

# Create the plot with labels and color based on NAME20 condition
tract_map <- ggplot() +
  geom_sf(data = census_shapefile, aes(fill = Description)) +
  scale_fill_manual(values = c("white", "lightgrey")) +
  geom_sf_text(
    data = subset(census_shapefile, NAME20 %in% c(7312.02,7329.02)),  # select tracts where NAME20 == 7 or 8
    aes(label = NAME20),
    size = 2,
    color = "red",
    fontface = "bold",check_overlap = TRUE) +
  geom_sf_text(
    data = subset(census_shapefile, !(NAME20 %in% c(7312.02,7329.02))),  # select tracts where NAME20 != 7 or 8
    aes(label = NAME20),
    size = 2,
    color = "black",
    nudge_y = -0.002,
    fontface = "bold",check_overlap = TRUE)+
  labs(title = "Census Tracts") +
  xlim(c(bbox[1], bbox[3])) +
  ylim(c(bbox[2], bbox[4]))+
  theme_map()+
  theme(legend.position = c(1, 1), # Top right
        legend.justification = c(1, 1), # Top right
        legend.box.just = "right",
        plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# tract_map
ggsave(paste(figure_path,"tract_map.png",sep = ''), plot =tract_map , width = W, height = H, dpi = D)

# drop university tracts
census_shapefile <- subset(census_shapefile, TRACTCE20 != 731202)
census_shapefile <- subset(census_shapefile, TRACTCE20 != 732902)
tract_names <- unique(census_shapefile$NAME20)
census_shapefile$area <- st_area(census_shapefile)

# Load Public Transit Stops and Stop Times Data
stops <- read.table(paste0(file_path, "WRTA/stops.txt"), header = TRUE, sep = ",")
stop_times <- read.table(paste0(file_path, "WRTA/stop_times.txt"), header = TRUE, sep = ",")

# Convert Stops Data to Spatial Data and Join with Census Shapefile
stops_sf <- st_as_sf(stops, coords = c("stop_lon", "stop_lat"),crs = st_crs(4326))

# Trim down to stops in city boundary:
stops_sf <- st_transform(stops_sf, st_crs(city_shapefile))
stops_sf <- st_join(stops_sf, city_shapefile, join = st_intersects)
stops_sf <- stops_sf[stops_sf$town=='WORCESTER', ]

# Calculate Number of Departures for Each Stop
for (each_stop in unique(stops_sf$stop_id)) {
  num_dep <- sum(stop_times$stop_id == each_stop)
  stops_sf$num_dep[stops_sf$stop_id == each_stop] <- as.numeric(num_dep)
}
crs <- st_crs(stops_sf)
selected_columns <- c("stop_id", "stop_code", "stop_name", "geometry", "num_dep")
stops_sf <- stops_sf[selected_columns]
# st_write(stops_sf, paste0(file_path,"rta_stops.shp"),crs=crs)
stops_sf <- st_transform(stops_sf, st_crs(census_shapefile))
stops_sf <- st_join(stops_sf, census_shapefile, join = st_within)

# Assign Total Number of Departures to Census Tracts
for (each_tract in tract_names) {
  # Calculate the sum of non-NA values
  sum_num_dep <- as.numeric(sum(stops_sf$num_dep[stops_sf$NAME20 == each_tract], na.rm = TRUE))
  census_shapefile[which(census_shapefile$NAME20 == each_tract), 'num_dep'] <- sum_num_dep
}
census_shapefile$num_dep
# Access to green space: 
green_path <- paste(file_path,'Open Space/Open_Space.shp',sep = '')
green_space <- read_sf(green_path)
# drop owned by massport OWNERSHIP_CLASS == MassPort
green_space <- green_space[green_space$OWNERSHIP_ != 'MassPort', ]
crs <- st_crs(green_space)
# st_write(green_space, paste0(file_path,"green_space.shp"),crs=crs)

green_space <- st_transform(green_space, st_crs(census_shapefile))

# Perform spatial join to assign census tract to each green_space polygon
green_space <- st_join(green_space, census_shapefile, join = st_within)

# Calculate area of each green space polygon
green_space$green_area <- st_area(green_space)

for (each_tract in tract_names) {
  # Calculate the sum of non-NA values
  sum_area <- sum(green_space$green_area[green_space$NAME20 == each_tract], na.rm = TRUE)
  census_shapefile[which(census_shapefile$NAME20 == each_tract), 'green_space'] <- sum_area
}

# Calculate the percentage of each tract's area that is green space
census_shapefile$percent_green <- as.numeric(100*(census_shapefile$green_space/census_shapefile$area))

# Access to blue space: (https://www.worcesterma.gov/parks/activities/beaches-pools-spray-parks)
manmade_blue_space <- read.table(paste0(file_path, "manmade_bluespace.txt"), header = TRUE, sep = ",")

# Convert blue space to Spatial Data and Join with Census Shapefile
manmade_blue_space <- st_as_sf(manmade_blue_space, coords = c("Lon", "Lat"), crs = st_crs(4326))
# Change from lat lon points to .25 mile circle 

# Define the radius for the buffer (0.25 miles)
radius_miles <- 0.25

# Convert radius to meters
radius_meters <- radius_miles * 1609.34

# Create a buffer around the points in blue_space
manmade_blue_space_buffer <- st_buffer(manmade_blue_space, dist = radius_meters)

# Specify the coordinate system (CRS)
crs <- st_crs(manmade_blue_space)

# save both
# st_write(manmade_blue_space, paste0(file_path,"manmade_bluespace.shp"),crs=crs)

# Save buffer data as shapefile
# st_write(manmade_blue_space_buffer, paste0(file_path,"manmade_bluespace_buffer.shp"),crs=crs)

# Add lakes, ponds, rivers
blue_path <- paste(file_path,'Lakes_Ponds_and_Rivers/Lakes_Ponds_and_Rivers.shp',sep = '')
blue_space <- read_sf(blue_path)
crs <- st_crs(blue_space)

# drop upland and wetarea
blue_space <- blue_space[blue_space$TYPE != 'UPLAND', ]
blue_space <- blue_space[blue_space$TYPE != 'WETAREA', ]
# st_write(blue_space, paste0(file_path,"natural_bluespace.shp"),crs=crs)

blue_space <- st_transform(blue_space, st_crs(census_shapefile))
blue_space <- st_join(blue_space, manmade_blue_space_buffer)
blue_space <- st_join(blue_space, census_shapefile, join = st_within)

# Calculate area of each green space polygon
blue_space$area <- st_area(blue_space)

for (each_tract in tract_names) {
  # Calculate the sum of non-NA values
  sum_area <- sum(blue_space$area[blue_space$NAME20 == each_tract], na.rm = TRUE)
  census_shapefile[which(census_shapefile$NAME20 == each_tract), 'blue_space'] <- sum_area
}

# Calculate the percentage of each tract's area that is blue space
census_shapefile$percent_blue <- as.numeric(100*(census_shapefile$blue_space/census_shapefile$area))


## Parcel Shapefiles
polygon_path <- paste(file_path,"Parcel_Polygons/M348TaxPar_CY21_FY21.shp",sep = '')
parcels_shapefile <- read_sf(polygon_path)

## Age
age_path <- paste(file_path,'Census/S0101.csv',sep = '')
age_data <- read.csv(file = age_path, header = TRUE)

## Poverty
poverty_path <- paste(file_path,'Census/S1701.csv',sep = '')
poverty_data <- read.csv(file = poverty_path, header = TRUE)

## Disabled
disabled_path <- paste(file_path,'Census/S1810.csv',sep = '')
disabled_data <- read.csv(file = disabled_path, header = TRUE)

## Home Owner
ownership_path <- paste(file_path,'Census/DP04.csv',sep = '')
ownership_data <- read.csv(file = ownership_path, header = TRUE)

## Parcel data
parcel_path <- paste(file_path,'matched_parcels.csv',sep = '')
parcels_data <- read.csv(file = parcel_path, header = TRUE)

## Social Capital
social_path <- paste(file_path,'social_capital.csv',sep = '')
social_data <- read.csv(file = social_path, header = TRUE)
# reduce to matching social data and newest 
social_data <- social_data[social_data$geoid %in% census_shapefile$GEOID20,] 
social_data <- social_data[social_data$year == max(social_data$year), ]

## Urban Heat Island
uhi_path <- paste(file_path,'UHI/UHI_2022.shp',sep = '')
uhi_shapefile <- read_sf(uhi_path)

## Vintage Prob
vintage_path <- paste(file_path,'vintage_prob.csv',sep = '')
vintage_data <- read.csv(file = vintage_path, header = TRUE)

## Vintage Prob
type_path <- paste(file_path,'type_prob.csv',sep = '')
type_data <- read.csv(file = type_path, header = TRUE)

# Add Factors Blanks to census shapefile:
blank <- array(0, dim = c(nrow(census_shapefile), 1))

# Function to perform z-score transformation
z_score <- function(x) {
  
  # Calculate the mean and standard deviation of the input vector
  mean_x <- mean(x,na.rm = TRUE)
  sd_x <- sd(x,na.rm = TRUE)
  
  # Perform z-score transformation
  z <- (x - mean_x) / sd_x
  
  # Return the z-score transformed vector
  return(z)
}

assign_index_neg <- function(df, col_name, target_col_name) {
  z <- z_score(df[[col_name]])
  mean_col <- mean(z, na.rm = TRUE)
  sd_col <- sd(z, na.rm = TRUE)
  
  for (i in 1:nrow(df)) {
    c <- z[i]
    if (!is.na(c)) {
      if (c < mean_col - 2 * sd_col) {
        df[[target_col_name]][i] <- 1
      } else if (mean_col - 2 * sd_col <= c & c <= mean_col - sd_col) {
        df[[target_col_name]][i] <- 2
      } else if (mean_col - sd_col < c & c <= mean_col) {
        df[[target_col_name]][i] <- 3
      } else if (mean_col < c & c <= mean_col + sd_col) {
        df[[target_col_name]][i] <- 4
      } else if (mean_col + sd_col < c & c <= mean_col + 2 * sd_col) {
        df[[target_col_name]][i] <- 5
      } else if (mean_col + 2 * sd_col <= c) {
        df[[target_col_name]][i] <- 6
      }
    } else {
      df[[target_col_name]][i] <- 1
    }
  }
  
  if (any(df[[target_col_name]] != 1)){
  
    df[[target_col_name]][which.min(z)] <- 1
  }
  if (any(df[[target_col_name]] != 6)){
   
    df[[target_col_name]][which.max(z)] <- 6
  }
  
  
  if (!any(df[[target_col_name]] == 2)){
    second_smallest_index <- which(z == sort(unique(z))[2])  # Find the index of the second smallest value in the z array
    df[[target_col_name]][second_smallest_index] <- 2
  }
  
  if (!any(df[[target_col_name]] == 5)){
    second_largest_index <- which(z == sort(unique(z), decreasing = TRUE)[2])  # Find the index of the second largest value in the z array
    df[[target_col_name]][second_largest_index] <- 5
  }
  
  
  return(df)
}

assign_index_pos <- function(df, col_name, target_col_name) {
  z <- z_score(df[[col_name]])
  mean_col <- mean(z, na.rm = TRUE)
  sd_col <- sd(z, na.rm = TRUE)
  
  for (i in 1:nrow(df)) {
    c <- z[i]
    if (!is.na(c)) {
      if (c < mean_col - 2 * sd_col) {
        df[[target_col_name]][i] <- 6
      } else if (mean_col - 2 * sd_col <= c & c <= mean_col - sd_col) {
        df[[target_col_name]][i] <- 5
      } else if (mean_col - sd_col < c & c <= mean_col) {
        df[[target_col_name]][i] <- 4
      } else if (mean_col < c & c <= mean_col + sd_col) {
        df[[target_col_name]][i] <- 3
      } else if (mean_col + sd_col < c & c <= mean_col + 2 * sd_col) {
        df[[target_col_name]][i] <- 2
      } else if (mean_col + 2 * sd_col <= c) {
        df[[target_col_name]][i] <- 1
      }
    } else {
      df[[target_col_name]][i] <- 6
    }
  }
  

  if (any(df[[target_col_name]] != 1)){
    df[[target_col_name]][which.max(z)] <- 1
  }
  if (any(df[[target_col_name]] != 6)){
    df[[target_col_name]][which.min(z)] <- 6}
  
  if (!any(df[[target_col_name]] == 2)){
    second_largest_index <- which(z == sort(unique(z), decreasing = TRUE)[2])  
    df[[target_col_name]][second_largest_index] <- 2
  }
  
  if (!any(df[[target_col_name]] == 5)){
    second_smallest_index <- which(z == sort(unique(z))[2])  
    df[[target_col_name]][second_smallest_index] <- 5
  }
  
  return(df)
}

# Analysis

## Demographic
tot_pop <-0
for (each_tract in tract_names){
  total_col <- paste("Census.Tract.",each_tract,
                     "..Worcester.County..Massachusetts..Total..Estimate",sep='')
  # Total Population
  tot_pop <- tot_pop + as.numeric(gsub(",","",as.character(age_data[age_data$ï..Label..Grouping. == 'Total population',total_col])))
 
}

for (each_tract in tract_names){
  # Children
  num_child <-  as.numeric(gsub("%$","",age_data[age_data$ï..Label..Grouping. %like% "Under 5 years",
                                                 paste("Census.Tract.",each_tract,"..Worcester.County..Massachusetts..Total..Estimate",sep='')]))
  
  if (is.na(num_child)) { 
    perc_child <- 0
    } else {
      perc_child <- 100*num_child/tot_pop
    } 
  census_shapefile[which(census_shapefile$NAME20 == each_tract),'percent_children'] <- perc_child
  
  # Elderly
  num_elder <-  as.numeric(gsub("%$","",age_data[age_data$ï..Label..Grouping. %like% "65 years and over",
                                                 paste("Census.Tract.",each_tract,"..Worcester.County..Massachusetts..Total..Estimate",sep='')]))
  
  if (is.na(num_elder)) {
    perc_elder <- 0
  } else {
    perc_elder <- 100 * num_elder / tot_pop
  }
  census_shapefile[which(census_shapefile$NAME20 == each_tract), 'percent_elderly'] <- perc_elder
  
  # Poverty
  num_pov <-   as.numeric(gsub("%$","",poverty_data[poverty_data$ï..Label..Grouping. == 'Population for whom poverty status is determined',
                                                    paste("Census.Tract.",each_tract,"..Worcester.County..Massachusetts..Below.poverty.level..Estimate",sep='')]))
  if (is.na(num_pov)) {
    perc_pov <- 0 
  } else { 
    perc_pov <- 100*num_pov/tot_pop
  }
  census_shapefile[which(census_shapefile$NAME20 == each_tract),'percent_poverty'] <- perc_pov
  
  # Disabled 
  num_dis <-  as.numeric(gsub("%$","",disabled_data[disabled_data$ï..Label..Grouping. == 'Total civilian noninstitutionalized population',
                                                    paste("Census.Tract.",each_tract,"..Worcester.County..Massachusetts..With.a.disability..Estimate",sep='')]))
  if (is.na(num_dis)) {
    perc_dis <- 0
  } else {
    perc_dis <- 100*num_dis/tot_pop
  } 
  census_shapefile[which(census_shapefile$NAME20 == each_tract),'percent_disabled'] <- perc_dis
   
}


for (each_tract in tract_names){
  
  col <- paste("Census.Tract.",each_tract,
                     "..Worcester.County..Massachusetts..Percent",sep='')
  
  # Ownership
  perc_own <-as.numeric(gsub("%$","",ownership_data[ownership_data$ï..Label..Grouping. == "Owner-occupied",
                                                   paste("Census.Tract.",each_tract,"..Worcester.County..Massachusetts..Percent",sep='')]))
  
  census_shapefile[which(census_shapefile$NAME20 == each_tract),'percent_own'] <- perc_own
  
} 

geo_names <- unique(census_shapefile$GEOID20)

for (each_geo in geo_names){
  # Bonding
  census_shapefile[which(census_shapefile$GEOID20 == each_geo),'bonding_val'] <- social_data$bonding[which(social_data$geoid==each_geo)]
  # Bridging
  census_shapefile[which(census_shapefile$GEOID20 == each_geo),'bridging_val'] <- social_data$bridging[which(social_data$geoid==each_geo)]
  # Linking 
  census_shapefile[which(census_shapefile$GEOID20 == each_geo),'linking_val'] <- social_data$linking[which(social_data$geoid==each_geo)]
}



census_shapefile <- st_transform(census_shapefile, crs= st_crs(uhi_shapefile))
census_shapefile$area <- st_area(census_shapefile)
clipped_uhi <- st_intersection(uhi_shapefile,census_shapefile)
clipped_uhi$area <- st_area(clipped_uhi)
for (each_tract in tract_names){
  total_area <- census_shapefile[which(census_shapefile$NAME20==each_tract),]
  uhi <- vector(mode='numeric',5)
  for (each_value in unique(uhi_shapefile$gridcode)){
    ans <- clipped_uhi[which(clipped_uhi$NAME20==each_tract & clipped_uhi$gridcode==each_value),]
    area <- sum(ans$area)
    uhi[each_value]<- each_value*(area/total_area$area)
  }
  census_shapefile[which(census_shapefile$NAME20 == each_tract),'uhi_weighted'] <- sum(uhi) 
}

# Merge matched matched_parcels and parcels_shapefile
parcels_shapefile <- merge(parcels_shapefile,parcels_data,by.x="LOC_ID",by.y="LOC_ID")
parcels_shapefile <- st_make_valid(parcels_shapefile)
vintages <- c('<1940','1940s','1950s','1960s','1970s','1980s','1990s','2000s','2010s')

vintage_colors <- c('<1940' = color1, '1940s' = color2, '1950s' = color3, 
                    '1960s' = color4, '1970s' = color5, '1980s' = color6,
                    '1990s' = color7, '2000s' = color8,'2010s' = color9)

# Plot Vintages
vintage_map <- ggplot() +
  geom_sf(data=city_shapefile,fill = "lightgrey", color = NA) +
  geom_sf(data = parcels_shapefile, aes(fill = as.factor(vintage)),show.legend = FALSE, color = NA) +
  labs(title = "Vintages") +
  scale_fill_manual(name = "Vintage",values= vintage_colors) + 
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -20)))
ggsave(paste(figure_path,"vintage_parcel_map.png",sep = ''), plot =vintage_map, width = W, height = H, dpi = D)

types <- c('Mobile Home','S.F. Detached','S.F. Attached','2 Unit','3 or 4 Unit',
           '5 to 9 Unit','10 to 19 Unit','20 to 49 Unit', '50 + Unit')
types_colors <- c('Mobile Home' = color1, 'S.F. Detached' = color2, 'S.F. Attached' = color3, 
                  '2 Unit' = color4, '3 or 4 Unit' = color5, '5 to 9 Unit' = color6,
                  '10 to 19 Unit' = color7, '20 to 49 Unit' = color8, '50 + Unit' = color9)
# Plot Types
types_map <- ggplot() +
  geom_sf(data=city_shapefile,fill = "lightgrey", color = NA) +
  geom_sf(data = parcels_shapefile, aes(fill = as.factor(style_type)),show.legend = FALSE, color = NA) +
  labs(title = "Types") +
  scale_fill_manual(name = "Types",values= types_colors) + 
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -20)))
# types_map
ggsave(paste(figure_path,"types_parcel_map.png",sep = ''), plot =types_map , width = W, height = H, dpi = D)


ac <- c('None','Central AC','Room AC','Heat Pump')
ac_colors <- c('None' = '#f46d43', 'Central AC' = '#fee090',
               'Room AC' = '#e0f3f8','Heat Pump' = '#74add1')
# Plot Types
ac_map <- ggplot() +
  geom_sf(data=city_shapefile,fill = "lightgrey", color = NA) +
  geom_sf(data = parcels_shapefile,aes(fill = as.factor(ac_type)),show.legend = FALSE, color = NA) +
  labs(title = "AC Type") +
  scale_fill_manual(name = "AC Types",values= ac_colors) + 
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -20)))

# ac_map
ggsave(paste(figure_path,"ac_parcel_map.png",sep = ''), plot =ac_map , width = W, height = H, dpi = D)

# Calculate HIP Per Census Block
parcels_shapefile$time_to_80 <- parcels_shapefile$num_units*parcels_shapefile$time_to_80

# Plot P4
time_map <- ggplot() +
  geom_sf(data=city_shapefile,fill = "lightgrey", color = NA) +
  geom_sf(data = parcels_shapefile,aes(fill = time_to_80),show.legend = FALSE, color = NA) +
  labs(title = "Average HI Prob. in first 4 Hours") +
  scale_fill_gradient(low = "white", high = "black", limits = c(0, 1)) +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# time_map
ggsave(paste(figure_path,"time_map.png",sep = ''), plot =time_map , width = W, height = H, dpi = D)

# transform
census_shapefile <- st_transform(census_shapefile, crs= st_crs(parcels_shapefile))
census_shapefile<- st_make_valid(census_shapefile)
clipped_parcels <- st_intersection(parcels_shapefile,census_shapefile)
census_shapefile['total_units'] <- NA
vintage_types <- unique(clipped_parcels$vintage)
for (each_vintage in vintage_types){
  census_shapefile[paste(each_vintage)] <- NA
}

style_types <- unique(clipped_parcels$style_type)
for (each_style in style_types){
  census_shapefile[paste(each_style)] <- NA
}

ac_types <- unique(clipped_parcels$ac_type)
ac_types <- na.omit(ac_types)
for (each_ac in ac_types){
  census_shapefile[paste(each_ac)] <- NA
}
census_shapefile$time <- NA

# add to each tract
for (each_tract in tract_names){
  tot_units <- sum(clipped_parcels$num_units[which(clipped_parcels$NAME20==each_tract)])
  census_shapefile[which(census_shapefile$NAME20 == each_tract),'total_units'] <- tot_units 
  tot_units <- sum(clipped_parcels$num_units[which(clipped_parcels$NAME20==each_tract)])
  
  for (each_vintage in vintage_types){
    perc_vin <- 100*sum(clipped_parcels$num_units[which(clipped_parcels$NAME20 == each_tract & clipped_parcels$vintage==each_vintage)])/tot_units
    census_shapefile[which(census_shapefile$NAME20 == each_tract),each_vintage] <-perc_vin
  }
  for (each_style in style_types){
    perc_style <- 100*sum(clipped_parcels$num_units[which(clipped_parcels$NAME20 == each_tract & clipped_parcels$style_type==each_style)])/tot_units
    census_shapefile[which(census_shapefile$NAME20 == each_tract),each_style] <-perc_style
  }
  for (each_ac in ac_types){
    perc_ac <- 100*sum(clipped_parcels$num_units[which(clipped_parcels$NAME20 == each_tract & clipped_parcels$ac_type==each_ac)])/tot_units
    census_shapefile[which(census_shapefile$NAME20 == each_tract),each_ac] <-perc_ac
  }
  census_shapefile$time_to_80[which(census_shapefile$NAME20 == each_tract)]<-sum(clipped_parcels$time_to_80[which(clipped_parcels$NAME20==each_tract)],na.rm = TRUE)/tot_units
}

# Assign Values to Factors
census_shapefile <- assign_index_neg(census_shapefile, "percent_children", "children")
census_shapefile <- assign_index_neg(census_shapefile, "percent_elderly", "elderly")
census_shapefile <- assign_index_neg(census_shapefile, "percent_poverty", "income")
census_shapefile <- assign_index_neg(census_shapefile, "percent_disabled", "disability")
census_shapefile <- assign_index_pos(census_shapefile, "bridging_val", "bridging")
census_shapefile <- assign_index_pos(census_shapefile, "bonding_val", "bonding")
census_shapefile <- assign_index_pos(census_shapefile, "linking_val", "linking")
census_shapefile <- assign_index_neg(census_shapefile, "uhi_weighted", "uhi")
census_shapefile <- assign_index_neg(census_shapefile, "None", "ac")
census_shapefile <- assign_index_pos(census_shapefile, "time_to_80", "housing")
census_shapefile <- assign_index_pos(census_shapefile, "num_dep", "transit")
census_shapefile <- assign_index_pos(census_shapefile, "percent_green", "green")
census_shapefile <- assign_index_pos(census_shapefile, "percent_blue", "blue")
census_shapefile <- assign_index_pos(census_shapefile, "percent_own", "ownership")

for (each_vintage in colnames(vintage_data)[-1]){
  vintage_data <- assign_index_neg(vintage_data,each_vintage,paste0(each_vintage,"score"))
}

colors <- c('#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15')
labels <- c('1','2','3','4','5','6')

# Transit
transit_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(transit)),show.legend = FALSE) +
  scale_fill_manual(name = "Transit Score", values = colors) +  
  labs(title = "Public Transit") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# transit_map                   
ggsave(paste(figure_path,"transit_map.png",sep = ''), plot = transit_map, width = W, height = H, dpi = D)

# Green Space
green_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(green)),show.legend = FALSE) +
  scale_fill_manual(name = "Green Space Score", values = colors) +  
  labs(title = "Green Space") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# green_map                   
ggsave(paste(figure_path,"green_map.png",sep = ''), plot = green_map, width = W, height = H, dpi = D)

# Blue Space
blue_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(blue)),show.legend = FALSE) +
  scale_fill_manual(name = "Blue Space Score", values = colors) +  
  labs(title = "Blue Space") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# blue_map                   
ggsave(paste(figure_path,"blue_map.png",sep = ''), plot = blue_map, width = W, height = H, dpi = D)

# Ownership
ownership_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(ownership)),show.legend = FALSE) +
  scale_fill_manual(name = "Ownership Score", values = colors) +  
  labs(title = "Home Ownership") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# ownership_map                   
ggsave(paste(figure_path,"ownership.png",sep = ''), plot = ownership_map, width = W, height = H, dpi = D)


# Child
children_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(children)),show.legend = FALSE) +
  scale_fill_manual(name = "Children Score", values = colors) +  
  labs(title = "Children") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# children_map                   
ggsave(paste(figure_path,"children_map.png",sep = ''), plot = children_map, width = W, height = H, dpi = D)

# Plot Elderly Score
elderly_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(elderly)),show.legend = FALSE) +
  scale_fill_manual(name = "Elderly Score", values = colors) +  
  labs(title = "Elderly") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
# elderly_map
ggsave(paste(figure_path,"elderly_map.png",sep = ''), plot = elderly_map, width = W, height = H, dpi = D)

# Plot Income Score
income_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(income)),show.legend = FALSE) +
  scale_fill_manual(name = "Low Income Score", values = colors) +  
  labs(title = "Low-Income") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#income_map 
ggsave(paste(figure_path,"income_map.png",sep = ''), plot = income_map, width = W, height = H, dpi = D)


# Plot Disability Score
disability_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(disability)),show.legend = FALSE) +
  scale_fill_manual(name = "Disability Score", values = colors) +  
  labs(title = "Disabled") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#disability_map
ggsave(paste(figure_path,"disability_map.png",sep = ''), plot = disability_map, width = W, height = H, dpi = D)

# Plot Bonding Score
bonding_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(bonding)),show.legend = FALSE) +
  scale_fill_manual(name = "Bonding Score", values = colors) +  
  labs(title = "Bonding") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#bonding_map
ggsave(paste(figure_path,"bonding_map.png",sep = ''), plot = bonding_map, width = W, height = H, dpi = D)

# Plot Bridging Score
bridging_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(bridging)),show.legend = FALSE) +
  scale_fill_manual(name = "bridging Score", values = colors) +  
  labs(title = "Bridging") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#bridging_map
ggsave(paste(figure_path,"bridging_map.png",sep = ''), plot = bridging_map, width = W, height = H, dpi = D)

# Plot Linking Score
linking_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(linking)),show.legend = FALSE) +
  scale_fill_manual(name = "Linking Score", values = colors) +  
  labs(title = "Linking") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#linking_map
ggsave(paste(figure_path,"linking_map.png",sep = ''), plot = linking_map, width = W, height = H, dpi = D)

# Plot UHI Score
uhi_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(uhi)),show.legend = FALSE) +
  scale_fill_manual(name = "Urban Heat Island", values = colors) +  
  labs(title = "Urban Heat Island") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#uhi_map
ggsave(paste(figure_path,"uhi_map.png",sep = ''), plot = uhi_map, width = W, height = H, dpi = D)

# Plot AC Score
ac_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(ac)),show.legend = FALSE) +
  scale_fill_manual(name = "No AC Score", values = colors) +  
  labs(title = "Air Conditioning") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
ac_map
ggsave(paste(figure_path,"ac_map.png",sep = ''), plot = ac_map, width = W, height = H, dpi = D)

# Plot Housing Score
housing_map <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(housing)),show.legend = FALSE) +
  scale_fill_manual(name = "Housing", values = colors) +  
  labs(title = "Housing") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
#housing_map
ggsave(paste(figure_path,"housing.png",sep = ''), plot = housing_map, width = W, height = H, dpi = D)

# Function to calculate Spearman's rank correlation coefficient for multiple factors
calculate_spearman_correlation <- function(data, factors) {
  # Initialize an empty results data frame
  results <- data.frame(Factor1 = character(),
                        Factor2 = character(),
                        Correlation = numeric(),
                        stringsAsFactors = FALSE)
  
  # Loop through each combination of factors
  for (i in 1:(length(factors)-1)) {
    for (j in (i+1):length(factors)) {
      # Extract the factor names
      factor1 <- factors[i]
      factor2 <- factors[j]
      
      # Calculate Spearman's rank correlation coefficient and p-value
      cor_test <- cor.test(data[[factor1]], data[[factor2]], method = "spearman",exact=FALSE)
      correlation <- round(cor_test$estimate,3)
      p_value <- round(cor_test$p.value,3)
      
      # Add the results to the data frame
      results <- rbind(results, data.frame(Factor1 = factor1,
                                           Factor2 = factor2,
                                           Correlation = correlation,
                                           P_Value = p_value,
                                           stringsAsFactors = FALSE))
    }
  }
  
  # Convert the results data frame to wide format
  results_wide <- pivot_wider(results, names_from = Factor2, values_from = c(Correlation, P_Value))
  
  return(results_wide)
}

# Spearmans R OG 
factors <- c("ac", "bonding", "blue", "bridging", "children", "disability", "elderly", "green", "housing", "linking", "income", "ownership", "transit", "uhi")

results <- calculate_spearman_correlation(census_shapefile, factors)
write.csv(results, paste0(file_path,"results.csv"))

print_factors <- c("NAME20","ac", "bonding", "blue", "bridging", "children", "disability", "elderly", "green", "housing", "linking", "income", "ownership", "transit", "uhi")
# Optionally, you can select specific columns from the dataframe
selected_columns <- census_shapefile[, print_factors]
selected_columns<-as.data.frame(selected_columns)
selected_columns <-  selected_columns[, !grepl("^geometry$", colnames(selected_columns))]
selected_columns <- selected_columns[order(selected_columns$NAME20, decreasing = FALSE), ]
write.csv(selected_columns,  paste0(file_path,"result_table.csv"), row.names = TRUE)

census_shapefile <- st_transform(census_shapefile, crs= st_crs(parcels_shapefile))

## Plot parcels and tracts in same plot 
both_plot <- ggplot() +
  # Plot parcels shapefile with black lines
  geom_sf(data = parcels_shapefile, aes(), fill = NA, color = "black") +
  # Plot census shapefile with red lines
  geom_sf(data = census_shapefile, aes(), fill = NA, color = "red") +
  # Set plot title
  labs(title = "Parcels and Census Shapefiles Overlay") +
  # Set theme
  theme_map() +
  # Add custom color scale for lines
  scale_color_manual(values = c("black" = "black", "red" = "red"),
                     labels = c("Parcels", "Census")) +
  # Add legend to top right
  guides(color = guide_legend(title = "Shapefile", nrow = 2, byrow = TRUE,
                              title.position = "top",
                              label.position = "right"))

# Display the plot
# both_plot
# ggsave(paste(figure_path,"overlay.png",sep = ''), plot = both_plot, width = W, height = H, dpi = D)

# Calculate spatial weights
weights <- poly2nb(census_shapefile, queen = TRUE)
weights <- nb2listw(weights)

# Calculate spatial lag
census_shapefile$children_lag <- lag.listw(weights, census_shapefile$percent_children)
census_shapefile$elderly_lag <- lag.listw(weights, census_shapefile$percent_elderly)
census_shapefile$income_lag <- lag.listw(weights, census_shapefile$percent_poverty)
census_shapefile$disability_lag <- lag.listw(weights, census_shapefile$percent_disabled)
census_shapefile$bonding_lag <- lag.listw(weights, census_shapefile$bonding_val)
census_shapefile$bridging_lag <- lag.listw(weights, census_shapefile$bridging_val)
census_shapefile$linking_lag <- lag.listw(weights, census_shapefile$linking_val)
census_shapefile$ac_lag <- lag.listw(weights, census_shapefile$None)
census_shapefile$uhi_lag <- lag.listw(weights, census_shapefile$uhi_weighted)
census_shapefile$housing_lag <- lag.listw(weights, census_shapefile$time_to_80)
census_shapefile$transit_lag <- lag.listw(weights, census_shapefile$num_dep)
census_shapefile$green_lag <- lag.listw(weights, census_shapefile$percent_green)
census_shapefile$blue_lag <- lag.listw(weights, census_shapefile$percent_blue)
census_shapefile$ownership_lag <- lag.listw(weights, census_shapefile$percent_own)

# Assign Values to Lag Factors
census_shapefile <- assign_index_neg(census_shapefile, "children_lag", "children_lag_rank")
census_shapefile <- assign_index_neg(census_shapefile, "elderly_lag", "elderly_lag_rank")
census_shapefile <- assign_index_neg(census_shapefile, "income_lag", "income_lag_rank")
census_shapefile <- assign_index_neg(census_shapefile, "disability_lag", "disability_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "bonding_lag", "bonding_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "bridging_lag", "bridging_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "linking_lag", "linking_lag_rank")
census_shapefile <- assign_index_neg(census_shapefile, "uhi_lag", "uhi_lag_rank")
census_shapefile <- assign_index_neg(census_shapefile, "ac_lag", "ac_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "housing_lag", "housing_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "transit_lag", "transit_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "green_lag", "green_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "blue_lag", "blue_lag_rank")
census_shapefile <- assign_index_pos(census_shapefile, "ownership_lag", "ownership_lag_rank")

transit_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(transit_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Transit Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nPublic Transit") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
transit_lag_map_rank
ggsave(paste(figure_path,"transit_lag_map_rank.png",sep = ''), plot = transit_lag_map_rank, width = W, height = H, dpi = D)


green_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(green_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Green Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nGreen Space") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
green_lag_map_rank
ggsave(paste(figure_path,"green_lag_map_rank.png",sep = ''), plot = green_lag_map_rank, width = W, height = H, dpi = D)

blue_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(blue_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Blue Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nBlue Space") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
blue_lag_map_rank
ggsave(paste(figure_path,"blue_lag_map_rank.png",sep = ''), plot = blue_lag_map_rank, width = W, height = H, dpi = D)

ownership_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(ownership_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Ownership Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nHome Ownership") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
ownership_lag_map_rank
ggsave(paste(figure_path,"ownership_lag_map_rank.png",sep = ''), plot = ownership_lag_map_rank, width = W, height = H, dpi = D)


children_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(children_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Children Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nChildren") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
children_lag_map_rank
ggsave(paste(figure_path,"children_lag_map_rank.png",sep = ''), plot = children_lag_map_rank, width = W, height = H, dpi = D)

elderly_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(elderly_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Elderly Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nElderly") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
elderly_lag_map_rank
ggsave(paste(figure_path,"elderly_lag_map_rank.png",sep = ''), plot = elderly_lag_map_rank, width = W, height = H, dpi = D)

income_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(income_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "income Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nLow-Income") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
income_lag_map_rank
ggsave(paste(figure_path,"income_lag_map_rank.png",sep = ''), plot = income_lag_map_rank, width = W, height = H, dpi = D)

disability_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(disability_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Disability Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nDisabled") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
disability_lag_map_rank
ggsave(paste(figure_path,"disability_lag_map_rank.png",sep = ''), plot = disability_lag_map_rank, width = W, height = H, dpi = D)

bond_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(bonding_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Bond Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nBonding") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
bond_lag_map_rank
ggsave(paste(figure_path,"bond_lag_map_rank.png",sep = ''), plot = bond_lag_map_rank, width = W, height = H, dpi = D)

bridging_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(bridging_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Bridging Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nBridging") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
bridging_lag_map_rank
ggsave(paste(figure_path,"bridging_lag_map_rank.png",sep = ''), plot = bridging_lag_map_rank, width = W, height = H, dpi = D)

linking_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(linking_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "Linking Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nLinking") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
linking_lag_map_rank
ggsave(paste(figure_path,"linking_lag_map_rank.png",sep = ''), plot = linking_lag_map_rank, width = W, height = H, dpi = D)

ac_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(ac_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "ac Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nAir Conditioning") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
ac_lag_map_rank
ggsave(paste(figure_path,"ac_lag_map_rank.png",sep = ''), plot = ac_lag_map_rank, width = W, height = H, dpi = D)

uhi_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(uhi_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "UHI Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nUrban Heat Island") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))
uhi_lag_map_rank
ggsave(paste(figure_path,"uhi_lag_map_rank.png",sep = ''), plot = uhi_lag_map_rank, width = W, height = H, dpi = D)

housing_lag_map_rank <- ggplot(census_shapefile) +
  geom_sf(aes(fill = as.factor(housing_lag_rank)),show.legend = FALSE) +
  scale_fill_manual(name = "IHI Lag Rank", values = colors) +  
  labs(title = "Spatial Lag:\nHousing") +
  theme_map() + 
  theme(plot.title = element_text(size = Font, face = "bold", margin = margin(b = -M)))

housing_lag_map_rank
ggsave(paste(figure_path,"housing_lag_map_rank.png",sep = ''), plot = housing_lag_map_rank, width = W, height = H, dpi = D)


# Spearmans R Spatial
lag_factors <-  paste0(factors, "_lag_rank")
lag_results <- calculate_spearman_correlation(census_shapefile, lag_factors)
print(lag_results)
write.csv(lag_results, paste0(file_path,"lag_results.csv"))
# Optionally, you can select specific columns from the dataframe
selected_columns <- census_shapefile[, c("NAME20",lag_factors)]
selected_columns<-as.data.frame(selected_columns)
selected_columns <-  selected_columns[, !grepl("^geometry$", colnames(selected_columns))]
selected_columns <- selected_columns[order(selected_columns$NAME20, decreasing = FALSE), ]
write.csv(selected_columns,  paste0(file_path,"lag_result_table.csv"), row.names = TRUE)

