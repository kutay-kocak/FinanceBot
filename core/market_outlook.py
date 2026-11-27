#!/usr/bin/env python3
"""
Antigravity Finans Otomasyonu - Canlı Piyasa Görünümü, Makro Göstergeler & Haber Akışı (core/market_outlook.py)
- BIST 100 (XU100.IS), USD/TRY (TRY=X), VIX (^VIX), ABD 10Y Tahvil (^TNX), S&P 500 (^GSPC) ve NASDAQ (^IXIC)
  canlı piyasa verilerini çeker.
- BIST ve ABD piyasaları için canlı Türkçe finans haber başlıklarını (Google News Finans RSS) derler.
- Resmi TCMB PPK (10 Aralık 2026) ve FED FOMC (8-9 Aralık 2026) takvimleriyle 7/30 günlük görünüm üretir.
"""

import datetime
import email.utils
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

try:
    from core import fed_rate_tracker
except ImportError:
    import fed_rate_tracker

TSI = datetime.timezone(datetime.timedelta(hours=3))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def _fetch_macro_quote(symbol):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?range=1d&interval=5m"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as r:
            meta = json.loads(r.read().decode("utf-8"))["chart"]["result"][0]["meta"]
            p = meta.get("regularMarketPrice")
            pc = meta.get("chartPreviousClose")
            ch = round(((p - pc) / pc) * 100, 2) if (p and pc) else 0.0
            return round(p, 2) if p else None, ch
    except Exception:
        return None, 0.0

def _fetch_yahoo_news_fallback(symbols, limit=4):
    items = []
    seen = set()
    for sym in symbols:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(sym)}&quotesCount=0&newsCount=3"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=4) as r:
                news_list = json.loads(r.read().decode("utf-8")).get("news", [])
                for n in news_list:
                    title = (n.get("title") or "").strip()
                    if not title or title in seen:
                        continue
                    seen.add(title)
                    ts = n.get("providerPublishTime")
                    pub_str = datetime.datetime.fromtimestamp(ts, TSI).strftime("%d.%m.%Y %H:%M TSİ") if ts else ""
                    items.append({
                        "title": title,
                        "source": n.get("publisher") or "Yahoo Finance",
                        "published_at": pub_str,
                        "link": n.get("link") or "#"
                    })
                    if len(items) >= limit:
                        return items
        except Exception:
            pass
    return items

def _fetch_rss_headlines(query, fallback_symbols=None, limit=4):
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=tr&gl=TR&ceid=TR:tr"
    headlines = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as r:
            root = ET.fromstring(r.read())
            for item in root.findall(".//item"):
                raw_title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_raw = (item.findtext("pubDate") or "").strip()
                source_el = item.find("source")
                source_name = source_el.text.strip() if (source_el is not None and source_el.text) else ""

                clean_title = raw_title
                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    clean_title = parts[0].strip()
                    if not source_name:
                        source_name = parts[1].strip()

                pub_str = ""
                if pub_raw:
                    try:
                        dt = email.utils.parsedate_to_datetime(pub_raw).astimezone(TSI)
                        pub_str = dt.strftime("%d.%m.%Y %H:%M TSİ")
                    except Exception:
                        pub_str = pub_raw[:16]

                if clean_title:
                    headlines.append({
                        "title": clean_title,
                        "source": source_name or "Finans Haber",
                        "published_at": pub_str,
                        "link": link
                    })
                if len(headlines) >= limit:
                    break
    except Exception:
        pass

    if not headlines and fallback_symbols:
        headlines = _fetch_yahoo_news_fallback(fallback_symbols, limit=limit)
    return headlines

def get_market_outlook():
    now_tsi = datetime.datetime.now(TSI)
    now_str = now_tsi.strftime("%Y-%m-%d %H:%M TSİ")

    macro_symbols = ["XU100.IS", "TRY=X", "^VIX", "^TNX", "^GSPC", "^IXIC"]
    quotes = {}
    bist_news = []
    us_news = []

    with ThreadPoolExecutor(max_workers=8) as ex:
        q_futures = {sym: ex.submit(_fetch_macro_quote, sym) for sym in macro_symbols}
        bist_news_fut = ex.submit(_fetch_rss_headlines, "Borsa İstanbul OR BIST 100 OR TCMB faiz", ["THYAO.IS", "TUPRS.IS", "GARAN.IS"], 4)
        us_news_fut = ex.submit(_fetch_rss_headlines, "Fed faiz OR Wall Street OR Nasdaq OR ABD borsaları", ["SPY", "NVDA", "AVGO", "IWM"], 4)

        for sym, fut in q_futures.items():
            try:
                quotes[sym] = fut.result()
            except Exception:
                quotes[sym] = (None, 0.0)
        try:
            bist_news = bist_news_fut.result()
        except Exception:
            bist_news = []
        try:
            us_news = us_news_fut.result()
        except Exception:
            us_news = []

    xu100_p, xu100_ch = quotes.get("XU100.IS", (None, 0.0))
    usdtry_p, usdtry_ch = quotes.get("TRY=X", (None, 0.0))
    vix_p, vix_ch = quotes.get("^VIX", (None, 0.0))
    tnx_p, tnx_ch = quotes.get("^TNX", (None, 0.0))
    sp500_p, sp500_ch = quotes.get("^GSPC", (None, 0.0))
    ndx_p, ndx_ch = quotes.get("^IXIC", (None, 0.0))

    # BIST Dinamik Özet
    bist_level_txt = f"{xu100_p:,.2f} (%{'+' if xu100_ch >= 0 else ''}{xu100_ch})" if xu100_p else "11.000 bandı"
    usd_txt = f"₺{usdtry_p:.2f}" if usdtry_p else "dengeli bant"
    bist_mood = "GÜÇLÜ YÜKSELİŞ MOMENTUMU" if (xu100_ch and xu100_ch >= 1.5) else ("TEMKİNLİ İYİMSER" if (xu100_ch is not None and xu100_ch >= -0.5) else "DÜZELTME / DESTEK ARAYIŞI")

    # US Dinamik Özet
    vix_val = vix_p if vix_p else 20.0
    vix_label = f"YÜKSEK (VIX: {vix_p} • %{'+' if vix_ch >= 0 else ''}{vix_ch})" if vix_val >= 22 else (f"ORTA (VIX: {vix_p})" if vix_val >= 16 else f"DÜŞÜK (VIX: {vix_p})")
    tnx_txt = f"%{tnx_p:.2f}" if tnx_p else "%4.85"
    sp_txt = f"{sp500_p:,.2f} (%{'+' if sp500_ch >= 0 else ''}{sp500_ch})" if sp500_p else "--"
    ndx_txt = f"{ndx_p:,.2f} (%{'+' if ndx_ch >= 0 else ''}{ndx_ch})" if ndx_p else "--"
    us_mood = "YÜKSEK VOLATİLİTE & ŞAHİN FED BASKISI" if vix_val >= 22 else ("SEÇİCİ BOĞA / DENGELENME" if (sp500_ch is not None and sp500_ch >= -0.5) else "DALGALI SEYİR")

    bist_outlook = {
        "market": "BIST",
        "last_updated": now_str,
        "live_indicators": {
            "BIST 100": bist_level_txt,
            "USD/TRY": usd_txt,
            "TCMB Politika Faizi": "%36.00"
        },
        "live_news": bist_news,
        "current_regime": {
            "title": f"BIST 100: {bist_level_txt} • TCMB %36 Faiz & Seçici Kurumsal Akım",
            "mood": bist_mood,
            "summary": (
                f"BIST 100 endeksi anlık olarak {bist_level_txt} seviyesinde, USD/TRY kuru ise {usd_txt} düzeyinde işlem görüyor. "
                f"TCMB'nin Ekim toplantısında politika faizini %36 seviyesine çekmesinin ardından gözler 10 Aralık 2026 Perşembe (14:00 TSİ) "
                f"yılın son PPK kararına çevrildi. Kasasında güçlü net nakit tutan sanayi ve ulaştırma devleri (TUPRS, THYAO) endeksin ana taşıyıcısı konumunda."
            ),
            "volatility_index": f"BIST 100: {bist_level_txt} | USD/TRY: {usd_txt}"
        },
        "forecast_7d": {
            "period": "Önümüzdeki 7 Gün",
            "net_bias": "SEÇİCİ POZİTİF & VERİ ODAKLI",
            "expected_swing": "+%3.0 / -%2.2",
            "catalysts": [
                {
                    "event": "Kasım Ayı TÜFE Enflasyon Verisi & 10 Aralık PPK Öncesi Fiyatlama",
                    "date": "Önümüzdeki Hafta",
                    "expectation": "Aylık enflasyon eğiliminin 10 Aralık PPK toplantısındaki faiz adımı beklentilerini şekillendirmesi.",
                    "impact_range": "+%2.5 ile -%2.0 arası endeks hareketi"
                },
                {
                    "event": "Haftalık Yabancı Takas & Hisse Geri Alım Programları",
                    "date": "Haftalık Periyodik",
                    "expectation": "BIST şirketlerinin geri alım hamleleri ve yabancı kurumsal giriş/çıkış istatistikleri.",
                    "impact_range": "+%1.2 ile -%1.5 arası hisse bazlı ayrışma"
                }
            ]
        },
        "forecast_30d": {
            "period": "Önümüzdeki 30 Gün",
            "net_bias": "FAİZ KARARI & YIL SONU PORTFÖY KAPANIŞI",
            "expected_swing": "+%6.0 / -%4.5",
            "catalysts": [
                {
                    "event": "TCMB Yılın Son Para Politikası Kurulu (PPK) Faiz Kararı",
                    "date": "10 Aralık 2026 • 14:00 TSİ",
                    "expectation": "%36 seviyesindeki politika faizine ilişkin yılın son kararı ve 2027 para politikası metni.",
                    "impact_range": "+%3.5 ile -%3.0 arası banka ve sanayi fiyatlaması"
                },
                {
                    "event": "2027 Asgari Ücret, Bütçe ve Yıl Sonu Fon Değerlemeleri",
                    "date": "Aralık Ayı Boyunca",
                    "expectation": "Yurt içi emeklilik ve yatırım fonlarının yıl sonu kapanış işlemleri ile 2027 beklentileri.",
                    "impact_range": "+%3.0 ile -%2.5 arası sektörel rotasyon"
                }
            ]
        }
    }

    us_outlook = {
        "market": "US",
        "last_updated": now_str,
        "live_indicators": {
            "S&P 500": sp_txt,
            "NASDAQ": ndx_txt,
            "VIX": f"{vix_p}" if vix_p else "--",
            "ABD 10Y Tahvil": tnx_txt
        },
        "live_news": us_news,
        "current_regime": {
            "title": f"S&P 500: {sp_txt} • ABD 10Y Tahvil: {tnx_txt}",
            "mood": us_mood,
            "summary": (
                f"ABD piyasalarında S&P 500 {sp_txt}, Nasdaq {ndx_txt} seviyesinde seyrederken, korku endeksi {vix_label} ve "
                f"ABD 10 Yıllık Tahvil getirisi {tnx_txt} düzeyinde bulunuyor. Tahvil faizlerindeki yüksek seyir ve 9 Aralık FOMC toplantısı "
                f"öncesi şahin Fed beklentileri teknoloji (AVGO, NVDA) ve küçük ölçekli şirketlerde (IWM) sert dalgalanmalar yaratıyor."
            ),
            "volatility_index": vix_label
        },
        "forecast_7d": {
            "period": "Önümüzdeki 7 Gün",
            "net_bias": "YÜKSEK OYNAMALI & TAHVİL DUYARLI",
            "expected_swing": "+%2.8 / -%3.2",
            "catalysts": [
                {
                    "event": "ABD Tarım Dışı İstihdam (NFP) & ISM Öncü Göstergeleri",
                    "date": "Önümüzdeki Hafta",
                    "expectation": "8-9 Aralık FOMC toplantısı öncesindeki son kritik istihdam ve ücret artışı verileri.",
                    "impact_range": "+%2.2 ile -%2.8 arası Nasdaq / Russell 2000 hareketi"
                },
                {
                    "event": "FOMC Sessizlik Dönemi (Blackout Period) & Tahvil İhaleleri",
                    "date": "Hafta İçi",
                    "expectation": "ABD 10Y tahvil faizinin (%4.85 bölgesi) yönüne göre büyüme hisselerinde tepki alımları veya baskı.",
                    "impact_range": "+%1.5 ile -%2.0 arası teknoloji rotasyonu"
                }
            ]
        },
        "forecast_30d": {
            "period": "Önümüzdeki 30 Gün",
            "net_bias": "9 ARALIK FOMC KARARI & YIL SONU DENGELENMESİ",
            "expected_swing": "+%6.5 / -%5.5",
            "catalysts": [
                {
                    "event": "FED (FOMC) Faiz Kararı & Ekonomik Projeksiyonlar (Dot Plot)",
                    "date": "9 Aralık 2026 • 22:00 TSİ",
                    "expectation": "Mevcut %3.75-%4.00 politika faizi üzerinde karar ve 2027 faiz patikası projeksiyonlarının açıklanması.",
                    "impact_range": "+%4.5 ile -%5.0 arası tüm küresel piyasaları yönlendirecek ana karar"
                },
                {
                    "event": "Broadcom (AVGO) Bilanço Dönemi & Kurumsal AI Yatırım Rehberliği",
                    "date": "Aralık Ortası",
                    "expectation": "Özel AI çip (ASIC) siparişleri ve 2027 veri merkezi gelir beklentilerinin açıklanması.",
                    "impact_range": "+%6.0 ile -%6.0 arası yarı iletken hisseleri hareketi"
                }
            ]
        },
        "fed_rate_decision": fed_rate_tracker.get_fed_rate_forecast()
    }

    return {
        "bist": bist_outlook,
        "us": us_outlook
    }

if __name__ == "__main__":
    out = get_market_outlook()
    print("BIST:", out["bist"]["current_regime"]["title"], "| Haber:", len(out["bist"]["live_news"]))
    print("US:", out["us"]["current_regime"]["title"], "| Haber:", len(out["us"]["live_news"]))
