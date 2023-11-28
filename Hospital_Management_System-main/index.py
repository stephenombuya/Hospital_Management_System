import http.server
import socketserver
import datetime
import json
from urllib.parse import urlparse, parse_qs
import mysql.connector
from base64 import b64decode
from http import HTTPStatus
import bcrypt


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

# Database configuration (replace with your database settings)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'hospital_management_system',
}

# Create a MySQL database connection
db_connection = mysql.connector.connect(**db_config)

# Create a cursor object to execute SQL queries
db_cursor = db_connection.cursor()


#CRUD OPERATIONS
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()
        
    def count(self):
        # Count for patients, doctors, and appointments
        db_cursor.execute("SELECT COUNT(*) FROM patients")
        patients_count = db_cursor.fetchone()[0]

        db_cursor.execute("SELECT COUNT(*) FROM doctors")
        doctors_count = db_cursor.fetchone()[0]

        db_cursor.execute("SELECT COUNT(*) FROM appointments")
        appointments_count = db_cursor.fetchone()[0]

        counts = {
            'patients': patients_count,
            'doctors': doctors_count,
            'appointments': appointments_count
        }

        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(counts).encode())


    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == '/':
            # Serve the index.html file
            self.path = 'http://localhost:8083/index.html'
        elif path == '/api/patients':
            if 'patient_id' in query_params:
                # Get a specific patient by ID
                patient_id = query_params['patient_id'][0]
                db_cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
                result = db_cursor.fetchone()

                if result:
                    patient = {
                        'patient_id': result[0],
                        'first_name': result[1],
                        'last_name': result[2],
                        'dob': result[3].isoformat(),
                        'gender': result[4]
                    }

                    self.send_response(200)
                    self.send_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(patient, cls=CustomJSONEncoder).encode())
                else:
                    self.send_response(404)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Patient not found'}).encode())
            else:
                # List all patients
                db_cursor.execute("SELECT * FROM patients")
                results = db_cursor.fetchall()
                patients = [{'patient_id': row[0], 'first_name': row[1], 'last_name': row[2], 'dob': row[3].isoformat(), 'gender': row[4]} for row in results]

                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(patients).encode())
        elif path == '/api/doctors':
            if 'doctor_id' in query_params:
                # Get a specific doctor by ID
                doctor_id = query_params['doctor_id'][0]
                db_cursor.execute("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
                result = db_cursor.fetchone()

                if result:
                    doctor = {
                        'doctor_id': result[0],
                        'first_name': result[1],
                        'last_name': result[2],
                        'specialization': result[3],
                    }

                    self.send_response(200)
                    self.send_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(doctor, cls=CustomJSONEncoder).encode())
                else:
                    self.send_response(404)
                    self.send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Doctor not found'}).encode())
            else:
                # List all doctors
                db_cursor.execute("SELECT * FROM doctors")
                results = db_cursor.fetchall()
                doctors = [{'doctor_id': row[0], 'first_name': row[1], 'last_name': row[2], 'specialization': row[3]} for row in results]
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(doctors).encode())
        elif path == '/api/appointments':
            if 'patient_id' in query_params:
                # Get appointments for a specific patient
                patient_id = query_params['patient_id'][0]
                db_cursor.execute("SELECT * FROM appointments WHERE patient_id = %s", (patient_id,))
                results = db_cursor.fetchall()
                appointments = [{'appointment_id': row[0], 'patient_id': row[1], 'doctor_id': row[2], 'appointment_date': row[3].isoformat(), 'status': row[4]} for row in results]
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(appointments, cls=CustomJSONEncoder).encode())
            else:
                # List all appointments
                db_cursor.execute(""" SELECT 
        appointments.appointment_id,
        appointments.patient_id,
        patients.first_name AS patient_first_name,
        patients.last_name AS patient_last_name,
        appointments.doctor_id,
        doctors.first_name AS doctor_first_name,
        doctors.last_name AS doctor_last_name,
        appointments.appointment_date,
        appointments.status
    FROM 
        appointments
    JOIN 
        patients ON appointments.patient_id = patients.patient_id
    JOIN 
        doctors ON appointments.doctor_id = doctors.doctor_id
""")

                results = db_cursor.fetchall()
                appointments = [
    {
        'appointment_id': row[0],
        'patient_id': row[1],
        'patient_first_name': row[2],  # Updated to use the joined patient's first name
        'patient_last_name': row[3],   # Updated to use the joined patient's last name
        'doctor_id': row[4],
        'doctor_first_name': row[5],   # Updated to use the joined doctor's first name
        'doctor_last_name': row[6],    # Updated to use the joined doctor's last name
        'appointment_date': row[7].isoformat(),
        'status': row[8]
    } for row in results
]
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(appointments, cls=CustomJSONEncoder).encode())
            
            
        elif path == '/api/counts':
            self.count()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/patients':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data.decode())
            
            print(post_data)

            # Create a new patient
            db_cursor.execute("INSERT INTO patients (first_name, last_name, dob, gender) VALUES (%s, %s, %s, %s)",
                              (post_data['first_name'], post_data['last_name'], post_data['dob'], post_data['gender']))
            db_connection.commit()

            patient_id = db_cursor.lastrowid
            self.send_response(201)
            self.send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {"code": 201,'message': 'Patient created successfully', 'patient_id': patient_id}
            self.wfile.write(json.dumps(response_data).encode())
        elif self.path == '/api/doctors':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data.decode())

            # Create a new doctor
            db_cursor.execute("INSERT INTO doctors (first_name, last_name, specialization) VALUES (%s, %s, %s)",
                              (post_data['first_name'], post_data['last_name'], post_data['specialization']))
            db_connection.commit()

            doctor_id = db_cursor.lastrowid
            self.send_response(201)
            self.send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'message': 'Doctor created successfully', 'doctor_id': doctor_id}
            self.wfile.write(json.dumps(response_data).encode())
        elif self.path == '/api/appointments':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data.decode())

            # Create a new appointment
            db_cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, status) VALUES (%s, %s, %s, %s)",
                              (post_data['patient_id'], post_data['doctor_id'], post_data['appointment_date'], post_data['status']))
            db_connection.commit()

            appointment_id = db_cursor.lastrowid
            self.send_response(201)
            self.send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {"code": 201,'message': 'Appointment booked successfully', 'appointment_id': appointment_id}
            self.wfile.write(json.dumps(response_data).encode())
        elif self.path == '/api/auth/register':
            # User registration
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data.decode())
            print(post_data)

            # Hash the password before storing it in the database
            password = post_data['password'].encode('utf-8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

            db_cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                              (post_data['username'], hashed_password.decode('utf-8')))
            db_connection.commit()

            user_id = db_cursor.lastrowid
            self.send_response(201)
            self.send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {'message': 'User registered successfully', 'user_id': user_id}
            self.wfile.write(json.dumps(response_data).encode())
        elif self.path == '/api/auth/login':
            # User login
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            post_data = json.loads(post_data.decode())
            print(post_data)

            # Extract username and password from post_data
            username = post_data.get('username')
            password = post_data.get('password')

            if username and password:
                # Hash the password before storing it in the database
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                db_cursor.execute("SELECT user_id, username, password_hash FROM users WHERE username = %s", (username,))
                user_data = db_cursor.fetchone()

                if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data[2].encode('utf-8')):
                    self.send_response(200)
                    self.send_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response_data = {'message': 'Login successful', 'user_id': user_data[0], 'username': user_data[1]}
                    self.wfile.write(json.dumps(response_data).encode())
                    return
            self.send_response(401)
            self.send_cors_headers()
            self.send_header('WWW-Authenticate', 'Basic realm="Hospital Management System"')
            self.end_headers()
            self.wfile.write(b'Unauthorized')

        else:
            super().do_POST()

    def do_PUT(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == '/api/patients' and 'patient_id' in query_params:
            patient_id = query_params['patient_id'][0]
            db_cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            result = db_cursor.fetchone()
            if result:
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                put_data = json.loads(put_data.decode())

                # Update patient information
                db_cursor.execute("UPDATE patients SET first_name = %s, last_name = %s, dob = %s, gender = %s WHERE patient_id = %s",
                                  (put_data['first_name'], put_data['last_name'], put_data['dob'], put_data['gender'], patient_id))
                db_connection.commit()

                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {"code": 200,'message': 'Patient information updated successfully', 'patient_id': patient_id}
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Patient Not Found')
        elif path == '/api/doctors' and 'doctor_id' in query_params:
            doctor_id = query_params['doctor_id'][0]
            db_cursor.execute("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
            result = db_cursor.fetchone()
            if result:
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                put_data = json.loads(put_data.decode())

                # Update doctor information
                db_cursor.execute("UPDATE doctors SET first_name = %s, last_name = %s, specialization = %s WHERE doctor_id = %s",
                                  (put_data['first_name'], put_data['last_name'], put_data['specialization'], doctor_id))
                db_connection.commit()

                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {"code": 200,'message': 'Doctor information updated successfully', 'doctor_id': doctor_id}
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Doctor Not Found')
        elif path == '/api/appointments' and 'appointment_id' in query_params:
            appointment_id = query_params['appointment_id'][0]
            db_cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s", (appointment_id,))
            result = db_cursor.fetchone()
            if result:
                content_length = int(self.headers['Content-Length'])
                put_data = self.rfile.read(content_length)
                put_data = json.loads(put_data.decode())

                # Update appointments information
                db_cursor.execute("UPDATE appointments SET status = %s, appointment_date = %s WHERE appointment_id = %s",
                    (put_data['status'], put_data['appointment_date'], appointment_id)
                )
                db_connection.commit()

                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {
                    "code": 200,
                    'message': 'Appointment information updated successfully',
                    'appointment_id': appointment_id
                }
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Appointment Not Found')
            super().do_PUT()

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)

        if path == '/api/patients' and 'patient_id' in query_params:
            patient_id = query_params['patient_id'][0]
            db_cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            result = db_cursor.fetchone()
            if result:
                # Delete patient
                db_cursor.execute("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
                db_connection.commit()
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Patient Not Found')
        elif path == '/api/doctors' and 'doctor_id' in query_params:
            doctor_id = query_params['doctor_id'][0]
            db_cursor.execute("SELECT * FROM doctors WHERE doctor_id = %s", (doctor_id,))
            result = db_cursor.fetchone()
            if result:
                # Delete doctor
                db_cursor.execute("DELETE FROM doctors WHERE doctor_id = %s", (doctor_id,))
                db_connection.commit()
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Doctor Not Found')

        elif path == '/api/appointments' and 'appointment_id' in query_params:
            appointment_id = query_params['appointment_id'][0]
            db_cursor.execute("SELECT * FROM appointments WHERE appointment_id = %s", (appointment_id,))
            result = db_cursor.fetchone()
            if result:
                # Delete appointment
                db_cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
                db_connection.commit()
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Appointment Not Found')
        else:
            super().do_DELETE()
   

# Define the host and port for the server
host = 'localhost'
port = 8083

# Create and start the server
with socketserver.TCPServer((host, port), MyHandler) as server:
    print(f'Starting server on http://{host}:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Server stopped.')



#         CREATE DATABASE hms;
# USE hms;
# CREATE TABLE users(

# user_id int PRIMARY KEY auto_increment,
# username varchar(255) NOT NULL,
# password_hash varchar(255) NOT NULL);
# CREATE TABLE doctors(
#     doctor_id INT PRIMARY KEY auto_increment,
#     first_name VARCHAR(255) NOT NULL,
#     last_name VARCHAR(255) NOT NULL,
#     specialization VARCHAR(255) NOT NULL
# );

# CREATE TABLE patients (
#     patient_id INT PRIMARY KEY auto_increment,
#     first_name VARCHAR(255) NOT NULL,
#     last_name VARCHAR(255) NOT NULL,
#     dob DATE NOT NULL,
#     gender enum('Male', 'Female','Other') NOT NULL
# );

# drop table patient;

# CREATE TABLE Appointments (
#     appointment_id INT PRIMARY KEY AUTO_INCREMENT,
#     patient_id INT NOT NULL,
#     doctor_id INT NOT NULL,
#     appointment_date DATE NOT NULL,
#     status VARCHAR(255) NOT NULL,
#     FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
#     FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
# );
# DROP TABLE appointments;
# show tables;
# desc doctors;
# desc patients;

# ALTER TABLE appointments
# DROP COLUMN status;
# select * from doctors;
# desc doctors;
# desc appointments;

# select * from patients;
# select * from users;


