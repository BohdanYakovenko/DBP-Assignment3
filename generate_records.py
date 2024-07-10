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

def random_date(start, end):
    return start + timedelta(days=random.randint(0, int((end - start).days)))

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

def insert_data():
    connection = create_connection()

    if connection is None:
        return

    customer_query = """
    INSERT INTO Customer (customerNo, houseNo, street, city, postcode, country, phoneNo, email, firstName, lastName, dateBirth, gender)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    customer_data = generate_unique_values(
        1000,
        set(),
        lambda: (fake.unique.random_int(min=1, max=100000), fake.building_number(), fake.street_name(), fake.city(), fake.postcode(), fake.country(), truncate_string(fake.phone_number(), 15), fake.email(), fake.first_name(), fake.last_name(), fake.date_of_birth(), random.choice(['M', 'F', 'Other']))
    )
    for data in customer_data:
        execute_query(connection, customer_query, data)

    staff_query = """
    INSERT INTO Staff (staffNo, firstName, lastName, houseNo, street, city, postcode, privatePhoneNo, email, dateBirth, gender, position, startDateWork, endDateWork, salary, employmentStatus)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    staff_data = generate_unique_values(
        200,
        set(),
        lambda: (fake.unique.random_int(min=1, max=100000), fake.first_name(), fake.last_name(), fake.building_number(), fake.street_name(), fake.city(), fake.postcode(), truncate_string(fake.phone_number(), 15), fake.email(), fake.date_of_birth(), random.choice(['M', 'F', 'Other']), truncate_string(fake.job(), 20), fake.date_this_decade(), fake.date_this_decade(), round(random.uniform(30000, 100000), 2), random.choice(['active', 'inactive']))
    )
    for data in staff_data:
        execute_query(connection, staff_query, data)

    staff_ids = [staff[0] for staff in staff_data]

    driver_query = """
    INSERT INTO Driver (staffNo, licenceNo)
    VALUES (%s, %s)
    """
    driver_data = generate_unique_values(
        100,
        set(),
        lambda: (random.choice(staff_ids), fake.unique.random_int(min=1, max=100000))
    )
    for data in driver_data:
        execute_query(connection, driver_query, data)

    depot_query = """
    INSERT INTO Depot (depotNo, houseNo, street, city, postcode, phoneNo, parkingAreaSize, overseenBy)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    depot_data = generate_unique_values(
        50,
        set(),
        lambda: (fake.unique.random_int(min=1, max=100000), fake.building_number(), fake.street_name(), fake.city(), fake.postcode(), truncate_string(fake.phone_number(), 15), round(random.uniform(500, 2000), 2), random.choice(staff_ids))
    )
    for data in depot_data:
        execute_query(connection, depot_query, data)

    depot_ids = [depot[0] for depot in depot_data]

    vehicle_query = """
    INSERT INTO Vehicle (vehicleNo, registrationNo, brand, model, category, yearManufacture, passengerSeatsCapacity, bootSizeInLitres, mileage, nextMaintenanceDate, stationedAt)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    vehicle_data = generate_unique_values(
        200,
        set(),
        lambda: (fake.unique.random_int(min=1, max=100000), fake.unique.random_int(min=1, max=100000), fake.company(), fake.word(), fake.word(), fake.year(), random.randint(2, 60), round(random.uniform(100, 1000), 2), round(random.uniform(10000, 200000), 2), fake.date_between(start_date='-2y', end_date='today'), random.choice(depot_ids))
    )
    for data in vehicle_data:
        execute_query(connection, vehicle_query, data)

    route_query = """
    INSERT INTO Route (routeNo, startDepot, endDepot, plannedStartDate, plannedStartTime, plannedEndDate, plannedEndTime, actualStartDate, actualStartTime, actualEndDate, actualEndTime, currentStatus)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    route_data = generate_unique_values(
        50000,
        set(),
        lambda: (fake.unique.random_int(min=1, max=1000000), random.choice(depot_ids), random.choice(depot_ids), fake.date_this_decade(), fake.time(), fake.date_this_decade(), fake.time(), fake.date_this_decade(), fake.time(), fake.date_this_decade(), fake.time(), random.choice(['not started', 'in progress', 'completed', 'interrupted']))
    )
    for data in route_data:
        execute_query(connection, route_query, data)

    route_ids = [route[0] for route in route_data]

    stop_query = """
    INSERT INTO Stop (stopNo, runningNo, locationData, plannedStopDate, plannedStopTime, duration, stopType, runningNoWithinRoute, actualStopDate, actualStopTime, routeNo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    stop_data = generate_unique_values(
        100000,
        set(),
        lambda: (fake.unique.random_int(min=1, max=1000000), fake.unique.random_int(min=1, max=1000000), fake.address(), fake.date_this_decade(), fake.time(), random.randint(5, 120), random.choice(['pick-up', 'drop-off', 'both', 'break', 'technical']), fake.unique.random_int(min=1, max=1000000), fake.date_this_decade(), fake.time(), random.choice(route_ids))
    )
    for data in stop_data:
        execute_query(connection, stop_query, data)

    booking_query = """
    INSERT INTO Booking (bookingNo, bookingDate, bookedBy)
    VALUES (%s, %s, %s)
    """
    booking_data = generate_unique_values(
        50000,
        set(),
        lambda: (fake.unique.random_int(min=1, max=1000000), fake.date_this_decade(), random.choice(customer_data)[0])
    )
    for data in booking_data:
        execute_query(connection, booking_query, data)

    booking_ids = [booking[0] for booking in booking_data]

    trip_query = """
    INSERT INTO Trip (tripNo, recurrence, numberOfPersons, isActivated, requestedBy)
    VALUES (%s, %s, %s, %s, %s)
    """
    trip_data = generate_unique_values(
        50000,
        set(),
        lambda: (fake.unique.random_int(min=1, max=1000000), random.choice(['daily', 'weekly', 'monthly', 'yearly', 'one-time']), random.randint(1, 100), random.choice(['yes', 'no']), random.choice(customer_data)[0])
    )
    for data in trip_data:
        execute_query(connection, trip_query, data)

    invoice_query = """
    INSERT INTO Invoice (invoiceNo, invoiceDate, amount, relatedBooking)
    VALUES (%s, %s, %s, %s)
    """
    invoice_data = generate_unique_values(
        50000,
        set(),
        lambda: (fake.unique.random_int(min=1, max=1000000), fake.date_this_decade(), round(random.uniform(100, 10000), 2), random.choice(booking_ids))
    )
    for data in invoice_data:
        execute_query(connection, invoice_query, data)

    trip_stop_query = """
    INSERT INTO Trip_Stop (tripNo, stopNo)
    VALUES (%s, %s)
    """
    trip_stop_data = generate_unique_values(
        50000,
        set(),
        lambda: (random.choice(trip_data)[0], random.choice(stop_data)[0])
    )
    for data in trip_stop_data:
        execute_query(connection, trip_stop_query, data)

    driver_vehicle_route_query = """
    INSERT INTO Driver_Vehicle_Route (driver, vehicle, route)
    VALUES (%s, %s, %s)
    """
    driver_vehicle_route_data = generate_unique_values(
        50000,
        set(),
        lambda: (random.choice(driver_data)[0], random.choice(vehicle_data)[0], random.choice(route_data)[0])
    )
    for data in driver_vehicle_route_data:
        execute_query(connection, driver_vehicle_route_query, data)

    connection.close()

if __name__ == "__main__":
    insert_data()
