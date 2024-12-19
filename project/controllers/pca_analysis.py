from project import app
from flask import render_template, request
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import io
import base64
import warnings
warnings.filterwarnings('ignore')

def get_plot_as_base64(fig):
    """Konversi matplotlib figure ke base64 string"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def analyze_feature_contributions(X, pca, numeric_columns, input_val):
    # Hitung kontribusi setiap fitur berdasarkan loadings PCA
    feature_contributions = pd.DataFrame({
        'Bulan': numeric_columns,
        'PC1_contribution': np.abs(pca.components_[0]),
        'Data_Availability': X[numeric_columns].count() / len(X) * 100,
        'Mean_Value': X[numeric_columns].mean(),
        'Std_Value': X[numeric_columns].std()  # Tambah standar deviasi untuk melihat variasi
    })
    
    if input_val >= 2:
        feature_contributions['PC2_contribution'] = np.abs(pca.components_[1])
    
    # Interpretasi untuk setiap grafik
    interpretations = {
        'scree_plot': [],
        'biplot': [],
        'feature': []
    }
    
    # 1. Scree Plot Analysis
    variance_ratio = pca.explained_variance_ratio_
    cumulative_variance = np.cumsum(variance_ratio)
    
    interpretations['scree_plot'].append("Analisis Scree Plot:")
    for i, var in enumerate(variance_ratio):
        interpretations['scree_plot'].append(
            f"- PC{i+1}: menjelaskan {var:.2%} variasi data "
            f"(kumulatif: {cumulative_variance[i]:.2%})"
        )
    
    # 2. Biplot Analysis
    if input_val >= 2:
        pc1_loadings = pd.Series(pca.components_[0], index=numeric_columns)
        pc2_loadings = pd.Series(pca.components_[1], index=numeric_columns)
        
        # Analisis pola musiman dan tren
        interpretations['biplot'].append("Analisis Pola Data:")
        
        # Identifikasi bulan dengan nilai tinggi
        high_mean = X[numeric_columns].mean().nlargest(3)
        interpretations['biplot'].append(
            f"- Bulan dengan rata-rata kunjungan tertinggi: "
            f"{', '.join(high_mean.index)} "
            f"(rata-rata: {', '.join([f'{x:.0f}' for x in high_mean.values])})"
        )
        
        # Identifikasi bulan dengan variasi tinggi
        high_var = X[numeric_columns].std().nlargest(3)
        interpretations['biplot'].append(
            f"- Bulan dengan variasi tertinggi: "
            f"{', '.join(high_var.index)} "
            f"(std: {', '.join([f'{x:.0f}' for x in high_var.values])})"
        )
    
    # 3. Feature Contribution Analysis
    sorted_contributions = feature_contributions.sort_values('PC1_contribution', ascending=False)
    
    # Gunakan metode IQR untuk pengelompokan yang lebih robust
    q75 = sorted_contributions['PC1_contribution'].quantile(0.75)
    q25 = sorted_contributions['PC1_contribution'].quantile(0.25)
    iqr = q75 - q25
    
    # Definisikan threshold berdasarkan IQR
    high_threshold = q75 + 1.5 * iqr
    low_threshold = q25 - 1.5 * iqr
    
    # Kelompokkan berdasarkan kontribusi
    high_impact = sorted_contributions[sorted_contributions['PC1_contribution'] >= high_threshold]
    med_impact = sorted_contributions[
        (sorted_contributions['PC1_contribution'] < high_threshold) & 
        (sorted_contributions['PC1_contribution'] > low_threshold)
    ]
    low_impact = sorted_contributions[sorted_contributions['PC1_contribution'] <= low_threshold]
    
    interpretations['feature'].append("Analisis Kontribusi Bulan:")
    if not high_impact.empty:
        bulan_list = ', '.join(high_impact['Bulan'].tolist())
        interpretations['feature'].append(
            f"- Kontribusi Signifikan: {bulan_list}\n"
            f"  (rata-rata: {high_impact['Mean_Value'].mean():.0f}, "
            f"variasi: {high_impact['Std_Value'].mean():.0f})"
        )
    if not med_impact.empty:
        bulan_list = ', '.join(med_impact['Bulan'].tolist())
        interpretations['feature'].append(
            f"- Kontribusi Moderat: {bulan_list}\n"
            f"  (rata-rata: {med_impact['Mean_Value'].mean():.0f}, "
            f"variasi: {med_impact['Std_Value'].mean():.0f})"
        )
    if not low_impact.empty:
        bulan_list = ', '.join(low_impact['Bulan'].tolist())
        interpretations['feature'].append(
            f"- Kontribusi Minimal: {bulan_list}\n"
            f"  (rata-rata: {low_impact['Mean_Value'].mean():.0f}, "
            f"variasi: {low_impact['Std_Value'].mean():.0f})"
        )
    
    return interpretations, feature_contributions

@app.route('/hitungpca', methods=['POST', 'GET'])
def hitungpca():
    # Default values untuk template
    default_data = {
        'analysis_results': {'transformed_data': []},
        'feature_contributions': [],
        'scree_plot': None,
        'biplot': None,
        'scree_interpretations': [],  # Empty list instead of None
        'biplot_interpretations': [],  # Empty list instead of None
        'variance_interpretations': [],  # Empty list instead of None
        'total_variance': "0.00%"
    }

    if request.method == 'GET':
        return render_template('hitungpca.html', **default_data)

    if request.method == 'POST':
        try:
            # 1. Load dan persiapkan data
            df = pd.read_csv('project/uploads/dataku4.csv')
            numeric_columns = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            
            # 2. Preprocessing data
            X = df[numeric_columns].copy()
            
            # 3. Handle missing values berdasarkan kategori
            categories = df['Sasaran'].str.split('_').str[0].unique()
            
            for category in categories:
                cat_mask = df['Sasaran'].str.contains(category)
                cat_data = X[cat_mask].copy()
                
                if cat_data.isnull().any().any():
                    if 'Tingkat Hunian' in category:
                        # Untuk Tingkat Hunian, gunakan nilai September untuk bulan lainnya
                        sept_values = cat_data['September'].values
                        for month in numeric_columns:
                            if month != 'September':
                                X.loc[cat_mask, month] = float(sept_values[0])
                    elif 'Penumpang Speedboat' in category:
                        # Untuk Speedboat, interpolasi antara Juli dan Agustus
                        X.loc[cat_mask, 'Juli':'Agustus'] = cat_data.loc[:, 'Juli':'Agustus'].interpolate(axis=1)
                        # Gunakan mean untuk bulan lainnya
                        mean_val = cat_data.loc[:, ['Juli', 'Agustus']].mean(axis=1).values[0]
                        for month in numeric_columns:
                            if month not in ['Juli', 'Agustus']:
                                X.loc[cat_mask, month] = mean_val
                    else:
                        # Untuk kategori lain, gunakan interpolasi linear
                        X.loc[cat_mask] = cat_data.interpolate(method='linear', axis=1)
                        # Jika masih ada NaN, isi dengan forward fill dan backward fill
                        X.loc[cat_mask] = X.loc[cat_mask].fillna(method='ffill', axis=1).fillna(method='bfill', axis=1)
            
            # 4. Cek dan handle NaN values yang tersisa
            if X.isnull().any().any():
                print("Debug - Columns with NaN:", X.columns[X.isnull().any()].tolist())
                print("Debug - Rows with NaN:\n", X[X.isnull().any(axis=1)])
                
                # Gunakan SimpleImputer untuk mengisi nilai yang masih NaN
                imputer = SimpleImputer(strategy='mean')
                X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)

            # 5. Normalisasi data menggunakan MinMaxScaler
            minmax_scaler = MinMaxScaler(feature_range=(0, 1))
            X_scaled = minmax_scaler.fit_transform(X)

            # Simpan informasi scaling untuk interpretasi
            feature_ranges = pd.DataFrame({
                'min': minmax_scaler.data_min_,
                'max': minmax_scaler.data_max_,
                'range': minmax_scaler.data_range_
            }, index=numeric_columns)

            # Verifikasi hasil scaling
            scaled_df = pd.DataFrame(X_scaled, columns=numeric_columns)
            print("Range data setelah scaling:")
            print(f"Min: {scaled_df.min().min():.3f}")
            print(f"Max: {scaled_df.max().max():.3f}")

            # Tambahkan interpretasi scaling ke dalam hasil
            scaling_interpretations = []
            for col in numeric_columns:
                if feature_ranges.loc[col, 'range'] > 0:
                    scaling_interpretations.append(
                        f"Data {col}: range [{feature_ranges.loc[col, 'min']:.0f} - {feature_ranges.loc[col, 'max']:.0f}] "
                        f"dinormalisasi ke [0-1]"
                    )

            # Verifikasi tidak ada NaN sebelum PCA
            assert not np.isnan(X_scaled).any(), "Masih terdapat NaN setelah preprocessing"

            # 6. Validasi input komponen
            input_val = int(request.form.get('jumlah_komponen', 2))
            if input_val > len(numeric_columns):
                return render_template('hitungpca.html',
                    error=f"Jumlah komponen tidak boleh lebih dari {len(numeric_columns)}")
            
            # 7. Analisis PCA dan perhitungan variance
            pca = PCA(n_components=input_val)
            X_pca = pca.fit_transform(X_scaled)

            # 8. Hitung variance ratio dan cumulative variance
            variance_ratio = pca.explained_variance_ratio_
            cumulative_variance = np.cumsum(variance_ratio)
            total_var = cumulative_variance[input_val-1] if input_val > 0 else 0

            # Pastikan total_var terdefinisi untuk semua kondisi
            if total_var is None or not np.isfinite(total_var):
                total_var = 0
                print("Warning: Total variance tidak valid, menggunakan nilai default 0")

            # 9. Visualisasi
            # 9.1 Scree Plot
            fig, ax = plt.subplots(figsize=(10, 6))
            components = range(1, len(variance_ratio) + 1)
            
            ax.plot(components, variance_ratio, 'bo-', label='Individual explained variance')
            ax.plot(components, cumulative_variance, 'ro-', label='Cumulative explained variance')
            
            ax.set_xlabel('Principal Component')
            ax.set_ylabel('Explained variance ratio')
            ax.set_title('Scree Plot')
            ax.grid(True)
            ax.legend()
            
            scree_plot = get_plot_as_base64(fig)
            plt.close()
            
            # 9.2 Biplot (jika komponen >= 2)
            fig = plt.figure(figsize=(12, 8))
            
            if input_val >= 2:
                plt.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.7)
                
                for i, (x, y) in enumerate(zip(pca.components_[0], pca.components_[1])):
                    plt.arrow(0, 0, x, y, color='r', alpha=0.5)
                    plt.text(x*1.15, y*1.15, numeric_columns[i], 
                            color='r', ha='center', va='center')
                
                plt.xlabel(f'PC1 ({variance_ratio[0]:.2%} variance)')
                plt.ylabel(f'PC2 ({variance_ratio[1]:.2%} variance)')
                plt.title('PCA Biplot')
                plt.grid(True)
            
            biplot = get_plot_as_base64(fig)
            plt.close()

            # 10. Interpretasi
            interpretations = {
                'scree_plot': [],  # Interpretasi untuk Scree Plot
                'biplot': [],       # Interpretasi untuk Biplot
                'feature': []       # Interpretasi untuk Kontribusi Fitur
            }

            # 1. Interpretasi Scree Plot & Cumulative Variance
            scree_interpretations = []
            # Analisis titik siku (elbow point)
            differences = np.diff(variance_ratio)
            elbow_point = np.argmin(differences) + 1
            scree_interpretations.append(f"Berdasarkan Scree Plot, titik siku berada pada PC{elbow_point + 1}")

            # Analisis variance ratio
            for i, var in enumerate(variance_ratio):
                scree_interpretations.append(f"PC{i+1} menjelaskan {var:.2%} variasi data")

            # Analisis cumulative variance
            threshold = 0.8  # 80% threshold
            n_components_needed = np.where(cumulative_variance >= threshold)[0][0] + 1
            scree_interpretations.append(f"Diperlukan {n_components_needed} komponen untuk menjelaskan >{threshold:.0%} variasi data")

            interpretations['scree_plot'] = scree_interpretations

            # 2. Interpretasi Biplot
            if input_val >= 2:
                biplot_interpretations = []
                
                # Loading factors analysis
                pc1_loadings = pd.Series(pca.components_[0], index=numeric_columns)
                pc2_loadings = pd.Series(pca.components_[1], index=numeric_columns)
                
                # PC1 analysis
                pc1_positive = pc1_loadings[pc1_loadings > 0.3].index.tolist()
                pc1_negative = pc1_loadings[pc1_loadings < -0.3].index.tolist()
                
                if pc1_positive:
                    biplot_interpretations.append(f"PC1 berkorelasi positif kuat dengan: {', '.join(pc1_positive)}")
                if pc1_negative:
                    biplot_interpretations.append(f"PC1 berkorelasi negatif kuat dengan: {', '.join(pc1_negative)}")
                
                # PC2 analysis
                pc2_positive = pc2_loadings[pc2_loadings > 0.3].index.tolist()
                pc2_negative = pc2_loadings[pc2_loadings < -0.3].index.tolist()
                
                if pc2_positive:
                    biplot_interpretations.append(f"PC2 berkorelasi positif kuat dengan: {', '.join(pc2_positive)}")
                if pc2_negative:
                    biplot_interpretations.append(f"PC2 berkorelasi negatif kuat dengan: {', '.join(pc2_negative)}")
                
                # Cluster analysis from biplot
                if len(X_pca) > 1:
                    # Analisis pengelompokan pada biplot
                    categories = df['Sasaran'].str.split('_').str[0].unique()
                    for category in categories:
                        cat_mask = df['Sasaran'].str.contains(category)
                        cat_points = X_pca[cat_mask]
                        if len(cat_points) > 0:
                            mean_pos = cat_points.mean(axis=0)
                            biplot_interpretations.append(f"{category} cenderung berada pada posisi (PC1: {mean_pos[0]:.2f}, PC2: {mean_pos[1]:.2f})")
                
                interpretations['biplot'] = biplot_interpretations

            # Simpan hasil PCA
            pca_results = pd.DataFrame(
                X_pca,
                columns=[f'PC{i+1}' for i in range(input_val)]
            )
            pca_results['Kategori'] = df['Sasaran']
            pca_results.to_csv('project/uploads/hasil_pca.csv', index=False)
            
            # Analisis kontribusi fitur yang dinamis
            variance_interpretations, feature_contributions = analyze_feature_contributions(
                X, pca, numeric_columns, input_val
            )

            # Template data dengan nilai default
            template_data = default_data.copy()
            
            # Update template data dengan hasil analisis
            if 'pca_results' in locals():
                template_data.update({
                    'analysis_results': {
                        'transformed_data': pca_results.to_dict('records')
                    },
                    'feature_contributions': feature_contributions.to_dict('records'),
                    'scree_plot': scree_plot if 'scree_plot' in locals() else None,
                    'biplot': biplot if 'biplot' in locals() and input_val >= 2 else None,
                    'scree_interpretations': variance_interpretations['scree_plot'],
                    'biplot_interpretations': variance_interpretations['biplot'] if input_val >= 2 else [],
                    'variance_interpretations': variance_interpretations['feature'],
                    'total_variance': f'{total_var*100:.2f}%'
                })

            return render_template('hitungpca.html', **template_data)

        except Exception as e:
            print(f"Error: {str(e)}")
            return render_template('hitungpca.html', 
                                error=f"Terjadi kesalahan: {str(e)}", 
                                **default_data)

if __name__ == '__main__':
    app.run(debug=True) 