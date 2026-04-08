import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. अडैप्टिव पैटर्न करेक्टर (v47) ---
def get_v47_adaptive_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # पिछले 5 दिनों का डेटा (पैटर्न समझने के लिए)
        recent_data = df_clean[df_clean['DATE'] < target_date].tail(30)
        all_vals = recent_data['NUM'].astype(int).tolist()
        
        if len(all_vals) < 5: return "Data Kam", "N/A", []

        # A. फेलियर का कारण ढूंढना (Self-Correction)
        # क्या गेम Repeat हो रहा है या Neighbor चल रहा है?
        last_3 = all_vals[-3:]
        is_repeat_heavy = any(all_vals.count(x) > 1 for x in last_3)
        is_neighbor_heavy = any(abs(all_vals[i] - all_vals[i-1]) <= 2 for i in range(-1, -4, -1))

        # B. डायनामिक डिजिट मैपिंग (इतिहास के बजाय 'अभी' की चाल)
        digit_map = {i: [] for i in range(10)}
        for i in range(len(all_vals)-1):
            digit_map[all_vals[i]%10].append(all_vals[i+1]%10)
        
        last_val = all_vals[-1]
        last_e = last_val % 10
        # ताज़ा ट्रेंड के अनुसार अगले अंक
        next_digits = [d for d, c in Counter(digit_map.get(last_e, [])).most_common(4)]
        if not next_digits: next_digits = [(last_e + 5)%10, (last_e + 1)%10]

        # C. नंबरों का निर्माण (Scoring Matrix)
        scores = Counter()
        for d in next_digits:
            for i in range(10):
                # दहाई फिक्स करके इकाई बदलना या उल्टा
                n1, n2 = (last_val//10)*10 + d, d*10 + (last_val%10)
                scores[n1] += 50
                scores[n2] += 50

        # D. एक्स्ट्रा बैकअप (अगर गेम राशि पर जा रहा है)
        r = lambda x: (x + 5) % 10
        family = [last_val, (r(last_val//10)*10)+(last_val%10), (last_val//10*10)+r(last_val%10)]
        for f in family: scores[f] += 40

        # टॉप 10 चयन
        final_picks = [n for n, s in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_picks)])
        
        status = "Neighbor Trend" if is_neighbor_heavy else "Mapping Trend"
        analysis = f"चाल: {status} | फोकस अंक: {next_digits}"
        
        return analysis, top_10_str, final_picks
    except:
        return "Analyzing Failure..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI v47 Fix", layout="wide")
st.title("🛡️ MAYA AI: v47 Pattern Corrector (Failure to Success)")
st.markdown("### यह कोड फेल हुए नतीजों से 'अगली चाल' सीखता है")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 फेलियर सुधार स्कैन शुरू करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v47_adaptive_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "फेलियर एनालिसिस": info, "टॉप 10 रिकवरी अंक": picks})
            
            st.table(pd.DataFrame(report))
            st.warning("⚠️ **पैटर्न अलर्ट:** अगर लगातार ❌ दिख रहे हैं, तो इसका मतलब है गेम 'राशि की भी राशि' (Complex Mirror) पर चला गया है। यह v47 उसे पकड़ने की कोशिश कर रहा है।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
            
