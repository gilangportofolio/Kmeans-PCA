from project import app
from flask import render_template, request, session, send_file, jsonify
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import davies_bouldin_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import warnings
import os
warnings.filterwarnings('ignore')

@app.route('/hitungcluster_kmeans', methods=['POST', 'GET'])
def hitungcluster_kmeans():
    # Definisi warna dasar untuk cluster (bisa diperluas)
    base_colors = [
        '#4e73df',  # Blue
        '#1cc88a',  # Green
        '#36b9cc',  # Cyan
        '#f6c23e',  # Yellow
        '#e74a3b',  # Red
        '#6f42c1',  # Purple
        '#fd7e14',  # Orange
        '#20c9a6',  # Teal
        '#858796',  # Gray
        '#5a5c69',  # Dark Gray
        '#2e59d9',  # Royal Blue
        '#17a673',  # Forest Green
        '#2c9faf',  # Sea Blue
        '#f4b619',  # Golden
        '#e02d1b'   # Crimson
    ]

    def get_cluster_colors(n_clusters):
        # Jika jumlah cluster melebihi warna dasar, generate warna tambahan
        if n_clusters <= len(base_colors):
            return {f'Cluster {i+1}': color 
                   for i, color in enumerate(base_colors[:n_clusters])}
        else:
            # Generate warna tambahan jika diperlukan
            import random
            extra_colors = ['#' + ''.join([random.choice('0123456789ABCDEF') 
                           for _ in range(6)]) 
                           for _ in range(n_clusters - len(base_colors))]
            all_colors = base_colors + extra_colors
            return {f'Cluster {i+1}': color 
                   for i, color in enumerate(all_colors[:n_clusters])}

    def calculate_elbow_data(X_normalized):
        wcss_data = []
        # Hitung WCSS untuk K=2 sampai K yang diminta
        k_range = range(2, requested_clusters + 1)
        
        for k in k_range:
            kmeans_temp = KMeans(n_clusters=k, random_state=42, max_iter=300)
            kmeans_temp.fit(X_normalized)
            wcss = kmeans_temp.inertia_
            
            # Hitung pengurangan WCSS
            if len(wcss_data) > 0:
                wcss_reduction = (wcss_data[-1]['wcss'] - wcss) / wcss_data[-1]['wcss'] * 100
            else:
                wcss_reduction = 0
                
            wcss_data.append({
                'k': int(k),
                'wcss': float(wcss),
                'reduction': float(wcss_reduction),
                'is_elbow': False
            })
        
        # Deteksi titik siku
        if len(wcss_data) > 1:
            # Gunakan metode second derivative untuk mendeteksi titik siku
            derivatives = []
            for i in range(1, len(wcss_data)-1):
                d1 = wcss_data[i]['wcss'] - wcss_data[i-1]['wcss']
                d2 = wcss_data[i+1]['wcss'] - wcss_data[i]['wcss']
                derivatives.append(abs(d1 - d2))
            
            if derivatives:
                elbow_idx = derivatives.index(max(derivatives))
                wcss_data[elbow_idx+1]['is_elbow'] = True
        
        return wcss_data

    if not app.secret_key:
        app.secret_key = os.urandom(24)

    if request.method == 'GET':
        return render_template('hitungcluster_kmeans.html',
                             data=[],
                             cluster_data={},
                             evaluasi={},
                             visualisasi={},
                             clusterColors=get_cluster_colors(2))

    if request.method == 'POST':
        try:
            # A. Validasi Input
            df = pd.read_csv('dataku4.csv')
            max_possible_clusters = len(df) - 1  # Maksimum cluster adalah n-1
            requested_clusters = int(request.form['jumlah_klaster'])

            # Validasi jumlah cluster
            if requested_clusters < 2:
                raise ValueError("Jumlah cluster minimal harus 2")
            
            if requested_clusters >= len(df):
                raise ValueError(f"Jumlah cluster ({requested_clusters}) tidak boleh melebihi jumlah data ({len(df)}). Maksimum cluster yang diperbolehkan: {max_possible_clusters}")

            # Generate warna sesuai jumlah cluster yang valid
            cluster_colors_dict = get_cluster_colors(requested_clusters)

            # B. Preprocessing
            numeric_columns = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            
            # Validasi data numerik
            X = df[numeric_columns].copy()
            if X.isnull().all().all():  # Jika semua data null
                raise ValueError("Tidak ada data numerik yang valid untuk clustering")

            # Handle missing values
            X = X.fillna(method='ffill')
            
            # Normalisasi
            scaler = MinMaxScaler()
            X_normalized = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

            # B. Hitung Elbow Method
            elbow_data = calculate_elbow_data(X_normalized)

            # C. K-Means dengan K yang diminta
            kmeans = KMeans(n_clusters=requested_clusters, random_state=42)
            kmeans.fit(X_normalized)

            # D. Evaluasi
            evaluasi = {
                'silhouette': {
                    'score': float(silhouette_score(X_normalized, kmeans.labels_)),
                    'samples': silhouette_samples(X_normalized, kmeans.labels_).tolist()
                },
                'davies_bouldin': float(davies_bouldin_score(X_normalized, kmeans.labels_)),
                'wcss': float(kmeans.inertia_)
            }

            # Tambahkan interpretasi Silhouette
            if evaluasi['silhouette']['score'] > 0.7:
                evaluasi['silhouette']['interpretasi'] = 'Struktur cluster sangat baik'
                evaluasi['silhouette']['color_class'] = 'success'
            elif evaluasi['silhouette']['score'] > 0.5:
                evaluasi['silhouette']['interpretasi'] = 'Struktur cluster baik'
                evaluasi['silhouette']['color_class'] = 'info'
            elif evaluasi['silhouette']['score'] > 0.25:
                evaluasi['silhouette']['interpretasi'] = 'Struktur cluster lemah'
                evaluasi['silhouette']['color_class'] = 'warning'
            else:
                evaluasi['silhouette']['interpretasi'] = 'Tidak ada struktur cluster yang jelas'
                evaluasi['silhouette']['color_class'] = 'danger'

            # E. Prepare Cluster Data
            cluster_data = []
            for i in range(requested_clusters):
                mask = kmeans.labels_ == i
                sasaran_list = df.loc[mask, 'Sasaran'].tolist()
                
                # Hitung statistik cluster
                cluster_stats = {
                    'name': f'Kelompok {i+1}',
                    'count': int(len(sasaran_list)),
                    'sasaran': sasaran_list,
                    'color': cluster_colors_dict[f'Cluster {i+1}'],
                    'color_class': ['primary', 'success', 'info', 'warning', 'danger'][i % 5],
                    'mean_value': float(X_normalized[mask].mean().mean()),
                    'min_value': float(X_normalized[mask].min().min()),
                    'max_value': float(X_normalized[mask].max().max())
                }
                
                # Tambahkan karakteristik cluster
                if cluster_stats['mean_value'] > 0.7:
                    cluster_stats['karakteristik'] = 'Tinggi'
                elif cluster_stats['mean_value'] > 0.3:
                    cluster_stats['karakteristik'] = 'Sedang'
                else:
                    cluster_stats['karakteristik'] = 'Rendah'
                
                cluster_data.append(cluster_stats)

            # F. Prepare Visualisasi Data
            visualisasi = {
                'elbow_data': elbow_data,
                'recommended_k': next((d['k'] for d in elbow_data if d.get('recommendation')), 3),
                'silhouette_data': {
                    'scores': evaluasi['silhouette']['samples'],
                    'labels': kmeans.labels_.tolist()
                },
                'cluster_means': [float(X_normalized[kmeans.labels_ == i].mean().mean()) 
                                for i in range(requested_clusters)]
            }

            # Simpan hasil ke session untuk download
            session['cluster_labels'] = kmeans.labels_.tolist()
            session['cluster_evaluation'] = {
                'silhouette_score': float(evaluasi['silhouette']['score']),
                'davies_bouldin': float(evaluasi['davies_bouldin']),
                'wcss': float(evaluasi['wcss']),
                'n_clusters': requested_clusters
            }

            # Simpan statistik cluster
            cluster_stats = []
            for i in range(requested_clusters):
                mask = kmeans.labels_ == i
                stats = {
                    'cluster': i,
                    'count': int(mask.sum()),
                    'mean': float(X_normalized[mask].mean().mean()),
                    'min': float(X_normalized[mask].min().min()),
                    'max': float(X_normalized[mask].max().max())
                }
                cluster_stats.append(stats)
            
            session['cluster_stats'] = cluster_stats

            return render_template('hitungcluster_kmeans.html',
                                data=df.to_dict('records'),
                                cluster_data=cluster_data,
                                evaluasi=evaluasi,
                                visualisasi=visualisasi,
                                clusterColors=cluster_colors_dict)

        except ValueError as ve:
            return render_template('hitungcluster_kmeans.html',
                                error=str(ve),
                                data=[],
                                cluster_data=[],
                                evaluasi={},
                                visualisasi={},
                                clusterColors=get_cluster_colors(2))
        except Exception as e:
            return render_template('hitungcluster_kmeans.html',
                                error=f"Terjadi kesalahan: {str(e)}",
                                data=[],
                                cluster_data=[],
                                evaluasi={},
                                visualisasi={},
                                clusterColors=cluster_colors_dict)

@app.route('/download_cluster')
def download_cluster():
    try:
        # Ambil data cluster terakhir dari session
        if 'cluster_labels' not in session:
            return jsonify({
                'success': False,
                'error': 'Tidak ada data cluster yang tersedia'
            }), 404

        # Baca data asli
        df = pd.read_csv('project/uploads/dataku4.csv')
        
        # Tambahkan kolom cluster
        df['Cluster'] = session['cluster_labels']
        
        # Buat statistik cluster
        cluster_stats = pd.DataFrame(session.get('cluster_stats', []))
        
        # Buat file Excel dengan multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Data dengan label cluster
            df.to_excel(writer, sheet_name='Data_Dengan_Cluster', index=False)
            
            # Sheet 2: Statistik cluster
            if not cluster_stats.empty:
                cluster_stats.to_excel(writer, sheet_name='Statistik_Cluster', index=False)
            
            # Sheet 3: Evaluasi cluster
            if 'cluster_evaluation' in session:
                eval_df = pd.DataFrame([session['cluster_evaluation']])
                eval_df.to_excel(writer, sheet_name='Evaluasi_Cluster', index=False)
            
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='hasil_cluster_kmeans.xlsx'
        )
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)