# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 17:25:17 2022

@author: shogh
"""

from flask import Flask, request
import requests
import uuid
from flask_cors import CORS
import pandas as pd

from database_interface import Search_Query, Food_Database

app = Flask(__name__)
CORS(app)

api_key = 'tBpRsC0HwbeunTGK0tw2tYgfkN3WZKmTYtbsB1da'

#Reads in table containing daily values from https://ods.od.nih.gov/HealthInformation/dailyvalues.aspx
dvdf = pd.read_excel('DV Table.xlsx', index_col=0, engine='openpyxl')


@app.route('/')
def hello_world():
	return 'Hello World!'

'''
This method searches for a food item in the database and returns its brand information, id, description, and ingredients.
The search should be a body posted to the method in the following format:
    {
        "main": {
            "fdcid": "apple", "brand": "", "ingd": "", "cat": "fruit"
         },
        "addFields": [
            { "field": "iron", "amt": "0", "ltm": "less" },
            { "field": "vc", "amt": "0", "ltm": "more" }
         ]
    }
'''
@app.route('/getdatabasefood',methods=['GET','POST'])
def get_database_food():
    if request.method == "POST":  
        #Processes post body
        inp = request.get_json()
        
        #References MongoDB Atlas database
        food_db = Food_Database('atlas_pass.txt', 'leaf', 'food_data')
        search_this = Search_Query()
        
        #Builds search query for ingredients, category, and id
        if inp['main']['ingd']:
            search_this.find_by_ingredients(inp['main']['ingd'])
        if inp['main']['cat']:
            search_this.find_by_category(inp['main']['cat'])
        if inp['main']['fdcid']:
            search_this.find_by_name_or_brand(inp['main']['fdcid'])
        
        #Builds search query for nutrients
        #Ensures nutrient query is in {field, amt, ltm} format
        nutdict = {}
        for f in inp['addFields']:
            #Adds "ltm" field
            if f['ltm'] == "less":
                tf = False
            else:
                tf = True
            #Adds "field" field
            nutdict[f["field"]] = (float(f['amt']), tf)
        if nutdict:
            search_this.find_by_percentage(nutdict)
        
        search = food_db.execute_search(search_this)
        
        #Filters out the fields we specifically want to return (id, description, ingredients, brand info)
        retlist = []
        ret_keys = set(["fdcId", "description", "brandedFoodCategory", "brandOwner", "ingredients"]) # "brandName"
        
        #Filters through search results and adds each result to a list, deleting the id
        for doc in search:
            del doc['_id'] #id must be deleted in order to avoid error
            retlist.append(doc)
            
        #Builds return format (list of dictionaries)
        for i in range(len(retlist)):
            temp = {}
            for k in ret_keys:
                if k in retlist[i]:
                    temp[k] = retlist[i][k]
                else:
                    temp[k] = ""
            retlist[i] = temp
        return {"result": retlist}

'''
This method searches for a food item in the database using its id and returns its nutritional information.
The search should be a body posted to the method in the following format:
    {
        "main": {
            "fdcid": "2120395"
         }
    }
'''
@app.route('/getdatabasenutrient',methods=['GET','POST'])
def get_database_nutrient():
    if request.method == "POST":
        #Processes post body
        inp = request.get_json()
        
        #References MongoDB Atlas database
        food_db = Food_Database('atlas_pass.txt', 'leaf', 'food_data')
        search_this = Search_Query()

        search_this.find_by_fdcId(int(inp['main']['fdcid'])) #Adds id field to search
        search = food_db.execute_search(search_this)
        
        #Filters through search results and adds each result to a list, deleting the id
        retlist = []
        for doc in search:
            del doc['_id'] #id must be deleted in order to avoid error
            retlist.append(doc)
            
        #Creates format to return (list of list of dictionaries), outer list is all foods, inner list is one food, inner dictionary is one nutrient
        retnut = []
        for i in range(len(retlist)):
            templ =[]
            
            #Constructs nutrient dictionary, which consists of nutrient name, amount, and daily value
            #Numerical fields (i.e. amount and daily value) are rounded to two decimal places
            for lk in retlist[i]['labelNutrients']:
                temp = {}
                temp['nutrientName'] = lk
                temp['nutrientAmount'] = round(retlist[i]['labelNutrients'][lk]['value'],2)
                temp['dv'] = round(retlist[i]['percentNutrients'][lk]['value'],2)
                templ.append(temp)
            retnut.append(templ)
        return {"result": retnut}



'''
This method searches for a food item in the API and returns its brand information, id, description, and ingredients.
The search should be a body posted to the method in the following format:
    {
        "main": {
            "fdcid": "2120395"
         }
    }
'''
@app.route('/getfoodinfo',methods=['POST'])
def get_food_info():
    if request.method == "POST":
        #Processes post body
        inp = request.get_json()

        #Constructs search string based off of API documentation
        params = {"query": inp['main']['fdcid'], "api_key": api_key}
        res = requests.get("https://api.nal.usda.gov/fdc/v1/foods/search",params=params).json()
        res = res["foods"] 
        
        #Filters out the fields we specifically want to return (id, description, ingredients, brand info)
        ret_keys = set(["fdcId", "description", "brandOwner", "brandName", "ingredients"])

        #Builds return format (list of dictionaries)
        for i in range(len(res)):
            temp = res[i]
            for k in ret_keys:
                if k not in temp:
                    temp[k] = ""
            res[i] = { k: temp[k] for k in ret_keys }
        return {"food": res}

'''
This method searches for a food item in the API using its id and returns its nutrient information
The search should be a body posted to the method in the following format:
    {
        "main": {
            "fdcid": "2120395"
         }
    }
'''
@app.route('/getnutrientinfo',methods=['POST'])
def get_nutrient_info():
    if request.method == "POST":
        #Processes post body
        inp = request.get_json()
        
        #Constructs search string based off of API documentation
        params = {"api_key": api_key}
        reso = requests.get("https://api.nal.usda.gov/fdc/v1/food/" + str(inp['main']['fdcid']),params=params).json()
        res = reso["foodNutrients"] 
        
        #Scale all nutrient info to 2000 calorie serving size
        factor = 1
        for i in range(len(res)):
            res[i] = res[i]["nutrient"]
            
            if res[i]["name"] == "Energy":
                if res[i]["unitName"] == "kcal":
                    factor = 2000/(float(res[i]["number"]) * 1000)
                    res[i]["unitName"] = "cal"
                    res[i]["number"] = str(float(res[i]["number"]) * 1000)
                elif res[i]["unitName"] == "cal":
                    factor = 2000/float(res[i]["number"])
        
        #Rounds amount to 3 decimal places
        for i in range(len(res)):
            res[i]["number"] = str(round(factor*float(res[i]["number"]),3))
        
        #Clean data
        for i in range(len(res)):
            
            #Standardize units to g (if they are in mg)
            if res[i]["unitName"] == "mg":
                res[i]["number"] = str(round(float(res[i]["number"])/1000,3))
                res[i]["unitName"] = "g"
            
            #Delete unwanted fields
            del res[i]["id"]
            del res[i]["rank"]
            
            #Calculate daily value info from excel table imported above
            if res[i]["name"] in dvdf.index:
                res[i]["dv"] = str(round(float(res[i]["number"])/float(dvdf.loc[res[i]["name"], "RDI"]) * 100,3))
            else:
                res[i]["dv"] = "NA" #Put "NA" if daily value info not in table
        
        return {"nutrients": res}

'''
This method searches for a food item in the API using its id and returns both its food and nutrient information.
This method is essentially a consolidated version of the above 2 methods.
The search should be a body posted to the method in the following format:
    {
        "main": {
            "fdcid": "2120395"
         }
    }
'''
@app.route('/getinfo',methods=['POST'])
def get_info():
    if request.method == "POST":
        #Processes post body
        inp = request.get_json()

        #Constructs search string based off of API documentation
        params = {"query": inp['main']['fdcid'], "api_key": api_key}
        res = requests.get("https://api.nal.usda.gov/fdc/v1/foods/search",params=params).json()
        res = res["foods"] 
        
        #Filters out the food info fields we specifically want to return (id, description, ingredients, brand info)
        ret_keys = set(["fdcId", "description", "brandOwner", "brandName", "ingredients"])
        
        #Filters out the nutrient info fields we specifically want to return (name, amount, daily value)
        nut_keys=set(["nutrientName","nutrientNumber","unitName","dv"])
        
        #Constructs nutrient appending format (list of list of of dictionaries)
        nut = []
        for j in range(len(res)):
            temp = res[j]
            fn = res[j]["foodNutrients"] #Inner list for nutrient info (list of dictionaries, each corresponding to a nutrient)
            
            #Normalizes nutrient info to 2000 calories serving size
            factor = 1
            for i in range(len(fn)):
                fn[i]["unitName"] = fn[i]["unitName"].lower()  #Standardizes all nutrient unit names in lower case
                
                if fn[i]["nutrientName"] == "Energy":
                    if fn[i]["unitName"].lower() == "kcal" :
                        factor = 2000/(float(fn[i]["nutrientNumber"]) * 1000)
                        fn[i]["unitName"] = "cal"
                        fn[i]["nutrientNumber"] = str(float(fn[i]["nutrientNumber"]) * 1000)
                    elif fn[i]["unitName"].lower() == "cal":
                        factor = 2000/float(fn[i]["nutrientNumber"])
            
            #Rounds nutrient amounts to 3 decimal places
            for i in range(len(fn)):
                fn[i]["nutrientNumber"] = str(round(factor*float(fn[i]["nutrientNumber"]),3))
            
            #Cleaning data
            for i in range(len(fn)):
                #Standardizes nutrient units (i.e. convert mg to g)
                if fn[i]["unitName"].lower() == "mg":
                    fn[i]["nutrientNumber"] = str(round(float(fn[i]["nutrientNumber"])/1000,3))
                    fn[i]["unitName"] = "g"
                
                #Adds nutrient daily value info if it exists in daily value excel sheet
                if fn[i]["nutrientName"] in dvdf.index:
                    fn[i]["dv"] = str(round(float(fn[i]["nutrientNumber"])/float(dvdf.loc[fn[i]["nutrientName"], "RDI"]) * 100,3))
                else:
                    fn[i]["dv"] = "NA" #If daily value info does not exist, adds "NA" for daily value
            
            #Uses nut_keys set to filter out unwanted fields from nutrient dictionary
            for i in range(len(fn)):
                for k in nut_keys:
                    if k not in fn[i]:
                        fn[i][k] = ""
                    fn[i] = { k: fn[i][k] for k in nut_keys }
            nut.append(fn)  #Adds inner list of nutrient info to outer list 
            
            #Uses ret_keys set to filter out unwanted fields from food dictionary
            for k in ret_keys:
                if k not in temp:
                    temp[k] = ""
            res[j] = { k: temp[k] for k in ret_keys }
        
        #Separately returns food info and nutrient info
        return {"food": res, "nutrient": nut}

if __name__ == '__main__':
    #serve(app, host='0.0.0.0', port=80)
    app.run()