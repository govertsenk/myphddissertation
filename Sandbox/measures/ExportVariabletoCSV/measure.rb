require 'erb'
require 'csv'

#start the variable
class ExportVariabletoCSV < OpenStudio::Measure::ReportingMeasure

  # human readable name
  def name
    return 'ExportVariabletoCSV'
  end

  # human readable description
  def description
    return 'Exports an OutputVariable specified in the AddOutputVariable OpenStudio measure to a csv file.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'This measure searches for the OutputVariable name in the eplusout sql file and saves it to a csv file.'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    #make an argument for the variable name
    variable_name = OpenStudio::Measure::OSArgument::makeStringArgument('variable_name', true)
    variable_name.setDisplayName('Enter Variable Name.')
    args << variable_name

    #make an argument for the reporting frequency
    reporting_frequency_chs = OpenStudio::StringVector.new
    reporting_frequency_chs << 'Hourly'
    reporting_frequency_chs << 'Zone Timestep'
    reporting_frequency = OpenStudio::Measure::OSArgument::makeChoiceArgument('reporting_frequency', reporting_frequency_chs, true)
    reporting_frequency.setDisplayName('Reporting Frequency.')
    reporting_frequency.setDefaultValue('Hourly')
    args << reporting_frequency 

    return args
  end

  # define what happens when the measure is run
  def run(runner, user_arguments)
    super(runner, user_arguments)

    # get the last model and sql file
    model = runner.lastOpenStudioModel
    if model.empty?
      runner.registerError('Cannot find last model.')
      return false
    end
    model = model.get

    # use the built-in error checking 
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    #assign the user inputs to variables
    variable_name = runner.getStringArgumentValue('variable_name', user_arguments)
    reporting_frequency = runner.getStringArgumentValue('reporting_frequency', user_arguments) 

    #check the user_name for reasonableness
    if variable_name == ''
      runner.registerError('No variable name was entered.')
      return false
    end



    sql = runner.lastEnergyPlusSqlFile
    if sql.empty?
      runner.registerError('Cannot find last sql file.')
      return false
    end
    sql = sql.get
    model.setSqlFile(sql)

    # get the weather file run period (as opposed to design day run period)
    ann_env_pd = nil
    sql.availableEnvPeriods.each do |env_pd|
      env_type = sql.environmentType(env_pd)
      if env_type.is_initialized
        if env_type.get == OpenStudio::EnvironmentType.new('WeatherRunPeriod')
          ann_env_pd = env_pd
          break
        end
      end
    end

    variable_names = sql.availableVariableNames(ann_env_pd, reporting_frequency)
    puts variable_names
    if !variable_names.include? "#{variable_name}"
      runner.registerError("Variable #{variable_name} is not in the sql file.  Please add the associated Output:variable object.  You can do this with the AddVariable reporting measure available on BCL.")
    end
      
    headers = ["#{reporting_frequency}"]
    output_timeseries = {}

    timeseries = sql.timeSeries(ann_env_pd, reporting_frequency, variable_name.to_s,"")
    puts timeseries.value 
    if !timeseries.empty?
      timeseries = timeseries.get
      units = timeseries.units
      headers << "#{variable_name.to_s}[#{units}]"
      output_timeseries[headers[-1]] = timeseries
    else 
      runner.registerWarning("Timeseries data is not available for #{variable_name} with frequency #{reporting_frequency}.  Did you remember to include the associated Output:Variable request?")
    end

    csv_array = []
    csv_array << headers
    date_times = output_timeseries[output_timeseries.keys[0]].dateTimes

    values = {}
    for key in output_timeseries.keys
      values[key] = output_timeseries[key].values
    end

    num_times = date_times.size - 1
    for i in 0..num_times
      date_time = date_times[i]
      row = []
      row << date_time
      for key in headers[1..-1]
      value = values[key][i]
      row << value
      end
      csv_array << row
    end

    File.open("./report_#{variable_name.delete(' ').delete(':')}_#{reporting_frequency.delete(' ')}.csv", 'wb') do |file|
      csv_array.each do |elem|
      file.puts elem.join(',')
      end
    end

    # close the sql file
    sql.close()
    return true
  end
end

# register the measure to be used by the application
ExportVariabletoCSV.new.registerWithApplication
