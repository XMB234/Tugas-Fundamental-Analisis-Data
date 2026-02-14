# Dicoding Collection Dashboard
## Setup Environment - Anaconda

```bash
# Membuat environment conda dengan nama 'myenv' dan Python 3.13
conda create --name myenv python=3.13

# Mengaktifkan environment 'myenv'
conda activate myenv

# Menginstal semua package dari file requirements.txt
pip install -r requirements.txt

# Menginisialisasi conda agar bisa digunakan di terminal (PowerShell/VS Code)
conda init
```

## Run steamlit app
```bash
python -m streamlit run dashboard/app.py
#atau
streamlit run .\dashboard\app.py
```
