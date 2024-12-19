#Project Flask MVC

import os
import sys
import subprocess

def activate_venv():
    venv_path = os.path.join(os.path.dirname(__file__), '.venv')
    if sys.platform == 'win32':
        activate_script = os.path.join(venv_path, 'Scripts', 'activate')
    else:
        activate_script = os.path.join(venv_path, 'bin', 'activate')
    
    if os.path.exists(activate_script):
        if sys.platform == 'win32':
            os.system(f'call {activate_script}')
        else:
            os.system(f'source {activate_script}')

# Aktifkan venv
activate_venv()

#Project Flask MVC

from project import app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
