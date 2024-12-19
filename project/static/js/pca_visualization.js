function initializePCAVisualizations(pcaData) {
    // Pastikan data ada
    if (!pcaData) return;
    
    // Variance Chart
    const ctx = document.getElementById('varianceChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: pcaData.explained_variance.map((_, i) => `PC${i+1}`),
                datasets: [{
                    label: 'Explained Variance Ratio',
                    data: pcaData.explained_variance.map(v => parseFloat(v)),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }, {
                    label: 'Cumulative Variance',
                    data: pcaData.cumulative_variance.map(v => parseFloat(v)),
                    type: 'line',
                    fill: false,
                    borderColor: 'rgba(255, 99, 132, 1)',
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: function(value) {
                                return (value * 100).toFixed(0) + '%';
                            }
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Explained Variance Ratio per Component'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return (context.raw * 100).toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

// 2. Scatter Plot PC1 vs PC2
function initializeScatterPlot(components) {
    var ctx = document.getElementById("scatterPlot");
    if (!ctx) return;

    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                data: components.map(point => ({
                    x: point[0],
                    y: point[1]
                })),
                backgroundColor: 'rgba(78, 115, 223, 0.5)',
                borderColor: 'rgba(78, 115, 223, 1)',
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'First Principal Component'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Second Principal Component'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'PCA Scatter Plot'
                }
            }
        }
    });
} 