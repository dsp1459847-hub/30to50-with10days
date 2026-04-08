import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. डीप-ग्रेव रिकवरी इंजन (v51) ---
def get_v51_deep_recovery(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # डेटा पुल (पिछले 120 रिकॉर्ड्स - करीब 20 दिन)
        recent_all = df_clean[df_clean['DATE'] < target_date].tail(120)
        all_vals = recent_all['NUM'].astype(int).tolist()
        
        if len(all_vals) < 10: return "Data Kam", "N/A", []

        scores = Counter()
        last_val = all_vals[-1]

        # 🎯 पैटर्न 1: 'मरे हुए नंबर' (Dead Numbers)
        # 42 के फेलियर के बाद वो नंबर आते हैं जो पिछले 20 दिनों से 'मरे' हुए थे
        appeared_20_days = set(all_vals)
        dead_nums = list(set(range(100)) - appeared_20_days)
        for n in dead_nums:
            scores[n] += 120 # सबसे ज्यादा प्राथमिकता

        # 🎯 पैटर्न 2: 'राशि का तिरछा जंप' (Mirror-Diagonal Jump)
        # पिछले नंबर की दहाई की राशि और इकाई का सेम अंक या उल्टा
        r = lambda x: (x + 5) % 10
        d, e = last_val // 10, last_val % 10
        diagonal_nums = [(r(d)*10)+e, (d*10)+r(e), (e*10)+d, (r(e)*10)+r(d)]
        for n in diagonal_nums:
            scores[n] += 100

        # 🎯 पैटर्न 3: 'अंकों की लुका-छिपी' (Missing Haruf)
        # वो 3 अंक जो पिछले 50 नतीजों में सबसे कम दिखे हैं
        digit_counts = Counter([d for n in all_vals[-50:] for d in [n//10, n%10]])
        weakest_digits = [d for d, c in sorted(digit_counts.items(), key=lambda x: x[1])[:3]]
        
        for d in weakest_digits:
            for i in range(10):
                scores[d*10 + i] += 60
                scores[i*10 + d] += 60

        # टॉप 10 चयन (Prioritize Dead + Diagonal)
        final_list = [n for n, s in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_list)])
        
        analysis = f"डेड डिजिट्स सक्रिय | कमज़ोर हरुफ़: {weakest_digits}"
        
        return analysis, top_10_str, final_list
    except:
        return "Deep Scanning..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI v51 Deep Recovery", layout="wide")
st.title("🛡️ MAYA AI: v51 Deep-Grave Recovery Engine")
st.markdown("### 42/1 के भारी फेलियर को रिकवर करने का अंतिम प्रहार")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 डीप रिकवरी स्कैन रन करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v51_deep_recovery(df_match, s, target_date)
                
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
            st.warning("🚨 **रिकवरी मोड:** जब गेम 98% फेल होता है, तो वह उन नंबरों को निकालता है जो 'आउट ऑफ चार्ट' हो चुके होते हैं। v51 उन्हीं सोए हुए नंबरों को टारगेट कर रहा है।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
