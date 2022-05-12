from database_interface import Food_Database

'''
@author: nathanielwang01
'''

def normalize_fdb(source_db, source_col, target_db, target_col, source_pass=None, target_pass=None):
    '''
    Create a copy of a food collection that is normalized and with percentages.
    '''
    source_db = Food_Database(source_pass, source_db, source_col)
    target_db = Food_Database(target_pass, target_db, target_col)

    everything = source_db.execute_search({})
    for doc in everything:
        if doc['servingSize'] == 0:
            pass
        norm_doc = Food_Database.normalize_daily_values(doc)
        target_db.food_collection.insert_one(norm_doc)

if __name__ == '__main__':
    normalize_fdb('leaf', 'food_data', 'leaf', 'food_data_norm')
