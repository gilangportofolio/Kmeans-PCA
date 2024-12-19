from project import app
from flask import render_template, jsonify, request
import pandas as pd
import numpy as np
from pathlib import Path
import os

# Pindahkan fungsi ke scope global
def detect_consecutive_same(row, threshold=3):
    """
    Fungsi untuk mendeteksi data berurutan yang sama
    Args:
        row: Series pandas berisi data satu baris
        threshold: minimal jumlah data berurutan yang sama
    Returns:
        list: grup data yang berurutan dan sama
    """
    bulan_cols = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    
    same_value_groups = []
    current_value = None
    current_count = 0
    current_cols = []
    
    for col in bulan_cols:
        if pd.isna(row[col]):
            continue
            
        if row[col] == current_value:
            current_count += 1
            current_cols.append(col)
        else:
            if current_count >= threshold:
                same_value_groups.append({
                    'value': current_value,
                    'count': current_count,
                    'columns': current_cols
                })
            current_value = row[col]
            current_count = 1
            current_cols = [col]
    
    # Cek grup terakhir
    if current_count >= threshold:
        same_value_groups.append({
            'value': current_value,
            'count': current_count,
            'columns': current_cols
        })
        
    return same_value_groups

@app.route('/check_data', methods=['GET'])
def check_data():
    try:
        file_path = os.path.join('project', 'uploads', 'dataku4.csv')
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File tidak ditemukan di {file_path}")
            
        df = pd.read_csv(file_path)
        df_clean = handle_missing_values(df)
        
        # Analisis Data Dinamis
        data_analysis = {
            'info_umum': {
                'jumlah_baris': len(df),
                'jumlah_kolom': len(df.columns),
                'kolom_numerik': [col for col in df.columns if col not in ['Sasaran', 'Total', 'Kumulatif']],
                'ukuran_data': f"{Path(file_path).stat().st_size / 1024:.2f} KB"
            },
            'missing_values': {
                'total': int(df.isna().sum().sum()),
                'per_kolom': df.isna().sum().to_dict()
            }
        }
        
        # Deteksi Masalah Data Spesifik
        masalah_data = []
        bulan_cols = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                      'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        
        for idx, row in df.iterrows():
            missing_bulan = []
            for bulan in bulan_cols:
                if pd.isna(row[bulan]):
                    missing_bulan.append(bulan)
            
            if missing_bulan:
                masalah_data.append({
                    'sasaran': row['Sasaran'],
                    'detail': f"Data kosong pada bulan: {', '.join(missing_bulan)}"
                })
        
        # Filter hanya baris yang memiliki missing values
        mask_missing = df.isna().any(axis=1)
        df_missing = df[mask_missing]
        df_clean_missing = df_clean[mask_missing]
        
        # Perbandingan sebelum dan sesudah cleaning
        comparison = {
            'original': df_missing.to_dict('records'),
            'cleaned': df_clean_missing.to_dict('records'),
            'changes': {
                'total_missing_before': int(df.isna().sum().sum()),
                'total_missing_after': int(df_clean.isna().sum().sum()),
                'changed_cells': int((df != df_clean).sum().sum()),
                'jumlah_sasaran_bermasalah': len(masalah_data)
            }
        }

        return render_template('check_data.html',
                             analysis=data_analysis,
                             masalah=masalah_data,
                             comparison=comparison,
                             zip=zip)

    except FileNotFoundError as e:
        return jsonify({
            'error': 'File tidak ditemukan',
            'detail': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'error': str(e),
            'trace': str(e.__traceback__.tb_next)
        }), 500

@app.route('/handle_missing', methods=['POST'])
def process_missing_data():
    try:
        # Baca file original
        input_path = os.path.join('project', 'uploads', 'dataku4.csv')
        df = pd.read_csv(input_path)
        
        # Ambil metode yang dipilih user
        method = request.form.get('method', 'interpolate')
        save_option = request.form.get('save_option', 'new')
        
        # Validasi metode
        valid_methods = ['mean', 'median', 'interpolate', 'ffill', 'unique']
        if method not in valid_methods:
            raise ValueError(f"Metode {method} tidak valid. Pilih salah satu dari {valid_methods}")
        
        # Proses data dengan metode yang dipilih
        df_clean = handle_missing_values(df, method=method)
        
        # Simpan hasil
        if save_option == 'replace':
            df_clean.to_csv(input_path, index=False)
            message = f'Data berhasil dibersihkan menggunakan metode {method} dan menggantikan file asli'
        else:
            output_path = os.path.join('project', 'uploads', f'dataku4_clean_{method}.csv')
            df_clean.to_csv(output_path, index=False)
            message = f'Data berhasil dibersihkan menggunakan metode {method} dan disimpan sebagai {output_path}'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def handle_missing_values(df, method='interpolate'):
    df_clean = df.copy()
    bulan_cols = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    if method == 'unique':
        print("\nMemproses dengan metode unique...")
        
        # Persentase perubahan yang akan diterapkan
        variations = {
            1: 1.05,  # +5%
            2: 1.10,  # +10%
            3: 1.15,  # +15%
            4: 1.20   # +20%
        }
        
        for idx, row in df_clean.iterrows():
            print(f"\nMengecek baris {idx}: {row['Sasaran']}")
            
            # Cek setiap 3 bulan berurutan
            for i in range(len(bulan_cols)-2):
                val1 = row[bulan_cols[i]]
                val2 = row[bulan_cols[i+1]]
                val3 = row[bulan_cols[i+2]]
                
                # Jika ketiga nilai sama dan bukan NaN
                if val1 == val2 == val3 and not pd.isna(val1):
                    print(f"Menemukan 3 nilai sama berurutan: {val1} pada bulan {bulan_cols[i]}, {bulan_cols[i+1]}, {bulan_cols[i+2]}")
                    
                    # Terapkan variasi
                    df_clean.at[idx, bulan_cols[i]] = val1 * variations[1]
                    df_clean.at[idx, bulan_cols[i+1]] = val1 * variations[2]
                    df_clean.at[idx, bulan_cols[i+2]] = val1 * variations[3]
                    
                    print(f"Nilai diubah menjadi:")
                    print(f"{bulan_cols[i]}: {df_clean.at[idx, bulan_cols[i]]}")
                    print(f"{bulan_cols[i+1]}: {df_clean.at[idx, bulan_cols[i+1]]}")
                    print(f"{bulan_cols[i+2]}: {df_clean.at[idx, bulan_cols[i+2]]}")
    
    elif method == 'mean':
        df_clean[bulan_cols] = df_clean[bulan_cols].fillna(df_clean[bulan_cols].mean())
    
    elif method == 'median':
        df_clean[bulan_cols] = df_clean[bulan_cols].fillna(df_clean[bulan_cols].median())
    
    elif method == 'interpolate':
        df_clean[bulan_cols] = df_clean[bulan_cols].interpolate(method='linear', axis=1)
    
    elif method == 'ffill':
        df_clean[bulan_cols] = df_clean[bulan_cols].fillna(method='ffill', axis=1)

    # Hitung ulang Total dan Kumulatif
    df_clean['Total'] = df_clean[bulan_cols].sum(axis=1)
    df_clean['Kumulatif'] = df_clean['Total'].cumsum()

    return df_clean

# Tambahkan route baru untuk preview
@app.route('/preview_cleaning', methods=['POST'])
def preview_cleaning():
    try:
        file_path = os.path.join('project', 'uploads', 'dataku4.csv')
        if not os.path.exists(file_path):
            raise FileNotFoundError("File tidak ditemukan")
            
        df = pd.read_csv(file_path)
        method = request.form.get('method', 'interpolate')
        
        print(f"Memproses preview dengan metode: {method}")
        df_clean = handle_missing_values(df, method=method)
        
        # Ambil 5 baris pertama untuk preview
        preview_data = {
            'original': df.head().to_dict('records'),
            'cleaned': df_clean.head().to_dict('records')
        }
        
        print("Preview berhasil dibuat")
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        print(f"Error saat preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500