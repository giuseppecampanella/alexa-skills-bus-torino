import os
import datetime
import psycopg2
import yaml

class Database:

    def close_db(self):
        self.conn.commit()
        self.conn.close()

    def __init__(self):
        self.db, self.user, self.hostname, self.password = self.config()
        self.conn = psycopg2.connect(dbname=self.db, password=self.password, user=self.user, host=self.hostname)

    def config(self):
        yaml_dir = './polls/postgres_interface/config.yaml'
        if os.path.isfile(yaml_dir):
            with open(yaml_dir, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, yaml.Loader)
            # ricavo dalle variabili di ambiente il valore salvato su /etc/bash.bashrc
            dbname = os.environ.get(cfg['dbname'])
            user = os.environ.get(cfg['username'])
            password = os.environ.get(cfg['password'])
            hostname = os.environ.get(cfg['hostname'])
            return (dbname, user, hostname, password)
        else:
            print('''
                You have to create a config file in yaml format
                with following fields:
                \tdbname:
                \tusername:
                \tpassword:
                \thostname:
                ''')
            exit()
            
    def save_bus_and_stop(self, bus, stop):
        response = False
        # Add query to save in the db and a True response if the query went ok
        return response
    
    def get_stop_from_bus(self, bus):
        stop = None
        # Add query to retrieve the stop number from the db
        return stop
