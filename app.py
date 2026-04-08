import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. टोटल एंटी-पैटर्न इंजन (v53) ---
def get_v53_last_stand_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # डेटा पुल (पिछले 200 रिकॉर्ड्स)
        recent_all = df_clean[df_clean['DATE'] < target_date].tail(200)
        all_vals = recent_all['NUM'].astype(int).tolist()
        
        if len(all_vals) < 20: return "Data Reset..", "N/A", []

        scores = Counter()
        last_val = all_vals[-1]

        # 🎯 नियम 1: 'अछूते नंबर' (Zero Frequency)
        # पिछले 90 शिफ्ट में जो नंबर एक बार भी नहीं आया, उसे 150 पॉइंट्स
        appeared_90 = set(all_vals[-90:])
        untouched = list(set(range(100)) - appeared_90)
        for n in untouched:
            scores[n] += 150

        # 🎯 नियम 2: 'विपरीत हरुफ़' (Inverse Haruf)
        # सबसे 'ठंडे' (Coldest) 3 अंक जो चार्ट से गायब हैं
        digit_counts = Counter([d for n in all_vals[-60:] for d in [n//10, n%10]])
        cold_digits = [d for d, c in sorted(digit_counts.items(), key=lambda x: x[1])[:3]]
        
        for d in cold_digits:
            for i in range(10):
                scores[d*10 + i] += 80
                scores[i*10 + d] += 80

        # 🎯 नियम 3: 'अंकों का योग' (Sum Logic)
        # पिछले नंबर के अंकों का जोड़ (जैसे 43 -> 4+3 = 7)
        # गेम अक्सर उस जोड़ के मिरर पर अगला नंबर मारता है
        last_sum = (last_val // 10 + last_val % 10) % 10
        mirror_sum = (last_sum + 5) % 10
        for n in range(100):
            if (n // 10 + n % 10) % 10 == mirror_sum:
                scores[n] += 60

        # टॉप 10 चयन (अछूते नंबरों को सबसे पहले)
        final_list = [n for n, s in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_list)])
        
        analysis = f"कोल्ड डिजिट्स: {cold_digits} | टारगेट सम: {mirror_sum}"
        
        return analysis, top_10_str, final_list
    except:
        return "Critical Reboot..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI v53 Final", layout="wide")
st.title("🛡️ MAYA AI: v53 The Last Stand (Anti-Logic)")
st.error("🚨 भारी फेलियर के बाद सिस्टम 'Manual Reset' मोड में है")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 महा-रिकवरी स्कैन शुरू करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v53_last_stand_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "एंटी-लॉजिक विश्लेषण": info, "टॉप 10 रिकवरी अंक": picks})
            
            st.table(pd.DataFrame(report))
            st.warning("🔄 **सिस्टम सूचना:** जब प्रेडिक्शन 0% हो जाए, तो समझ लें कि गेम 'गणित' से नहीं 'गैप' से चल रहा है। v53 उन्हीं गैप्स को भर रहा है।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
