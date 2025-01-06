import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="datmin_predict",
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()
sql_query = """
CREATE TABLE users (
    id integer PRIMARY KEY AUTO_INCREMENT,
    name varchar(255) NOT NULL,
    email varchar(255) UNIQUE NOT NULL,
    password varchar(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

cursor.execute(sql_query)

sql_query = """CREATE TABLE predicts (
    id integer PRIMARY KEY AUTO_INCREMENT,
    user_id integer NOT NULL,
    gender ENUM('MALE', 'FEMALE') NOT NULL DEFAULT 'MALE',
    age integer NOT NULL,
    hypertension tinyint(1) NOT NULL default 1,
    heart_desease tinyint(1) NOT NULL default 1,
    smoking_history ENUM('never', 'no info', 'current', 'former') NOT NULL DEFAULT 'never',
    bmi float NOT NULL,
    hbac float NOT NULL,
    blood_glucose integer NOT NULL,
    diabetes tinyint(1) NOT NULL default 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);"""

cursor.execute(sql_query)

conn.close()
