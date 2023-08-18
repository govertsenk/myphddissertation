# see the URL below for information on how to write OpenStudio measures
# http://openstudio.nrel.gov/openstudio-measure-writing-guide

# see the URL below for information on using life cycle cost objects in OpenStudio
# http://openstudio.nrel.gov/openstudio-life-cycle-examples

# see the URL below for access to C++ documentation on model objects (click on "model" in the main window to view model objects)
# http://openstudio.nrel.gov/sites/openstudio.nrel.gov/files/nv_data/cpp_documentation_it/model/html/namespaces.html

# start the measure
class PowerOutage < OpenStudio::Measure::ModelMeasure
  # define the name that a user will see, this method may be deprecated as
  # the display name in PAT comes from the name field in measure.xml
  def name
    return "Set Residential Power Outage"
  end

  def description
    return "This measures allows building power outages to be modeled. The user specifies the start time of the outage and the duration of the outage. During an outage, all energy consumption is set to 0, although occupants are still simulated in the home."
  end

  def modeler_description
    return "This measure zeroes out the schedule for anything that consumes energy (equipment and lighting) for the duration of the power outage."
  end

  # define the arguments that the user will input (start date, start hour, and duration)
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    # make a string argument for for the start date of the outage
    arg = OpenStudio::Measure::OSArgument.makeStringArgument("otg_date", true)
    arg.setDisplayName("Outage Start Date")
    arg.setDescription("Date of the start of the outage.")
    arg.setDefaultValue("January 1")
    args << arg

    # make a double argument for hour of outage start
    arg = OpenStudio::Measure::OSArgument::makeIntegerArgument("otg_hr", true)
    arg.setDisplayName("Outage Start Hour")
    arg.setUnits("hours")
    arg.setDescription("Hour of the day when the outage starts.")
    arg.setDefaultValue(0)
    args << arg

    # make a double argument for outage duration
    arg = OpenStudio::Measure::OSArgument::makeIntegerArgument("otg_len", true)
    arg.setDisplayName("Outage Duration")
    arg.setUnits("hours")
    arg.setDescription("Duration of the power outage in hours.")
    arg.setDefaultValue(24)
    args << arg 


    return args
  end # end the arguments method
  
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # use the built-in error checking
    if not runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # assign the user inputs to variables
    otg_date = runner.getStringArgumentValue("otg_date", user_arguments)
    otg_hr = runner.getIntegerArgumentValue("otg_hr", user_arguments)
    otg_len = runner.getIntegerArgumentValue("otg_len", user_arguments)
    if !otg_len.is_a? Integer
      runner.registerError("Outage length must be in hours (whole number/integer).")
      return false
    end

    if otg_hr < 0 or otg_hr > 23
      runner.registerError("Start hour must be between 0 and 23.")
      return false
    end

    if otg_len < 2
      runner.registerError("Outage must last at least two hours.")
      return false
    end

    # Making longer than 24 hours next 
    # if otg_len >= 24
    #   runner.registerError("Outage must less than one day.")
    #   return false
    # end

    # Testing out multiday capacity now 

    # if otg_hr + otg_len >= 24
    #   runner.registerError("Outage must start and end within one calendar day.")
    #   return false
    # end

    # get the run period
    year_description = model.getYearDescription
    assumed_year = year_description.assumedYear
    run_period = model.getRunPeriod
    run_period_start = Time.new(assumed_year, run_period.getBeginMonth, run_period.getBeginDayOfMonth)
    run_period_start_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(run_period.getBeginMonth),run_period.getBeginDayOfMonth,assumed_year)
    run_period_end = Time.new(assumed_year, run_period.getEndMonth, run_period.getEndDayOfMonth, 24)
    run_period_end_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(run_period.getEndMonth),run_period.getEndDayOfMonth,assumed_year)
    
    # get the outage period
    months = { "January" => 1, "February" => 2, "March" => 3, "April" => 4, "May" => 5, "June" => 6, "July" => 7, "August" => 8, "September" => 9, "October" => 10, "November" => 11, "December" => 12 }
    weekday = { "Sunday" => 1, "Monday" => 2, "Tuesday" => 3, "Wednesday" => 4, "Thursday" => 5, "Friday" => 6, "Saturday" => 7}

    otg_start_date_month = months[otg_date.split[0]]
    otg_start_date_day = otg_date.split[1].to_i
    begin
      otg_period_start = Time.new(assumed_year, otg_start_date_month, otg_start_date_day, otg_hr)
    rescue
      runner.registerError("Invalid outage start date specified.")
      return false
    end
    #print('start: ',otg_period_start,"\n")
    otg_period_end = otg_period_start + otg_len * 3600.0
    #print('end:',otg_period_end,"\n")
    
    # check that inputs make sense
    if otg_period_start < run_period_start
      runner.registerError("Outage period starts before the run period starts.")
      return false
    elsif otg_period_end > run_period_end
      runner.registerError("Outage period ends after the run period ends.")
      return false
    end

    # get outage start and end days of the year
    otg_start_date_day = ((otg_period_start - Time.new(assumed_year)) / 3600.0 / 24.0 + 1).floor
    otg_end_date_day = ((otg_period_end - Time.new(assumed_year)) / 3600.0 / 24.0 + 1).floor

    # make openstudio dates for outage period
    otg_start_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_period_start.month), otg_period_start.day, otg_period_start.year)   
    otg_start_time = OpenStudio::Time.new(0,otg_period_start.hour()+1,1,0)
   # print(otg_start_time,"\n")

    pre_outage_end_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_period_start.month), otg_period_start.day - 1, otg_period_start.year)   

   
    otg_end_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_period_end.month), otg_period_end.day, otg_period_end.year)
    otg_end_time = OpenStudio::Time.new(0,otg_period_end.hour()+1,0,0)
    #print(otg_end_time,"\n")
    post_outage_start_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_period_end.month), otg_period_end.day + 1, otg_period_end.year)  
    
    #if otg_len > 24 
    # print('pre_outage_end_date: ', pre_outage_end_date,"\n")
    # print('day outage starts: ', otg_start_date,"\n")
    # print('day outage ends: ', otg_end_date,"\n")
    # print('post_outage_start_date: ', post_outage_start_date,"\n")
    scenario = 0

    if otg_period_start.day == otg_period_end.day
      scenario = 1
    elsif otg_period_start.day + 1 == otg_period_end.day
      scenario = 2
    else
      scenario = 3
      blk_start_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_period_start.month), otg_period_start.day + 1, otg_period_start.year)   
      blk_end_date = OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_period_start.month), otg_period_end.day - 1, otg_period_start.year)   
    end 
    
    if scenario < 1
      runner.registerError("Unable to identify outage scenario.")
      return false
    end 

    # print('day black out starts: ',blk_start_date,"\n")
    # print('day black out ends: ',blk_end_date,"\n")
   # Constant to Ruleset, no outage 
#       model.getScheduleConstants.each do |sch|
# #         if schedule has 'occupant in name, skip
#         next if sch.name.to_s.include? "occupant"
          
#         new_sch_name = "New " + sch.name.to_s
#         old_sch_value = sch.to_Schedule.get.to_ScheduleConstant.get.value
#         old_sch_handle = sch.to_Schedule.get.to_ScheduleConstant.get.handle
#         old_sch_limit = sch.to_Schedule.get.to_ScheduleConstant.get.scheduleTypeLimits.get
#         new_sch_ruleset = OpenStudio::Model::ScheduleRuleset.new(model)
#         new_sch_ruleset.setName(new_sch_name)
#         new_sch_handle = new_sch_ruleset.handle
#         # Set old schedule to new handle
# #         sch.handle(new_sch_handle)
#         # Set new schedule to old handle
# #         new_sch_ruleset.handle(old_sch_handle)
# #         new_handle = sch.to_Schedule.get.to_ScheduleRuleset.get.handle  
#         new_rule_index = 0
#         new_sch_value = 0
#         if sch.name.to_s.include? "Off"
#             new_sch_value = 1
#         end
    
#         new_sch_ruleset.defaultDaySchedule.setScheduleTypeLimits(old_sch_limit)
#         new_times = Array(1..24)
#         ## BEFORE
#         new_sch_rule_constant_before = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
#         new_sch_rule_constant_before.setName("#{new_sch_name} Constant Before")
#         new_sch_rule_constant_before.setStartDate(run_period_start_date)
#         new_sch_rule_constant_before.setEndDate(pre_outage_end_date)
#         new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_constant_before,new_rule_index)
#         new_rule_index = new_rule_index + 1

#         new_sch_ruleday_constant_before = new_sch_rule_constant_before.daySchedule
#         new_sch_ruleday_constant_before.setName("#{new_sch_name} Before Power Outage")
#         for eachTime in 0..new_times.size-1
#           new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
#           new_sch_ruleday_constant_before.addValue(new_time,old_sch_value)
#         end
#         new_sch_ruleday_constant_before.setScheduleTypeLimits(old_sch_limit)
        
#         ## DURING
#         new_sch_rule_constant_during = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
#         new_sch_rule_constant_during.setName("#{new_sch_name} Constant During")
#         new_sch_rule_constant_during.setStartDate(otg_start_date)
#         new_sch_rule_constant_during.setEndDate(otg_end_date)
#         new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_constant_during,new_rule_index)
#         new_rule_index = new_rule_index + 1
          
#         new_sch_ruleday_constant_during = new_sch_rule_constant_during.daySchedule
#         new_sch_ruleday_constant_during.setName("#{new_sch_name} During Power Outage")
# #         for eachTime in 0..new_times.size-1
# #           new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
# #           new_sch_ruleday_constant_during.addValue(new_time,old_sch_value)
# #         end
#         for eachTime in 0..new_times.size-1
#             new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
#             new_sch_ruleday_constant_during.addValue(new_time,old_sch_value)
#             if (new_time >= otg_start_time && new_time <= otg_end_time)
#               new_sch_ruleday_constant_during.addValue(new_time,new_sch_value)
#             end
#         end
                
#         new_sch_ruleday_constant_during.setScheduleTypeLimits(old_sch_limit)
        
#         ## AFTER
#         new_sch_rule_constant_after = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
#         new_sch_rule_constant_after.setName("#{new_sch_name} Constant")
#         new_sch_rule_constant_after.setStartDate(post_outage_start_date)
#         new_sch_rule_constant_after.setEndDate(run_period_end_date)
#         new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_constant_after,new_rule_index)
#         new_rule_index = new_rule_index + 1

#         new_sch_ruleday_constant_after = new_sch_rule_constant_before.daySchedule
#         new_sch_ruleday_constant_after.setName("#{new_sch_name} after Power Outage")
#         for eachTime in 0..new_times.size-1
#           new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
#           new_sch_ruleday_constant_after.addValue(new_time,old_sch_value)
#         end
#         new_sch_ruleday_constant_after.setScheduleTypeLimits(old_sch_limit)

#       end
    # Change all Schedule Constants to Rulesets
    model.getScheduleConstants.each do |sch|
        # if schedule has 'occupant in name, skip
        next if sch.name.to_s.include? "occupant"

        new_sch_name = "New " + sch.name.to_s
        old_sch_value = sch.to_Schedule.get.to_ScheduleConstant.get.value
#         print(new_sch_name,' old value: ',old_sch_value,"\n")
        old_sch_handle = sch.to_Schedule.get.to_ScheduleConstant.get.handle
        old_sch_limit = sch.to_Schedule.get.to_ScheduleConstant.get.scheduleTypeLimits.get
        new_sch_value = 0 
        if sch.name.to_s.include? "Off"
            new_sch_value = 1
        end
        new_rule_index = 0
        new_sch_ruleset = OpenStudio::Model::ScheduleRuleset.new(model)
        new_sch_ruleset.setName(new_sch_name)

        new_sch_ruleset.defaultDaySchedule.setScheduleTypeLimits(old_sch_limit)
        new_times = Array(1..24)

        ## Start with after, then during, then before. 
        # After Power Outage Rule
        new_sch_rule_after_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
        new_sch_rule_after_outage.setName("#{new_sch_name} after Power Outage")
        new_sch_rule_after_outage.setStartDate(post_outage_start_date)
        new_sch_rule_after_outage.setEndDate(run_period_end_date)
        
        new_sch_ruleday_after_outage = new_sch_rule_after_outage.daySchedule
        new_sch_ruleday_after_outage.setName("#{new_sch_name} after Power Outage")
#         if new_sch_ruleday_after_outage.scheduleTypeLimits.empty?
        new_sch_ruleday_after_outage.setScheduleTypeLimits(old_sch_limit)
#         end
        new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_after_outage,new_rule_index)
        new_rule_index = new_rule_index + 1

        for eachTime in 0..new_times.size-1
          new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
          new_sch_ruleday_after_outage.addValue(new_time,old_sch_value)
        end
        
        if scenario == 1
          # Day Power Goes Out 
          new_sch_rule_during_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
          new_sch_rule_during_outage.setName("#{new_sch_name} during Power Outage")
          new_sch_rule_during_outage.setStartDate(otg_start_date)
          new_sch_rule_during_outage.setEndDate(otg_end_date)
          new_sch_ruleday_during_outage = new_sch_rule_during_outage.daySchedule
          new_sch_ruleday_during_outage.setName("#{new_sch_name} during Power Outage")
          new_sch_ruleday_during_outage.setScheduleTypeLimits(old_sch_limit)

          new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_during_outage,new_rule_index)
          new_rule_index = new_rule_index + 1

          for eachTime in 0..new_times.size-1
            new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
            new_sch_ruleday_during_outage.addValue(new_time,old_sch_value)
            if (new_time >= otg_start_time && new_time <= otg_end_time)
              new_sch_ruleday_during_outage.addValue(new_time,new_sch_value)
            end
          end

        elsif scenario == 2
          # Day Power Comes Back On 
          new_sch_rule_during_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
          new_sch_rule_during_outage.setName("#{new_sch_name} end of Power Outage")
          new_sch_rule_during_outage.setStartDate(otg_end_date)
          new_sch_rule_during_outage.setEndDate(otg_end_date)
          new_sch_ruleday_during_outage = new_sch_rule_during_outage.daySchedule
          new_sch_ruleday_during_outage.setName("#{new_sch_name} end of Power Outage")
          new_sch_ruleday_during_outage.setScheduleTypeLimits(old_sch_limit)
          new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_during_outage,new_rule_index)
          new_rule_index = new_rule_index + 1

          for eachTime in 0..new_times.size-1
            new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
            new_sch_ruleday_during_outage.addValue(new_time,old_sch_value)
            if (new_time <= otg_end_time)
              new_sch_ruleday_during_outage.addValue(new_time,new_sch_value)
            end
          end

          # Day Power Goes Out 
          new_sch_rule_during_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
          new_sch_rule_during_outage.setName("#{new_sch_name} start of Power Outage")
          new_sch_rule_during_outage.setStartDate(otg_start_date)
          new_sch_rule_during_outage.setEndDate(otg_start_date)
          new_sch_ruleday_during_outage = new_sch_rule_during_outage.daySchedule
          new_sch_ruleday_during_outage.setName("#{new_sch_name} start of Power Outage")
          new_sch_ruleday_during_outage.setScheduleTypeLimits(old_sch_limit)
            
          new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_during_outage,new_rule_index)
          new_rule_index = new_rule_index + 1

          for eachTime in 0..new_times.size-1
            new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
            new_sch_ruleday_during_outage.addValue(new_time,old_sch_value)
            if (new_time >= otg_start_time)
              new_sch_ruleday_during_outage.addValue(new_time,new_sch_value)
            end
          end

        elsif scenario == 3
          # Day Power Comes Back On 
          new_sch_rule_during_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
          new_sch_rule_during_outage.setName("#{new_sch_name} end of Power Outage")
          new_sch_rule_during_outage.setStartDate(otg_end_date)
          new_sch_rule_during_outage.setEndDate(otg_end_date)
          new_sch_ruleday_during_outage = new_sch_rule_during_outage.daySchedule
          new_sch_ruleday_during_outage.setName("#{new_sch_name} end of Power Outage")
          new_sch_ruleday_during_outage.setScheduleTypeLimits(old_sch_limit)
          new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_during_outage,new_rule_index)
          new_rule_index = new_rule_index + 1

          for eachTime in 0..new_times.size-1
            new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
            new_sch_ruleday_during_outage.addValue(new_time,old_sch_value)
            if (new_time <= otg_end_time)
              new_sch_ruleday_during_outage.addValue(new_time,new_sch_value)
            end # end if 
          end # end for loop

          # During Power Outage Rule 
          new_sch_rule_during_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
          new_sch_rule_during_outage.setName("#{new_sch_name} during Power Outage")
          new_sch_rule_during_outage.setStartDate(blk_start_date)
          new_sch_rule_during_outage.setEndDate(blk_end_date)
          new_sch_ruleday_during_outage = new_sch_rule_during_outage.daySchedule
          new_sch_ruleday_during_outage.setName("#{new_sch_name} during Power Outage")
          new_sch_ruleday_during_outage.setScheduleTypeLimits(old_sch_limit)
          new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_during_outage,new_rule_index)
          new_rule_index = new_rule_index + 1
  
          for eachTime in 0..new_times.size-1
            new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
            new_sch_ruleday_during_outage.addValue(new_time,new_sch_value)
          end # end for loop

          # Day Power Goes Out 
          new_sch_rule_during_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
          new_sch_rule_during_outage.setName("#{new_sch_name} start of Power Outage")
          new_sch_rule_during_outage.setStartDate(otg_start_date)
          new_sch_rule_during_outage.setEndDate(otg_start_date)
          new_sch_ruleday_during_outage = new_sch_rule_during_outage.daySchedule
          new_sch_ruleday_during_outage.setName("#{new_sch_name} start of Power Outage")
          new_sch_ruleday_during_outage.setScheduleTypeLimits(old_sch_limit)
          new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_during_outage,new_rule_index)
          new_rule_index = new_rule_index + 1

          for eachTime in 0..new_times.size-1
            new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
            new_sch_ruleday_during_outage.addValue(new_time,old_sch_value)
            if (new_time >= otg_start_time)
              new_sch_ruleday_during_outage.addValue(new_time,new_sch_value)
            end # end if 
          end # end for loop
        end # end scenario if statement
          
        # Before Power Outage Rule
        new_sch_rule_before_outage = OpenStudio::Model::ScheduleRule.new(new_sch_ruleset)
        new_sch_rule_before_outage.setName("#{new_sch_name} before Power Outage")
        new_sch_rule_before_outage.setStartDate(run_period_start_date)
        new_sch_rule_before_outage.setEndDate(pre_outage_end_date)
 
        new_sch_ruleday_before_outage = new_sch_rule_before_outage.daySchedule
        new_sch_ruleday_before_outage.setName("#{new_sch_name} before Power Outage")
        new_sch_ruleday_before_outage.setScheduleTypeLimits(old_sch_limit)

        new_sch_ruleset.setScheduleRuleIndex(new_sch_rule_before_outage,new_rule_index)
        new_rule_index = new_rule_index + 1
        for eachTime in 0..new_times.size-1
          new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
          new_sch_ruleday_before_outage.addValue(new_time,old_sch_value)
        end # end for loop
        new_sch_ruleset.setScheduleTypeLimits(old_sch_limit)
#         print(new_sch_ruleset)
#         # Assign to respective places 
#         model.getSetpointManagerScheduleds.each do |spms|
#           if spms.schedule.handle == old_sch_handle
# #               print("New Schedule is:\n",new_sch_ruleset,"\n")
# #               print("Old Schedule is:\n",spms.schedule,"\n")
#               spms.setSchedule(new_sch_ruleset)
# #             spms.setScheduleTypeLimits(old_sch_limit)
# #               print("spms set as:\n",spms)
#           end # end if 
#         end # end setpoint manager 

#         model.getWaterHeaterMixeds.each do |wh|
#           if wh.setpointTemperatureSchedule.get.handle == old_sch_handle
#               print("Old Schedule is:\n",wh.setpointTemperatureSchedule.get,"\n")
#               print("New Schedule is:\n",new_sch_ruleset,"\n")
#               wh.setSetpointTemperatureSchedule(new_sch_ruleset)
#               print("wh set as:\n",wh.setSetpointTemperatureSchedule.get)
#           end # end if 
#         end # end water heater mixed 

#         model.getWaterUseConnectionss.each do |water|
#           water.waterUseEquipment.each do |equip|
#              if equip.waterUseEquipmentDefinition.targetTemperatureSchedule.get.handle == old_sch_handle
#               # Set new schedule
#               equip.waterUseEquipmentDefinition.setTargetTemperatureSchedule(new_sch_ruleset)
#              end  # end if
#            end # end water use equipment 
#          end # end water use connection

#         model.getZoneMixings.each do |mix|
#           if mix.schedule.handle == old_sch_handle
#              mix.setSchedule(new_sch_ruleset)
#           end # end if
#         end # end zone mizings 
    end # end constant 

    # Split Rulesets into before, during and after
    model.getScheduleRulesets.each do |set|
#       print("rulesets")
#         print(set.name.to_s)
      #new_rule_index = 0
  
      # Exclude the following schedules:
      next if set.name.to_s.include? "New"
      next if set.name.to_s.include? "shading"
      next if set.name.to_s.include? "season"
      
      # change setpoint based on schedule
      if set.name.to_s.include? "cooling setpoint"
        new_setpoint = 90;
      else
        new_setpoint = 0;
      end 

      next_rule_index = 0
      schedule_ruleset = set.to_ScheduleRuleset.get
      rules = set.to_ScheduleRuleset.get.scheduleRules
      outage_indicator =0
      rules.each_with_index do |each_rule,i|
        
        # rule order is set from end of year to beginning of year (0: December -- 11: January) 
        # in our case there should be 14 rules. 
        #print(each_rule,"\n")
        # If month is greater than start date, skip
        next if  each_rule.startDate.get > OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_start_date_month),1,assumed_year)
        
        if (each_rule.startDate.get == OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_start_date_month),1,assumed_year))
          
          rule_name = each_rule.name
          dayschedule_name = each_rule.daySchedule.name

          if outage_indicator == 0
            new_rule_index = each_rule.ruleIndex
            og_rule_index = each_rule.ruleIndex
            outage_indicator = 1 
          else
            new_rule_index = next_rule_index
          end
          
          # Create After Power Outage Rule 
          rule_clone_after_outage = each_rule.clone
          rule_clone_after_outage = rule_clone_after_outage.to_ScheduleRule.get
          rule_clone_after_outage.setName("#{rule_name} after Power Outage")
          rule_clone_after_outage.setStartDate(post_outage_start_date)
          rule_clone_after_outage.setEndDate(each_rule.endDate.get)
          ruleday_clone_after_outage = rule_clone_after_outage.daySchedule
          ruleday_clone_after_outage.setName("#{dayschedule_name} after Power Outage")
          schedule_ruleset.setScheduleRuleIndex(rule_clone_after_outage,new_rule_index)
          new_rule_index = new_rule_index + 1
          #print(rule_clone_after_outage,"\n")

          if scenario == 1
            #print(rule_name,"\n")
              
            # Create Power Outage Rule During Power Outage 
            rule_clone_during_outage = each_rule.clone
            rule_clone_during_outage = rule_clone_during_outage.to_ScheduleRule.get
            rule_clone_during_outage.setName("#{rule_name} during Power Outage")
            rule_clone_during_outage.setStartDate(otg_start_date)
            rule_clone_during_outage.setEndDate(otg_end_date)
            ruleday_clone_during_outage = rule_clone_during_outage.daySchedule
            ruleday_clone_during_outage.setName("#{dayschedule_name} during Power Outage")
            schedule_ruleset.setScheduleRuleIndex(rule_clone_during_outage,new_rule_index)
            new_rule_index = new_rule_index + 1
            
            times = ruleday_clone_during_outage.times
            values = ruleday_clone_during_outage.values
            
            new_times = Array(1..24)
            new_values = Array.new(new_times.size,0)
            
            iValue = 0
            for eachTime in new_times
              new_time = OpenStudio::Time.new(0,eachTime,0,0)
              
              if new_time <= times[iValue]
                new_values[eachTime-1] = values[iValue]
              else
                iValue = iValue + 1
                redo
              end 
            end 

            ruleday_clone_during_outage.clearValues()
            
            for eachTime in 0..new_times.size-1
              new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
              # Assign original values as if there is no power outage, but for 24 hours
              ruleday_clone_during_outage.addValue(new_time,new_values[eachTime])

              # Re-Assign power outage values during power outage
              if (new_time >= otg_start_time && new_time <= otg_end_time)
                ruleday_clone_during_outage.addValue(new_time,new_setpoint)
              end
            end 

          elsif scenario == 2
            # Create Power Outage Rule End Power Outage 
            rule_clone_during_outage = each_rule.clone
            rule_clone_during_outage = rule_clone_during_outage.to_ScheduleRule.get
            rule_clone_during_outage.setName("#{rule_name} Start Power Outage")
            rule_clone_during_outage.setStartDate(otg_end_date)
            rule_clone_during_outage.setEndDate(otg_end_date)
            ruleday_clone_during_outage = rule_clone_during_outage.daySchedule
            ruleday_clone_during_outage.setName("#{dayschedule_name} End Power Outage")
            schedule_ruleset.setScheduleRuleIndex(rule_clone_during_outage,new_rule_index)
            new_rule_index = new_rule_index + 1
            
            times = ruleday_clone_during_outage.times
            values = ruleday_clone_during_outage.values

            new_times = Array(1..24)
            new_values = Array.new(new_times.size,0)

            iValue = 0
            for eachTime in new_times
              new_time = OpenStudio::Time.new(0,eachTime,0,0)
              
              if new_time <= times[iValue]
                new_values[eachTime-1] = values[iValue]
              else
                iValue = iValue + 1
                redo
              end 
            end 

            ruleday_clone_during_outage.clearValues()
            
            for eachTime in 0..new_times.size-1
              new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
              # Assign original values as if there is no power outage, but for 24 hours
              ruleday_clone_during_outage.addValue(new_time,new_values[eachTime])

              # Re-Assign power outage values during power outage
              if (new_time <= otg_end_time)
                ruleday_clone_during_outage.addValue(new_time,new_setpoint)
              end
            end 

            # Create Power Outage Rule Start Power Outage 
            rule_clone_during_outage = each_rule.clone
            rule_clone_during_outage = rule_clone_during_outage.to_ScheduleRule.get
            rule_clone_during_outage.setName("#{rule_name} Start Power Outage")
            rule_clone_during_outage.setStartDate(otg_start_date)
            rule_clone_during_outage.setEndDate(otg_start_date)
            ruleday_clone_during_outage = rule_clone_during_outage.daySchedule
            ruleday_clone_during_outage.setName("#{dayschedule_name} Start Power Outage")
            schedule_ruleset.setScheduleRuleIndex(rule_clone_during_outage,new_rule_index)
            new_rule_index = new_rule_index + 1
            
            times = ruleday_clone_during_outage.times
            values = ruleday_clone_during_outage.values

            new_times = Array(1..24)
            new_values = Array.new(new_times.size,0)

            iValue = 0
            for eachTime in new_times
              new_time = OpenStudio::Time.new(0,eachTime,0,0)
              
              if new_time <= times[iValue]
                new_values[eachTime-1] = values[iValue]
              else
                iValue = iValue + 1
                redo
              end 
            end 

            ruleday_clone_during_outage.clearValues()
            
            for eachTime in 0..new_times.size-1
              new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
              # Assign original values as if there is no power outage, but for 24 hours
              ruleday_clone_during_outage.addValue(new_time,new_values[eachTime])

              # Re-Assign power outage values during power outage
              if (new_time >= otg_start_time)
                ruleday_clone_during_outage.addValue(new_time,new_setpoint)
              end
            end 

        elsif scenario == 3
            # Create Power Outage Rule End Power Outage 
            rule_clone_during_outage = each_rule.clone
            rule_clone_during_outage = rule_clone_during_outage.to_ScheduleRule.get
            rule_clone_during_outage.setName("#{rule_name} Start Power Outage")
            rule_clone_during_outage.setStartDate(otg_end_date)
            rule_clone_during_outage.setEndDate(otg_end_date)
              ruleday_clone_during_outage = rule_clone_during_outage.daySchedule
              ruleday_clone_during_outage.setName("#{dayschedule_name} End Power Outage")
              schedule_ruleset.setScheduleRuleIndex(rule_clone_during_outage,new_rule_index)
              new_rule_index = new_rule_index + 1

              times = ruleday_clone_during_outage.times
              values = ruleday_clone_during_outage.values

              new_times = Array(1..24)
              new_values = Array.new(new_times.size,0)

              iValue = 0
              for eachTime in new_times
                new_time = OpenStudio::Time.new(0,eachTime,0,0)

                if new_time <= times[iValue]
                  new_values[eachTime-1] = values[iValue]
                else
                  iValue = iValue + 1
                  redo
                end 
              end 
              ruleday_clone_during_outage.clearValues()

              for eachTime in 0..new_times.size-1
                new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
                # Assign original values as if there is no power outage, but for 24 hours
                ruleday_clone_during_outage.addValue(new_time,new_values[eachTime])

                # Re-Assign power outage values during power outage
                if (new_time <= otg_end_time)
                  ruleday_clone_during_outage.addValue(new_time,new_setpoint)
                end
              end 
              # Create Power Outage Rule During Power Outage 
              rule_clone_during_outage = each_rule.clone
              rule_clone_during_outage = rule_clone_during_outage.to_ScheduleRule.get
              rule_clone_during_outage.setName("#{rule_name} During Power Outage")
              rule_clone_during_outage.setStartDate(blk_start_date)
              rule_clone_during_outage.setEndDate(blk_end_date)
              ruleday_clone_during_outage = rule_clone_during_outage.daySchedule
              ruleday_clone_during_outage.setName("#{dayschedule_name} During Power Outage")
              schedule_ruleset.setScheduleRuleIndex(rule_clone_during_outage,new_rule_index)
              new_rule_index = new_rule_index + 1

              times = ruleday_clone_during_outage.times
              values = ruleday_clone_during_outage.values

              new_times = Array(1..24)
              new_values = Array.new(new_times.size,0)

              iValue = 0
              for eachTime in new_times
                new_time = OpenStudio::Time.new(0,eachTime,0,0)

                if new_time <= times[iValue]
                  new_values[eachTime-1] = values[iValue]
                else
                  iValue = iValue + 1
                  redo
                end 
              end 

              ruleday_clone_during_outage.clearValues()

              for eachTime in 0..new_times.size-1
                new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
                # Assign original values as if there is no power outage, but for 24 hours
                ruleday_clone_during_outage.addValue(new_time,new_values[eachTime])

                # Re-Assign power outage values during power outage
                ruleday_clone_during_outage.addValue(new_time,new_setpoint)
              end 

              # Create Power Outage Rule Start Power Outage 
              rule_clone_during_outage = each_rule.clone
              rule_clone_during_outage = rule_clone_during_outage.to_ScheduleRule.get
              rule_clone_during_outage.setName("#{rule_name} Start Power Outage")
              rule_clone_during_outage.setStartDate(otg_start_date)
              rule_clone_during_outage.setEndDate(otg_start_date)
              ruleday_clone_during_outage = rule_clone_during_outage.daySchedule
              ruleday_clone_during_outage.setName("#{dayschedule_name} Start Power Outage")
              schedule_ruleset.setScheduleRuleIndex(rule_clone_during_outage,new_rule_index)
              new_rule_index = new_rule_index + 1

              times = ruleday_clone_during_outage.times
              values = ruleday_clone_during_outage.values

              new_times = Array(1..24)
              new_values = Array.new(new_times.size,0)

              iValue = 0
              for eachTime in new_times
                new_time = OpenStudio::Time.new(0,eachTime,0,0)

                if new_time <= times[iValue]
                  new_values[eachTime-1] = values[iValue]
                else
                  iValue = iValue + 1
                  redo
                end 
              end 
              ruleday_clone_during_outage.clearValues()

              for eachTime in 0..new_times.size-1
                new_time = OpenStudio::Time.new(0,new_times[eachTime],0,0)
                # Assign original values as if there is no power outage, but for 24 hours
                ruleday_clone_during_outage.addValue(new_time,new_values[eachTime])

                # Re-Assign power outage values during power outage
                if (new_time >= otg_start_time)
                  ruleday_clone_during_outage.addValue(new_time,new_setpoint)
                end
              end
          end 
          #print(rule_clone_during_outage,"\n")
          # Create Before Power Outage Rule
          each_rule.setName("#{rule_name} before Power Outage")
          each_rule.setEndDate(pre_outage_end_date)
          schedule_ruleset.setScheduleRuleIndex(each_rule,new_rule_index)
          new_rule_index = new_rule_index + 1  
          next_rule_index = new_rule_index   
          #new_rule_index = new_rule_index.to_i     
          #print('before outage rule index =',new_rule_index,"\n")

      # Change ruleIndex of every schedule after outage 
    # print(next_rule_index,"\n")
        elsif (each_rule.startDate.get <= OpenStudio::Date.new(OpenStudio::MonthOfYear.new(otg_start_date_month + 1),1,assumed_year))
          new_rule_index = next_rule_index
          schedule_ruleset.setScheduleRuleIndex(each_rule,new_rule_index)
          new_rule_index = new_rule_index + 1
          next_rule_index = new_rule_index 
        end
      end 
    end
    output_file_path = "#{File.dirname(__FILE__)}/new_model.osm"
    model.save(output_file_path, true)
  end # end the run
end # end the measure

# this allows the measure to be use by the application
PowerOutage.new.registerWithApplication