from flask import Flask, render_template, request, redirect, url_for, flash, session
from multiprocessing import connection
from flask_mysqldb import MySQL
from functools import wraps
import MySQLdb.cursors
import joblib
import pandas as pd
import numpy as np
import os
from os.path import join, dirname, realpath
from mysqlx import Session
import mysql.connector
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import metrics

app = Flask(__name__,template_folder='template')

app.secret_key = 'many random bytes'

# Database
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="prediksi2"
)

mycursor = mydb.cursor()
mycursor.execute("SHOW DATABASES")

# View All Database
for x in mycursor:
  print(x)
mysql = MySQL()
  
# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'prediksi2'

# init MYSQL
mysql = MySQL(app)

# Upload folder
UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

# Upload folder
UPLOAD_DATATRAINING = 'static/file_datatraining'
app.config['UPLOAD_DATATRAINING'] =  UPLOAD_DATATRAINING

# Index
@app.route("/")
def main():
    if session.get('index') == True:
        return redirect(url_for('dashboard'))
    return render_template("homepage/index.html")

# Menu Home
@app.route('/ManualRegresi')
def ManualRegresi():
        return render_template('homepage/ManualRegresi.html')

# Menu Home
@app.route('/ManualANN')
def ManualANN():
        return render_template('homepage/ManualANN.html')
        

# Check if user logged in (dekorator)
def logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            #flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return decorated_function

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():   
    if session.get('login') == True:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']

        # Create cursor
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users WHERE username = % s AND password = % s AND level = % s', (username, password,level ))
        account = cur.fetchone()
        if account:
            session['logged_in'] = True
            session['id_users'] = account['id_users']
            session['username'] = account['username']
            session['password'] = account['password']
            session['level'] = account['level']
            msg = 'Logged in successfully !'
            return redirect(url_for('dashboard', msg = msg))
        else:
            msg = 'Incorrect username / password !'
            return render_template('login.html', msg = msg)
    else:
        error = 'Username not found'
        return render_template('login.html', error=error)
    return render_template('login.html')

# Menu Dashboard Algoritma Prediksi
@app.route("/profile")
@logged_in
def profile():
    if 'logged_in' in session:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users WHERE id_users = %s', (session['id_users'], ))
        account = cur.fetchone()
        return render_template('profile/profile.html',account=account)
    else:
        return redirect(url_for('profile'))

@app.route('/update_profile',methods=['GET','POST'])
@logged_in
def update_profile():

    if request.method == 'POST':
        id_data = request.form['id_users']
        nama = request.form['nama']
        nip = request.form['nip']
        jenis_kelamin = request.form['jenis_kelamin']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']

        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE users
               SET nama=%s, nip=%s, jenis_kelamin=%s, fakultas=%s, program_studi=%s, username=%s, password=%s, level=%s
               WHERE id_users=%s
            """, (nama, nip, jenis_kelamin, fakultas, program_studi, username, password, level, id_data ))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('profile'))

# Logout
@app.route('/logout')
@logged_in
def logout():
    session.clear()
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@logged_in
def dashboard():
    
    query1 = "SELECT COUNT(*) FROM data_mahasiswa_alumni"      
    mycursor.execute(query1)
    data1 = mycursor.fetchall() 

    query2 = "SELECT COUNT(*) FROM data_mahasiswa_aktif"      
    mycursor.execute(query2)
    data2 = mycursor.fetchall() 

    query3 = "SELECT COUNT(*) FROM data_prediksi"      
    mycursor.execute(query3)
    data3 = mycursor.fetchall() 

    return render_template('dashboard.html', data1=data1, data2=data2, data3=data3)



# Menu Dashboard Prediksi
@app.route('/prediksiMLR')
@logged_in
def prediksiregresi():
        return render_template('prediksi/prediksiMLR.html')

# Menu Dashboard Algoritma Prediksi
@app.route('/algoritmaPrediksi')
@logged_in
def algoritmaPrediksi():
        return render_template('algoritma/algoritmaPrediksi.html')

# Menu Dashboard Algoritma Prediksi
@app.route('/output')
@logged_in
def output():
        return render_template('algoritma/output.html')

# Menu Dashboard Algoritma Prediksi
@app.route('/output_DD')
@logged_in
def output_DD():
        return render_template('isi_dashboard_dosen/algoritma_prediksi/output_DD.html')



# ALGORITMA PREDIKSI PADA TAMPILAN HALAMAN HOME ALGORITMA ANN DAN MLR
@app.route("/predictMLR", methods=['GET', 'POST'])
def predictMLR():
    if request.method == 'POST':
            jenis_kelamin = request.form['jenis_kelamin']
            ips1 = float(request.form['ips1'])
            ips2 = float(request.form['ips2'])
            ips3 = float(request.form['ips3'])
            ips4 = float(request.form['ips4'])
            ips5 = float(request.form['ips5'])
            ips6 = float(request.form['ips6'])
            ipk = float(request.form['ipk'])
            sumber_biaya = request.form['sumber_biaya']
            ket_jalur_masuk = request.form['ket_jalur_masuk']
            sekolah_asal = request.form['sekolah_asal']

            pred_var = [jenis_kelamin,ips1,ips2,ips3,ips4,ips5,ips6,ipk,sumber_biaya,ket_jalur_masuk,sekolah_asal]
            pred_var_arr = np.array(pred_var,dtype=float)
            pred_var_arr = pred_var_arr.reshape(1, -1)

            # reload model Multiple Linier Regression
            mul_reg = open("multiple_regression_model.pkl", "rb")
            mlr_model = joblib.load(mul_reg)
            mlr_model_prediction = mlr_model.predict(pred_var_arr)
            mlr_model_prediction = round(float(mlr_model_prediction), 2)

            if mlr_model_prediction <= float(48):
                return render_template('homepage/ManualRegresi.html',prediction_text_mlr="LULUS TEPAT WAKTU", prediction_mlr = mlr_model_prediction)
            elif mlr_model_prediction > float(48):
                return render_template('homepage/ManualRegresi.html',prediction_text_mlr="LULUS TIDAK TEPAT WAKTU",prediction_mlr = mlr_model_prediction)
            else :
                return render_template('homepage/ManualRegresi.html')

@app.route("/predictANN", methods=['GET', 'POST'])
def predictANN():
    if request.method == 'POST':
            jenis_kelamin = request.form['jenis_kelamin']
            ips1 = float(request.form['ips1'])
            ips2 = float(request.form['ips2'])
            ips3 = float(request.form['ips3'])
            ips4 = float(request.form['ips4'])
            ips5 = float(request.form['ips5'])
            ips6 = float(request.form['ips6'])
            ipk = float(request.form['ipk'])
            sumber_biaya = request.form['sumber_biaya']
            ket_jalur_masuk = request.form['ket_jalur_masuk']
            sekolah_asal = request.form['sekolah_asal']

            pred_var = [jenis_kelamin,ips1,ips2,ips3,ips4,ips5,ips6,ipk,sumber_biaya,ket_jalur_masuk,sekolah_asal]
            pred_var_arr = np.array(pred_var,dtype=float)
            pred_var_arr = pred_var_arr.reshape(1, -1)

            # reload model ANN
            mul_reg2 = open("neural_network_model.pkl", "rb")
            ann_model = joblib.load(mul_reg2)
            ann_model_prediction = ann_model.predict(pred_var_arr)
            ann_model_prediction = round(float(ann_model_prediction), 2)

            if ann_model_prediction <= float(48):
                return render_template('homepage/ManualANN.html',prediction_text_ann="LULUS TEPAT WAKTU", prediction_ann = ann_model_prediction)
            elif ann_model_prediction > float(48):
                return render_template('homepage/ManualANN.html',prediction_text_ann="LULUS TIDAK TEPAT WAKTU",prediction_ann = ann_model_prediction)
            else :
                return render_template('homepage/ManualANN.html')

# ALGORITMA PREDIKSI PADA TAMPILAN HALAMAN ADMINISTRATOR ALGORITMA ANN DAN MLR
@app.route("/predict", methods=['GET', 'POST'])
@logged_in
def predict():
    if request.method == 'POST':
            jenis_kelamin = request.form['jenis_kelamin']
            ips1 = float(request.form['ips1'])
            ips2 = float(request.form['ips2'])
            ips3 = float(request.form['ips3'])
            ips4 = float(request.form['ips4'])
            ips5 = float(request.form['ips5'])
            ips6 = float(request.form['ips6'])
            ipk = float(request.form['ipk'])
            sumber_biaya = request.form['sumber_biaya']
            ket_jalur_masuk = request.form['ket_jalur_masuk']
            sekolah_asal = request.form['sekolah_asal']

            pred_var = [jenis_kelamin,ips1,ips2,ips3,ips4,ips5,ips6,ipk,sumber_biaya,ket_jalur_masuk,sekolah_asal]
            pred_var_arr = np.array(pred_var,dtype=float)
            pred_var_arr = pred_var_arr.reshape(1, -1)

            # reload model ANN
            mul_reg2 = open("neural_network_model.pkl", "rb")
            ann_model = joblib.load(mul_reg2)
            ann_model_prediction = ann_model.predict(pred_var_arr)
            ann_model_prediction = round(float(ann_model_prediction), 2)


            # reload model Multiple Linier Regression
            mul_reg = open("multiple_regression_model.pkl", "rb")
            mlr_model = joblib.load(mul_reg)
            mlr_model_prediction = mlr_model.predict(pred_var_arr)
            mlr_model_prediction = round(float(mlr_model_prediction), 2)

            if mlr_model_prediction <= float(48) and ann_model_prediction <= float(48):
                return render_template('algoritma/output.html',prediction_text_mlr="LULUS TEPAT WAKTU", prediction_mlr = mlr_model_prediction,prediction_text_ann="LULUS TEPAT WAKTU", prediction_ann = ann_model_prediction)
            elif mlr_model_prediction > float(48) and ann_model_prediction > float(48):
                return render_template('algoritma/output.html',prediction_text_mlr="LULUS TIDAK TEPAT WAKTU",prediction_mlr = mlr_model_prediction,prediction_text_ann="LULUS TIDAK TEPAT WAKTU",prediction_ann = ann_model_prediction)
            else :
                return render_template('algoritma/output.html')

# ALGORITMA PREDIKSI PADA TAMPILAN HALAMAN DOSEN (LECTURER) ALGORITMA ANN DAN MLR
@app.route("/predict_DD", methods=['GET', 'POST'])
@logged_in
def predict_DD():
    if request.method == 'POST':
            jenis_kelamin = request.form['jenis_kelamin']
            ips1 = float(request.form['ips1'])
            ips2 = float(request.form['ips2'])
            ips3 = float(request.form['ips3'])
            ips4 = float(request.form['ips4'])
            ips5 = float(request.form['ips5'])
            ips6 = float(request.form['ips6'])
            ipk = float(request.form['ipk'])
            sumber_biaya = request.form['sumber_biaya']
            ket_jalur_masuk = request.form['ket_jalur_masuk']
            sekolah_asal = request.form['sekolah_asal']

            pred_var = [jenis_kelamin,ips1,ips2,ips3,ips4,ips5,ips6,ipk,sumber_biaya,ket_jalur_masuk,sekolah_asal]
            pred_var_arr = np.array(pred_var,dtype=float)
            pred_var_arr = pred_var_arr.reshape(1, -1)

            # reload model ANN
            mul_reg2 = open("neural_network_model.pkl", "rb")
            ann_model = joblib.load(mul_reg2)
            ann_model_prediction = ann_model.predict(pred_var_arr)
            ann_model_prediction = round(float(ann_model_prediction), 2)


            # reload model Multiple Linier Regression
            mul_reg = open("multiple_regression_model.pkl", "rb")
            mlr_model = joblib.load(mul_reg)
            mlr_model_prediction = mlr_model.predict(pred_var_arr)
            mlr_model_prediction = round(float(mlr_model_prediction), 2)

            if mlr_model_prediction <= float(48) and ann_model_prediction <= float(48):
                return render_template('isi_dashboard_dosen/algoritma_prediksi/output_DD.html',prediction_text_mlr="LULUS TEPAT WAKTU", prediction_mlr = mlr_model_prediction,prediction_text_ann="LULUS TEPAT WAKTU", prediction_ann = ann_model_prediction)
            elif mlr_model_prediction > float(48) and ann_model_prediction > float(48):
                return render_template('isi_dashboard_dosen/algoritma_prediksi/output_DD.html',prediction_text_mlr="LULUS TIDAK TEPAT WAKTU",prediction_mlr = mlr_model_prediction,prediction_text_ann="LULUS TIDAK TEPAT WAKTU",prediction_ann = ann_model_prediction)
            else :
                return render_template('isi_dashboard_dosen/algoritma_prediksi/output_DD.html')




       ###-- DASHBOARD ADMINISTRATOR --###
    ##########--HALAMAN PREDIKSI--##########

# Menu Dashboard Prediksi
@app.route("/halaman_prediksi")
@logged_in
def halaman_prediksi():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT data_prediksi.id, data_prediksi.fakultas, data_prediksi.program_studi,  data_prediksi.nim, data_prediksi.nama, data_prediksi.tahun_angkatan, data_prediksi.jenis_kelamin, data_prediksi.ips1, data_prediksi.ips2, data_prediksi.ips3, data_prediksi.ips4, data_prediksi.ips5, data_prediksi.ips6, data_prediksi.ipk, data_prediksi.sumber_biaya, data_prediksi.ket_jalur_masuk, data_prediksi.sekolah_asal, hasil_prediksi.lama_studi_MLR, hasil_prediksi.lama_studi_ANN FROM data_prediksi INNER JOIN hasil_prediksi ON data_prediksi.id=hasil_prediksi.id")
    data = cur.fetchall()                  
    cur.close()
    return render_template('prediksi/prediksi.html', data = data )


#--IMPORT--IMPORT--IMPORT--#
@app.route("/uploadFileprediksi", methods=['GET','POST'])
@logged_in
def uploadFileprediksi():
        # get the uploaded file
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_prediksi = os.path.join(app.config['UPLOAD_DATATRAINING'], uploaded_file.filename)
            # set the file path
            uploaded_file.save(file_prediksi)
            # save the file 
            
            # CSV Column Names
            col_names = ['id_training','nama','fakultas','program_studi','nim','tahun_angkatan','jenis_kelamin', 'ips1', 'ips2', 'ips3', 'ips4', 'ips5', 'ips6', 'ipk', 'sumber_biaya', 'ket_jalur_masuk', 'sekolah_asal','lama_studi','status_kelulusan']
            # Use Pandas to parse the CSV file
            csvData = pd.read_csv(file_prediksi,names=col_names)
            #integrasi data
            csvData.drop(columns=['id_training','nama','fakultas','program_studi','nim','tahun_angkatan','lama_studi','status_kelulusan'], axis = 1, inplace = True)
            
            #TRANSFORMASI DATA
            #mengubah kategori ke numerik (2 kategori)
            data2 = ['sumber_biaya']
            def biaya(csvData):
                return csvData.map({"Reguler": 1, "Bidikmisi": 0})
            csvData[data2] = csvData[data2].apply(biaya)

            data3 = ['jenis_kelamin']
            def jeniskelamin(csvData):
                return csvData.map({"Perempuan": 1, "Laki-Laki": 0})
            csvData[data3] = csvData[data3].apply(jeniskelamin)

            data4 = ['ket_jalur_masuk']
            def jalurmasuk(csvData):
                return csvData.map({"SNMPTN": 0, "SBMPTN": 1, "SM": 2})
            csvData[data4] = csvData[data4].apply(jalurmasuk)

            data5 = ['sekolah_asal']
            def asalsekolah(csvData):
                return csvData.map({"SMA": 0, "SMK": 1, "MA": 2})
            csvData[data5] = csvData[data5].apply(asalsekolah)

            #Ganti NaN dengan mean
            imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
            result_imputer = imputer.fit_transform(csvData)
            pred_var_arr = pd.DataFrame(result_imputer)
            pred_var_arr = pred_var_arr.reshape(1, -1)

            # reload model ANN
            mul_reg2 = open("neural_network_model.pkl", "rb")
            ann_model = joblib.load(mul_reg2)
            ann_hasil_prediction = ann_model.predict(pred_var_arr)
            #ann_hasil_prediction = round(float(ann_hasil_prediction), 2)


            # reload model Multiple Linier Regression
            mul_reg = open("multiple_regression_model.pkl", "rb")
            mlr_model = joblib.load(mul_reg)
            mlr_hasil_prediction = mlr_model.predict(pred_var_arr)
            #mlr_hasil_prediction = round(float(mlr_hasil_prediction), 2)

            y_pred_hasil = pd.DataFrame({'lama_studi_ANN':ann_hasil_prediction.flatten(),'lama_studi_MLR':mlr_hasil_prediction.flatten()})
            y_pred_hasil.to_csv("data_hasil_prediksi.csv")


            #if (mlr_hasil_prediction <= 48).any():
                #return render_template('prediksi/outputprediksi.html',prediction_text_mlr="LULUS TEPAT WAKTU", prediction_mlr = mlr_hasil_prediction)
            #elif (mlr_hasil_prediction > 48).any():
               # return render_template('prediksi/outputprediksi.html',prediction_text_mlr="LULUS TIDAK TEPAT WAKTU",prediction_mlr = mlr_hasil_prediction)

            # CVS Column Names
            col_names = ['lama_studi_ANN','lama_studi_MLR']
            # Use Pandas to parse the CSV file
            csvPrediksi = pd.read_csv('data_hasil_prediksi.csv',names=col_names)
            # Loop through the Rows
            for i,row in csvPrediksi.iterrows():
                    sql = "INSERT INTO hasil_prediksi (lama_studi_ANN,lama_studi_MLR) VALUES (%s, %s)"
                    value = (row['lama_studi_ANN'],row['lama_studi_MLR'])
                    mycursor.execute(sql, value)
                    mydb.commit()
                    print(i,row['lama_studi_ANN'],row['lama_studi_MLR'])

            return render_template('prediksi/prediksi.html')

#--IMPORT--IMPORT--IMPORT--#
@app.route("/uploadFileprediksi3", methods=['GET','POST'])
@logged_in
def uploadFileprediksi3():
        # get the uploaded file
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_prediksi = os.path.join(app.config['UPLOAD_DATATRAINING'], uploaded_file.filename)
            # set the file path
            uploaded_file.save(file_prediksi)
            # save the file 
            
            # CSV Column Names
            col_names = ['id','fakultas','program_studi','nim','nama','tahun_angkatan','jenis_kelamin', 'ips1', 'ips2', 'ips3', 'ips4', 'ips5', 'ips6', 'ipk', 'sumber_biaya', 'ket_jalur_masuk', 'sekolah_asal']
            # Use Pandas to parse the CSV file
            csvData = pd.read_csv(file_prediksi,names=col_names)

            # Loop through the Rows
            #for i,row in csvData.fillna(0).iterrows():
            for i,row in csvData.fillna(csvData.mean()).iterrows():
                sql = "INSERT INTO data_prediksi (id,fakultas,program_studi,nim,nama,tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5,ips6,ipk,sumber_biaya, ket_jalur_masuk, sekolah_asal) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                value = (row['id'],row['fakultas'],row['program_studi'],row['nim'],row['nama'],row['tahun_angkatan'],row['jenis_kelamin'],row['ips1'],row['ips2'],row['ips3'],row['ips4'],row['ips5'],row['ips6'],row['ipk'],row['sumber_biaya'],row['ket_jalur_masuk'],row['sekolah_asal'])
                mycursor.execute(sql, value)
                mydb.commit()
                print(i,row['id'],row['fakultas'],row['program_studi'],row['nim'],row['nama'],row['tahun_angkatan'],row['jenis_kelamin'],row['ips1'],row['ips2'],row['ips3'],row['ips4'],row['ips5'],row['ips6'],row['ipk'],row['sumber_biaya'],row['ket_jalur_masuk'],row['sekolah_asal'])
            
            #integrasi data
            csvData.drop(columns=['id','nama','fakultas','program_studi','nim','tahun_angkatan'], axis = 0, inplace = True)

            #TRANSFORMASI DATA
            #mengubah kategori ke numerik (2 kategori)
            data2 = ['sumber_biaya']
            def biaya(csvData):
                return csvData.map({"Reguler": 1, "Bidikmisi": 0})
            csvData[data2] = csvData[data2].apply(biaya)

            data3 = ['jenis_kelamin']
            def jeniskelamin(csvData):
                return csvData.map({"Perempuan": 1, "Laki-Laki": 0})
            csvData[data3] = csvData[data3].apply(jeniskelamin)

            data4 = ['ket_jalur_masuk']
            def jalurmasuk(csvData):
                return csvData.map({"SNMPTN": 0, "SBMPTN": 1, "SM": 2})
            csvData[data4] = csvData[data4].apply(jalurmasuk)

            data5 = ['sekolah_asal']
            def asalsekolah(csvData):
                return csvData.map({"SMA": 0, "SMK": 1, "MA": 2})
            csvData[data5] = csvData[data5].apply(asalsekolah)

            imputer = SimpleImputer(missing_values=np.nan, strategy='mean')
            result_imputer = imputer.fit_transform(csvData)
            pred_var_arr = pd.DataFrame(result_imputer)
            
            # reload model ANN
            mul_reg2 = open("neural_network_model.pkl", "rb")
            ann_model = joblib.load(mul_reg2)
            ann_hasil_prediction = ann_model.predict(pred_var_arr)

            # reload model Multiple Linier Regression
            mul_reg = open("multiple_regression_model.pkl", "rb")
            mlr_model = joblib.load(mul_reg)
            mlr_hasil_prediction = mlr_model.predict(pred_var_arr)

            y_pred_hasil = pd.DataFrame({'lama_studi_ANN':ann_hasil_prediction.flatten(),'lama_studi_MLR':mlr_hasil_prediction.flatten()})
            y_pred_hasil.to_csv("data_hasil_prediksi.csv")

            # CVS Column Names
            col_names = ['lama_studi_ANN','lama_studi_MLR']
            # Use Pandas to parse the CSV file
            csvPrediksi = pd.read_csv('data_hasil_prediksi.csv')
            # Loop through the Rows
            for i,row in csvPrediksi.iterrows():
                    sql = "INSERT INTO hasil_prediksi (lama_studi_ANN,lama_studi_MLR) VALUES (%s, %s)"
                    #sql = "UPDATE data_prediksi1 SET lama_studi_ANN=%s, lama_studi_MLR=%s WHERE id_prediksi=%s  "
                    value = (row['lama_studi_ANN'],row['lama_studi_MLR'])
                    mycursor.execute(sql, value)
                    mydb.commit()
                
            return render_template('prediksi/prediksi.html')

@app.route('/delete_dataprediksi/<string:id_data>', methods = ['GET'])
@logged_in
def delete_dataprediksi(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute ("DELETE FROM data_prediksi WHERE id= %s", [id_data])
    cur.execute ("DELETE FROM hasil_prediksi WHERE id= %s", [id_data])
    mysql.connection.commit()
    return redirect(url_for('halaman_prediksi'))

#--RESET-RESET-RESET-#
@app.route('/resetdataprediksi', methods = ['GET'])
@logged_in
def resetdataprediksi():
    cur = mysql.connection.cursor()
    cur.execute ("TRUNCATE TABLE data_prediksi")
    cur.execute ("TRUNCATE TABLE hasil_prediksi")
    mysql.connection.commit()
    return redirect(url_for('halaman_prediksi'))



 



    ###--OPERASI PADA MENU INPUT DATA MAHASSIWA--###
    ##########--DATA ALUMNI MAHASISWA--##########


@app.route("/alumnimahasiswa")
@logged_in
def alumnimahasiswa():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT * FROM data_mahasiswa_alumni")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('inputdata_alumni_mahasiswa/alumnimahasiswa.html', data = data )

@app.route("/forminputdataalumni")    #koneksi ke form input data alumni
@logged_in
def forminputdataalumni():
    return render_template('inputdata_alumni_mahasiswa/forminputdataalumni.html')

@app.route("/formeditdataalumni")    #koneksi ke form input data alumni
@logged_in
def formeditdataalumni():
    return render_template('inputdata_alumni_mahasiswa/formeditdataalumni.html')

#--ADD--TAMBAH--ADD--#

@app.route("/add_dataalumni", methods=["POST"])    #route simpan data ke form input data alumni
@logged_in
def add_dataalumni():
    if request.method == 'POST':
        flash("Data Inserted Successfully") #tidak berfungsi
        id_mahasiswa_alumni = request.form['id_mahasiswa_alumni']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        nim = request.form['nim']
        nama = request.form['nama']
        tahun_angkatan = request.form['tahun_angkatan']
        jenis_kelamin = request.form['jenis_kelamin']
        ips1 = request.form['ips1']
        ips2 = request.form['ips2']
        ips3 = request.form['ips3']
        ips4 = request.form['ips4']
        ips5 = request.form['ips5']
        ips6 = request.form['ips6']
        ipk = request.form['ipk']
        sumber_biaya = request.form['sumber_biaya']
        ket_jalur_masuk = request.form['ket_jalur_masuk']
        sekolah_asal = request.form['sekolah_asal']
        lama_studi = request.form['lama_studi']
        status_kelulusan = request.form['status_kelulusan']

    cur = mysql.connection.cursor()   
    cur.execute("INSERT INTO data_mahasiswa_alumni (id_mahasiswa_alumni, fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, lama_studi, status_kelulusan) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id_mahasiswa_alumni, fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, lama_studi, status_kelulusan)) 
    mysql.connection.commit()
    return redirect(url_for('alumnimahasiswa'))

#--DELETE--HAPUS--DELETE--#

@app.route('/delete1/<string:id_data>', methods = ['GET'])
@logged_in
def delete1(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM data_mahasiswa_alumni WHERE id_mahasiswa_alumni=%s", [id_data])
    mysql.connection.commit()
    return redirect(url_for('alumnimahasiswa'))

#--EDIT--EDIT--EDIT--#

 
@app.route('/editalumni/<int:id>', methods=['GET', 'POST'])
def editalumni(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute('''
        SELECT * FROM data_mahasiswa_alumni WHERE id_mahasiswa_alumni=%s''', (id, ))
        row = cursor.fetchone()
        cursor.close()
    
        return render_template('inputdata_alumni_mahasiswa/formeditdataalumni.html', row=row)
    else:
        id_mahasiswa_alumni = request.form['id_mahasiswa_alumni']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        nim = request.form['nim']
        nama = request.form['nama']
        tahun_angkatan = request.form['tahun_angkatan']
        jenis_kelamin = request.form['jenis_kelamin']
        ips1 = request.form['ips1']
        ips2 = request.form['ips2']
        ips3 = request.form['ips3']
        ips4 = request.form['ips4']
        ips5 = request.form['ips5']
        ips6 = request.form['ips6']
        ipk = request.form['ipk']
        sumber_biaya = request.form['sumber_biaya']
        ket_jalur_masuk = request.form['ket_jalur_masuk']
        sekolah_asal = request.form['sekolah_asal']
        lama_studi = request.form['lama_studi']
        status_kelulusan = request.form['status_kelulusan']
    
        cursor = mysql.connection.cursor()
        cursor.execute(''' 
        UPDATE data_mahasiswa_alumni
        SET 
            id_mahasiswa_alumni = %s, fakultas = %s, program_studi = %s, nim = %s, nama = %s, tahun_angkatan = %s,
            jenis_kelamin = %s, ips1 = %s, ips2 = %s, ips3 = %s, ips4 = %s, ips5 = %s, ips6 = %s, ipk = %s,
            sumber_biaya = %s, ket_jalur_masuk = %s, lama_studi = %s, status_kelulusan = %s
        WHERE
            id_mahasiswa_alumni = %s;
        ''',(fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, lama_studi, status_kelulusan, id_mahasiswa_alumni))
            
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('alumnimahasiswa'))
    
    return render_template('inputdata_alumni_mahasiswa/alumnimahasiswa.html')   


#--IMPORT--IMPORT--IMPORT--#
@app.route("/uploadFiles_alumni", methods=['POST'])
@logged_in
def uploadFiles_alumni():
      # get the uploaded file
      uploaded_file = request.files['file']
      if uploaded_file.filename != '':
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
          # set the file path
           uploaded_file.save(file_path)
           parseCSV_alumni(file_path)
          # save the file 
        
      return redirect(url_for('alumnimahasiswa'))

def parseCSV_alumni(file_Path): 
      # CVS Column Names
      col_names = ['id_mahasiswa_alumni','fakultas','program_studi','nim','nama','tahun_angkatan','jenis_kelamin','ips1', 'ips2', 'ips3', 'ips4', 'ips5', 'ips6', 'ipk', 'sumber_biaya', 'ket_jalur_masuk', 'sekolah_asal','lama_studi','status_kelulusan']
      # Use Pandas to parse the CSV file
      csvData = pd.read_csv(file_Path,names=col_names)
      # Loop through the Rows
      #for i,row in csvData.fillna(csvData.mean()).iterrows():
      for i,row in csvData.fillna(0).iterrows():
             sql = "INSERT INTO data_mahasiswa_alumni (id_mahasiswa_alumni,fakultas,program_studi,nim,nama,tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5,ips6,ipk,sumber_biaya, ket_jalur_masuk, sekolah_asal,lama_studi,status_kelulusan) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
             value = (row['id_mahasiswa_alumni'],row['fakultas'],row['program_studi'],row['nim'],row['nama'],row['tahun_angkatan'],row['jenis_kelamin'],row['ips1'],row['ips2'],row['ips3'],row['ips4'],row['ips5'],row['ips6'],row['ipk'],row['sumber_biaya'],row['ket_jalur_masuk'],row['sekolah_asal'],row['lama_studi'],row['status_kelulusan'])
             mycursor.execute(sql, value)
             mydb.commit()
             print(i,row['id_mahasiswa_alumni'],row['fakultas'],row['program_studi'],row['nim'],row['nama'],row['tahun_angkatan'],row['jenis_kelamin'],row['ips1'],row['ips2'],row['ips3'],row['ips4'],row['ips5'],row['ips6'],row['ipk'],row['sumber_biaya'],row['ket_jalur_masuk'],row['sekolah_asal'],row['lama_studi'],row['status_kelulusan'])

#--RESET-RESET-RESET-#
@app.route('/resetdataalumni', methods = ['GET'])
@logged_in
def resetdataalumni():
    cur = mysql.connection.cursor()
    cur.execute ("TRUNCATE TABLE data_mahasiswa_alumni")
    mysql.connection.commit()
    return redirect(url_for('alumnimahasiswa'))





    ###--OPERASI PADA MENU INPUT DATA MAHASISWA--###
    ##########--DATA MAHASISWA AKTIF--##########

@app.route("/mahasiswaaktif")
@logged_in
def mahasiswaaktif():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT * FROM data_mahasiswa_aktif ")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('inputdata_mahasiswa_aktif/mahasiswaaktif.html', data = data )


@app.route("/forminputdataaktif")    #koneksi ke form input data aktif
@logged_in
def forminputdataaktif():
    return render_template('inputdata_mahasiswa_aktif/forminputdataaktif.html')

@app.route("/formeditdataaktif") 
@logged_in
def formeditdataaktif():
    return render_template('inputdata_mahasiswa_aktif/formeditdataaktif.html')


#--ADD--TAMBAH--ADD--#

@app.route("/add_dataaktif", methods=["POST"])    #route simpan data ke form input data aktif
@logged_in
def add_dataaktif():
 
    if request.method == 'POST':
        flash("Data Inserted Successfully") #tidak berfungsi
        id_mahasiswa_aktif = request.form['id_mahasiswa_aktif']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        nim = request.form['nim']
        nama = request.form['nama']
        tahun_angkatan = request.form['tahun_angkatan']
        jenis_kelamin = request.form['jenis_kelamin']
        ips1 = request.form['ips1']
        ips2 = request.form['ips2']
        ips3 = request.form['ips3']
        ips4 = request.form['ips4']
        ips5 = request.form['ips5']
        ips6 = request.form['ips6']
        ipk = request.form['ipk']
        sumber_biaya = request.form['sumber_biaya']
        ket_jalur_masuk = request.form['ket_jalur_masuk']
        sekolah_asal = request.form['sekolah_asal']

    cur = mysql.connection.cursor()   
    cur.execute("INSERT INTO data_mahasiswa_aktif (id_mahasiswa_aktif,fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id_mahasiswa_aktif,fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal))  
    mysql.connection.commit()
    return redirect(url_for('mahasiswaaktif'))

#--DELETE--HAPUS--DELETE--#

@app.route('/delete2/<string:id_data>', methods = ['GET'])
@logged_in
def delete2(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute ("DELETE FROM data_mahasiswa_aktif WHERE id_mahasiswa_aktif= %s", [id_data])
    mysql.connection.commit()
    return redirect(url_for('mahasiswaaktif'))


#--EDIT--EDIT--EDIT--#
@app.route('/editaktif/<int:id>', methods=['GET', 'POST'])
def editaktif(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute('''
        SELECT * FROM data_mahasiswa_aktif WHERE id_mahasiswa_aktif=%s''', (id, ))
        row = cursor.fetchone()
        cursor.close()
    
        return render_template('inputdata_mahasiswa_aktif/formeditdataaktif.html', row=row)
    else:
        id_mahasiswa_aktif = request.form['id_mahasiswa_aktif']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        nim = request.form['nim']
        nama = request.form['nama']
        tahun_angkatan = request.form['tahun_angkatan']
        jenis_kelamin = request.form['jenis_kelamin']
        ips1 = request.form['ips1']
        ips2 = request.form['ips2']
        ips3 = request.form['ips3']
        ips4 = request.form['ips4']
        ips5 = request.form['ips5']
        ips6 = request.form['ips6']
        ipk = request.form['ipk']
        sumber_biaya = request.form['sumber_biaya']
        ket_jalur_masuk = request.form['ket_jalur_masuk']
        sekolah_asal = request.form['sekolah_asal']

        cursor = mysql.connection.cursor()
        cursor.execute(''' 
        UPDATE data_mahasiswa_aktif
        SET 
            id_mahasiswa_aktif = %s, fakultas = %s, program_studi = %s, nim = %s, nama = %s, tahun_angkatan = %s,
            jenis_kelamin = %s, ips1 = %s, ips2 = %s, ips3 = %s, ips4 = %s, ips5 = %s, ips6 = %s, ipk = %s,
            sumber_biaya = %s, ket_jalur_masuk = %s
        WHERE
            id_mahasiswa_aktif = %s;
        ''',(fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, id_mahasiswa_aktif))
            
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('mahasiswaaktif'))
    
    return render_template('inputdata_alumni_mahasiswa/alumnimahasiswa.html')   


#--IMPORT--IMPORT--IMPORT--#
@app.route("/uploadFiles_aktif", methods=['POST'])
@logged_in
def uploadFiles_aktif():
      # get the uploaded file
      uploaded_file = request.files['file']
      if uploaded_file.filename != '':
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
          # set the file path
           uploaded_file.save(file_path)
           parseCSV_aktif(file_path)
          # save the file 
        
      return redirect(url_for('mahasiswaaktif'))

def parseCSV_aktif(file_Path):
      # CVS Column Names
      col_names = ['id_mahasiswa_aktif','fakultas', 'program_studi', 'nim', 'nama', 'tahun_angkatan', 'jenis_kelamin', 'ips1', 'ips2', 'ips3', 'ips4', 'ips5', 'ips6', 'ipk', 'sumber_biaya', 'ket_jalur_masuk', 'sekolah_asal']
      # Use Pandas to parse the CSV file
      csvData = pd.read_csv(file_Path,names=col_names)
      # Loop through the Rows
      #for i,row in csvData.fillna(csvData.mean()).iterrows():
      for i,row in csvData.fillna(0).iterrows():
             sql = "INSERT INTO data_mahasiswa_aktif (id_mahasiswa_aktif, fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
             value = (row['id_mahasiswa_aktif'],row['fakultas'],row['program_studi'],row['nim'],row['nama'],row['tahun_angkatan'],row['jenis_kelamin'],row['ips1'],row['ips2'],row['ips3'],row['ips4'],row['ips5'],row['ips6'],row['ipk'],row['sumber_biaya'],row['ket_jalur_masuk'],row['sekolah_asal'])
             mycursor.execute(sql, value)
             mydb.commit()
             print(i,row['id_mahasiswa_aktif'],row['fakultas'],row['program_studi'],row['nim'],row['nama'],row['tahun_angkatan'],row['jenis_kelamin'],row['ips1'],row['ips2'],row['ips3'],row['ips4'],row['ips5'],row['ips6'],row['ipk'],row['sumber_biaya'],row['ket_jalur_masuk'],row['sekolah_asal'])

#--RESET-RESET-RESET-#
@app.route('/resetdataaktif', methods = ['GET'])
@logged_in
def resetdataaktif():
    cur = mysql.connection.cursor()
    cur.execute ("TRUNCATE TABLE data_mahasiswa_aktif")
    mysql.connection.commit()
    return redirect(url_for('mahasiswaaktif'))





    ###--OPERASI PADA MENU INPUT DATA USER--###
    ##########--DATA USER LOGIN--##########

@app.route("/datauser")
@logged_in
def datauser():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT * FROM users ")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('inputdata_user_login/datauser.html', menu='datauser', data = data )

@app.route("/forminputdatauser")    #koneksi ke form input data user
@logged_in
def forminputdatauser():
    return render_template('inputdata_user_login/forminputdatauser.html',menu='inputdata',submenu='datauser')

#--ADD--TAMBAH--ADD--#

@app.route("/add_datauser", methods=["POST"])    #route simpan data ke form input data user
@logged_in
def add_datauser():
 
    if request.method == 'POST':
        flash("Data Inserted Successfully") #tidak berfungsi
        id_data = request.form['id_users']
        nama = request.form['nama']
        nip = request.form['nip']
        jenis_kelamin = request.form['jenis_kelamin']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']


    cur = mysql.connection.cursor()   
    cur.execute("INSERT INTO users (id_users,nama,nip,jenis_kelamin,fakultas,program_studi,username,password,level) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id_data,nama,nip,jenis_kelamin,fakultas,program_studi,username,password,level))  
    mysql.connection.commit()
    return redirect(url_for('datauser'))

#--DELETE--HAPUS--DELETE--#

@app.route('/delete3/<string:id_data>', methods = ['GET'])
@logged_in
def delete3(id_data):
    cur = mysql.connection.cursor()
    cur.execute ("DELETE FROM users WHERE id_users=%s", [id_data])
    mysql.connection.commit()
    return redirect(url_for('datauser'))

#--EDIT--EDIT--EDIT--#

@app.route('/update3',methods=['GET','POST'])
@logged_in
def update3():

    if request.method == 'POST':
        id_data = request.form['id_users']
        nama = request.form['nama']
        nip = request.form['nip']
        jenis_kelamin = request.form['jenis_kelamin']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        username = request.form['username']
        password = request.form['password']
        level = request.form['level']

        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE users
               SET nama=%s, nip=%s, jenis_kelamin=%s, fakultas=%s, program_studi=%s, username=%s, password=%s, level=%s
               WHERE id_users=%s
            """, (nama, nip, jenis_kelamin, fakultas, program_studi, username, password, level, id_data ))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('datauser'))


#--IMPORT--IMPORT--IMPORT--#
@app.route("/uploadFiles_users", methods=['POST'])
@logged_in
def uploadFiles_users():
      # get the uploaded file
      uploaded_file = request.files['file']
      if uploaded_file.filename != '':
           file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
          # set the file path
           uploaded_file.save(file_path)
           parseCSV_users(file_path)
          # save the file 
        
      return redirect(url_for('inputdatauser'))

def parseCSV_users(file_Path):
      # CVS Column Names
      col_names = ['id_users','nama','nip','jenis_kelamin','fakultas','program_studi','username','password','level']
      # Use Pandas to parse the CSV file
      csvData = pd.read_csv(file_Path,names=col_names)
      # Loop through the Rows
      for i,row in csvData.iterrows():
             sql = "INSERT INTO users (id_users, nama, nip, jenis_kelamin, fakultas, program_studi, username, password, level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
             value = (row['id_users'],row['name'],row['nip'],row['jenis_kelamin'],row['fakultas'],row['program_studi'],row['username'],row['password'],row['level'])
             mycursor.execute(sql, value)
             mydb.commit()
             print(i,row['id_users'],row['name'],row['nip'],row['jenis_kelamin'],row['fakultas'],row['program_studi'],row['username'],row['password'],row['level'])


#--RESET-RESET-RESET-#
@app.route('/resetdatauser', methods = ['GET'])
@logged_in
def resetdatauser():
    cur = mysql.connection.cursor()
    cur.execute ("TRUNCATE TABLE users")
    mysql.connection.commit()
    return redirect(url_for('inputdatauser'))







    ###--OPERASI PADA MENU TRAINING DATA (MODEL)--###
        ##########--DATA TRAINING--##########


@app.route("/modeltrainingdata")
@logged_in
def modeltrainingdata():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT hasil_training.id_data, hasil_training.lama_studi_MLR, hasil_training.lama_studi_ANN, data_actual.lama_studi FROM hasil_training INNER JOIN data_actual ON hasil_training.id_data = data_actual.id_data")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('modeltrainingdata/modeltrainingdata.html', data = data )

@app.route("/hasilmodel")    #koneksi ke form input data training
@logged_in
def hasilmodel():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT hasil_training.id_data, data_actual.lama_studi, hasil_training.lama_studi_MLR, hasil_training.lama_studi_ANN FROM hasil_training INNER JOIN data_actual ON hasil_training.id_data = data_actual.id_data")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('modeltrainingdata/hasilmodel.html', data = data)

#--ADD--TAMBAH--ADD--#

@app.route("/add_datamodel", methods=["POST"])    #route simpan data ke form input data training
@logged_in
def add_datamodel():
 
    if request.method == 'POST':
        flash("Data Inserted Successfully") #tidak berfungsi
        id_training = request.form['id_training']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        nim = request.form['nim']
        nama = request.form['nama']
        tahun_angkatan = request.form['tahun_angkatan']
        jenis_kelamin = request.form['jenis_kelamin']
        ips1 = request.form['ips1']
        ips2 = request.form['ips2']
        ips3 = request.form['ips3']
        ips4 = request.form['ips4']
        ips5 = request.form['ips5']
        ips6 = request.form['ips6']
        ipk = request.form['ipk']
        sumber_biaya = request.form['sumber_biaya']
        ket_jalur_masuk = request.form['ket_jalur_masuk']
        sekolah_asal = request.form['sekolah_asal']
        status_kelulusan = request.form['status_kelulusan']

    cur = mysql.connection.cursor()   
    cur.execute("INSERT INTO data_training (id_training, fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, status_kelulusan) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id_training, fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, status_kelulusan)) 
    mysql.connection.commit()
    return redirect(url_for('modeltrainingdata'))

#--DELETE--HAPUS--DELETE--#

@app.route('/deletedatamodel/<string:id_data>', methods = ['GET'])
@logged_in
def deletedatamodel(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM data_training WHERE id_training=%s", [id_data])
    mysql.connection.commit()
    return redirect(url_for('modeltrainingdata'))

#--EDIT--EDIT--EDIT--#

@app.route('/updatedatamodel',methods=['GET','POST'])
@logged_in
def updatedatamodel():

    if request.method == 'POST':
        id_data = request.form['id_training']
        fakultas = request.form['fakultas']
        program_studi = request.form['program_studi']
        nim = request.form['nim']
        nama = request.form['nama']
        tahun_angkatan = request.form['tahun_angkatan']
        jenis_kelamin = request.form['jenis_kelamin']
        ips1 = request.form['ips1']
        ips2 = request.form['ips2']
        ips3 = request.form['ips3']
        ips4 = request.form['ips4']
        ips5 = request.form['ips5']
        ips6 = request.form['ips6']
        ipk = request.form['ipk']
        sumber_biaya = request.form['sumber_biaya']
        ket_jalur_masuk = request.form['ket_jalur_masuk']
        sekolah_asal = request.form['sekolah_asal']
        status_kelulusan = request.form['status_kelulusan']

        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE data_training
               SET fakultas=%s, program_studi=%s, nim=%s, nama=%s, tahun_angkatan=%s, jenis_kelamin=%s, ips1=%s, ips2=%s, ips3=%s, ips4=%s, ips5=%s, ips6=%s, ipk=%s, sumber_biaya=%s, ket_jalur_masuk=%s, sekolah_asal=%s, status_kelulusan=%s
               WHERE id_training=%s
            """, (fakultas, program_studi, nim, nama, tahun_angkatan, jenis_kelamin, ips1, ips2, ips3, ips4, ips5, ips6, ipk, sumber_biaya, ket_jalur_masuk, sekolah_asal, status_kelulusan, id_data, ))
        flash("Data Updated Successfully")
        mysql.connection.commit()
        return redirect(url_for('modeltrainingdata'))

#--IMPORT--IMPORT--IMPORT--#
@app.route("/uploadFilesmodel", methods=['POST'])
@logged_in
def uploadFilesmodel():
      # get the uploaded file
      uploaded_file = request.files['file']
      if uploaded_file.filename != '':
            file_training = os.path.join(app.config['UPLOAD_DATATRAINING'], uploaded_file.filename)
            # set the file path
            uploaded_file.save(file_training)
            # save the file 
        
            # CVS Column Names
            col_names = ['id_training','fakultas', 'program_studi', 'nim', 'nama', 'tahun_angkatan', 'jenis_kelamin', 'ips1', 'ips2', 'ips3', 'ips4', 'ips5', 'ips6', 'ipk', 'sumber_biaya', 'ket_jalur_masuk', 'sekolah_asal','lama_studi', 'status_kelulusan']
            
            # Use Pandas to parse the CSV file
            csv_training = pd.read_csv(file_training,names=col_names)
            
            # integrasi data
            csv_training.drop(columns=['id_training','nama','fakultas','program_studi','nim','tahun_angkatan','status_kelulusan'], axis = 0, inplace = True)
            
            #TRANSFORMASI DATA
            #mengubah kategori ke numerik 
            data2 = ['sumber_biaya']
            def biaya(x):
                return x.map({"Reguler": 1, "Bidikmisi": 0})
            csv_training[data2] = csv_training[data2].apply(biaya)

            data3 = ['jenis_kelamin']
            def jeniskelamin(x):
                return x.map({"Perempuan": 1, "Laki-Laki": 0})
            csv_training[data3] = csv_training[data3].apply(jeniskelamin)

            data4 = ['ket_jalur_masuk']
            def jalurmasuk(x):
                return x.map({"SNMPTN": 0, "SBMPTN": 1, "SM": 2})
            csv_training[data4] = csv_training[data4].apply(jalurmasuk)

            data5 = ['sekolah_asal']
            def asalsekolah(x):
                return x.map({"SMA": 0, "SMK": 1, "MA": 2})
            csv_training[data5] = csv_training[data5].apply(asalsekolah)
            
            #MENANGANI NILAI KOSONG PADA (NaN)PADA ATRIBUT
            from sklearn.impute import SimpleImputer
            #Ganti NaN dengan mean
            imputer = SimpleImputer(missing_values=np.NaN,strategy='mean')
            imputer = imputer.fit_transform(csv_training.values.reshape(-1,1))[:,:]

            # memilih variabel x dan y
            X = csv_training.iloc[:,:-1]
            y = csv_training.iloc[:,-1]

            #membagi jumlah data menjadi data training dan testing
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state=1)

            jml_total_data = len(csv_training)
            jml_data_Xtrain = len(X_train)
            jml_data_Xtest =len(X_test)

            # ALGORITMA MLR
            model_mlr = LinearRegression()
            model_mlr.fit(X_train, y_train)
            y_pred_mlr = model_mlr.predict(X_test)

            # EVALUASI PENGUJIAN PREDIKSI MLR
            #MAE_mlr = metrics.mean_absolute_error(y_test, y_pred_mlr)
            MAPE_mlr = metrics.mean_absolute_percentage_error(y_test, y_pred_mlr)*100
            MSE_mlr = metrics.mean_squared_error(y_test, y_pred_mlr)
            RMSE_mlr = np.sqrt(metrics.mean_squared_error(y_test, y_pred_mlr))
            #R2_mlr = metrics.r2_score(y_test, y_pred_mlr)

            # ALGORITMA ANN
            from sklearn.neural_network import MLPRegressor
            model_ann = MLPRegressor(hidden_layer_sizes=(10), activation='relu', solver='adam', learning_rate_init = 0.001, max_iter=1000, random_state=1).fit(X_train, y_train)
            y_pred_ann = model_ann.predict(X_test)

            # EVALUASI PENGUJIAN PREDIKSI ANN
            #MAE_ann = metrics.mean_absolute_error(y_test, y_pred_ann)
            MAPE_ann = metrics.mean_absolute_percentage_error(y_test, y_pred_ann)*100
            MSE_ann = metrics.mean_squared_error(y_test, y_pred_ann)
            RMSE_ann = np.sqrt(metrics.mean_squared_error(y_test, y_pred_ann))
            #R2_ann = metrics.r2_score(y_test, y_pred_ann)

            # SAVE DATA KE DATABASE
            y_pred_hasil = pd.DataFrame({'lama_studi_MLR':y_pred_mlr.flatten(), 'lama_studi_ANN':y_pred_ann.flatten()})
            y_pred_hasil.to_csv("data_hasil_training.csv")
            
            data_actual = y_test
            data_actual.to_csv("data_actual.csv")

            # CVS Column Names
            col_names = ['lama_studi_ANN','lama_studi_MLR']
            # Use Pandas to parse the CSV file
            csvPrediksi = pd.read_csv('data_hasil_training.csv',names=col_names)
            # Loop through the Rows
            for i,row in csvPrediksi.iterrows():
                    sql = "INSERT INTO hasil_training (lama_studi_ANN, lama_studi_MLR) VALUES (%s, %s)"
                    value = (row['lama_studi_ANN'],row['lama_studi_MLR'])
                    mycursor.execute(sql, value)
                    mydb.commit()
                    print(i,row['lama_studi_ANN'],row['lama_studi_MLR'])
            
            # CVS Column Names
            col_names = ['lama_studi']
            # Use Pandas to parse the CSV file
            csvPrediksi1 = pd.read_csv('data_actual.csv',names=col_names)
            # Loop through the Rows
            for i,row in csvPrediksi1.iterrows():
                    sql = "INSERT INTO data_actual (lama_studi) VALUES (%s)"
                    value = (row['lama_studi'])
                    mycursor.execute(sql, (value,)) 
                    mydb.commit()
                    print(i,row['lama_studi'])

            return render_template('modeltrainingdata/modeltrainingdata.html', y_pred_mlr = y_pred_mlr, MAPE_mlr = MAPE_mlr, MSE_mlr = MSE_mlr, RMSE_mlr = RMSE_mlr,
            y_pred_ann = y_pred_ann, MAPE_ann = MAPE_ann, MSE_ann = MSE_ann, RMSE_ann = RMSE_ann, jml_total_data = jml_total_data, 
            jml_data_Xtrain = jml_data_Xtrain, jml_data_Xtest = jml_data_Xtest)


#--RESET-RESET-RESET-#
@app.route('/resetdatamodel', methods = ['GET'])
@logged_in
def resetdatamodel():
    cur = mysql.connection.cursor()
    cur.execute ("TRUNCATE TABLE hasil_training")
    cur.execute ("TRUNCATE TABLE data_actual")
    mysql.connection.commit()
    return redirect(url_for('modeltrainingdata'))




             ###-- DASHBOARD DOSEN --###
    ##########--DATA ALUMNI MAHASISWA--##########


@app.route("/alumnimahasiswa_DD")
@logged_in
def alumnimahasiswa_DD():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT * FROM data_mahasiswa_alumni ")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('isi_dashboard_dosen/data_alumni_mahasiswa/alumnimahasiswa_DD.html', data = data )

            ###-- DASHBOARD DOSEN --###
    ##########--DATA MAHASISWA AKTIF--##########

@app.route("/mahasiswaaktif_DD")
@logged_in
def mahasiswaaktif_DD():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT * FROM data_mahasiswa_aktif ")  
    data = cur.fetchall()                  
    cur.close()
    return render_template('isi_dashboard_dosen/data_mahasiswa_aktif/mahasiswaaktif_DD.html', data = data )

# Menu Data Prediksi
@app.route("/data_prediksi_DD")
@logged_in
def data_prediksi_DD():
    cur = mysql.connection.cursor()            
    cur.execute("SELECT data_prediksi.id, data_prediksi.fakultas, data_prediksi.program_studi, data_prediksi.nim, data_prediksi.nama, data_prediksi.jenis_kelamin, data_prediksi.tahun_angkatan, data_prediksi.ips1, data_prediksi.ips2, data_prediksi.ips3, data_prediksi.ips4, data_prediksi.ips5, data_prediksi.ips6, data_prediksi.ipk, data_prediksi.sumber_biaya, data_prediksi.ket_jalur_masuk, data_prediksi.sekolah_asal, hasil_prediksi.lama_studi_MLR, hasil_prediksi.lama_studi_ANN FROM data_prediksi INNER JOIN hasil_prediksi ON data_prediksi.id=hasil_prediksi.id")
    data = cur.fetchall()                  
    cur.close()
    return render_template('isi_dashboard_dosen/data_prediksi/data_prediksi_DD.html', data = data )

# Menu Algoritma Prediksi
@app.route('/algoritmaPrediksi_DD')
@logged_in
def algoritmaPrediksi_DD():
        return render_template('isi_dashboard_dosen/algoritma_prediksi/algoritmaPrediksi_DD.html')


if __name__ == "__main__":
    app.run(debug=True)



