
#!/usr/bin/env python3

###############################################################################
#                     LABORANALYSIS (analyzing service)                       #
#                This script searches freshly ordered reports.                #
#                    If any exists, it starts data analysis.                  #
#                  and stores results to apropriate directory.                #
# Then, moves completed order to another collection for next service staging. #
#      Always sends email notification with results to application admin.     #
###############################################################################
#  This is CONTAINER version, intended for deploying to DOCKER environment!   #
###############################################################################

# MongoDB connection stuff:
from pymongo import MongoClient
# Our send mail class:
from mailsender import MailSender
# Application delay to become idle
from time import sleep
# Our credentials:
from credentials import mongo, mail_creds

# Email message subjects
problem = 'Analyze application ran into an issue'
success = 'Analyze application completes successfully'

# This function tries to get an orders from MongoDB,
# and starts data analysis process if any exists.
def get_orders_from_mongo():
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'analyze' collection of 'hh_orders' database
        collection = mongodb.hh_orders['analyze']
        # Search for orders
        orders = list(collection.find({}))
        # If any exists
        if orders:
            for order in orders:
                if 'occupation' in order.keys():
                    # If it's vacancy order
                    start_vacancies_analyze(order)
                    # If it's resume order
                if 'criteria' in order.keys():
                        start_resumes_analyze(order)

# This function changes an analyze order status from staging to complete,
# by moving an order document from 'analyze' collection to 'notify' collection
def change_order_status(order):
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'notify' collection of 'hh_orders' database
        collection = mongodb.hh_orders['notify']
        # Put completed order
        collection.insert_one(order)
        # Connection to 'analyze' collection of 'hh_orders' database
        collection = mongodb.hh_orders['analyze']
        # Drop completed order
        collection.delete_one(order)  

# This function makes vacancies analyze process
def start_vacancies_analyze(order):
    # Try to make processing on geted order
    try:
        # Import our vacancy processing class
        from vacancyhandler import VacancyHandler
        vacancies = VacancyHandler(order.get('occupation'))
        vacancies.restore_vacancies_from_mongo()
        vacancies.analyze()
        vacancies.store_results_to_xlsx()
        change_order_status(order)
    # If run into an issue, notificates application admin
    except:
        mail = MailSender( [mail_creds['admin']], 
                            problem,
                            str(order) )
        mail.send_email()
    # If completes successfully, notificates application admin
    mail = MailSender( [mail_creds['admin']],
                        success, 
                        order.get('occupation') )
    mail.send_email()

# This function makes resume analyze process
def start_resumes_analyze(order):
    # Try to make processing on geted order
    try:
        # Import our vacancy processing class
        from resumehandler import ResumeHandler
        resumes = ResumeHandler(order.get('criteria'))
        resumes.restore_resumes_from_mongo()
        resumes.analyze()
        resumes.store_results_to_xlsx()
        change_order_status(order)
    # If run into an issue, notificates application admin
    except:
        mail = MailSender( [mail_creds['admin']], 
                            problem, 
                            str(order) )
        mail.send_email()        
    # If completes successfully, notificates application admin
    mail = MailSender( [mail_creds['admin']],
                        success, 
                        order.get('criteria') )
    mail.send_email()


# Checks importing issue
if __name__ == "__main__":
    # Endless loop
    while True:
        # Buffer start interval
        sleep(10)
        # Checks for new orders
        get_orders_from_mongo()
        # Go to bed for 1 hour
        sleep(3600)
    