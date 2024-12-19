"""
    Example Controllers
"""

from project import app
from flask import render_template
import pandas as pd
"""
    Import MOdels
from project.models.Hello import Hello
"""
#route index
@app.route('/')
@app.route('/index')
def index():
    # Baca data CSV
    df = pd.read_csv('dataku4.csv')
    datacsv = df.to_dict('records')
    return render_template('index.html', datacsv=datacsv)
