
#!/usr/bin/env python3

###############################################################################
#                     LABORANALYSIS (analyzing service)                       #
#              This script runs by OS timer and analyze data.                 #
#           After, it stores report to the appropriate directory              #
#     If any exists, it starts data harvest and stores results to MongoDB     #
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
problem = 'Laboranalysis application ran into an issue'
success = 'Ваш отчёт готов!'

# This function tries to get an orders from MongoDB
def get_orders_from_mongo():
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'orders' collection of 'hh_reports' database
        collection = mongodb.hh_reports['orders']
        # Search for orders
        orders = list(collection.find({}))
        # Collections names in 'hh_vacancies' database
        vacancies = mongodb.hh_vacancies.list_collection_names()
        # Collections names in 'hh_resumes' database
        resumes = mongodb.hh_resumes.list_collection_names()

        if orders:
            for order in orders:
                if order.get('occupation') in vacancies and 'occupation' in order.keys():
                    # If it's vacancy order
                    start_vacancies_analyze(order)
                    # If it's resume order
                if order.get('criteria') in resumes and 'criteria' in order.keys():
                        start_resumes_analyze(order)

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
    