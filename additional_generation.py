import mysql.connector
from mysql.connector import Error
import random
from faker import Faker
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connection settings
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DATABASE = os.getenv('DATABASE')

fake = Faker()

def create_connection():
    """Create a database connection"""
    try:
        connection = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        if connection.is_connected():
            print("Connection to MySQL DB successful")
        return connection
    except Error as e:
        print(f"The error '{e}' occurred")
        return None

def execute_query(connection, query, data=None):
    """Execute a single query"""
    cursor = connection.cursor()
    try:
        if data:
            cursor.execute(query, data)
        else:
            cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

def fetch_all_ids(connection, table, id_column):
    cursor = connection.cursor()
    cursor.execute(f"SELECT {id_column} FROM {table}")
    return [row[0] for row in cursor.fetchall()]

def truncate_string(input_string, max_length):
    return input_string[:max_length]

def generate_unique_values(count, value_set, generator_func):
    attempts = 0
    while len(value_set) < count and attempts < count * 20:
        try:
            value = generator_func()
            value_set.add(value)
        except faker.exceptions.UniquenessException:
            pass
        attempts += 1
    if len(value_set) < count:
        raise Exception("Could not generate enough unique values")
    return list(value_set)

def insert_missing_data():
    connection = create_connection()

    if connection is None:
        return

    customer_ids = fetch_all_ids(connection, 'customer', 'customerNo')
    booking_ids = fetch_all_ids(connection, 'booking', 'bookingNo')
    stop_ids = fetch_all_ids(connection, 'stop', 'stopNo')

    invoice_query = """
    INSERT INTO invoice (invoiceNo, issueDate, invoicingPeriod, amountCharged, paymentDueDate, paymentStatus, bookingNo)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    invoice_data = generate_unique_values(
        50000,
        set(),
        lambda: (
            fake.unique.random_int(min=1, max=1000000),
            fake.date_this_decade(),
            fake.date_this_decade(),
            round(random.uniform(100, 10000), 2),
            fake.date_this_decade(),
            random.choice(['paid', 'unpaid', 'pending']),
            random.choice(booking_ids)
        )
    )
    for data in invoice_data:
        execute_query(connection, invoice_query, data)

    trip_query = """
    INSERT INTO trip (tripNo, recurrence, numberOfPersons, isActivated, requestedBy)
    VALUES (%s, %s, %s, %s, %s)
    """
    trip_data = generate_unique_values(
        50000,
        set(),
        lambda: (
            fake.unique.random_int(min=1, max=1000000),
            random.choice(['one-off', 'daily', 'weekly', 'monthly', 'annually']),
            random.randint(1, 100),
            fake.boolean(),
            random.choice(customer_ids)
        )
    )
    for data in trip_data:
        execute_query(connection, trip_query, data)

    trip_ids = [trip[0] for trip in trip_data]

    trip_stop_query = """
    INSERT INTO trip_stop (tripNo, stopNo)
    VALUES (%s, %s)
    """
    trip_stop_data = generate_unique_values(
        50000,
        set(),
        lambda: (random.choice(trip_ids), random.choice(stop_ids))
    )
    for data in trip_stop_data:
        execute_query(connection, trip_stop_query, data)

    vehicle_category_query = """
    INSERT INTO vehicle_categories (vehicleCategory, staffNo)
    VALUES (%s, %s)
    """
    staff_ids = fetch_all_ids(connection, 'staff', 'staffNo')
    vehicle_category_data = generate_unique_values(
        50000,
        set(),
        lambda: (fake.word(), random.choice(staff_ids))
    )
    for data in vehicle_category_data:
        execute_query(connection, vehicle_category_query, data)

    connection.close()

if __name__ == "__main__":
    insert_missing_data()
