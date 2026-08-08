import os
import pandas as pd
from flask import Flask, render_template_string, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

app = Flask(__name__)

def bersihkan_harga(harga_str):
    try:
        if ',' in harga_str:
            harga_str = harga_str.split(',')[0]
        clean = "".join([c for c in str(harga_str) if c.isdigit()])
        return float(clean) if clean else 0.0
    except:
        return 0.0

def run_selenium_search(keyword_produk):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
    
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    
    data_hasil = []
    try:
        url = f"https://katalog.inaproc.id/search?keyword={keyword_produk}"
        driver.get(url)
        time.sleep(5)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 3);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 1.5);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        all_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]
        seen_names = set()
        keyword_exact = " ".join(keyword_produk.lower().split())
        
        for i, line in enumerate(lines):
            if re.search(r'Rp\s*[\d\.,]+', line):
                harga = line
                nama = ""
                
                for j in range(1, 5):
                    if i - j >= 0:
                        kandidat = lines[i - j]
                        kata_sampah = ['stok', 'terjual', 'lokasi', 'toko', 'tkdn', '%', 'pt.', 'cv.', 'ulasan']
                        if len(kandidat) > 5 and "Rp" not in kandidat and not any(s in kandidat.lower() for s in kata_sampah):
                            nama = kandidat
                            break
                
                if nama and nama not in seen_names:
                    nama_clean = " ".join(nama.lower().split())
                    if nama_clean == keyword_exact: 
                        seen_names.add(nama)
                        data_hasil.append({'Nama': nama, 'Harga': harga})
        
        driver.quit()
        return data_hasil
    except Exception as e:
        print(f"Error: {e}")
        try: driver.quit() 
        except: pass
        return []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Katalog Pro Analytics</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); min-height: 100vh; padding-bottom: 50px; }
        .header-section { padding: 40px 0 20px; text-align: center; }
        .header-section h1 { font-weight: 700; color: #2c3e50; letter-spacing: -1px; }
        .header-section span { color: #3498db; }
        .glass-card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 20px; box-shadow: 0 15px 35px rgba(0,0,0,0.05); border: 1px solid rgba(255,255,255,0.2); padding: 30px; margin-bottom: 30px; }
        .search-input { border-radius: 12px; padding: 15px 20px; font-size: 16px; border: 2px solid #e0e0e0; box-shadow: none !important; }
        .search-input:focus { border-color: #3498db; }
        .btn-search { background: linear-gradient(135deg, #3498db, #2980b9); border: none; border-radius: 12px; color: white; font-weight: 600; padding: 15px; transition: all 0.3s; }
        .btn-search:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(52, 152, 219, 0.4); }
        .stat-box { border-radius: 16px; padding: 25px 20px; color: white; text-align: center; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
        .bg-high { background: linear-gradient(135deg, #ff6b6b, #ee5253); }
        .bg-low { background: linear-gradient(135deg, #1dd1a1, #10ac84); }
        .bg-avg { background: linear-gradient(135deg, #5f27cd, #341f97); }
        .stat-box i { font-size: 30px; margin-bottom: 10px; opacity: 0.8; }
        .stat-box h6 { font-weight: 400; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
        .stat-box h3 { font-weight: 700; margin: 0; font-size: 24px; }
        .table-container { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .table { margin-bottom: 0; }
        .table thead { background-color: #f8f9fa; }
        .table th { font-weight: 600; color: #7f8c8d; border-bottom: 2px solid #ecf0f1; padding: 15px; }
        .table td { padding: 15px; vertical-align: middle; font-size: 15px; }
        #loader-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(5px); z-index: 9999; flex-direction: column; justify-content: center; align-items: center; }
        .spinner { width: 60px; height: 60px; border: 6px solid #e0e0e0; border-top: 6px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <div id="loader-overlay">
        <div class="spinner"></div>
        <h4 class="text-primary fw-bold">Memproses Data...</h4>
        <p class="text-muted">Sistem sedang menarik data dari E-Katalog. Mohon tunggu sebentar.</p>
    </div>

    <div class="container">
        <div class="header-section">
            <h1>Inaproc <span>Analytics Pro</span></h1>
            <p class="text-muted fw-bold">MADE BY PT. CHASA MEDIKA ABADI</p>
        </div>

        <div class="glass-card">
            <form id="searchForm" method="POST" class="row g-3">
                <div class="col-md-9">
                    <div class="input-group">
                        <span class="input-group-text bg-white border-0" style="position: absolute; z-index: 10; padding: 17px;"><i class="fas fa-search text-muted"></i></span>
                        <input type="text" name="query" class="form-control search-input ps-5" placeholder="Masukkan nama produk persis (Cth: Laptop ASUS Expertbook BG1409CVA)" value="{{ keyword }}" required>
                    </div>
                </div>
                <div class="col-md-3">
                    <button type="submit" class="btn btn-search w-100 h-100">
                        <i class="fas fa-rocket me-2"></i> Ekstrak Data
                    </button>
                </div>
            </form>
        </div>

        {% if request.method == 'POST' and not hasil %}
            <div class="alert alert-danger shadow-sm border-0" style="border-radius: 12px;">
                <i class="fas fa-exclamation-circle me-2"></i> <b>Tidak Ditemukan:</b> Pastikan ketikan nama produk 100% sama dengan yang ada di E-Katalog.
            </div>
        {% endif %}

        {% if hasil %}
            <div class="alert alert-success shadow-sm border-0 mb-4" style="border-radius: 12px;">
                <i class="fas fa-check-circle me-2"></i> Berhasil menyaring <b>{{ hasil|length }}</b> data valid.
            </div>

            <div class="row mb-4">
                <div class="col-md-4 mb-3">
                    <div class="stat-box bg-high">
                        <i class="fas fa-arrow-up"></i>
                        <h6>Harga Tertinggi</h6>
                        <h3>{{ stats.max }}</h3>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="stat-box bg-low">
                        <i class="fas fa-arrow-down"></i>
                        <h6>Harga Terendah</h6>
                        <h3>{{ stats.min }}</h3>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="stat-box bg-avg">
                        <i class="fas fa-chart-line"></i>
                        <h6>Rata-Rata Pasar</h6>
                        <h3>{{ stats.avg }}</h3>
                    </div>
                </div>
            </div>

            <div class="table-container">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th width="5%"><i class="fas fa-hashtag"></i></th>
                            <th width="65%">Nama Produk (Sesuai Keyword)</th>
                            <th width="30%">Penawaran Harga</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in hasil %}
                        <tr>
                            <td class="text-muted fw-bold">{{ loop.index }}</td>
                            <td>{{ item.Nama }}</td>
                            <td class="text-success fw-bold">{{ item.Harga }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% endif %}
    </div>

    <script>
        document.getElementById('searchForm').addEventListener('submit', function() {
            document.getElementById('loader-overlay').style.display = 'flex';
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    hasil, stats, keyword = [], None, ""
    if request.method == 'POST':
        keyword = request.form.get('query', '')
        hasil = run_selenium_search(keyword)
        
        if hasil:
            h_list = [bersihkan_harga(x['Harga']) for x in hasil]
            h_list = [h for h in h_list if h > 0]
            
            if h_list:
                stats = {
                    'max': f"Rp {max(h_list):,.0f}".replace(',', '.'),
                    'min': f"Rp {min(h_list):,.0f}".replace(',', '.'),
                    'avg': f"Rp {sum(h_list)/len(h_list):,.0f}".replace(',', '.')
                }
                
    return render_template_string(HTML_TEMPLATE, hasil=hasil, stats=stats, keyword=keyword)

if __name__ == '__main__':
    # Mengambil port otomatis yang diberikan oleh Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)