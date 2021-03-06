import sqlite3
import pickle
import itertools
import psi4
import configparser
import sys
from database import Database
import calculator

def fill_database(settings, database_name, directory = "unused"): # argument is unused, but I haven't removed yet because it will break a lot of code
    """
    Walks through a database and calculates all missing energies
    
    settings is the .ini file to use to fill this database

    database_name is file the database is stored in

    directory is unued. # should probably be removed.

    """
    # add .db to the database name if it doesn't already end in .db
    if database_name[-3:] != ".db":
        print("Database name \"{}\" does not end in database suffix \".db\". Automatically adding \".db\" to end of database name.".format(database_name))
        database_name += ".db"

    database = Database(database_name) 

    print("Filling database {}".format(database_name))

    # parse settings file
    config = configparser.SafeConfigParser(allow_no_value=False)
    config.read(settings)
    # set defaults
    config['DEFAULT'] = {}
    config['DEFAULT']['num_threads'] = '1'

    counter = 0
    
    for calculation in database.missing_energies():

        counter += 1
        print_progress(counter)

        try:
            # calculate the missing energy
            energy = calculator.calculate_energy(calculation.molecule, calculation.fragments, calculation.method + "/" + calculation.basis, calculation.cp, config)
            # update the energy in the database
            database.set_energy(calculation.job_id, energy, "some/log/path")
        except RuntimeError:
            database.set_failed(calculation.job_id, "failed", "some/log/path")

        # commit changes to database
        database.save()

    #close database
    database.close()

    print("\nFilling of database {} successful".format(database_name))

def print_progress(counter):
    s = "{:6d}".format(counter)
    if counter % 10 == 0:
       s += "\n" 
    print(s, end="", flush=True)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Incorrect number of arguments");
        print("Usage: python database_filler.py <settings_file> <database_name> <directory>")
        exit(1)
    fill_database(sys.argv[1], sys.argv[2], sys.argv[3])
