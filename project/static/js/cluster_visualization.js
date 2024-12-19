document.addEventListener('DOMContentLoaded', function() {
    // Inisialisasi tombol download jika ada
    const downloadBtn = document.querySelector('a[href="/download_cluster"]');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Tampilkan loading indicator
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
            downloadBtn.classList.add('disabled');

            // Lakukan request download
            fetch('/download_cluster')
                .then(response => {
                    if (!response.ok) throw new Error('Download failed');
                    return response.blob();
                })
                .then(blob => {
                    // Buat link untuk download
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'hasil_cluster_kmeans.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    // Reset tombol
                    downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Hasil';
                    downloadBtn.classList.remove('disabled');
                })
                .catch(error => {
                    console.error('Download error:', error);
                    alert('Gagal mengunduh file. Silakan coba lagi.');
                    
                    // Reset tombol
                    downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Hasil';
                    downloadBtn.classList.remove('disabled');
                });
        });
    }
});

// Fungsi untuk inisialisasi semua visualisasi
function initializeVisualizations(clusterData, evaluasiData, visualisasiData) {
    initializePieChart(clusterData);
    initializeElbowChart(visualisasiData.elbow_data);
    initializeSilhouetteChart(evaluasiData.silhouette);
    initializeDistribusiChart(clusterData);
}

// 1. Pie Chart untuk distribusi cluster
function initializePieChart(clusterData) {
    var ctx = document.getElementById("clusterPieChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(clusterData).map(key => 
                `${key}`
            ),
            datasets: [{
                data: Object.values(clusterData).map(val => val.count),
                backgroundColor: Object.values(clusterData).map(val => val.color),
                hoverBorderColor: "rgba(234, 236, 244, 1)"
            }]
        },
        options: {
            maintainAspectRatio: false,
            tooltips: {
                backgroundColor: "rgb(255,255,255)",
                bodyFontColor: "#858796",
                borderColor: '#dddfeb',
                borderWidth: 1,
                xPadding: 15,
                yPadding: 15,
                displayColors: false,
                caretPadding: 10,
                callbacks: {
                    label: function(tooltipItem, data) {
                        var dataset = data.datasets[tooltipItem.datasetIndex];
                        var total = dataset.data.reduce((a, b) => a + b, 0);
                        var currentValue = dataset.data[tooltipItem.index];
                        var percentage = Math.round((currentValue/total) * 100);
                        return `${data.labels[tooltipItem.index]}: ${currentValue} sasaran (${percentage}%)`;
                    }
                }
            },
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    padding: 20,
                    boxWidth: 12
                }
            },
            cutoutPercentage: 70
        }
    });
}

// 2. Elbow Method Chart
function initializeElbowChart(elbowData) {
    var ctx = document.getElementById("elbowChart");
    if (!ctx) return;

    // Set ukuran canvas yang tetap
    ctx.height = 250;

    const labels = elbowData.map(d => `K=${d.k}`);
    const wcssValues = elbowData.map(d => d.wcss);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'WCSS',
                data: wcssValues,
                borderColor: 'rgba(78, 115, 223, 1)',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                pointRadius: (context) => {
                    const index = context.dataIndex;
                    return elbowData[index].is_elbow ? 8 : 6;
                },
                pointBackgroundColor: (context) => {
                    const index = context.dataIndex;
                    return elbowData[index].is_elbow ? '#1cc88a' : 'rgba(78, 115, 223, 1)';
                },
                pointBorderColor: (context) => {
                    const index = context.dataIndex;
                    return elbowData[index].is_elbow ? '#1cc88a' : 'rgba(78, 115, 223, 1)';
                },
                pointStyle: (context) => {
                    const index = context.dataIndex;
                    return elbowData[index].is_elbow ? 'star' : 'circle';
                },
                pointBorderWidth: 2,
                lineTension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,  // Rasio lebar:tinggi = 2:1
            layout: {
                padding: {
                    left: 10,
                    right: 25,
                    top: 25,
                    bottom: 0
                }
            },
            scales: {
                xAxes: [{
                    gridLines: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: 7
                    }
                }],
                yAxes: [{
                    ticks: {
                        maxTicksLimit: 5,
                        padding: 10,
                        callback: function(value) {
                            return value.toFixed(2);
                        }
                    },
                    gridLines: {
                        color: "rgb(234, 236, 244)",
                        zeroLineColor: "rgb(234, 236, 244)",
                        drawBorder: false,
                        borderDash: [2],
                        zeroLineBorderDash: [2]
                    }
                }]
            },
            legend: {
                display: false
            },
            tooltips: {
                backgroundColor: "rgb(255,255,255)",
                bodyFontColor: "#858796",
                titleMarginBottom: 10,
                titleFontColor: '#6e707e',
                titleFontSize: 14,
                borderColor: '#dddfeb',
                borderWidth: 1,
                xPadding: 15,
                yPadding: 15,
                displayColors: false,
                intersect: false,
                mode: 'index',
                caretPadding: 10,
                callbacks: {
                    label: function(tooltipItem, chart) {
                        const index = tooltipItem.index;
                        const data = elbowData[index];
                        let label = `WCSS: ${data.wcss.toFixed(2)}`;
                        if (data.reduction) {
                            label += `\nPenurunan: ${data.reduction.toFixed(1)}%`;
                        }
                        if (data.is_elbow) {
                            label += '\n⭐ Titik Optimal';
                        }
                        return label;
                    }
                }
            }
        }
    });
}

// 3. Silhouette Score Visualization
function initializeSilhouetteChart(silhouetteData) {
    var ctx = document.getElementById("silhouetteChart");
    if (!ctx) return;

    // Menambahkan interpretasi warna berdasarkan score
    function getScoreColor(score) {
        if (score > 0.7) return '#1cc88a';  // Hijau - Sangat Baik
        if (score > 0.5) return '#36b9cc';  // Biru - Cukup Baik
        if (score > 0.25) return '#f6c23e'; // Kuning - Kurang Optimal
        return '#e74a3b';                   // Merah - Tidak Optimal
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Silhouette Score'],
            datasets: [{
                data: [silhouetteData.score],
                backgroundColor: getScoreColor(silhouetteData.score),
                maxBarThickness: 50
            }]
        },
        options: {
            responsive: true,
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true,
                        max: 1
                    }
                }]
            },
            tooltips: {
                callbacks: {
                    label: function(tooltipItem) {
                        return `Score: ${tooltipItem.yLabel.toFixed(3)} (${silhouetteData.interpretasi})`;
                    }
                }
            },
            legend: {
                display: false
            }
        }
    });
}

// 4. Distribusi Data dalam Cluster
function initializeDistribusiChart(clusterData) {
    var ctx = document.getElementById("distribusiChart");
    if (!ctx) return;

    const datasets = Object.entries(clusterData).map(([key, value]) => ({
        label: key,
        data: value.sasaran.map((_, idx) => value.mean_value),
        backgroundColor: value.color,
        borderColor: value.color,
        fill: false
    }));

    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            scales: {
                xAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'Rata-rata Nilai Ternormalisasi'
                    }
                }],
                yAxes: [{
                    scaleLabel: {
                        display: true,
                        labelString: 'Index Data'
                    }
                }]
            },
            tooltips: {
                callbacks: {
                    label: function(tooltipItem, data) {
                        const dataset = data.datasets[tooltipItem.datasetIndex];
                        return `${dataset.label}: ${dataset.data[tooltipItem.index].toFixed(3)}`;
                    }
                }
            }
        }
    });
} 