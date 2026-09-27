# ============================================================
# AUTOMATIC DATABASE SETUP — MySQL Version
# Smart CPUT Bus Tracker
# ============================================================

import mysql.connector
from mysql.connector import Error

# ---- MySQL connection settings ----
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Amyol2009!',           # ← PUT YOUR MySQL root PASSWORD HERE
    'database': 'bus_tracker'
}


def get_connection():
    """Return a MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def create_database_if_missing():
    """Create the bus_tracker database if it doesn't exist yet."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS bus_tracker "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database `bus_tracker` is ready.")
    except Error as e:
        print(f"❌ Could not create database: {e}")


def init_db():
    """Create all 9 tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS User (
            UserID INT AUTO_INCREMENT PRIMARY KEY,
            FullName VARCHAR(100) NOT NULL,
            Email VARCHAR(100) UNIQUE NOT NULL,
            Password VARCHAR(255) NOT NULL,
            PhoneNumber VARCHAR(15),
            Role VARCHAR(20) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Driver (
            DriverID INT AUTO_INCREMENT PRIMARY KEY,
            FullName VARCHAR(100) NOT NULL,
            PhoneNumber VARCHAR(15),
            UserID INT,
            FOREIGN KEY (UserID) REFERENCES User(UserID)
                ON DELETE SET NULL ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Admin (
            AdminID INT AUTO_INCREMENT PRIMARY KEY,
            FullName VARCHAR(100) NOT NULL,
            Email VARCHAR(100) UNIQUE NOT NULL,
            UserID INT,
            FOREIGN KEY (UserID) REFERENCES User(UserID)
                ON DELETE SET NULL ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Route (
            RouteID INT AUTO_INCREMENT PRIMARY KEY,
            RouteName VARCHAR(100) NOT NULL,
            StartLocation VARCHAR(100) NOT NULL,
            Destination VARCHAR(100) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Bus (
            BusID INT AUTO_INCREMENT PRIMARY KEY,
            BusNumber VARCHAR(20) NOT NULL,
            Capacity INT NOT NULL,
            CurrentLocation VARCHAR(150),
            ActiveStatus VARCHAR(20) DEFAULT 'Active',
            RouteID INT,
            DriverID INT,
            FOREIGN KEY (RouteID) REFERENCES Route(RouteID)
                ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (DriverID) REFERENCES Driver(DriverID)
                ON DELETE SET NULL ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Bus_Stop (
            StopID INT AUTO_INCREMENT PRIMARY KEY,
            StopName VARCHAR(100) NOT NULL,
            Location VARCHAR(150),
            RouteID INT,
            FOREIGN KEY (RouteID) REFERENCES Route(RouteID)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Schedule (
            ScheduleID INT AUTO_INCREMENT PRIMARY KEY,
            BusID INT,
            RouteID INT,
            DepartureTime TIME NOT NULL,
            ArrivalTime TIME NOT NULL,
            Date DATE NOT NULL,
            FOREIGN KEY (BusID) REFERENCES Bus(BusID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (RouteID) REFERENCES Route(RouteID)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Notification (
            NotificationID INT AUTO_INCREMENT PRIMARY KEY,
            UserID INT,
            Message VARCHAR(255) NOT NULL,
            DateSent DATETIME DEFAULT CURRENT_TIMESTAMP,
            Status VARCHAR(20) DEFAULT 'Unread',
            FOREIGN KEY (UserID) REFERENCES User(UserID)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Favourite_Stop (
            FavouriteID INT AUTO_INCREMENT PRIMARY KEY,
            UserID INT,
            StopID INT,
            DateAdded DATE,
            FOREIGN KEY (UserID) REFERENCES User(UserID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (StopID) REFERENCES Bus_Stop(StopID)
                ON DELETE CASCADE ON UPDATE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ All 9 tables created successfully.")


def seed_data():
    """Insert demo data on first run only."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM User")
    if cursor.fetchone()[0] > 0:
        print("ℹ️  Database already has data. Skipping seed.")
        cursor.close()
        conn.close()
        return

    # ---- USERS ----
    users = [
        ('John Smith',     'john@cput.ac.za',    'password123', '0824567890', 'Driver'),
        ('Sipho Nkosi',    'sipho@cput.ac.za',   'password123', '0831123344', 'Driver'),
        ('Aisha Patel',    'aisha@cput.ac.za',   'password123', '0819987766', 'Driver'),
        ('David van Wyk',  'david@cput.ac.za',   'password123', '0842235566', 'Driver'),
        ('Nomsa Khumalo',  'nomsa@cput.ac.za',   'password123', '0826678899', 'Driver'),
        ('Thabo Mokoena',  'thabo@cput.ac.za',   'password123', '0821112233', 'Admin'),
        ('Lerato Dlamini', 'lerato@cput.ac.za',  'password123', '0834445566', 'Admin'),
        ('Sarah Adams',    'sarah@cput.ac.za',   'password123', '0847778899', 'Student'),
        ('Michael Ndlovu', 'michael@cput.ac.za', 'password123', '0829990011', 'Student'),
        ('Zanele Mthembu', 'zanele@cput.ac.za',  'password123', '0815556677', 'Student'),
    ]
    cursor.executemany(
        "INSERT INTO User (FullName, Email, Password, PhoneNumber, Role) VALUES (%s, %s, %s, %s, %s)",
        users
    )

    # ---- DRIVERS ----
    cursor.executemany(
        "INSERT INTO Driver (FullName, PhoneNumber, UserID) VALUES (%s, %s, %s)",
        [
            ('John Smith', '0824567890', 1),
            ('Sipho Nkosi', '0831123344', 2),
            ('Aisha Patel', '0819987766', 3),
            ('David van Wyk', '0842235566', 4),
            ('Nomsa Khumalo', '0826678899', 5),
        ]
    )

    # ---- ADMINS ----
    cursor.executemany(
        "INSERT INTO Admin (FullName, Email, UserID) VALUES (%s, %s, %s)",
        [
            ('Thabo Mokoena', 'thabo@cput.ac.za', 6),
            ('Lerato Dlamini', 'lerato@cput.ac.za', 7),
        ]
    )

    # ---- ROUTES ----
    cursor.executemany(
        "INSERT INTO Route (RouteName, StartLocation, Destination) VALUES (%s, %s, %s)",
        [
            ('Bellville – Cape Town', 'Bellville Campus', 'Cape Town Campus'),
            ('Mowbray – Residence', 'Mowbray Campus', 'Student Residence'),
            ('Granger Bay – District 6', 'Granger Bay', 'District Six'),
            ('Residence – Bellville', 'Student Residence', 'Bellville Campus'),
            ('Mowbray – Granger Bay', 'Mowbray Campus', 'Granger Bay'),
        ]
    )

    # ---- BUSES ----
    cursor.executemany(
        "INSERT INTO Bus (BusNumber, Capacity, CurrentLocation, ActiveStatus, RouteID, DriverID) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        [
            ('CPT-001', 45, 'Near Bellville Campus', 'Active', 1, 1),
            ('CPT-002', 40, 'Mowbray Main Road', 'Active', 2, 2),
            ('CPT-003', 50, 'District Six', 'Delayed', 3, 3),
            ('CPT-004', 45, 'Student Residence', 'Active', 4, 4),
            ('CPT-005', 40, 'Granger Bay', 'Inactive', 5, 5),
        ]
    )

    # ---- BUS STOPS ----
    cursor.executemany(
        "INSERT INTO Bus_Stop (StopName, Location, RouteID) VALUES (%s, %s, %s)",
        [
            ('Bellville Campus Stop', 'Sacks Circle, Bellville', 1),
            ('Cape Town Campus Stop', 'Keizersgracht, Cape Town', 1),
            ('Mowbray Campus Stop', 'Main Road, Mowbray', 2),
            ('Student Residence Stop', 'Stanhope Road', 2),
            ('Granger Bay Stop', 'Beach Road, Granger Bay', 3),
            ('District Six Stop', 'Tennant Street, District Six', 3),
            ('Residence Stop', 'Stanhope Road', 4),
            ('Bellville Stop', 'Symphony Way, Bellville', 4),
            ('Mowbray Stop', 'Main Road, Mowbray', 5),
            ('Granger Bay Stop 2', 'Beach Road, Granger Bay', 5),
        ]
    )

    # ---- SCHEDULES ----
    cursor.executemany(
        "INSERT INTO Schedule (BusID, RouteID, DepartureTime, ArrivalTime, Date) "
        "VALUES (%s, %s, %s, %s, %s)",
        [
            (1, 1, '07:30:00', '08:15:00', '2026-08-18'),
            (2, 2, '08:00:00', '08:25:00', '2026-08-18'),
            (3, 3, '09:00:00', '09:30:00', '2026-08-18'),
            (1, 1, '12:00:00', '12:45:00', '2026-08-18'),
            (4, 4, '14:30:00', '15:10:00', '2026-08-18'),
            (2, 2, '16:00:00', '16:25:00', '2026-08-18'),
            (3, 3, '17:30:00', '18:00:00', '2026-08-18'),
        ]
    )

    # ---- NOTIFICATIONS ----
    cursor.executemany(
        "INSERT INTO Notification (UserID, Message, Status) VALUES (%s, %s, %s)",
        [
            (8, 'Bus CPT-001 is arriving at Bellville in 5 min', 'Unread'),
            (8, 'Route 2 is delayed by 10 minutes', 'Read'),
            (9, 'Your favourite stop has an update', 'Unread'),
            (9, 'Bus CPT-003 has departed District Six', 'Read'),
            (10, 'Schedule change: Afternoon bus cancelled', 'Unread'),
        ]
    )

    # ---- FAVOURITE STOPS ----
    cursor.executemany(
        "INSERT INTO Favourite_Stop (UserID, StopID, DateAdded) VALUES (%s, %s, %s)",
        [
            (8, 1, '2026-08-15'),
            (8, 3, '2026-08-15'),
            (9, 5, '2026-08-16'),
        ]
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Seed data inserted successfully.")


def setup_database():
    create_database_if_missing()
    init_db()
    seed_data()