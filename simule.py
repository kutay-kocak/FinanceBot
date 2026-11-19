#!/usr/bin/env python3
"""
Tek Kelimelik Simülasyon Tetikleyicisi ('simule' komutu)
Kullanım: python simule.py
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core import engine

if __name__ == "__main__":
    print("==================================================")
    print("  'simule' Emri Alındı: 10.000x Simülasyon Başlıyor")
    print("==================================================")
    engine.run_full_pipeline()
    print("==================================================")
    print("  Simülasyon Tamamlandı! Dashboard güncellendi.")
    print("  Web: http://localhost:8080")
    print("==================================================")
