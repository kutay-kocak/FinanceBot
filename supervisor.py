#!/usr/bin/env python3
"""
Antigravity Trade Masası - Kesintisiz Hizmet Gözlemcisi (Supervisor)
- Web Sunucusunu (port 8080) ve Cloudflare Tünelini arka planda sürekli canlı tutar.
- Herhangi bir çökme veya kapanma durumunda 3 saniye içinde otomatik yeniden başlatır.
- Güncel tünel bağlantısını data/public_url.txt dosyasına kaydeder.
"""

import os
import sys
import time
import subprocess
import re
import datetime
import socket

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_URL_FILE = os.path.join(DATA_DIR, "public_url.txt")
SECRET_KEY = "trade-sec-8842"

def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] [Supervisor] {msg}"
    print(line, flush=True)

def start_web_server():
    cmd = [sys.executable, os.path.join(BASE_DIR, "web", "app.py"), "8080"]
    log("Web sunucusu (port 8080) başlatılıyor...")
    proc = subprocess.Popen(cmd, cwd=BASE_DIR)
    return proc

def start_tunnel():
    exe_path = os.path.join(BASE_DIR, "cloudflared.exe")
    if not os.path.exists(exe_path):
        log(f"HATA: {exe_path} bulunamadı!")
        return None
    cmd = [exe_path, "tunnel", "--url", "http://127.0.0.1:8080"]
    log("Cloudflare tüneli başlatılıyor...")
    proc = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return proc

def acquire_single_instance_lock():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 8089))
        s.listen(1)
        return s
    except socket.error:
        log("Zaten çalışan bir Supervisor örneği tespit edildi. Çift çalışma engellendi.")
        sys.exit(0)

def monitor_loop():
    lock_sock = acquire_single_instance_lock()
    web_proc = start_web_server()
    tunnel_proc = start_tunnel()

    url_saved = False
    
    while True:
        time.sleep(2)
        
        # 1. Web Sunucusu Kontrolü
        if web_proc.poll() is not None:
            log("UYARI: Web sunucusu durdu! Otomatik olarak yeniden başlatılıyor...")
            web_proc = start_web_server()
            
        # 2. Tünel Kontrolü
        if tunnel_proc is None or tunnel_proc.poll() is not None:
            log("UYARI: Cloudflare tüneli durdu! Otomatik olarak yeniden başlatılıyor...")
            tunnel_proc = start_tunnel()
            url_saved = False

        # 3. Tünel çıktısından URL yakalama
        if tunnel_proc and not url_saved:
            try:
                line = tunnel_proc.stdout.readline()
                if line:
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        raw_url = match.group(0)
                        full_url = f"{raw_url}/?key={SECRET_KEY}"
                        os.makedirs(DATA_DIR, exist_ok=True)
                        with open(PUBLIC_URL_FILE, "w", encoding="utf-8") as f:
                            f.write(full_url)
                        log(f"CANLI BAĞLANTI OLUŞTURULDU: {full_url}")
                        url_saved = True
            except Exception:
                pass

if __name__ == "__main__":
    try:
        monitor_loop()
    except KeyboardInterrupt:
        log("Supervisor kullanıcı tarafından kapatıldı.")
