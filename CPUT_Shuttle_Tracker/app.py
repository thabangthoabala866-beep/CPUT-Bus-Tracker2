# ============================================================
# FLASK APPLICATION — MySQL Version
# Smart CPUT Bus Tracker
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from database import get_connection, setup_database

app = Flask(__name__)
app.secret_key = 'cput-bus-tracker-secret-2026'

setup_database()


def query(sql, params=None, fetch='all'):
    """Run a MySQL query and return results."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    if fetch == 'all':
        rows = cursor.fetchall()
    elif fetch == 'one':
        rows = cursor.fetchone()
    else:
        conn.commit()
        rows = cursor.lastrowid
    cursor.close()
    conn.close()
    return rows


# ============================================================
# AUTHENTICATION
# ============================================================

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        user = query(
            "SELECT * FROM User WHERE Email = %s AND Role = %s",
            (email, role), fetch='one'
        )

        if user and user['Password'] == password:
            session['user_id'] = user['UserID']
            session['user_name'] = user['FullName']
            session['user_role'] = user['Role']
            session['user_email'] = user['Email']

            if role == 'Student':
                return redirect(url_for('dashboard'))
            elif role == 'Driver':
                return redirect(url_for('driver_dashboard'))
            elif role == 'Admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email, password, or role.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm = request.form.get('confirmPassword')
        role = request.form.get('role')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        try:
            user_id = query(
                "INSERT INTO User (FullName, Email, Password, PhoneNumber, Role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (full_name, email, password, phone, role),
                fetch='insert'
            )

            if role == 'Driver':
                query(
                    "INSERT INTO Driver (FullName, PhoneNumber, UserID) VALUES (%s, %s, %s)",
                    (full_name, phone, user_id), fetch='insert'
                )
            elif role == 'Admin':
                query(
                    "INSERT INTO Admin (FullName, Email, UserID) VALUES (%s, %s, %s)",
                    (full_name, email, user_id), fetch='insert'
                )

            flash('Account created. Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Registration failed: {e}', 'danger')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================================
# STUDENT PAGES
# ============================================================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    active_buses = query(
        "SELECT COUNT(*) AS c FROM Bus WHERE ActiveStatus='Active'", fetch='one'
    )['c']
    delayed = query(
        "SELECT COUNT(*) AS c FROM Bus WHERE ActiveStatus='Delayed'", fetch='one'
    )['c']
    fav_count = query(
        "SELECT COUNT(*) AS c FROM Favourite_Stop WHERE UserID=%s",
        (session['user_id'],), fetch='one'
    )['c']

    stats = {
        'active_buses': active_buses,
        'on_time': active_buses,
        'delayed': delayed,
        'favourites': fav_count,
    }
    return render_template('dashboard.html', user=session, stats=stats)


@app.route('/routes')
def routes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rows = query("SELECT * FROM Route")
    return render_template('routes.html', routes=rows, user=session)


@app.route('/schedule')
def schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rows = query("""
        SELECT s.ScheduleID, b.BusNumber, r.RouteName,
               s.DepartureTime, s.ArrivalTime, s.Date
        FROM Schedule s
        JOIN Bus b ON s.BusID = b.BusID
        JOIN Route r ON s.RouteID = r.RouteID
        ORDER BY s.Date, s.DepartureTime
    """)
    return render_template('schedule.html', schedules=rows, user=session)


@app.route('/favourites')
def favourites():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rows = query("""
        SELECT f.FavouriteID, s.StopName, s.Location, f.DateAdded
        FROM Favourite_Stop f
        JOIN Bus_Stop s ON f.StopID = s.StopID
        WHERE f.UserID = %s
    """, (session['user_id'],))
    return render_template('favourites.html', favourites=rows, user=session)


@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    rows = query(
        "SELECT * FROM Notification WHERE UserID = %s ORDER BY DateSent DESC",
        (session['user_id'],)
    )
    return render_template('notifications.html', notifications=rows, user=session)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    results = []
    if request.method == 'POST':
        stype = request.form.get('searchType')
        kw = f"%{request.form.get('keyword', '').lower()}%"
        if stype == 'route':
            results = query(
                "SELECT * FROM Route WHERE LOWER(RouteName) LIKE %s "
                "OR LOWER(StartLocation) LIKE %s OR LOWER(Destination) LIKE %s",
                (kw, kw, kw)
            )
        elif stype == 'bus':
            results = query(
                "SELECT * FROM Bus WHERE LOWER(BusNumber) LIKE %s", (kw,)
            )
        elif stype == 'stop':
            results = query(
                "SELECT * FROM Bus_Stop WHERE LOWER(StopName) LIKE %s "
                "OR LOWER(Location) LIKE %s",
                (kw, kw)
            )
    return render_template('search.html', results=results, user=session)


@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    stats = {
        'total_routes': query("SELECT COUNT(*) AS c FROM Route", fetch='one')['c'],
        'active_buses': query("SELECT COUNT(*) AS c FROM Bus WHERE ActiveStatus='Active'", fetch='one')['c'],
        'total_drivers': query("SELECT COUNT(*) AS c FROM Driver", fetch='one')['c'],
        'unread_notifications': query("SELECT COUNT(*) AS c FROM Notification WHERE Status='Unread'", fetch='one')['c'],
    }
    return render_template('report.html', stats=stats, user=session)


# ============================================================
# ADMIN PAGES
# ============================================================

@app.route('/admin-dashboard')
def admin_dashboard():
    if session.get('user_role') != 'Admin':
        return redirect(url_for('login'))
    stats = {
        'total_routes': query("SELECT COUNT(*) AS c FROM Route", fetch='one')['c'],
        'active_buses': query("SELECT COUNT(*) AS c FROM Bus WHERE ActiveStatus='Active'", fetch='one')['c'],
        'total_drivers': query("SELECT COUNT(*) AS c FROM Driver", fetch='one')['c'],
        'total_notifications': query("SELECT COUNT(*) AS c FROM Notification WHERE Status='Unread'", fetch='one')['c'],
    }
    buses = query("""
        SELECT b.BusNumber, r.RouteName, d.FullName AS DriverName,
               b.ActiveStatus, b.CurrentLocation
        FROM Bus b
        LEFT JOIN Route r ON b.RouteID = r.RouteID
        LEFT JOIN Driver d ON b.DriverID = d.DriverID
    """)
    return render_template('admin-dashboard.html', stats=stats, buses=buses, user=session)


@app.route('/manage-routes')
def manage_routes():
    if session.get('user_role') != 'Admin':
        return redirect(url_for('login'))
    rows = query("SELECT * FROM Route")
    return render_template('manage-routes.html', routes=rows, user=session)


@app.route('/manage-buses')
def manage_buses():
    if session.get('user_role') != 'Admin':
        return redirect(url_for('login'))
    rows = query("""
        SELECT b.*, r.RouteName, d.FullName AS DriverName
        FROM Bus b
        LEFT JOIN Route r ON b.RouteID = r.RouteID
        LEFT JOIN Driver d ON b.DriverID = d.DriverID
    """)
    return render_template('manage-buses.html', buses=rows, user=session)


@app.route('/manage-drivers')
def manage_drivers():
    if session.get('user_role') != 'Admin':
        return redirect(url_for('login'))
    rows = query("""
        SELECT d.DriverID, d.FullName, d.PhoneNumber, b.BusNumber
        FROM Driver d
        LEFT JOIN Bus b ON d.DriverID = b.DriverID
    """)
    return render_template('manage-drivers.html', drivers=rows, user=session)


@app.route('/admin-schedules')
def admin_schedules():
    if session.get('user_role') != 'Admin':
        return redirect(url_for('login'))
    rows = query("""
        SELECT s.ScheduleID, b.BusNumber, r.RouteName,
               s.DepartureTime, s.ArrivalTime, s.Date
        FROM Schedule s
        JOIN Bus b ON s.BusID = b.BusID
        JOIN Route r ON s.RouteID = r.RouteID
        ORDER BY s.Date, s.DepartureTime
    """)
    return render_template('admin-schedules.html', schedules=rows, user=session)


@app.route('/admin-notifications')
def admin_notifications():
    if session.get('user_role') != 'Admin':
        return redirect(url_for('login'))
    rows = query("""
        SELECT n.NotificationID, n.Message, n.Status, n.DateSent, u.FullName
        FROM Notification n
        JOIN User u ON n.UserID = u.UserID
        ORDER BY n.DateSent DESC
    """)
    return render_template('admin-notifications.html', notifications=rows, user=session)


# ============================================================
# DRIVER PAGES
# ============================================================

@app.route('/driver-dashboard')
def driver_dashboard():
    if session.get('user_role') != 'Driver':
        return redirect(url_for('login'))
    bus_info = query("""
        SELECT b.BusNumber, b.Capacity, r.RouteName
        FROM Driver d
        LEFT JOIN Bus b ON d.DriverID = b.DriverID
        LEFT JOIN Route r ON b.RouteID = r.RouteID
        WHERE d.UserID = %s
    """, (session['user_id'],), fetch='one')
    return render_template('driver-dashboard.html', bus=bus_info, user=session)


@app.route('/driver-route')
def driver_route():
    if session.get('user_role') != 'Driver':
        return redirect(url_for('login'))
    route_info = query("""
        SELECT b.BusNumber, r.RouteName, r.StartLocation, r.Destination, b.ActiveStatus
        FROM Driver d
        LEFT JOIN Bus b ON d.DriverID = b.DriverID
        LEFT JOIN Route r ON b.RouteID = r.RouteID
        WHERE d.UserID = %s
    """, (session['user_id'],), fetch='one')
    return render_template('driver-route.html', route=route_info, user=session)


@app.route('/driver-passengers')
def driver_passengers():
    if session.get('user_role') != 'Driver':
        return redirect(url_for('login'))
    return render_template('driver-passengers.html', user=session)


@app.route('/driver-notifications')
def driver_notifications():
    if session.get('user_role') != 'Driver':
        return redirect(url_for('login'))
    rows = query(
        "SELECT * FROM Notification WHERE UserID = %s ORDER BY DateSent DESC",
        (session['user_id'],)
    )
    return render_template('driver-notifications.html', notifications=rows, user=session)


# ============================================================
# JSON API
# ============================================================

@app.route('/api/buses')
def api_buses():
    rows = query("""
        SELECT b.BusID, b.BusNumber, b.Capacity, b.CurrentLocation,
               b.ActiveStatus, r.RouteName, d.FullName AS DriverName
        FROM Bus b
        LEFT JOIN Route r ON b.RouteID = r.RouteID
        LEFT JOIN Driver d ON b.DriverID = d.DriverID
    """)
    return jsonify(rows)


@app.route('/api/bus/<int:bid>')
def api_bus_detail(bid):
    row = query("""
        SELECT b.*, r.RouteName, r.StartLocation, r.Destination,
               d.FullName AS DriverName
        FROM Bus b
        LEFT JOIN Route r ON b.RouteID = r.RouteID
        LEFT JOIN Driver d ON b.DriverID = d.DriverID
        WHERE b.BusID = %s
    """, (bid,), fetch='one')
    if row:
        return jsonify(row)
    return jsonify({'error': 'Bus not found'}), 404


@app.route('/api/routes')
def api_routes():
    return jsonify(query("SELECT * FROM Route"))


@app.route('/api/schedules')
def api_schedules():
    rows = query("""
        SELECT s.ScheduleID, b.BusNumber, r.RouteName,
               s.DepartureTime, s.ArrivalTime, s.Date
        FROM Schedule s
        JOIN Bus b ON s.BusID = b.BusID
        JOIN Route r ON s.RouteID = r.RouteID
        ORDER BY s.Date, s.DepartureTime
    """)
    return jsonify(rows)


@app.route('/api/stops/<int:rid>')
def api_stops(rid):
    return jsonify(query("SELECT * FROM Bus_Stop WHERE RouteID = %s", (rid,)))


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)