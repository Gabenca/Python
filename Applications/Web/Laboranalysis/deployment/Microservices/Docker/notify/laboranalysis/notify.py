
#!/usr/bin/env python3

###############################################################################
#                   LABORANALYSIS (notifying service)                         #
#               This script searches freshly completed reports.               #
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
# Application delay to become idle
from time import sleep
# Our credentials:
from credentials import mongo, mail_creds, store_path

# Email message subjects
problem = 'Notify application ran into an issue'
success = 'Заказанный вами отчёт готов!'

# This function forms list of xlsx report files from 'store_path' directory.
def get_reports_list(report_type):
    # Forms path to directory with xlsx reports
    path = os.path.join(store_path, report_type)
    # Forms list of available reports from xlsx files located in the directory
    reports = [report.split('.')[0] 
        for report in os.listdir(path) 
            if os.path.isfile(os.path.join(path, report))]
    return reports

# This function changes an notify order status from staging to complete,
# by moving an order document from 'notify' collection to 'complete' collection
def change_order_status(order):
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'complete' collection of 'hh_orders' database
        collection = mongodb.hh_orders['complete']
        # Put completed order
        collection.insert_one(order)
        # Connection to 'notify' collection of 'hh_orders' database
        collection = mongodb.hh_orders['notify']
        # Drop completed order
        collection.delete_one(order)

# This function tries to get an orders from MongoDB,
# and notifies application admin and customer if any exists.
def get_orders_from_mongo():
    # Instantiate MongoDB connection context
    with MongoClient(mongo) as mongodb:
        # Connection to 'notify' collection of 'hh_orders' database
        collection = mongodb.hh_orders['notify']
        # Search for orders
        orders = list(collection.find({}))
        # Lists content of vacancies directory
        vacancies = get_reports_list('vacancies')
        # Lists content of resumes directory
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
    # Endless loop
    while True:
        # Buffer start interval
        sleep(10)
        # Checks for new orders
        get_orders_from_mongo()
        # Go to bed for 1 hour
        sleep(3600)
