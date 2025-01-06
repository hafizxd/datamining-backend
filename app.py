from flask import Flask , request , jsonify
import json
import pymysql
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import joblib
import pandas as pd
from flask_cors import CORS


app = Flask(__name__)

CORS(app)

app.config.from_object(Config)
jwt = JWTManager(app)
model = joblib.load("diabetes_model.joblib")

def db_connection():
    conn = None
    try:
        conn = pymysql.connect(host="localhost",
    			       	user="root",
                               	password="",
                               	database="datmin_predict",
                               	charset='utf8mb4',
                                cursorclass=pymysql.cursors.DictCursor)
    except pymysql.error as e :
        print(e)
    return conn

@app.route('/example', methods=['GET'])
def example():
    data = {"success": True, "message": "This is a JSON response"}
    return jsonify(data)

# AUTHENTICATION
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    hashed_password = generate_password_hash(password)
    conn = db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password),
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'User created successfully'}), 201
    except pymysql.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    
    conn = db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM users WHERE email = %s", (email)
    )
    user = cursor.fetchone()

    if user and check_password_hash(user['password'], password):
        # identity = {'name': user['name'], 'email': user['email']}
        access_token = create_access_token(identity=user['email'])
        conn.close()
        return jsonify({'success': True, 'message': 'Success login', 'access_token': access_token}), 200
    
    conn.close()
    return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    identity = get_jwt_identity()  # This will be a JSON string
    return jsonify({'success': True, 'logged_in_as': identity}), 200


# predictions

@app.route('/predicts', methods=['GET', 'POST'])
@jwt_required()
def all_predicts():
    conn = db_connection()
    cursor = conn.cursor()
    if request.method == 'GET':
        sql_query = """
            SELECT predicts.*, users.name, users.email FROM predicts
            INNER JOIN users ON predicts.user_id = users.id
            ORDER BY predicts.created_at DESC
        """
        cursor.execute(sql_query)
        allAuto = [
            dict(id=row['id'],
                user_name=row['name'],
                user_email=row['email'],
                gender=row['gender'],
                age=row['age'],
                hypertension=row['hypertension'],
                heart_desease=row['heart_desease'],
                smoking_history=row['smoking_history'],
                bmi=row['bmi'],
                hbac=row['hbac'],
                blood_glucose=row['blood_glucose'],
                diabetes=row['diabetes'],
                created_at=row['created_at'])
                for row in cursor.fetchall()
        ]
        if allAuto is not None :
            return jsonify({'success': True, 'payload': allAuto}), 200

    
    if request.method == 'POST':
        email = get_jwt_identity()
        print(email)
        cursor.execute(
            "SELECT * FROM users WHERE email = %s", (email)
        )
        user = cursor.fetchone()
        print(user)

        data = request.json
        user_id = user['id']
        gender = data.get("gender")
        age = data.get("age")
        hypertension = data.get("hypertension")
        heart_desease = data.get("heart_desease")
        smoking_history = data.get("smoking_history")
        bmi = data.get("bmi")
        hbac = data.get("hbac")
        blood_glucose = data.get("blood_glucose")

        # predict with model
        features = {
            'gender': [gender],
            'age': [int(age)],
            'hypertension': [int(hypertension)],
            'heart_disease': [int(heart_desease)],
            'smoking_history': [smoking_history],
            'bmi': [float(bmi)],
            'HbA1c_level': [float(hbac)],
            'blood_glucose_level': [int(blood_glucose)]
        }
        new_data_df = pd.DataFrame(features)
        new_data_encoded = pd.get_dummies(new_data_df)

        X_train_encoded = [
            'age', 'hypertension', 'heart_disease', 'bmi', 'HbA1c_level',
            'blood_glucose_level', 'gender_Female', 'gender_Male', 'gender_Other',
            'smoking_history_No Info', 'smoking_history_current',
            'smoking_history_ever', 'smoking_history_former',
            'smoking_history_never', 'smoking_history_not current'
        ]
        new_data_encoded = new_data_encoded.reindex(columns=X_train_encoded, fill_value=0)

        prediction = model.predict(new_data_encoded)  # Make a prediction

        diabetes = int(prediction[0])

        sql = """ 
            INSERT INTO predicts (
                user_id,
                gender,
                age,
                hypertension,
                heart_desease,
                smoking_history,
                bmi,
                hbac,
                blood_glucose,
                diabetes
            ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor = cursor.execute(sql, (
            user_id,
            gender,
            age,
            hypertension,
            heart_desease,
            smoking_history,
            bmi,
            hbac,
            blood_glucose,
            diabetes
        ))
        conn.commit()
        return jsonify({'success': True, 'message': "created successfully", "is_diabetes": diabetes}), 201
    
if __name__ == '__main__' :
    app.run(debug=True)