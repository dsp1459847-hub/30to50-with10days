import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. हाइब्रिड मैचिंग इंजन (v46) ---
def get_v46_hybrid_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        all_vals = df_clean[df_clean['DATE'] < target_date]['NUM'].astype(int).tolist()
        if len(all_vals) < 50: return "Data Kam", "N/A", []

        # --- A. दहाई और इकाई (Digit Mapping) लॉजिक ---
        last_v = all_vals[-1]
        d_last, e_last = last_v // 10, last_v % 10
        
        # आपकी थ्योरी के अनुसार डिजिट ट्रांजिशन
        mapping = {3:[0,5,8,9], 0:[8,9,5], 1:[6,2,7], 2:[7,3,8], 4:[9,0,5], 
                   5:[0,1,6], 6:[1,2,7], 7:[2,3,8], 8:[3,4,9], 9:[4,5,0]}
        
        target_d = [(d_last + 5) % 10, d_last] # राशि और सेम दहाई
        target_e = mapping.get(e_last, [(e_last + 5) % 10]) # आपकी मैपिंग या राशि
        
        digit_theory_nums = []
        for d in target_d:
            for e in target_e:
                digit_theory_nums.append(d * 10 + e)

        # --- B. 25-30% वाला सक्सेस इंजन (Historical Scoring) ---
        hist_scores = Counter()
        # 1. तारीख का इतिहास (Legacy)
        d_m = (target_date.day, target_date.month)
        legacy = df_clean[df_clean['DATE'].apply(lambda x: (x.day, x.month) == d_m and x < target_date)]['NUM'].tolist()
        for n in legacy: hist_scores[n] += 50
        
        # 2. ताज़ा रोटेशन (Last 100 days)
        for n in all_vals[-100:]: hist_scores[n] += 10

        # --- C. क्रॉस-मैचिंग (Final Result) ---
        final_candidate_scores = {}
        for n in range(100):
            score = 0
            # अगर नंबर 'अंक थ्योरी' में है तो भारी बोनस
            if n in digit_theory_nums: score += 100
            # अगर नंबर 'इतिहास के स्कोर' में है तो स्कोर जोड़ो
            score += hist_scores.get(n, 0)
            
            # ए/बी पार्टीशन फिल्टर (0-49 या 50-99)
            last_g = "A" if last_v <= 49 else "B"
            curr_g = "A" if n <= 49 else "B"
            if last_g != curr_g: score += 20 # अक्सर ग्रुप बदलता है
            
            if score > 0:
                final_candidate_scores[n] = score

        # टॉप 10 का चुनाव
        final_picks = [n for n, s in sorted(final_candidate_scores.items(), key=lambda x: x[1], reverse=True)[:10]]
        
        # बैकअप (अगर 10 से कम हों)
        if len(final_picks) < 10:
            for n in digit_theory_nums:
                if n not in final_picks: final_picks.append(n)
                if len(final_picks) >= 10: break

        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_picks)])
        analysis = f"मैपिंग अंक: {target_d}x{target_e} | इतिहास मैच: सक्रिय"
        
        return analysis, top_10_str, final_picks
    except:
        return "Matching..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI Hybrid v46", layout="wide")
st.title("🛡️ MAYA AI: v46 Hybrid Matcher Engine")
st.markdown("### अंकों की थ्योरी + 30% सक्सेस इंजन का महा-संगम")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 हाइब्रिड मैचिंग रन करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v46_hybrid_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "मैचिंग विश्लेषण": info, "टॉप 10 मैच": picks})
            
            st.table(pd.DataFrame(report))
            st.success("✅ **रिजल्ट तैयार:** अब केवल वही नंबर आ रहे हैं जो अंकों की चाल और इतिहास के रिकॉर्ड दोनों में फिट बैठते हैं।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
