#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import requests
import numpy as np
import time
import pandas as pd
import json

def UtilityCheck(utility):
    valid_utilities = ["speculoos_power"]
    error_string = "The utility provided is not available within Bayou Energy."
    if utility not in valid_utilities:
        return error_string
    else:
        return None
    
def BayouAPICustomer(utility, email):
    # Bayou has two environments, staging, as shown below, and production, bayou_domain="bayou.energy"

    bayou_domain = "staging.bayou.energy"

    # Get and manage API keys at f"https://{bayou_domain}/dashboard/keys"

    # API reference: https://docs.bayou.energy/v2.0/reference/authentication 
    
    # Note: This is mine (Chad's) personal API key. We may want to hide this during production.

    bayou_api_key = "test_221_f6f1a2d9daef91272215d4761f52ff80465c7dee839b4585a0aab96ddc284159"
    
    customer = requests.post(f"https://{bayou_domain}/api/v2/customers", json={

        "utility": utility, # Speculoos is Bayou's fake utility for testing, https://docs.bayou.energy/v2.0/reference/utility-support

        "email" : email # Email address isn't a required field, https://docs.bayou.energy/docs/merge-customer-code-with-your-project

    }, auth=(bayou_api_key, '')).json()
    
    return customer

#I made this to test dummy customer data as I've created the dummy customer like 30 times at this point
def BayouAPICustomer2(utility, email):
    # Bayou has two environments, staging, as shown below, and production, bayou_domain="bayou.energy"

    bayou_domain = "staging.bayou.energy"

    # Get and manage API keys at f"https://{bayou_domain}/dashboard/keys"

    # API reference: https://docs.bayou.energy/v2.0/reference/authentication 
    
    # Note: This is mine (Chad's) personal API key. We may want to hide this during production.

    bayou_api_key = "test_221_f6f1a2d9daef91272215d4761f52ff80465c7dee839b4585a0aab96ddc284159"
    
    customer = requests.get(f"https://{bayou_domain}/api/v2/customers", json={

        "utility": utility, # Speculoos is Bayou's fake utility for testing, https://docs.bayou.energy/v2.0/reference/utility-support

        "email" : email # Email address isn't a required field, https://docs.bayou.energy/docs/merge-customer-code-with-your-project

    }, auth=(bayou_api_key, '')).json()
    
    return customer[0]

def BayouAPICustomerLink(customer):
    
    return customer['onboarding_link']

def BayouAPICustomerBillData(customer):
    
    bayou_domain = "staging.bayou.energy"
    
    if customer["has_filled_credentials"]:
        
        # Note: This is mine (Chad's) personal API key. We may want to hide this during production.

        bayou_api_key = "test_221_f6f1a2d9daef91272215d4761f52ff80465c7dee839b4585a0aab96ddc284159"
        #customer = requests.get(f"https://{bayou_domain}/api/v2/customers/{customer['id']}", auth=(bayou_api_key, '')).json()
        
        try_number = 1
        while try_number < 5:
            try:
                billdata = requests.get(f"https://{bayou_domain}/api/v2/customers/{customer['id']}/bills", auth=(bayou_api_key, ''))
                bills = billdata.json()
                try_number = 5
            except:
                time.sleep(2**try_number)
                try_number = try_number + 1
                    
        elecarray = []
        eleccarray = []
        gasarray = []
        gascarray = []
        costarray = []
        for bill in bills[:12]:

            elecarray.append(bill['electricity_consumption'])
            eleccarray.append(bill['electricity_amount'])
            gasarray.append(bill['gas_consumption'])
            gascarray.append(bill['gas_amount'])
            
        elecavg = np.average(elecarray)
        elecyr = np.sum(elecarray)
        gasyr = np.sum(gasarray)
        eleccyr = np.sum(eleccarray)
        gascyr = np.sum(gascarray)
        
        elec_dict = {
            "Average Electricity Use": elecavg,
            "Yearly Electricity Consumption": elecyr,
            "Yearly Gas Consumption": gasyr,
            "Yearly Electricity Cost": eleccyr,
            "Yearly Gas Cost": gascyr
        }
        print(elec_dict)
        return elec_dict
    
        
        
# This function looks up the needed parameters for a given appliance if its brand name and model number are known.
# In order for this to work properly, we'll probably need to build selectors for the user's brand name and model number.
# Later on, we may be able to build OCR for camera photos to extract the data (through Tesseract or similar).
# The function returns a dict with the parameters needed.  Any additional keyword arguments are passed through to the end dict.

def EnergyStarAPIApplianceMatch(appliance_type, brand_name, model_number, **kwargs):
    
    energy_star_urls = {
        "dehumidifiers": "https://data.energystar.gov/resource/myec-ajj2.json",
        "clothes dryers": "https://data.energystar.gov/resource/t9u7-4d2j.json",
        "clothes washers": "https://data.energystar.gov/resource/bghd-e2wd.json",
        "dishwashers": "https://data.energystar.gov/resource/q8py-6w3f.json",
        "electric cooking": "https://data.energystar.gov/resource/m6gi-ng33.json",
        "freezers": "https://data.energystar.gov/resource/8t9c-g3tn.json",
    }
    
    needed_parameters = {
        "dehumidifiers": ["dehumidifier_efficiency_integrated_energy_factor_l_kwh_", "dehumidifier_water_removal_capacity_per_appendix_x1_pints_day", "dehumidifier_type"],
        "clothes dryers": ["combined_energy_factor_cef", "product_type", "type"]
    }
    
    
    appliance_dict = {
        "appliance_type": appliance_type,
        "brand_name": brand_name,
        "model_number": model_number
    }
    
    appliance_types = list(energy_star_urls.keys())
    
    if appliance_type in appliance_types:
        energy_star_url = energy_star_urls[appliance_type]
        needed_parameter_set = needed_parameters[appliance_type]
        
        headers = {
                "X-App-Token": "hKV3KyjBKxMoRTsr6dpGO8eII"
            }
    
        energy_star_app_token = "hKV3KyjBKxMoRTsr6dpGO8eII"



       
        try_number = 1
        while try_number < 5:
            try:
                test = requests.get(energy_star_url, headers={"X-Params": json.dumps(headers)})
                print(test)
                energy_star_json = test.json()
                try_number = 5
            except:
                time.sleep(2**try_number)
                try_number = try_number + 1
        
        energy_star_df = pd.DataFrame(test2)
        
        # As far as I can tell only the model number is needed - but brand name + model number should make a series of selectors easier
        energy_star_mod = energy_star_df[energy_star_df['model_number'] == model_number]
        
        for param in needed_parameter_set:
            appliance_dict[param] = energy_star_mod.iloc[0][param]
        
        for name, val in kwargs.items():
            appliance_dict[name] = val
        
        return appliance_dict
        
    else:
        
        #If the appliance type is not recognized for whatever reason the appliance dict is passed through unchanged
        
        for name, val in kwargs.items():
            appliance_dict[name] = val
        
        return appliance_dict
        
        
        
# Simplified Energy Star API Lookup - produces dataframe of Energy Star data based on appliance type    
def EnergyStarAPILookup(appliance_type):
        
    energy_star_urls = {
        "dehumidifiers": "https://data.energystar.gov/resource/myec-ajj2.json",
        "clothes dryers": "https://data.energystar.gov/resource/t9u7-4d2j.json",
        "clothes washers": "https://data.energystar.gov/resource/bghd-e2wd.json",
        "dishwashers": "https://data.energystar.gov/resource/q8py-6w3f.json",
        "electric cooking": "https://data.energystar.gov/resource/m6gi-ng33.json",
        "freezers": "https://data.energystar.gov/resource/8t9c-g3tn.json",
    }
        
    appliance_types = list(energy_star_urls.keys())  
       
    if appliance_type in appliance_types:
        energy_star_url = energy_star_urls[appliance_type]
    
        headers = {
                "X-App-Token": "hKV3KyjBKxMoRTsr6dpGO8eII"
            }
    
        energy_star_app_token = "hKV3KyjBKxMoRTsr6dpGO8eII"



       
        try_number = 1
        while try_number < 5:
            try:
                test = requests.get(energy_star_url, headers={"X-Params": json.dumps(headers)})
                print(test)
                energy_star_json = test.json()
                try_number = 5
            except:
                time.sleep(2**try_number)
                try_number = try_number + 1
        
        energy_star_df = pd.DataFrame(test2)
        
        return energy_star_df
        
        
def EIAElecPriceLookup(state_code):

    # This is my API key - may need to disguise it in some way
    
    params2 = {
        "api_key": "tgsLBY6uLeWqOU01LNiBfVBGaii5QWXLlOhybOiv"
    }

    headers = {
        "frequency": "monthly",
        "data": [
            "price"
        ],
        "facets": {
            "sectorid": [
                "RES"
            ]
        },
        "start": "2022-01",
        "end": "2023-01",
        "sort": [
            {
                "column": "period",
                "direction": "desc"
            }
        ],
        "offset": 0,
        "length": 5000
    }
        
    eiaapi = "tgsLBY6uLeWqOU01LNiBfVBGaii5QWXLlOhybOiv"
    eia_test_url = "https://api.eia.gov/API_route?api_key=" + eiaapi
    eia_elec_url = "https://api.eia.gov/v2/electricity/retail-sales/data?api_key=" + eiaapi


    print(eia_elec_url)
    try_number = 1
    while try_number < 5:
        try:
            test = requests.get(eia_elec_url, params = params2, headers={"X-Params": json.dumps(headers)})
            print(test)
            test2 = test.json()
            try_number = 5
        except:
            time.sleep(2**try_number)
            try_number = try_number + 1


    tdf = pd.DataFrame(test2['response']['data'])
    tdf2 = tdf[(tdf['stateid'] == state_code)]
    elec_price = tdf2.iloc[0]['price']
        
    return elec_price
