
#!/usr/bin/env python3

###############################################################################
#                   LABORANALYSIS (harvesting service)                        #
#     This script runs by OS timer and searches freshly ordered reports.      #
#    If any exists, it starts data harvest and stores results to MongoDB      #
#      Always sends email notification with results to application admin      #
###############################################################################
#  This is CONTAINER version, intended for deploying to DOCKER environment!   #
###############################################################################

# MongoDB connection stuff:
from pymongo import MongoClient
# Our send mail class:
from mailsender import MailSender
# Our credentials:
from credentials import mongo, mail_creds

# Email message subjects
problem = 'Harvest application ran into an issue'
success = 'Harvest application completes successfully'

# This function tries to get an orders from MongoDB
def get_orders_from_mongo():
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'orders' collection of 'hh_reports' database
        collection = mongodb.hh_reports['orders']
        # Search for orders
        orders = list(collection.find({}))
        if orders:
            for order in orders:
                # If it's vacancy order
                if 'occupation' in order.keys():
                    start_request(order)
                # If it's resume order
                else:
                    start_parse(order)

# This function makes vacancies retrievement process
def start_request(order):
    # Try to make processing on geted order
    try:
        # Import our vacancy processing class
        from vacancyhandler import VacancyHandler
        vacancies = VacancyHandler(order.get('occupation'))
        vacancies._vacancies_retriever(delay=10, number=None)
        vacancies.store_vacancies_to_mongo()
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

# This function makes resume retrievement process
def start_parse(order):
    # Try to make processing on geted order
    try:
        # Import our vacancy processing class
        from resumehandler import ResumeHandler
        resumes = ResumeHandler(order.get('criteria'))
        resumes._resumes_retriever(delay=30, number=None)
        resumes.store_resumes_to_mongo()
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
    # Start work
    get_orders_from_mongo()
    