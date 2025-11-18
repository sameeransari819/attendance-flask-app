from flask import Flask, render_template, redirect, request, url_for
import sqlite3
import os , cv2, face_recognition
from datetime import datetime
import numpy as np
from werkzeug.utils import secure_filename


app = Flask(__name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ Step 1: Database setup (table create)
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students_list (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    photo TEXT NOT NULL,
                    enrollment TEXT NOT NULL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,         -- 'YYYY-MM-DD'
                    time TEXT NOT NULL,              -- 'HH:MM:SS' (optional)
                    subject TEXT NOT NULL
                    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS timetable (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    branch TEXT,
                    day TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()  # Run when app starts

@app.route('/')
def home():
    return render_template("index.html")




@app.route('/add-new', methods= ['POST'])
def add_new():
    name = request.form['name'].upper()
    branch = request.form['branch'].upper()
    photo = request.files['photo']
    enrollment = request.form['enrollment'].upper()

    conn = sqlite3.connect('students.db')
    curr = conn.cursor()

    curr.execute("SELECT * FROM students_list WHERE(enrollment)=?",(enrollment,))
    existing_student = curr.fetchone()

    if existing_student:
        conn.close()
        return render_template("index.html", alert="Student already exists!")

    # Save photo in static/uploads/
    else: 
        ext = os.path.splitext(photo.filename)[1]
        new_filename = secure_filename(f"{enrollment.upper()}{ext}")
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        photo.save(photo_path)
 
        # Save data to SQLite
        curr.execute("INSERT INTO students_list (name, branch, photo, enrollment) VALUES (?, ?, ?, ?)",
                  (name, branch, new_filename, enrollment))
        conn.commit()
        conn.close()

    return render_template("index.html", alert="Student added successfully!")





@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == '1234':
            return render_template('dashboard.html')
        


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
        



@app.route("/logout")
def logout():
    return redirect(url_for('home'))




@app.route("/students", methods = ['GET', 'POST'])
def students():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students_list")
    data = c.fetchall()
    conn.close()

    return render_template('students.html', students=data)

  

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    # GET → Show form with current details
    if request.method == "GET":
        c.execute("SELECT * FROM students_list WHERE id=?", (id,))
        student = c.fetchone()
        conn.close()
        if not student:
            return redirect(url_for("students"))
        return render_template("edit.html", student=student)

    # POST → Update details
    elif request.method == "POST":
        name = request.form["name"].upper()
        branch = request.form["branch"].upper()
        enrollment = request.form["enrollment"]
        photo = request.files["photo"]

        # If photo is updated
        if photo and photo.filename != "":
            ext = os.path.splitext(photo.filename)[1]
            new_filename = secure_filename(f"{enrollment.upper()}{ext}")
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
            photo.save(photo_path)
            c.execute(
                "UPDATE students_list SET name=?, branch=?, enrollment=?, photo=? WHERE id=?",
                (name, branch, enrollment, new_filename, id),
            )
        else:
            # Update without changing photo
            c.execute(
                "UPDATE students_list SET name=?, branch=?, enrollment=? WHERE id=?",
                (name, branch, enrollment, id),
            )

        conn.commit()
        conn.close()
        return redirect(url_for("students"))


@app.route("/delete/<int:id>")
def delete_student(id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    
    # Get photo filename before deleting
    c.execute("SELECT photo FROM students_list WHERE id=?", (id,))
    student = c.fetchone()
    
    if student:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student[0])
        if os.path.exists(photo_path):
            os.remove(photo_path)  # delete the photo file
            
        c.execute("DELETE FROM students_list WHERE id=?", (id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('students'))






@app.route("/timetable")
def timetable():
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("SELECT * FROM timetable")
    data = c.fetchall()
    conn.close()
    return render_template("timetable.html", timetable=data)


@app.route("/add_timetable", methods=["GET", "POST"])
def add_timetable():
    if request.method == "GET":
        return render_template("add_timetable.html")

    elif request.method == "POST":
        subject = request.form["subject"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        branch = request.form["branch"]
        day = request.form["day"]

        conn = sqlite3.connect("students.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO timetable (subject, start_time, end_time, branch, day) VALUES (?, ?, ?, ?, ?)",
            (subject, start_time, end_time, branch, day),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("timetable"))


@app.route("/edit_timetable/<int:id>", methods=["GET", "POST"])
def edit_timetable(id):
    conn = sqlite3.connect("students.db")
    c = conn.cursor()

    if request.method == "GET":
        c.execute("SELECT * FROM timetable WHERE id=?", (id,))
        data = c.fetchone()
        conn.close()
        return render_template("edit_timetable.html", data=data)

    elif request.method == "POST":
        subject = request.form["subject"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        branch = request.form["branch"]
        day = request.form["day"]

        c.execute(
            "UPDATE timetable SET subject=?, start_time=?, end_time=?, branch=?, day=? WHERE id=?",
            (subject, start_time, end_time, branch, day, id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("timetable"))


@app.route("/delete_timetable/<int:id>")
def delete_timetable(id):
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    c.execute("DELETE FROM timetable WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("timetable"))



    
        
    

@app.route('/mark', methods=['GET', 'POST'])
def mark():
    known_encodings = []
    known_names = []

    path = "static/uploads"


    conn = sqlite3.connect('students.db')
    curr = conn.cursor()

    # 🔹 Step 1: Load all student encodings from upload folder
    for filename in os.listdir(path):
        if filename.endswith((".jpeg", ".png", ".jpg")):
            img_path = os.path.join(path, filename)
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)

            if len(encodings) > 0:
                enrollment = os.path.splitext(filename)[0]
                curr.execute("SELECT name FROM students_list WHERE enrollment=?", (enrollment,))
                result = curr.fetchone()

                if result:
                    student_name = result[0]
                else:
                    student_name = "Unknown"

                known_encodings.append(encodings[0])
                known_names.append(student_name)

    # 🔹 Step 2: Get timetable from DB
    curr.execute("SELECT subject, start_time, end_time FROM timetable")
    timetable = curr.fetchall()
    conn.close()

    def get_current_subject():
        now_time = datetime.now().time()
        for subject, start, end in timetable:
            start_t = datetime.strptime(start, "%H:%M").time()
            end_t = datetime.strptime(end, "%H:%M").time()
            if start_t <= now_time <= end_t:
                return subject
        return None

    # 🔹 Step 3: Start webcam
    cap = cv2.VideoCapture(0)

    motion_detected = False
    prev_frame = None
    motion_start_time = datetime.now()


    while True:
        ret, frame = cap.read()
        if not ret:
            break



        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = known_names[match_index]

                now = datetime.now()
                current_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")
                current_subject = get_current_subject()

                # 🔹 Agar koi class nahi chal rahi
                if not current_subject:
                    cap.release()
                    cv2.destroyAllWindows()
                    return render_template("index.html", message="No class scheduled right now!")

                conn = sqlite3.connect('students.db')
                curr = conn.cursor()

                # 🔹 Check agar same subject same date pe already mark ho chuki hai
                curr.execute("""
                    SELECT * FROM attendance 
                    WHERE name=? AND date=? AND subject=?
                """, (name, current_date, current_subject))
                existing_student = curr.fetchone()

                if existing_student:
                    conn.close()
                    cap.release()
                    cv2.destroyAllWindows()
                    return render_template("index.html", message=f"Attendance already marked for {name} in {current_subject}")

                # 🔹 Nahi hai to insert kar do
                curr.execute("""
                    INSERT INTO attendance (name, date, time, subject)
                    VALUES (?, ?, ?, ?)
                """, (name, current_date, current_time, current_subject))
                conn.commit()
                conn.close()

                cap.release()
                cv2.destroyAllWindows()
                message = f"Attendance marked for {name} ({current_subject}) on {current_date} at {current_time}"
                return render_template("index.html", message=message)

            # 🔹 Draw rectangle and name
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imshow("Webcam", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return render_template("index.html", message="No face detected!")

    

@app.route('/view')
def view_attendance():
    conn = sqlite3.connect("students.db")
    curr = conn.cursor()
    curr.execute("SELECT * FROM attendance")
    data = curr.fetchall()
    conn.close()
    
    # HTML page me data bhejna
    return render_template('view_attendance.html', attendance=data)



if __name__ ==  '__main__':
    app.run(debug=True)