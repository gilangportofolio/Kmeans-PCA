from flask import Flask, request, redirect, url_for, send_file, render_template
import pandas as pd
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16MB upload

# Tambahkan secret key untuk session
app.secret_key = os.urandom(24)  # Generate random secret key
# atau bisa juga menggunakan string tetap:
# app.secret_key = 'your-secret-key-here'  

# Pastikan folder uploads ada
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Buat template dataset
def create_template_dataset():
    template_data = {
        'Sasaran': [
            'Kunjungan Wisman_2020',
            'Kunjungan Wisman_2021',
            'Kunjungan Wisman_2022',
            'Tingkat Hunian Kamar (%)_2020',
            'Tingkat Hunian Kamar (%)_2021',
            'Tingkat Hunian Kamar (%)_2022'
        ],
        'Januari': [2285.0, 3112.0, 4037.0, '', '', ''],
        'Februari': [2045.0, 2611.0, 3501.0, '', '', ''],
        'Maret': [2237.0, 2728.0, 5123.0, '', '', ''],
        'April': [2021.0, 3153.0, 6250.0, '', '', ''],
        'Mei': [1608.0, 2722.0, 7032.0, '', '', ''],
        'Juni': [2202.0, 3328.0, 6801.0, '', '', ''],
        'Juli': [2228.0, 2565.0, 7200.0, '', '', ''],
        'Agustus': [2293.0, 3495.0, 7400.0, '', '', ''],
        'September': [1737.0, 3495.0, 7800.0, 28.0, 38.0, 50.26],
        'Oktober': [1587.0, 3366.0, 8050.0, '', '', ''],
        'November': [1708.0, 2526.0, 8800.0, '', '', ''],
        'Desember': [2295.0, 2971.0, 4258.0, '', '', ''],
        'Total': [24246.0, 36072.0, 76252.0, 28.0, 38.0, 50.26],
        'Kumulatif': [24246.0, 60318.0, 136570.0, 136598.0, 136636.0, 136686.26]
    }
    return pd.DataFrame(template_data)

# Route untuk upload dan download
@app.route('/upload', methods=['GET', 'POST'])
def upload_dataset():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
            
        if file and file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'dataku4.csv')
            file.save(filepath)
            return redirect(url_for('hitungpca'))
            
    return render_template('upload.html')

@app.route('/download_format')
def download_format():
    try:
        format_path = os.path.join(app.config['UPLOAD_FOLDER'], 'format_dataset.csv')
        
        # Buat template jika belum ada
        if not os.path.exists(format_path):
            df = create_template_dataset()
            df.to_csv(format_path, index=False)
            
        return send_file(format_path,
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name='format_dataset.csv')
                        
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug print
        return str(e), 400

@app.route('/hasil_clustering')
def hasil_clustering():
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'hasil_clustering.csv')
        if not os.path.exists(filepath):
            return "File hasil clustering belum tersedia", 404
            
        return send_file(filepath,
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name='hasil_clustering.csv')
    except Exception as e:
        return str(e), 404

@app.route('/hasil_pca')
def hasil_pca():
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'hasil_pca.csv')
        if not os.path.exists(filepath):
            return "File hasil PCA belum tersedia", 404
            
        return send_file(filepath,
                        mimetype='text/csv',
                        as_attachment=True,
                        download_name='hasil_pca.csv')
    except Exception as e:
        return str(e), 404

# Import semua controller
from project.controllers.index import *
from project.controllers.klasterisasi import *
from project.controllers.pca_analysis import *
from project.controllers.data_checking import *
