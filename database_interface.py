from pymongo import MongoClient
from pprint import pprint
from collections.abc import Mapping

'''
@author: nathanielwang01
'''

class Search_Query(Mapping):
    '''
    Class representing a food search to be run.
    Simplifies queries.
    '''

    def __init__(self) -> None:
        self._query_dict = {}
    
    def __str__(self) -> str:
        return str(self._query_dict)
    
    def __getitem__(self, __k):
        return self._query_dict[__k]
    
    def __iter__(self) -> iter:
        return iter(self._query_dict)
    
    def __len__(self) -> int:
        return len(self._query_dict)
    
    def clear_query(self) -> None:
        self._query_dict = {}

    ##
    ## NOTE: Below are assorted methods to construct a search query for execute_search.
    ##

    def find_by_name(self, name: str) -> str:
        '''
        Adds a name search to the query.
        Returns the added query string.
        '''

        query_key = "description"
        query_value = {'$regex': name, '$options': 'i'}

        self._query_dict[query_key] = query_value

        return f'{query_key}: {query_value}'

    def find_by_fdcId(self, fdcId: int) -> str:
        '''
        Adds a search by FDC ID to the query.
        Returns the added query string.
        '''

        query_key = "fdcId"
        query_value = fdcId

        self._query_dict[query_key] = query_value

        return f'{query_key}: {query_value}'
    
    def find_by_upc(self, upc: str) -> str:
        '''
        Adds a search by UPC to the query.
        Returns the added query string.
        '''

        query_key = "gtinUpc"
        query_value = upc

        self._query_dict[query_key] = query_value

        return f'{query_key}: {query_value}'

    def find_by_category(self, category: str) -> str:
        '''
        Adds a search for items that contain @category in the food category field.
        Returns the added query string.
        '''

        query_key = "brandedFoodCategory"
        query_value = {'$regex': category, '$options': 'i'}

        self._query_dict[query_key] = query_value

        return f'{query_key}: {query_value}'
    
    def find_by_ingredients(self, ing_list: list) -> str:
        '''
        Adds a search for items that contain all of the specified ingredients.
        Returns the added query string.
        '''

        query_key = "ingredients"
        # Build string iteratively
        query_value = {'$options': 'i'}
        query_value['$regex'] = ''
        for item in ing_list:
            query_value['$regex'] += f'(?=.*{item})'

        self._query_dict[query_key] = query_value

        return f'{query_key}: {query_value}'
    
    def find_by_brand(self, brand: str) -> str:
        '''
        Adds a search for items that contain @category in the food category field.
        Returns the added query string.
        '''

        query_key = "brandOwner"
        query_value = {'$regex': brand, '$options': 'i'}

        self._query_dict[query_key] = query_value

        return f'{query_key}: {query_value}'

    def find_by_name_or_brand(self, entry: str) -> str:
        '''
        Adds a search for items that contain @entry in the food category field OR the brand name field.
        Returns the added query string.
        '''

        query_key = "$or"
        query_value = [{"description": {'$regex': entry, '$options': 'i'}},
            {"brandOwner": {'$regex': entry, '$options': 'i'}}]

        self._query_dict[query_key] = query_value
        
        return f'''$or:  [{{"description": {{'$regex': {entry}, '$options': 'i'}}}},
            {{"brandOwner": {{'$regex': {entry}, '$options': 'i'}}]'''
    
    def _by_nutper(self, nutrients: dict, by_nutrients: bool):
        '''
        Internal function to add a query for either certain nutritial numbers or percentages.
        '''

        queries = []

        for nut in nutrients:
            if nut not in Food_Database.nutrient_units:
                raise ValueError(f'"{nut}" not a valid nutrient.')
            
            if by_nutrients:
                nut_key = f'labelNutrients.{nut}.value'
            else:
                nut_key = f'percentNutrients.{nut}.value'

            if nutrients[nut][1]:
                nut_val = {'$gt': nutrients[nut][0]}
            else:
                nut_val = {'$lt': nutrients[nut][0]}
            
            queries.append((nut_key, nut_val))
            
        # Only modify the query dictionary IF no errors occur
        query_string = ''
        for entry in queries:
            self._query_dict[entry[0]] = entry[1]
            query_string += f'{entry[0]}: {entry[1]}, '

        return query_string

    def find_by_nutrients(self, nutrients: dict):
        '''
        Adds a search for items that meet nutritional specifications.
        @nutrients should be in the format {nutrient: (amount, greater_than)}.
        greater_than: whether or not to get all records that are greater than the value
        Valid nutrients are fat, saturatedFat, transFat, cholesterol, sodium, carbohydrates,
        fiber, sugars, protein, calcium, iron, potassium, and calories.
        '''
        
        return self._by_nutper(nutrients, True)

    def find_by_percentage(self, nutrients: dict):
        '''
        Adds a search for items that meet nutritional specifications.
        @nutrients should be in the format {nutrient: (% daily intake, greater_than)}.
        greater_than: whether or not to get all records that are greater than the value
        Valid nutrients are fat, saturatedFat, transFat, cholesterol, sodium, carbohydrates,
        fiber, sugars, protein, calcium, iron, potassium, and calories.

        Obviously, do not use if the collection does not include the percentNutrients field.
        '''

        return self._by_nutper(nutrients, False)


class Food_Database():
    '''
    Class representing the MongoDB Leaf Database
    '''

    nutrient_units = {'calories': 'kcal', 'fat': 'g', 'saturatedFat': 'g', 'transFat': 'g',
            'cholesterol': 'mg', 'sodium': 'mg', 'carbohydrates': 'g', 'fiber': 'g', 'sugars': 'g',
            'protein': 'g', 'calcium': 'mg', 'iron': 'mg', 'potassium': 'mg'}
    serving_units = ['g', 'ml']

    '''
    See: https://www.fda.gov/media/99059/download
    See: https://www.fda.gov/media/99069/download
    '''
    daily_values = {'calories': 2000, 'fat': 78, 'saturatedFat': 20, 'transFat': 1, 
            'cholesterol': 300, 'sodium': 2300, 'carbohydrates': 275, 'fiber': 28, 'sugars': 50,
            'protein': 50, 'calcium': 1300, 'iron': 18, 'potassium': 4700}
    
    standard_serving = 150

    def __init__(self, password_path: str, db_name: str, collection_name: str) -> None:

        self.db_name = db_name
        self.collection_name = collection_name

        # If no password_path is None, use default (local) connection settings
        if password_path == None:
            self.client = MongoClient()
        else:
            # Read password from plaintext for now, I guess
            with open(password_path) as pass_file:
                password = pass_file.read().strip()

            self.client = MongoClient(
                f"mongodb+srv://admin:{password}@leaf-proto.caysi.mongodb.net/{self.db_name}?retryWrites=true&w=majority")
        
        self.food_collection = self.client[db_name][collection_name]

        # Determine if collection has percentage data or not
        #self.perc_ok = False
        #temp = self.food_collection.find_one({})
        #if temp['percentNutrients']:
        #    self.perc_ok = True

    @staticmethod
    def normalize_daily_values(record):
        '''
        Converts the nutrition data of @record from g/mg/kcal to %s based on FDA recommended guidelines.
        Normalizes serving sizes to 200g or 200ml.
        '''
        
        # NOTE: Data already cleaned, so it should not include anything that would break this.

        conv_factor = Food_Database.standard_serving / record['servingSize']
        record['servingSize'] = Food_Database.standard_serving

        record['percentNutrients'] = {}

        # Ignore added sugars as they should be accounted for in "sugars" already
        drop_added_sugar = False
        for key in record['labelNutrients']:
            if key == 'addedSugar':
                drop_added_sugar = True
                continue

            norm_nut = record['labelNutrients'][key]['value'] * conv_factor
            record['labelNutrients'][key]['value'] = norm_nut

            perc_nut = norm_nut / Food_Database.daily_values[key] * 100
            # Dict for formatting consistency
            record['percentNutrients'][key] = {'value': perc_nut} 
        
        if drop_added_sugar:
            record['labelNutrients'].pop('addedSugar')

        return record
    
    def execute_search(self, search_query: Search_Query, limit=10):
        '''
        Executes the search passed into it.
        '''
    
        return self.food_collection.find(search_query, limit=limit)


# Example usage
if __name__ == '__main__':
    food_db = Food_Database('atlas_pass.txt', 'leaf', 'food_data')
    search_this = Search_Query()
    #print(search_this.find_by_fdcId(1108347))
    print(search_this.find_by_ingredients(['salmon', 'salt']))
    print(search_this.find_by_category('fish'))
    print(search_this.find_by_name('lox'))
    #print(search_this.find_by_nutrients({'calories': (250, True), 'cholesterol': (40, False)}))
    print(search_this.find_by_percentage({'calories': (10, True), 'cholesterol': (20, False)}))
    print()

    print(search_this)
    print()
    
    search = food_db.execute_search(search_this)
    for doc in search:
        pprint(doc)
        #pprint(Food_Database.normalize_daily_values(doc))
        #pprint(doc['labelNutrients']['calories']['value'])
    