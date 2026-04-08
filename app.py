import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. ऑटो-डिजिट मैपिंग लॉजिक (Analyzing Your Real Data) ---
def get_auto_digit_mapping(df, s_name, target_date):
    try:
        # डेटा को साफ़ और व्यवस्थित करना
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # A. पूरे 5 साल का 'अंकों का सफर' एनालाइज करना (0-9)
        all_vals = df_clean[df_clean['DATE'] < target_date]['NUM'].astype(int).tolist()
        
        # हर अंक के बाद आने वाले अंकों को स्टोर करने के लिए डिक्शनरी
        digit_transitions = {i: [] for i in range(10)}
        
        for i in range(len(all_vals) - 1):
            curr_v = all_vals[i]
            next_v = all_vals[i+1]
            
            # आज के अंक (अंदर और बाहर)
            curr_digits = [curr_v // 10, curr_v % 10]
            # अगले दिन के अंक (अंदर और बाहर)
            next_digits = [next_v // 10, next_v % 10]
            
            for d in curr_digits:
                digit_transitions[d].extend(next_digits)

        # B. कल का रिजल्ट और उसके अंक निकालना
        yesterday_val = all_vals[-1]
        y_digits = [yesterday_val // 10, yesterday_val % 10]

        # C. कल के अंकों के आधार पर आज के 'सबसे हिट' अंक (Target Digits)
        target_digits = []
        for d in y_digits:
            # उस अंक के बाद सबसे ज्यादा बार आने वाले टॉप 4 अंक
            top_next = [digit for digit, count in Counter(digit_transitions[d]).most_common(4)]
            target_digits.extend(top_next)
        
        target_digits = list(set(target_digits)) # डुप्लीकेट हटाना

        # D. इन अंकों से बनने वाले टॉप 10 नंबर (00-99)
        candidate_nums = []
        for d in target_digits:
            for i in range(10):
                candidate_nums.append(d * 10 + i) # अंदर फिट
                candidate_nums.append(i * 10 + d) # बाहर फिट
        
        # इतिहास में इन नंबरों की अपनी पकड़ (Frequency)
        final_scores = Counter([n for n in candidate_nums if n in all_vals[-500:]])
        
        # टॉप 10 चुनाव
        final_list = [n for n, c in final_scores.most_common(10)]
        if len(final_list) < 10:
            for n in range(100):
                if n not in final_list: final_list.append(n)
                if len(final_list) >= 10: break

        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_list)])
        mapping_info = f"कल {yesterday_val:02d} था -> डेटा के अनुसार आज के अंक: {target_digits}"
        
        return mapping_info, top_10_str, final_list
    except Exception as e:
        return f"Error: {e}", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI Auto-Mapper", layout="wide")
st.title("🛡️ MAYA AI: v42 Auto-Digit Mapping Engine")
st.markdown("### आपकी Excel के 5 साल के डेटा का असली 'अंक ट्रांजिशन' विश्लेषण")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 ऑटो-मैपिंग स्कैन शुरू करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_auto_digit_mapping(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({
                    "शिफ्ट": s,
                    "असली नतीजा": actual,
                    "परिणाम": res_emoji,
                    "डेटा मैपिंग विश्लेषण": info,
                    "टॉप 10 मास्टर अंक": picks
                })
            
            st.table(pd.DataFrame(report))
            st.info("💡 **नोट:** यह कोड हर बार फाइल अपलोड होने पर 0-9 तक के अंकों की पूरी 'हिस्ट्री मैपिंग' दोबारा करता है, ताकि प्रेडिक्शन बिल्कुल ताजा रहे।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
