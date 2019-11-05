
#!/usr/bin/python3.7

# Our MongoDB connection class:
from laboranalysis.mongocon import MongoConnection

# This function tries to get an orders from MongoDB
def get_orders_from_mongo():
    # MongoDB connection object    
    client = MongoConnection()
    # Use our connection object with context manager to handle connection
    with client:
        # Connection to 'orders' collection of 'hh_reports' database
        collection = client.connection.hh_reports['orders']
        # Search for orders
        orders = [order for order in (collection.find({}))]
        if orders:
            for order in orders:
                if 'occupation' in order.keys():
                    # If it's vacancy order
                    start_request(order)
                else:
                    # If it's resume order
                    start_parse(order)

# This function makes vacancies retrievement and analyze process
def start_request(order):
    try:
        from laboranalysis.vacancyhandler import VacancyHandler
        v = VacancyHandler(order.get('occupation'))
        v.analyze()
        v.store_vacancies_to_mongo()
        v.store_results_to_xlsx()
        change_order_status(order)
    except:
        pass

# This function makes resume retrievement and analyze process
def start_parse(order):
    try:
        from laboranalysis.resumehandler import ResumeHandler
        r = ResumeHandler(order.get('criteria'))
        r.analyze()
        r.store_resumes_to_mongo()
        r.store_results_to_xlsx()
        change_order_status(order)
    except:
        pass

# This function moves order document from 'orders' collection to 'complete' collection
def change_order_status(order):
    # MongoDB connection object    
    client = MongoConnection()
    # Use our connection object with context manager to handle connection
    with client:
        # Connection to 'complete' collection of 'hh_reports' database
        collection = client.connection.hh_reports['complete']
        # Put completed order
        collection.insert_one(order)
    # Use our connection object with context manager to handle connection
    with client:
        # Connection to 'orders' collection of 'hh_reports' database
        collection = client.connection.hh_reports['orders']
        # Drop completed order
        collection.delete_one(order)

# Checks importing issue
if __name__ == "__main__":
    # Start work
    get_orders_from_mongo()
    