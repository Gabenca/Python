
#!/usr/bin/env python3

###############################################################################
#                   LABORANALYSIS (notifying service)                         #
#    This script runs by OS timer and searches freshly completed reports.     #
#        If any exists, it sends email notification with results to           #
#    application admin and a customer. Finally, it closes the order issue     #
#                        by change order data status.                         #
###############################################################################
#  This is CONTAINER version, intended for deploying to DOCKER environment!   #
###############################################################################

# Directory walking stuff for xlsx reports listing:
import os
# MongoDB connection stuff:
from pymongo import MongoClient
# Our send mail class:
from mailsender import MailSender
# Our credentials:
from credentials import mongo, mail_creds, store_path

# Email message subjects
problem = 'Laboranalysis application ran into an issue'
success = 'Ваш отчёт готов!'

# This function forms list of xlsx report files from 'store_path' dir.
def get_reports_list(report_type):
    path = os.path.join(store_path, report_type)
    reports = [report.split('.')[0] 
        for report in os.listdir(path) 
            if os.path.isfile(os.path.join(path, report))]
    return reports

# This function changes an order status from staging to complete,
# by moving an order document from 'orders' collection to 'complete' collection
def change_order_status(order):
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'complete' collection of 'hh_reports' database
        collection = mongodb.hh_reports['complete']
        # Put completed order
        collection.insert_one(order)
        # Connection to 'orders' collection of 'hh_reports' database
        collection = mongodb.hh_reports['orders']
        # Drop completed order
        collection.delete_one(order)

# This function tries to get an orders from MongoDB
def get_orders_from_mongo():
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'orders' collection of 'hh_reports' database
        collection = mongodb.hh_reports['orders']
        # Search for orders
        orders = list(collection.find({}))
        # Collections names in 'hh_vacancies' database
        vacancies = get_reports_list('vacancies')
        # Collections names in 'hh_resumes' database
        resumes = get_reports_list('resumes')

        if orders:
            for order in orders:
                # If it's vacancy order
                if order.get('occupation') in vacancies and 'occupation' in order.keys():
                    # If completes successfully,
                    # notificates application admin and order customer
                    order_customer = order.get('customer')
                    mail = MailSender( [mail_creds['admin'], order_customer],
                                        success, 
                                        order.get('occupation') )
                    mail.send_email()
                    change_order_status(order)

                # If it's resume order
                if order.get('criteria') in resumes and 'criteria' in order.keys():
                    # If completes successfully,
                    # notificates application admin and order customer
                    order_customer = order.get('customer')
                    mail = MailSender( [mail_creds['admin'], order_customer],
                                        success, 
                                        order.get('criteria') )
                    mail.send_email()
                    change_order_status(order)


# Checks importing issue
if __name__ == "__main__":
    # Start work
    get_orders_from_mongo()
