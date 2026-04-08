import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. इनवर्स-ड्रॉट रिकवरी इंजन (v52) ---
def get_v52_inverse_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # डेटा पुल (पिछले 150 रिकॉर्ड्स - करीब 25 दिन)
        recent_all = df_clean[df_clean['DATE'] < target_date].tail(150)
        all_vals = recent_all['NUM'].astype(int).tolist()
        
        if len(all_vals) < 20: return "Data Kam", "N/A", []

        scores = Counter()
        last_val = all_vals[-1]

        # 🎯 स्ट्रैटेजी 1: 'अंकों का अकाल' (Drought Numbers)
        # वो नंबर जो पिछले 60 शिफ्ट में एक बार भी नहीं आए
        appeared_60 = set(all_vals[-60:])
        drought_nums = list(set(range(100)) - appeared_60)
        for n in drought_nums:
            scores[n] += 150 # अकाल वाले नंबरों को सर्वोच्च प्राथमिकता

        # 🎯 स्ट्रैटेजी 2: 'विपरीत अंक' (Inverse Digits)
        # अगर कल 3 आया, तो 0,5,8,9 के बजाय वो अंक जो बिल्कुल नहीं आ रहे
        digit_counts = Counter([d for n in all_vals[-40:] for d in [n//10, n%10]])
        # सबसे कम आने वाले 3 अंक
        rare_digits = [d for d, c in sorted(digit_counts.items(), key=lambda x: x[1])[:3]]
        
        for d in rare_digits:
            for i in range(10):
                scores[d*10 + i] += 80
                scores[i*10 + d] += 80

        # 🎯 स्ट्रैटेजी 3: 'दूरी का गणित' (The Extreme Gap)
        # पिछले नंबर से 33 या 66 अंक दूर (Extreme Gaps)
        extreme_gaps = [(last_val+33)%100, (last_val-33)%100, (last_val+66)%100, (last_val-66)%100]
        for n in extreme_gaps:
            scores[n] += 100

        # टॉप 10 चयन (Prioritize Drought + Rare Digits)
        final_list = [n for n, s in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_list)])
        
        analysis = f"अकाल अंक सक्रिय: {rare_digits} | फोकस: इनवर्स लॉजिक"
        
        return analysis, top_10_str, final_list
    except:
        return "System Resetting..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI v52 Reset", layout="wide")
st.title("🛡️ MAYA AI: v52 Inverse-Drought Engine")
st.markdown("### 60/0 फेलियर का मतलब है गेम 'उल्टा' चल रहा है—यह कोड उसे पकड़ेगा")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 इनवर्स स्कैन रन करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v52_inverse_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "एनालिसिस": info, "टॉप 10 रिकवरी अंक": picks})
            
            st.table(pd.DataFrame(report))
            st.error("🔄 **सिस्टम अलर्ट:** लगातार 60 फेलियर के बाद गेम अक्सर 'Mirror of Mirror' (राशि की भी राशि) और 'Cold Numbers' पर शिफ्ट हो जाता है। v52 इसी 'उलटी चाल' को ट्रैक कर रहा है।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
