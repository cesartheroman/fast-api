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


# Used to build a member of the Appliance class based on values from a dict 
def appliance_builder(appliance_type, **kwargs):
    
    if appliance_type == "dehumidifiers":
        
        for name, val in kwargs.items():
            if name == "dehumidifier_efficiency_integrated_energy_factor_l_kwh_":
                IEF = val
            elif name == "dehumidifier_water_removal_capacity_per_appendix_x1_pints_day":
                water_removal = val*pints_to_L
            elif name == "tank_switches_per_day":
                tank_switches_per_day = val
            elif name == "usage_per_year":
                usage_per_year = val
            elif name == "dehumidifier_type":
                dehumidifier_type = val
                            
        appliance = Dehumidifier(
            IEF = IEF,
            water_removal = water_removal,
            tank_switches_per_day = tank_switches_per_day,
            usage_per_year = usage_per_year,
            dehumidifier_type = dehumidifier_type
        )
            
    elif appliance_type == "clothes dryers":
        
        for name, val in kwargs.items():
            if name == 'combined_energy_factor_cef':
                CEF = val
            elif name == "dryer_type":
                dryer_type = val
            elif name == "dryer_energy_type":
                dryer_energy_type = val
            elif name == "number_of_loads_per_week":
                weekly_user_loads = val
            elif name == "average_user":
                if val == "yes":
                    average_user = True
                elif val == "no":
                    average_user = False
            
                            
        appliance = Dryer(
            CEF = CEF,
            dryer_type = dryer_type,
            dryer_energy_type = dryer_energy_type,
            weekly_user_loads = weekly_user_loads,
            average_user = average_user
        )
        
        
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