import streamlit as st
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import numpy as np
import re
from huggingface_hub import login

# Page config
st.set_page_config(
    page_title="Phishing Psychological Trigger Analyser",
    page_icon="🎣",
    layout="wide"
)

# ---- Preprocessing ----
def preprocess_email(text):
    text = str(text)
    text = re.sub(r'http\S+|https\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'\bmonkey\s*org\b|\bjose\s*monkey\b|\bmonkey\b|\bjose\b',
                  '', text, flags=re.IGNORECASE)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ---- Per-label thresholds ----
thresholds = {
    'Urgency':      0.35,
    'Scarcity':     0.50,
    'Authority':    0.35,
    'Fear':         0.50,
    'Social Proof': 0.35,
    'Reciprocity':  0.35,
    'Liking':       0.35,
}

# ---- Load model ----
@st.cache_resource
def load_model():
    # Read HF token from Streamlit secrets 
    hf_token = st.secrets["HF_TOKEN"]
    login(token=hf_token)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    tokenizer = RobertaTokenizer.from_pretrained(
        "amyning/roberta-phishing-trigger",
        token=hf_token
    )
    model = RobertaForSequenceClassification.from_pretrained(
        "amyning/roberta-phishing-trigger",
        token=hf_token
    )
    model.to(device)
    model.eval()
    return tokenizer, model, device

tokenizer, model, device = load_model()

categories = ['Urgency', 'Scarcity', 'Authority', 'Fear', 'Social Proof', 'Reciprocity', 'Liking']

descriptions = {
    'Urgency':      'Creates time pressure to force quick decisions without careful thinking.',
    'Scarcity':     'Implies limited availability to make the offer seem more valuable.',
    'Authority':    'Impersonates trusted organisations or officials to gain compliance.',
    'Fear':         'Threatens negative consequences to manipulate emotional response.',
    'Social Proof': "Uses others' behaviour to influence decisions.",
    'Reciprocity':  'Offers tangible monetary or material benefit to create a sense of obligation.',
    'Liking':       "Builds rapport, flattery, or emotional appeal to lower the recipient's guard."
}

tips = {
    'Urgency':      '⚠️ Legitimate organisations rarely demand immediate action. Take time to verify.',
    'Scarcity':     '⚠️ Artificial scarcity is a common manipulation tactic. Question the legitimacy.',
    'Authority':    '⚠️ Always verify sender identity through official channels, not links in the email.',
    'Fear':         '⚠️ Do not act out of fear. Contact the organisation directly using official contact details.',
    'Social Proof': "⚠️ Claims about others' behaviour cannot be verified and may be fabricated.",
    'Reciprocity':  '⚠️ Unsolicited gifts or offers often come with hidden costs or intentions.',
    'Liking':       '⚠️ Excessive flattery or familiarity from unknown senders is a red flag.'
}

emojis = {
    'Urgency':      '⏰',
    'Scarcity':     '🔒',
    'Authority':    '🏛️',
    'Fear':         '😨',
    'Social Proof': '👥',
    'Reciprocity':  '🎁',
    'Liking':       '😊'
}

examples = {
    # ---- Phishing / Scam (簡單 → 複雜) ----
    '🚨 1. Free Gift': """Hello!
You've been selected to claim a complimentary Oral-B Dental Kit from United Healthcare.
Complete a short survey and receive yours — limited stock available!
Keep Your Smile Healthy
Claim Your Oral-B Dental Kit Now
Oral-B Dental Kit
The Oral-B Complete Dental Kit brings together the ultimate in oral care technology and daily freshness. Featuring the premium Oral-B iO10 electric toothbrush designed by Braun, advanced AquaCare Series 6 irrigator, soothing Sensitivity & Gum Calm toothpaste, refreshing Arctic Mint mouthwash, and essential mint floss, this kit ensures a superior clean, healthier gums, and lasting freshness with every use.
Claim Yours""",

    '🚨 2. Gmail Subscription Termination': """GMAIL - Subscription Termination Notice
Your Subscription has Closed at 01-04-2026.
[ Final Warning ]
Account Details
Account ID: 
User: fishcollector2025
Discount: 90%
Limited Time: 01-04-2026
Dear fishcollector2025,
We have tried to reach your account several times with notifications and alerts, but we did not receive a response from you.
Renew your subscription because you are now unprotected against cyber attacks and hackers. For your security, we strongly recommend renewing your subscription.
If you have not renewed your membership within 48 hours, your account will be closed.
Secure Your Device
GMAIL Support Team""",

    '🚨 3. IC3/FBI Restitution Scam': """Internet Crime Complaint Center (IC3)
In Partnership with: FBI/NU3C/IAI
REF: FLP-IP/2422-FM10089/0877
Our records indicate that you are eligible to receive restitution for one or more of the internet fraud schemes you've been a victim of. The case was closed based on the following terms: Restitution Order — seized assets shall be liquidated and converted into a restitution fund.
The perpetrator and his group of co-offenders had over 2000 aliases originating from China, Russia, Nigeria, Ghana, London, and many African countries. Our records indicate that you have been a victim of fraud because your contact details were found on several devices belonging to the perpetrator.
After having consistently pursued the case for two years, we successfully secured restitution payments of $10.5M for each victim. Restitutions are ordered to be paid immediately.
To start receiving your restitution benefits, you are required to pay $165 for the IMF CLEARANCE CERTIFICATE. Contact the bank manager (EDWARD GRADY) immediately using your reference code REF: FLP-IP/2422-FM10089/0877.
Sincerely Yours,
Ambassador Internet Relations
Internet Crime Complaint Center (IC3)""",

    '🚨 4. Sympathy Exploitation': """Dear Friend,

I am very sorry to message you like this, but I am in a very difficult situation and I do not know who else I can ask for help.

My rent is overdue, my phone bill has already been disconnected once, and I only have enough money left for one small meal today. I have tried asking people around me, but everyone says they cannot help. I feel ashamed writing this, but I am truly desperate.

If I cannot pay at least part of the emergency fee before tonight, I may lose the temporary room I am staying in. I only need a small amount to get through the next few days. Even $20 or $30 would mean a lot to me right now.

Please help me by sending support through this secure assistance form:

[Support Request Form]
https://help-support-review.example.com/urgent-case

I promise I will remember your kindness. I would not ask unless I really had no other choice. Please do not ignore this message — tonight is the deadline.

Thank you from the bottom of my heart.

Sincerely,
Emily Carter)""",

    '🚨 5. 水務署繳費通知 (Chinese Demo)': """水務署通知函
文號：WSD/ACC/2026/0318-02
主旨：用水帳戶資料更新及帳務狀況提示通知
致：用戶
本署於例行帳務核對期間，發現閣下名下用水帳戶尚有未完成處理之水費及相關收費項目。為保障帳戶運作正常及確保供水服務不受影響，現將有關事項通知如下：
一、帳戶資料查閱
有關帳戶編號、供水地址及帳務紀錄等詳情，請登入本署網上帳戶服務系統查閱最新資料。
二、帳務狀況說明
應繳金額：HK$18.54
繳費平台：水務署網上帳戶服務
官方網站：https://www.wsd.gov.hk
上述款項現時仍顯示為待處理狀態。為免產生額外費用或影響日後帳務安排，請於 2026年3月6日晚上12時前 完成繳費程序。
根據現行收費規定，如逾期未繳，有關帳項或會按規例加收逾期附加費（滯納金），並可能影響帳戶後續安排。建議閣下儘早登入系統核實帳戶狀況及辦理相關手續。
特此通知
水務署客戶服務組
日期：2026年3月5日""",

    '🚨 6. 東京電力エナジーパートナー (Japanese Demo)': """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
　東京電力エナジーパートナー　重要なお知らせ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

東京電力エナジーパートナーでございます。

誠に恐れ入りますが、これまで複数回にわたりご案内を
申し上げておりますものの、下記料金につきまして
本日23時59分時点において、ご入金の確認が
未だ取れておりません。

本件は電気需給契約約款第28条に基づき、
本日中にご入金の確認が取れない場合、事前の通告なく
電気の供給を停止させていただきます。

なお、供給停止後の復電につきましては、復電手数料
ならびに保証金として、別途 18,300円（税込）を
申し受けることとなりますので、あらかじめご承知おき
ください。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 未納料金明細（令和8年4月分）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

　基本料金（30A）　　　　　　　　　　842.40円
　従量料金（260kWh）　　　　　　　7,854.20円
　燃料費調整額　　　　　　　　　　3,201.00円
　再生可能エネルギー発電促進賦課金　　967.40円
　━━━━━━━━━━━━━━━━━━━━━━━━━━━
　合計　　　　　　　　　　　　　 12,865.00円

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ お支払期限
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

　本日　23時59分

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ お支払い方法のご確認
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

下記URLより、お支払い状況の確認およびお手続きを
お願いいたします。

　▼ お支払い・納付状況の確認はこちら
　https://TEPCO7e36ccbfb5b54a9cabb428581f77534f.csjyu.cn/TEPCO7e08c8b0f2944738b9980df676e9749e

現在ご利用いただけるお支払い方法は以下のとおりです。
　・クレジットカード
　・口座振替
　・PayPay
　・コンビニエンスストア払込票

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ ご注意事項
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

・本メールと行き違いで既にお支払いを完了されて
　いる場合は、何卒ご容赦くださいますようお願い
　申し上げます。

・本件に関するお問い合わせは、上記URLより
　チャットサポートをご利用ください。
　（受付時間 9:00～17:00／土日祝日を除く）

・本メールは送信専用のため、ご返信いただいても
　ご対応いたしかねます。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


東京電力エナジーパートナー株式会社
© TEPCO. All Rights Reserved.
催告番号：TYO-20260430-0387""",

    # ---- Legitimate ----
    '✅ Legitimate: Meeting Reminder': """Hi John, Just a reminder that the team meeting is scheduled for Wednesday at 3pm in Conference Room B. Please bring your project update slides. See you there. Thanks, Mary.""",

    '✅ Legitimate: IT Maintenance': """Hi Team, This is a reminder that our scheduled system maintenance will take place this Saturday, 2 November from 11pm to 2am. During this window, access to the internal portal will be unavailable. Please save your work before the maintenance window begins. No action is required on your part. Contact the IT helpdesk at helpdesk@company.com if you have any questions. Thanks, IT Operations Team.""",
}

# Session state
if 'email_input' not in st.session_state:
    st.session_state.email_input = ''

# Sidebar
with st.sidebar:
    st.header("📧 Example Emails")

    st.markdown("**🚨 Phishing / Scam**")
    for name, content in {k: v for k, v in examples.items() if k.startswith('🚨')}.items():
        if st.button(name, use_container_width=True):
            st.session_state.email_input = content

    st.divider()

    st.markdown("**✅ Legitimate**")
    for name, content in {k: v for k, v in examples.items() if k.startswith('✅')}.items():
        if st.button(name, use_container_width=True):
            st.session_state.email_input = content

    st.divider()
    st.markdown("**About this tool**")
    st.markdown("This system identifies psychological manipulation tactics used in phishing emails based on Cialdini's Principles of Influence.")
    st.caption("Note: This tool detects persuasive trigger language and is not a phishing classifier. Legitimate emails may also contain trigger language in a different context.")

# Main
st.title("🎣 Phishing Psychological Trigger Analyser")
st.markdown("Paste a suspicious email below to identify psychological manipulation tactics used by attackers.")

email_text = st.text_area(
    "📧 Email Content",
    value=st.session_state.email_input,
    height=250,
    placeholder="Paste email content here..."
)

if st.button("🔍 Analyse Email", type="primary"):
    if not email_text.strip():
        st.warning("Please paste an email to analyse.")
    else:
        with st.spinner("Analysing..."):
            cleaned_text = preprocess_email(email_text)
            inputs = tokenizer(
                cleaned_text, return_tensors='pt',
                truncation=True, padding=True, max_length=512
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
            probs = torch.sigmoid(outputs.logits).squeeze().cpu().numpy()

        with st.expander("🔍 Debug: Raw probabilities", expanded=False):
            for cat, prob in zip(categories, probs):
                st.write(f"{cat}: {prob:.4f} (threshold: {thresholds[cat]})")

        # Apply per-label thresholds
        detected     = [(cat, float(probs[i])) for i, cat in enumerate(categories)
                        if probs[i] > thresholds[cat]]
        not_detected = [(cat, float(probs[i])) for i, cat in enumerate(categories)
                        if probs[i] <= thresholds[cat]]

        detected_probs = [score for _, score in detected]
        risk_score = float(np.mean(detected_probs) * 100) if detected_probs else float(np.mean(probs) * 100)

        st.divider()

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("🎯 Psychological Trigger Intensity", f"{risk_score:.1f}%")
            if risk_score > 60:
                st.error("High Intensity — Strong persuasive language detected. Treat with caution.")
            elif risk_score > 30:
                st.warning("Medium Intensity — Some persuasive language detected.")
            else:
                st.success("Low Intensity — Minimal psychological triggers detected.")

        with col2:
            st.markdown("**✅ Detected Triggers:**")
            if detected:
                for cat, score in sorted(detected, key=lambda x: x[1], reverse=True):
                    st.progress(score, text=f"{emojis[cat]} {cat}: {score*100:.1f}%")
            else:
                st.info("No psychological triggers detected.")

            if not_detected:
                st.markdown("**➖ Not Detected:**")
                for cat, score in sorted(not_detected, key=lambda x: x[1], reverse=True):
                    st.progress(score, text=f"{emojis[cat]} {cat}: {score*100:.1f}%")

        st.divider()

        if detected:
            st.subheader("📋 Detailed Analysis")
            for cat, score in sorted(detected, key=lambda x: x[1], reverse=True):
                with st.expander(f"{emojis[cat]} {cat} — {score*100:.1f}% confidence"):
                    st.markdown(f"**What is {cat}?**")
                    st.markdown(descriptions[cat])
                    st.markdown("**How to protect yourself:**")
                    st.markdown(tips[cat])

        st.divider()
        st.caption(
            "⚠️ This tool identifies persuasive language patterns commonly associated with phishing. "
            "High scores indicate psychological manipulation tactics but should not be used as the sole "
            "indicator of phishing. Always verify suspicious emails through official channels."
        )