import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. प्रोबेबिलिटी ट्रांजिशन इंजन (The Logic You Suggested) ---
def get_probability_transition_picks(df, s_name, target_date):
    try:
        # डेटा क्लीनिंग
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        if len(df_clean) < 365: return "Data Kam", "N/A", []

        # A. प्रोबेबिलिटी ग्रुप बनाना (1 साल का डेटा)
        one_year_ago = target_date - datetime.timedelta(days=365)
        hist_year = df_clean[(df_clean['DATE'] >= one_year_ago) & (df_clean['DATE'] < target_date)]
        
        # नंबरों को उनकी फ्रीक्वेंसी के हिसाब से रैंक देना (0 to 99)
        counts = Counter(hist_year['NUM'].astype(int))
        sorted_nums = [n for n, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)]
        # जो नंबर नहीं आए उन्हें अंत में जोड़ना
        for n in range(100):
            if n not in sorted_nums: sorted_nums.append(n)
        
        # रैंक मैप (Number -> Rank)
        rank_map = {val: i for i, val in enumerate(sorted_nums)}
        # ग्रुप मैप (Rank 0-9 = Group 0, 10-19 = Group 1...)
        group_nums = {g: sorted_nums[g*10 : (g+1)*10] for g in range(10)}

        # B. ट्रांजिशन एनालिसिस (किसे बाद क्या आता है?)
        # पिछले 200 दिनों की चाल देखना
        transitions = []
        recent_data = df_clean[df_clean['DATE'] < target_date].tail(200)
        vals = recent_data['NUM'].astype(int).tolist()
        for i in range(len(vals)-1):
            g_curr = rank_map.get(vals[i], 99) // 10
            g_next = rank_map.get(vals[i+1], 99) // 10
            transitions.append((g_curr, g_next))
        
        # C. प्रेडिक्शन (आज के ग्रुप के आधार पर कल का ग्रुप)
        last_val = vals[-1]
        last_group = rank_map.get(last_val, 99) // 10
        
        # इस ग्रुप के बाद सबसे ज्यादा बार कौन सा ग्रुप आया?
        following_groups = [next_g for curr_g, next_g in transitions if curr_g == last_group]
        if not following_groups:
            # अगर डेटा कम है तो सबसे हॉट ग्रुप (0) लें
            target_group = 0
        else:
            target_group = Counter(following_groups).most_common(1)[0][0]

        # D. फाइनल 10 अंक (उस ग्रुप के नंबर)
        final_10 = group_nums.get(target_group, sorted_nums[:10])
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_10)])
        
        analysis = f"📊 पिछला नंबर: {last_val:02d} (ग्रुप {last_group}) -> अगला संभावित ग्रुप: {target_group}"
        
        return analysis, top_10_str, final_10
    except Exception as e:
        return f"Error: {e}", "N/A", []

# --- 2. UI सेटअप ---
st.set_page_config(page_title="MAYA AI Prob-Transition", layout="wide")
st.title("🛡️ MAYA AI: Probability Transition Engine")
st.markdown("### आपने जो लॉजिक बताया: 'ग्रुप के बाद ग्रुप' की चाल")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 विश्लेषण की तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 प्रोबेबिलिटी ट्रांजिशन स्कैन"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            day_results = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, t_10, r_list = get_probability_transition_picks(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    try:
                        v = str(selected_row[s].values[0]).strip()
                        if v.replace('.','',1).isdigit():
                            actual = f"{int(float(v)):02d}"
                            res_emoji = "✅ PASS" if int(actual) in r_list else "❌"
                        else: actual = v
                    except: pass

                day_results.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "ग्रुप विश्लेषण": info, "टॉप 10 (Target Group)": t_10})
            
            st.table(pd.DataFrame(day_results))
            st.success("✅ **लॉजिक अपडेटेड:** यह कोड अब आपकी थ्योरी पर चल रहा है—'अगर ग्रुप 10 का नंबर आया है, तो उसके बाद कौन सा ग्रुप खुलेगा?'")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
