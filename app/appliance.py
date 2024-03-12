#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# This file is used to declare classes for appliances located in Energy Star API data, as well as their functions.

from typing import Union, Annotated

from fastapi import FastAPI, Query, Path
from pydantic import BaseModel
import numpy as np
import requests
import pandas as pd
from copy import deepcopy

#base class for all appliances
class Appliance:
    appliance_type: str # Simple declaration of the type of appliance (dehumidifier, dryer, etc.)
    model_number: str # Used in most lookups for the Energy Star API regardless of appliance type
        
  
#class for dehumidifiers
class Dehumidifier(Appliance):
    
           # The dehumidifer integrated energy factor is calculated here: https://www.ecfr.gov/current/title-10/chapter-II/subchapter-D/part-430/subpart-B/appendix-Appendix%20X1%20to%20Subpart%20B%20of%20Part%20430
        # This provides a value for L removed per kWh under specified test conditions. 
        # Test temperature is 73 F (+/- 2 F) with 60% (+/- 5%) relative humidity
        # (averages must be 73 F +/- 0.5 F with 60% +/- 2% humidity)
        # The test must also be performed for 2 hours for the calculation of IEF.
        # The power is based off of both the 2 hour test and "low power mode" (both in hourly rates)
        # We can look up the maximum capacity of the user's existing dehumidifier and calculate an old and new kWh based on that. This is just a simple equation based on the user's info and best guess at tank switches per day.
        # When we compare this, we can use a different dehumidifier and use the user's old water removal capacity and tank switches to calculate a new energy requirement.
        # The result is energy consumed per year
        # The "most efficient" criteria is defined by this IEF and also by the size and type of dehumidifier
        # Source: https://www.energystar.gov/sites/default/files/asset/document/Dehumidifiers%20ENERGY%20STAR%20Most%20Efficient%202024%20Final%20Criteria.pdf
    
    
    IEF: float # integrated energy factor, in L/kWh, from Energy Star API (or user specified)
    water_removal: float # water removal for dehumidifier, in pints/day, from Energy Star API (or user specified)
    tank_switches_per_day: float # number of times the tank is emptied in a given day (user specified)
    usage_per_year: float # amount of usage for the dehumidifier per year (as a fraction of the year from 0 to 1) (user specified)
    pints_to_L = 0.473176
    dehumidifier_type: str # type of dehumidifier, whether "whole home" or "portable", from the Energy Star API (or user specified)
    
    @property
    def water_removal_to_L(self) -> float:
        return self.water_removal * self.pints_to_L

    @property
    def kWh_per_year(self) -> float:
        return self.water_removal_to_L / self.IEF * self.tank_switches_per_day * self.usage_per_year * 24 * 365
    
    
class Dryer(Appliance):
    
            # The combined energy factor (CEF), in lbs/kWh, calculates the amount of power for a test load (8.45 lbs for standard and 3.00 lbs for compact dryers)
        # Source: https://www.ecfr.gov/current/title-10/chapter-II/subchapter-D/part-430/subpart-B
        # The Energy Star API also calculates the estimated kWh/year, based on 283 loads (average use)
        # Source: https://data.energystar.gov/Active-Specifications/ENERGY-STAR-Certified-Residential-Clothes-Dryers/t9u7-4d2j/about_data
        # The "most efficient" energy criteria for clothes dryers automatically excludes all gas powered dryers. 
        # Source: https://www.energystar.gov/sites/default/files/asset/document/Clothes%20Dryer%20ENERGY%20STAR%20Most%20Efficient%202024%20Final%20Criteria.pdf
        # In addition (though the document does not say this) the only dryers listed as having this criteria have a heat pump. 
        # Source: https://www.energystar.gov/products/clothes_dryers#:~:text=All%20heat%20pump%20dryers%20meet,once%20the%20moisture%20is%20removed.
        
        # We use the CEF to estimate the user's power usage in conjunction with how much they think they use their dryer in a given week.
        # We can also provide an option to use the average.
        # We assume that all loads match the standard or compact test load.
        
        
    CEF: float # combined energy factor, in lbs/kWh, from Energy Star API (or user specified)
    dryer_type: str # type of dryer (standard or compact), from Energy Star API (or user specified)
    dryer_energy_type: str # electric or gas, from Energy Star API (or user specified)
    standard_test_load = 8.45 # test load for standard dryers, in lbs
    compact_test_load = 3.00 # test load for compact dryers, in lbs
    average_uses = 283 # average number of dryer uses per year
    weekly_user_loads: float # number of user loads in a given week
    average_user: bool #determine if average user, whether true or false

    @property
    def yearly_loads(self) -> float:
        if self.average_user:
            return self.average_uses
        else:
            return self.weekly_user_loads*52

    @property
    def kWh_per_year(self) -> float:
        if dryer_type == "standard":
            return 1 / self.CEF * self.standard_test_load * self.yearly_loads
        elif dryer_type == "compact":
            return 1 / self.CEF * self.compact_test_load * self.yearly_loads

class Washer(Appliance):

    # The integrated modified energy factor (IMEF, ft3/kWh/cycle) can be used to calculate the energy consumption.
    # This is the size of the container in cubic feet divided by the energy consumption per cycle.
    # We also need the volume (in cubic feet) and the number of washes the user typically does in a week.
    # Though it does not apply directly to the energy consumption we can also track water usage.
    # Another parameter (IWF) tracks water consumed per cubic feet of capacity (in gal/ft3)
    # Source: https://dev.socrata.com/foundry/data.energystar.gov/bghd-e2wd
    # The efficiency criteria from Energy Star is dependent on the size of the washer:
    # For residential washers (front loading) > 2.5 ft3, IMEF >= 2.76, IWF <= 3.2
    # For residential washers (top loading) > 2.5 ft3, IMEF >= 2.06, IWF <= 4.3
    # For all residential washers <= 2.5 ft3, IMEF >= 2.07, IWF <= 4.2
    # Commercial washers are different and are not included in this class currently
    # Source: https://www.energystar.gov/products/clothes_washers/key_product_criteria

    IMEF: float #integrated modified energy factor, ft3/kWh/cycle
    IWF: float #integrated water factor, gal/ft3
    ES_annual_water_use: float #this is based on the energy star parameter - NOT the actual user's annual water use (gal/year)
    washer_volume: float #volume of washer in ft3
    weekly_user_loads: float #number of washes the user does in a week
    average_uses = 295 #estimated on energy star site
    average_user: bool
    load_type: str # front or top loading, need to track but does not impact calcs

    @property
    def yearly_loads(self) -> float:
        if self.average_user:
            return self.average_uses
        else:
            return self.weekly_user_loads*52
    @property
    def kWh_per_year(self) -> float:
        return self.washer_volume/self.IMEF * self.yearly_loads

    @property
    def annual_water_use(self) -> float:
        return self.ES_annual_water_use/self.average_uses * self.yearly_loads

class Dishwasher(Appliance):


    # The energy use of a dishwasher is calculated using the provided Energy Star annual energy use.
    # This energy use is based on 215 loads per year (roughly 4 per week).
    # We just need the amount of times the user uses their dishwasher to calculate this more accurately.
    # Source: https://dev.socrata.com/foundry/data.energystar.gov/q8py-6w3f
    # To meet the Energy Star efficiency criteria the dishwasher must meet the following:
    # For Standard dishwashers (>= 8 place settings + 6 serving pieces): <= 270 kWh/year, <=3.5 gal/cycle
    # For Compact dishwashers (< 8 place settings + 6 serving pieces): <= 203 kWh/year, <=3.10 gal/cycle
    # Source: https://www.energystar.gov/products/dishwashers/key_product_criteria

    ES_annual_energy_use: float # Energy use in kWh/year for 215 uses
    weekly_user_loads: float # User defined, weekly loads
    water_use_per_cycle: float # Expected water use per cycle in gal/cycle
    average_uses = 215
    average_user: bool # Determines whether or not to use average_uses
    dishwasher_type: str # "Standard" or "Compact"

    @property
    def yearly_loads(self) -> float:
        if self.average_user:
            return self.average_uses
        else:
            return self.weekly_user_loads*52

    @property
    def kWh_per_year(self) -> float:
        return self.ES_annual_energy_use * self.yearly_loads / self.average_uses

    @property
    def annual_water_use(self) -> float:
        return self.water_use_per_cycle * self.yearly_loads


class Cooking(Appliance):

    # The energy use of cooking appliances (stoves, etc.) is measured by the API using the annual energy consumption.
    # This is based off of 4 "cooking events" per week, averaging 31 minutes.
    # In order to calculate the user's energy use we'll need how often they actually cook.
    # Source: https://dev.socrata.com/foundry/data.energystar.gov/m6gi-ng33
    # The "most efficient criteria" is dependent on the integrated annual energy consumption (must be less than 195 kWh/yr)
    # For ranges, the criteria is dependent on the low-power mode energy consumption <7 kWh/yr
    # Source: https://www.energystar.gov/products/electric_cooking_products/key_product_criteria


    ES_annual_energy_use: float
    average_uses = 418 # number of yearly uses per year for average user
    average_user: bool
    average_time_use = 31 #minutes for average cook
    weekly_user_uses: float # User defined, weekly uses
    weekly_user_time: float # User defined, minutes user uses cooktop
    cooking_type: str # "Cooktop" or "Range"


    @property
    def yearly_uses(self) -> float:
        if self.average_user:
            return self.average_uses
        else:
            return self.weekly_user_loads*52

    @property
    def time_use(self) -> float:
        if self.average_user:
            return self.average_time_use
        else:
            return self.weekly_user_time

    @property
    def kWh_per_year(self) -> float:
        return self.ES_annual_energy_use * self.yearly_uses / self.average_uses * self.time_use / self.average_time_use


class Freezer(Appliance):

    # Freezers are going to be difficult to estimate - there's not a "uses" parameter that's easy to extract.
    # In addition, in the home they're often paired with a refrigerator. Standalone freezers may not come up as often.
    # The metric for "most efficient" is "10% less energy use than the minimum federal efficiency standards".
    # Source: https://www.energystar.gov/products/refrigerators/key_product_criteria
    # The minimum efficiency standard is calculated based off of two tests at two reference temperatures.
    # Those reference temperatures are discussed here:
    # Source: https://www.aham.org/DownloadableFiles/HRF_1_2019_draft.pdf
    # The federal register discusses using this test method here:
    # Source: https://www.ecfr.gov/current/title-10/chapter-II/subchapter-D/part-430#Appendix-B-to-Subpart-B-of-Part-430
    # The ambient temp is set to 90 degF and the freezer has to at least hit 0 degF.
    # That temp requirement is the same for refrigerator-freezers (for the freezer component).
    # Currently I'm not sure how to modulate the energy use. My first thought is to collect data about the user's
    # ambient temperature.
    # However, literature suggests no clear relationship between ambient temperature and electrical power use.
    # Source: https://core.ac.uk/download/pdf/227106144.pdf
    # It mainly just seems to vary based on the time of the year.
    # Keep in mind however that all of that research was done in England which would have a more consistent climate
    # (than the US at least).
    # Another source suggests some relationship.
    # Source: https://www.sciencedirect.com/science/article/abs/pii/S0196890401000693
    # Finally another source suggests an additional relationship for temperature vs. power consumption (a thesis).
    # Source: https://oaktrust.library.tamu.edu/bitstream/handle/1969.1/155467/BURGESS-THESIS-2015.pdf?sequence=1
    # We'll just use the average power of the freezer for now - may need to investigate further later on.


    is_compact: bool
    average_user: bool
    ES_annual_energy_use: float

    @property
    def kWh_per_year(self) -> float:
        return self.ES_annual_energy_use

class HeatPump(Appliance):

    # There are multiple heat pump calculations - this appliance is much more involved.
    # For example, the SEER2 (seasonal energy efficiency ratio) is calculated using the "cooling season", with 8 bin
    # temperatures of 5F increments (67, 72, 77 ... 102 F).  At each "bin" (increment), the cooling capability is
    # compared to the electrical consumption.  The sum of this capability is compared to the sum of the consumption.
    # The 67F bin is 65 - 69F, the 72 bin is 70F - 74F and so on.

    # The HSPF2 is based on heating in six different climate regions, ranging from 67 F all the way down to
    # -23 F (binned similarly as SEER2).
    # Source: https://www.ecfr.gov/current/title-10/chapter-II/subchapter-D/part-430/subpart-B/appendix-Appendix%20M1%20to%20Subpart%20B%20of%20Part%20430
    # More reading on SEER2 and EER2:
    # https://www.energy.gov/gc/articles/air-conditioner-regional-standards-brochure
    # Interestingly, none of the ducted heat pumps on the Energy Star database meet the "most efficient criteria":
    # Source: https://dev.socrata.com/foundry/data.energystar.gov/3m3x-a2hy
    # This criteria excludes all air conditioners as they do not provide "compressor-based cooling".
    # Source: https://www.energystar.gov/sites/default/files/asset/document/ASHP%20ENERGY%20STAR%20Most%20Efficient%202024%20Final%20Criteria.pdf

    # The key to these calculations is the amount of energy removed or added to the system.
    # For cooling systems we'll need the energy removed which will come from the home model.
    # For heating systems it's in reverse - however, the amount of heat able to be delivered is typically related to the
    # temperature inside (bracketed at 47F, 17F, 7F).
    # For cooling we'll use the SEER2 value, and for heating we'll use HSFP2.
    # The energy_requirements value will come from the separate Home model.


    seer2: float # The seasonal energy efficiency ratio in Btu/W*h, total heat removed / electrical energy consumed
    # for an air conditioner in a cooling season
    eer2: float # energy efficiency ratio, cooling effect / energy consumed for air conditioner or heat pump in Btu/W*h
    hspf2: float # Heating seasonal performance factor, total heating output of central AC heat pump divided by the
    # total electric power input, in Btu/W*h
    operating_mode: str # "cooling" or "heating"
    energy_requirements: float # The energy delivered or removed from the home, in Btu/year

    @property
    def kWh_per_year(self) -> float:
        if self.operating_mode == "heating":
            return self.energy_requirements/self.hspf2 * 1000
        elif self.operating_mode == "cooling":
            return self.energy_requirements/self.seer2 * 1000





    

# Used to build a member of the Appliance class based on values from a dict 
def appliance_builder(appliance_type, **kwargs):
    
    if appliance_type == "dehumidifiers":
        IEF = 1
        water_removal = 1
        tank_switches_per_day = 1
        usage_per_year = 0.5
        dehumidifier_type = "portable"

        dehumidifier_flags = [0,0,0,0,0]

        for name, val in kwargs.items():
            if name == "dehumidifier_efficiency_integrated_energy_factor_l_kwh_":
                IEF = val
                dehumidifier_flags[0] = 1
            elif name == "dehumidifier_water_removal_capacity_per_appendix_x1_pints_day":
                water_removal = val
                dehumidifier_flags[1] = 1
            elif name == "tank_switches_per_day":
                tank_switches_per_day = val
                dehumidifier_flags[2] = 1
            elif name == "usage_per_year":
                usage_per_year = val
                dehumidifier_flags[3] = 1
            elif name == "dehumidifier_type":
                dehumidifier_type = val
                dehumidifier_flags[4] = 1

        if not 0 in dehumidifier_flags:
            appliance = Dehumidifier(
                IEF = IEF,
                water_removal = water_removal,
                tank_switches_per_day = tank_switches_per_day,
                usage_per_year = usage_per_year,
                dehumidifier_type = dehumidifier_type
            )

            return appliance
            
    elif appliance_type == "clothes dryers":

        CEF = 1
        dryer_type = "compact"
        dryer_energy_type = "gas"
        weekly_user_loads = 1
        average_user = False

        dryer_flags = [0,0,0,0,0]
        for name, val in kwargs.items():
            if name == 'combined_energy_factor_cef':
                CEF = val
                dryer_flags[0] = 1
            elif name == "dryer_type":
                dryer_type = val
                dryer_flags[1] = 1
            elif name == "dryer_energy_type":
                dryer_energy_type = val
                dryer_flags[2] = 1
            elif name == "number_of_loads_per_week":
                weekly_user_loads = val
                dryer_flags[3] = 1
            elif name == "average_user":
                dryer_flags[4] = 1
                if val == "yes":
                    average_user = True
                elif val == "no":
                    average_user = False
            

        if not 0 in dryer_flags:
            appliance = Dryer(
                CEF = CEF,
                dryer_type = dryer_type,
                dryer_energy_type = dryer_energy_type,
                weekly_user_loads = weekly_user_loads,
                average_user = average_user
            )

            return appliance

    elif appliance_type == "clothes washers":

        IMEF = 1
        IWF = 1
        load_type = "Front Load"
        ES_annual_water_use = 1
        washer_volume = 1
        weekly_user_loads = 1
        average_user = False

        washer_flags = [0,0,0,0,0,0,0]
        for name, val in kwargs.items():
            if name == 'integrated_modified_energy_factor_imef':
                IMEF = val
                washer_flags[0] = 1
            elif name == "load_configuration":
                load_type = val
                washer_flags[1] = 1
            elif name == "annual_water_use_gallons_year":
                ES_annual_water_use = val
                washer_flags[2] = 1
            elif name == "integrated_water_factor_iwf":
                IWF = val
                washer_flags[3] = 1
            elif name == "volume_cubic_feet":
                washer_volume = val
                washer_flags[4] = 1
            elif name == "number_of_loads_per_week":
                weekly_user_loads = val
                washer_flags[5] = 1
            elif name == "average_user":
                washer_flags[6] = 1
                if val == "yes":
                    average_user = True
                elif val == "no":
                    average_user = False

        if not 0 in washer_flags:
            appliance = Washer(
                IMEF = IMEF,
                load_type = load_type,
                ES_annual_water_use = ES_annual_water_use,
                IWF = IWF,
                washer_volume = washer_volume,
                weekly_user_loads = weekly_user_loads,
                average_user = average_user
            )

            return appliance

    elif appliance_type == "dishwashers":

        dishwasher_flags = [0,0,0,0,0]

        for name, val in kwargs.items():

            if name == "annual_energy_use_kwh_year":
                dishwasher_flags[0] = 1
                ES_annual_energy_use = val
            elif name == "water_use_gallons_cycle":
                dishwasher_flags[1] = 1
                water_use_per_cycle = val
            elif name == "number_of_loads_per_week":
                dishwasher_flags[2] = 1
                weekly_user_loads = val
            elif name == "type":
                dishwasher_flags[3] = 1
                dishwasher_type = val
            elif name == "average_user":
                dishwasher_flags[4] = 1
                if val == "yes":
                    average_user = True
                elif val == "no":
                    average_user = False

        if not 0 in dishwasher_flags:
            appliance = Dishwasher(
                ES_annual_energy_use = ES_annual_energy_use,
                water_use_per_cycle = water_use_per_cycle,
                weekly_user_loads = weekly_user_loads,
                dishwasher_type = dishwasher_type,
                average_user = average_user
            )

            return appliance

    elif appliance_type == "electric cooking":

        cooking_flags = [0,0,0,0,0]

        for name, val in kwargs.items():

            if name == "annual_energy_consumption_kwh_yr":
                cooking_flags[0] = 1
                ES_annual_energy_use = val
            elif name == "product_type":
                cooking_flags[1] = 1
                cooking_type = val
            elif name == "weekly_user_uses":
                cooking_flags[2] = 1
                weekly_user_uses = val
            elif name == "weekly_user_time":
                cooking_flags[3] = 1
                weekly_user_time = val
            elif name == "average_user":
                cooking_flags[4] = 1
                if val == "yes":
                    average_user = True
                elif val == "no":
                    average_user = False

        if not 0 in cooking_flags:

            appliance = Cooking(
                ES_annual_energy_use = ES_annual_energy_use,
                cooking_type = cooking_type,
                weekly_user_uses = weekly_user_uses,
                weekly_user_time = weekly_user_time,
                average_user = average_user
            )

            return appliance

def ApplianceEnergyStarComparison(appliance_type, Appliance, appliance_df):
    
    if appliance_type == "dehumidifiers":
        
        dehumidifier_type = Appliance.dehumidifier_type
        user_energy = Appliance.kWh_per_year
        tdf_best = appliance_df[(appliance_df['meets_most_efficient_criteria'] != 'No') & (appliance_df['dehumidifier_type'] == dehumidifier_type)]
        tdf_best = tdf_best.sort_values(by=['dehumidifier_efficiency_integrated_energy_factor_l_kwh_'])
        
        Dehumidifier_1 = deepcopy(Appliance)
        Dehumidifier_2 = deepcopy(Appliance)
        tdf_best_first = tdf_best.iloc[0]['dehumidifier_efficiency_integrated_energy_factor_l_kwh_']
        Dehumidifier_1.IEF = float(tdf_best_first)
        best_first_energy = Dehumidifier_1.kWh_per_year
        tdf_best_last = tdf_best.iloc[len(tdf_best)-1]['dehumidifier_efficiency_integrated_energy_factor_l_kwh_']
        Dehumidifier_2.IEF = float(tdf_best_last)
        best_last_energy = Dehumidifier_2.kWh_per_year
        savings_first = user_energy - best_first_energy
        savings_last = user_energy - best_last_energy
        
        # This is just an example of how the comparison could work
        if savings_first > 0:
            return_str = f"You could save between {savings_first} and {savings_last} kWh per year by switching your dehumidifier!"
        elif savings_last > 0:
            return_str = f"You already have an efficient dehumidifier, but you could save {savings_last} kWh per year by switching."
        else:
            return_str = "You already have one of the most efficient dehumidifiers on the market!"
