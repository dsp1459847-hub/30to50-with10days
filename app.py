import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. स्टैटिक-विज़न इंजन (v55 - No Prediction Flip) ---
def get_v55_static_logic(df, s_name, target_date):
    try:
        # डेटा को साफ़ करना
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # 🛑 सबसे ज़रूरी बदलाव: 
        # कोड सिर्फ 'Target Date' से पहले का डेटा देखेगा।
        # भले ही आज का रिजल्ट एक्सेल में हो, कोड उसे इस्तेमाल नहीं करेगा।
        hist_data = df_clean[df_clean['DATE'] < target_date]
        
        if hist_data.empty: return "No Past Data", "N/A", []

        all_vals = hist_data['NUM'].astype(int).tolist()
        last_val = all_vals[-1] # कल का आखिरी नंबर

        # --- यहाँ से आपका पुराना वर्किंग लॉजिक शुरू होता है ---
        scores = Counter()

        # A/B ट्रांजिशन और अंकों की चाल (सिर्फ पुरानी हिस्ट्री से)
        def get_g(n): return "A" if 0 <= n <= 49 else "B"
        last_g = get_g(last_val)
        
        # ग्रुप ट्रांजिशन (इतिहास से)
        group_series = [get_g(n) for n in all_vals]
        trans_map = {"A": [], "B": []}
        for i in range(len(group_series)-1):
            trans_map[group_series[i]].append(group_series[i+1])
        
        # टारगेट ग्रुप चुनना
        target_g = Counter(trans_map[last_g]).most_common(1)[0][0] if trans_map[last_g] else "A"

        # अंकों का सफर (Digit Mapping)
        digit_trans = {i: [] for i in range(10)}
        for i in range(len(all_vals)-1):
            digit_trans[all_vals[i]%10].append(all_vals[i+1]%10)
        
        target_digits = [d for d, c in Counter(digit_trans.get(last_val%10, [])).most_common(4)]
        
        # नंबरों का निर्माण (सिर्फ टारगेट ग्रुप वाले)
        for d in target_digits:
            for i in range(10):
                n1, n2 = d*10+i, i*10+d
                if get_g(n1) == target_g: scores[n1] += 100
                if get_g(n2) == target_g: scores[n2] += 100

        # टॉप 10 चुनाव
        final_list = [n for n, s in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_list)])
        
        analysis = f"पिछले {last_g} से {target_g} की चाल | अंकों का आधार: {target_digits}"
        
        return analysis, top_10_str, final_list
    except:
        return "Scanning History..", "N/A", []

# --- 2. UI सेटअप ---
st.set_page_config(page_title="MAYA AI Static Vision", layout="wide")
st.title("🛡️ MAYA AI: v55 Static-Vision Engine")
st.info("💡 **सुधार:** यह कोड अब आज का डेटा डालने के बाद भी प्रेडिक्शन नहीं बदलेगा।")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        # यूजर से तारीख पूछना
        target_date = st.date_input("📅 प्रेडिक्शन की तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 फिक्स्ड प्रेडिक्शन स्कैन"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                # यहाँ हमने सुनिश्चित किया कि एनालिसिस सिर्फ टारगेट डेट से पहले का हो
                info, picks, raw_list = get_v55_static_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "नतीजा": actual, "परिणाम": res_emoji, "एनालिसिस": info, "फिक्स्ड टॉप 10": picks})
            
            st.table(pd.DataFrame(report))
            st.warning("🔒 **Static-Mode:** अब रिजल्ट एक्सेल में होने के बावजूद प्रेडिक्शन वही रहेगी जो रिजल्ट आने से पहले थी।")
    except Exception as e:
        st.error(f"Error: {e}")
        
