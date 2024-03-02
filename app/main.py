#!/usr/bin/env python
# coding: utf-8

# In[ ]:

from contextlib import asynccontextmanager

from typing import Union, Annotated

from fastapi import FastAPI, Query, Path, BackgroundTasks
# from fastapi.testclient import TestClient
from pydantic import BaseModel
import numpy as np
import requests
import appliance
import InstallAPIcalls
import time
from fastapi.middleware.wsgi import WSGIMiddleware
from InstallGraphing import app as ElectricityGraph

app = FastAPI()



users = []
customers = []
elec_dicts = []


# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

# client = TestClient(app)

@app.post("/users/")
async def read_user_bayou(
        utility: str = "speculoos_power",
        email: str = "QuickStart@bayou.energy"
):
    bayou_user = {
        "utility": utility,
        "email": email
    }

    users.append(bayou_user)
    return users


@app.get("/users/{user_id}")
async def read_user(user_id: int):
    return users[user_id]


# This is to create a new customer in Bayou
@app.post("/new_customers/")
def bayou_customer_generation(
        user_id: int
):
    bayou_user = users[user_id]
    utility = bayou_user["utility"]
    email = bayou_user["email"]

    check = InstallAPIcalls.UtilityCheck(utility)
    if check:
        return check
    else:
        customer = InstallAPIcalls.BayouAPICustomer(utility, email)
    if not customer["has_filled_credentials"]:
        customer_link = InstallAPIcalls.BayouAPICustomerLink(customer)
        return customer_link
    else:
        customers.append(customer)
        return customer


# This is to pull customer data from Bayou
@app.post("/customers/")
def bayou_customer_pull(user_id: int):
    bayou_user = users[user_id]
    utility = bayou_user["utility"]
    email = bayou_user["email"]

    check = InstallAPIcalls.UtilityCheck(utility)
    if check:
        return check
    else:
        customer = InstallAPIcalls.BayouAPICustomer2(utility, email)
    if not customer["has_filled_credentials"]:
        customer_link = InstallAPIcalls.BayouAPICustomerLink(customer)
        return customer_link
    else:
        customers.append(customer)
        return customer


@app.put("/customers/{customer_id}")
def bayou_customer_credentials(customer_id: int):
    customer = customers[customer_id]
    customer_link = InstallAPIcalls.BayouAPICustomerLink(customer)
    return customer_link


@app.post("/electricity_data/")
def bayou_customer_elec_data(
        customer_id: int
):
    customer = customers[customer_id]
    elec_dict = InstallAPIcalls.BayouAPICustomerBillData(customer)
    elec_dicts.append(elec_dict)
    print(elec_dict)
    return elec_dict

@app.get("/elec_graphs/")
def create_electricity_graph(
        customer_id: int
):
    #Right now there's no logic for pulling in customer data so we'll just mount the dashboard
    app.mount("/electricity_graph/", WSGIMiddleware(ElectricityGraph.server))

# @app.put("/items/{item_id}")
# async def update_item(
#     item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
#     q: str | None = None,
#     item: Item | None = None,
# ):
#     results = {"item_id": item_id}
#     if q:
#         results.update({"q": q})
#     if item:
#         results.update({"item": item})
#     return results