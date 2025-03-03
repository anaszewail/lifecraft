import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pandas as pd
import io
import requests
import json
from prophet import Prophet
import uuid
import random

# إعداد الصفحة
st.set_page_config(
    page_title="LifeCraft™ - Craft Your Life",
    page_icon="🖌️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS فني مستوحى من المخطوطات
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&display=swap');
    * {font-family: 'Cinzel', serif;}
    .main {background: linear-gradient(135deg, #2D1B00, #4A2F00); color: #F9E8C9; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.8); background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAPUlEQVR4nGN4//8/AymG/////z8DAwP//////z8jIyP//////z8/P////z8/Pz8/P////z8/P////z8DAwMAvCkG/9nQ3gAAAABJRU5ErkJggg==');}
    h1, h2, h3 {background: linear-gradient(90deg, #D97706, #FCD34D); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700; letter-spacing: -1px; text-shadow: 0 2px 15px rgba(217,119,6,0.6);}
    .stButton>button {background: linear-gradient(90deg, #D97706, #FCD34D); color: #FFFFFF; border-radius: 50px; font-weight: 700; padding: 15px 35px; font-size: 18px; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); border: none; box-shadow: 0 8px 20px rgba(217,119,6,0.5); text-transform: uppercase;}
    .stButton>button:hover {transform: translateY(-5px) scale(1.05); box-shadow: 0 12px 30px rgba(252,211,77,0.7);}
    .stTextInput>div>div>input {background: rgba(255,255,255,0.1); border: 2px solid #D97706; border-radius: 15px; color: #FCD34D; font-weight: bold; padding: 15px; font-size: 18px; box-shadow: 0 5px 15px rgba(217,119,6,0.3); transition: all 0.3s ease;}
    .stTextInput>div>div>input:focus {border-color: #FCD34D; box-shadow: 0 5px 20px rgba(252,211,77,0.5);}
    .stSelectbox>label, .stRadio>label {color: #FCD34D; font-size: 22px; font-weight: 700; text-shadow: 1px 1px 5px rgba(0,0,0,0.5);}
    .stSelectbox>div>div>button {background: rgba(255,255,255,0.1); border: 2px solid #D97706; border-radius: 15px; color: #F9E8C9; padding: 15px; font-size: 18px;}
    .stRadio>div {background: rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; box-shadow: 0 5px 20px rgba(0,0,0,0.5);}
    .stMarkdown {color: #D4D4D4; font-size: 18px; line-height: 1.6;}
    .share-btn {background: linear-gradient(90deg, #10B981, #6EE7B7); color: #FFFFFF; border-radius: 50px; padding: 12px 25px; text-decoration: none; transition: all 0.3s ease; box-shadow: 0 5px 15px rgba(16,185,129,0.4); font-size: 16px;}
    .share-btn:hover {transform: translateY(-3px); box-shadow: 0 10px 25px rgba(110,231,183,0.6);}
    .animate-in {animation: fadeInUp 1s forwards; opacity: 0;}
    @keyframes fadeInUp {from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);}}
    </style>
""", unsafe_allow_html=True)

# تعريف الحالة الافتراضية
if "language" not in st.session_state:
    st.session_state["language"] = "English"
if "payment_verified" not in st.session_state:
    st.session_state["payment_verified"] = False
if "payment_initiated" not in st.session_state:
    st.session_state["payment_initiated"] = False
if "life_data" not in st.session_state:
    st.session_state["life_data"] = None

# بيانات PayPal Sandbox
PAYPAL_CLIENT_ID = "AQd5IZObL6YTejqYpN0LxADLMtqbeal1ahbgNNrDfFLcKzMl6goF9BihgMw2tYnb4suhUfprhI-Z8eoC"
PAYPAL_SECRET = "EPk46EBw3Xm2W-R0Uua8sLsoDLJytgSXqIzYLbbXCk_zSOkdzFx8jEbKbKxhjf07cnJId8gt6INzm6_V"
PAYPAL_API = "https://api-m.sandbox.paypal.com"

# دالة لجلب توصيات كتب من Open Library API
def fetch_openlibrary_books(life_goal):
    try:
        # تحليل الهدف لاستخراج كلمة مفتاحية
        keywords = life_goal.split()[0]  # أول كلمة كمفتاح (مثل "Travel" من "Travel the world")
        url = f"https://openlibrary.org/search.json?q={keywords}&limit=3"
        response = requests.get(url)
        response.raise_for_status()
        books = response.json().get("docs", [])
        recommendations = []
        for book in books:
            title = book.get("title", "Unknown Title")
            author = book.get("author_name", ["Unknown Author"])[0]
            recommendations.append(f"{title} by {author}")
        return recommendations if recommendations else ["The Alchemist by Paulo Coelho"]
    except Exception as e:
        st.error(f"Failed to fetch books from Open Library: {e}")
        return ["The Alchemist by Paulo Coelho"]  # قيمة افتراضية في حال الفشل

# العنوان والترحيب
st.markdown("""
    <h1 style='font-size: 60px; text-align: center; animation: fadeInUp 1s forwards;'>LifeCraft™</h1>
    <p style='font-size: 24px; text-align: center; animation: fadeInUp 1s forwards; animation-delay: 0.2s;'>
        Craft Your Life’s Masterpiece!<br>
        <em>By Anas Hani Zewail • Contact: +201024743503</em>
    </p>
""", unsafe_allow_html=True)

# واجهة المستخدم
st.markdown("<h2 style='text-align: center;'>Paint Your Life</h2>", unsafe_allow_html=True)
life_goal = st.text_input("Enter Your Life Goal (e.g., Travel the world):", "Travel the world", help="What’s your masterpiece?")
language = st.selectbox("Select Language:", ["English", "Arabic"])
st.session_state["language"] = language
plan = st.radio("Choose Your Craft Plan:", ["Craft Peek (Free)", "Craft Spark ($4)", "Craft Artisan ($9)", "Craft Master ($18)", "Craft Legend ($30/month)"])
st.markdown("""
    <p style='text-align: center;'>
        <strong>Craft Peek (Free):</strong> Quick Life Glimpse<br>
        <strong>Craft Spark ($4):</strong> Life Canvas + Basic Report<br>
        <strong>Craft Artisan ($9):</strong> Life Forge + Full Report<br>
        <strong>Craft Master ($18):</strong> Life Forecast + Book Recommendations<br>
        <strong>Craft Legend ($30/month):</strong> Daily Updates + Guild Access
    </p>
""", unsafe_allow_html=True)

# دوال PayPal
def get_paypal_access_token():
    try:
        url = f"{PAYPAL_API}/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}
        response = requests.post(url, headers=headers, auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET), data=data)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        st.error(f"Failed to connect to PayPal: {e}")
        return None

def create_payment(access_token, amount, description):
    try:
        url = f"{PAYPAL_API}/v1/payments/payment"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
        payment_data = {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{"amount": {"total": amount, "currency": "USD"}, "description": description}],
            "redirect_urls": {
                "return_url": "https://smartpulse-nwrkb9xdsnebmnhczyt76s.streamlit.app/?success=true",
                "cancel_url": "https://smartpulse-nwrkb9xdsnebmnhczyt76s.streamlit.app/?cancel=true"
            }
        }
        response = requests.post(url, headers=headers, json=payment_data)
        response.raise_for_status()
        for link in response.json()["links"]:
            if link["rel"] == "approval_url":
                return link["href"]
        st.error("Failed to extract payment URL.")
        return None
    except Exception as e:
        st.error(f"Failed to create payment request: {e}")
        return None

# دوال التحليل
def generate_life_canvas(life_goal, language):
    try:
        stages = ["Dream", "Plan", "Achieve"] if language == "English" else ["حلم", "تخطيط", "إنجاز"]
        progress = [20, 50, 80]  # بيانات داخلية ذكية تعكس التقدم
        plt.figure(figsize=(8, 6))
        plt.plot(stages, progress, marker='o', color="#FCD34D", linewidth=2.5, markersize=12)
        plt.title(f"{life_goal} Life Canvas" if language == "English" else f"لوحة حياة {life_goal}", fontsize=18, color="white", pad=20)
        plt.gca().set_facecolor('#2D1B00')
        plt.gcf().set_facecolor('#2D1B00')
        plt.xticks(color="white", fontsize=12)
        plt.yticks(color="white", fontsize=12)
        plt.grid(True, color="#D97706", alpha=0.3)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
        img_buffer.seek(0)
        plt.close()
        return img_buffer
    except Exception as e:
        st.error(f"Failed to generate life canvas: {e}")
        return None

def generate_life_forecast(life_goal, language):
    try:
        days = pd.date_range(start="2025-03-03", periods=7).strftime('%Y-%m-%d').tolist()
        progress = [random.randint(30, 90) for _ in range(7)]
        df = pd.DataFrame({'ds': days, 'y': progress})
        df['ds'] = pd.to_datetime(df['ds'])
        model = Prophet(daily_seasonality=True)
        model.fit(df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        plt.figure(figsize=(10, 6))
        plt.plot(df['ds'], df['y'], label="Life Progress" if language == "English" else "تقدم الحياة", color="#D97706", linewidth=2.5)
        plt.plot(forecast['ds'], forecast['yhat'], label="Forecast" if language == "English" else "التوقعات", color="#FCD34D", linewidth=2.5)
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color="#FCD34D", alpha=0.3)
        plt.title(f"{life_goal} 7-Day Life Forecast" if language == "English" else f"توقعات حياة {life_goal} لـ 7 أيام", fontsize=18, color="white", pad=20)
        plt.gca().set_facecolor('#2D1B00')
        plt.gcf().set_facecolor('#2D1B00')
        plt.legend(fontsize=12, facecolor="#2D1B00", edgecolor="white", labelcolor="white")
        plt.xticks(color="white", fontsize=10)
        plt.yticks(color="white", fontsize=10)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches="tight")
        img_buffer.seek(0)
        plt.close()
        
        # جلب توصيات الكتب من Open Library
        book_recommendations = fetch_openlibrary_books(life_goal)
        reco_text = "Your life is taking shape! Keep crafting.\nRecommended Books:\n" + "\n".join(book_recommendations)
        return img_buffer, reco_text
    except Exception as e:
        st.error(f"Failed to generate forecast: {e}")
        return None, None

def generate_report(life_goal, language, life_canvas_buffer, forecast_buffer=None, book_recommendations=None, plan="Craft Spark"):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        style.fontSize = 12
        style.textColor = colors.black
        style.fontName = "Helvetica"

        report = f"LifeCraft Report: {life_goal}\n"
        report += "=" * 50 + "\n"
        report += f"Plan: {plan}\n"
        report += "Your Life Canvas Unfolds!\n" if language == "English" else "لوحة حياتك تتكشف!\n"
        if language == "Arabic":
            report = arabic_reshaper.reshape(report)
            report = get_display(report)

        content = [Paragraph(report, style)]
        content.append(Image(life_canvas_buffer, width=400, height=300))
        
        if forecast_buffer and plan in ["Craft Artisan ($9)", "Craft Master ($18)", "Craft Legend ($30/month)"]:
            content.append(Image(forecast_buffer, width=400, height=300))
            content.append(Spacer(1, 20))
        
        if plan in ["Craft Master ($18)", "Craft Legend ($30/month)"] and book_recommendations:
            recommendations_text = "Craft Tip: Set small milestones - one step at a time!\nRecommended Books:\n" + "\n".join(book_recommendations)
            content.append(Paragraph(recommendations_text, style))
        
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Failed to generate report: {e}")
        return None

# تشغيل التطبيق
if st.button("Craft My Life!", key="craft_life"):
    with st.spinner("Crafting Your Life..."):
        life_canvas_buffer = generate_life_canvas(life_goal, language)
        if life_canvas_buffer:
            st.session_state["life_data"] = {"life_canvas": life_canvas_buffer.getvalue()}
            st.image(life_canvas_buffer, caption="Your Life Canvas")
            
            share_url = "https://lifecraft.streamlit.app/"  # استبدل بـ رابطك الفعلي بعد النشر
            telegram_group = "https://t.me/+K7W_PUVdbGk4MDRk"
            
            st.markdown("<h3 style='text-align: center;'>Share Your Craft!</h3>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<a href="https://api.whatsapp.com/send?text=See%20my%20life%20on%20LifeCraft:%20{share_url}" target="_blank" class="share-btn">WhatsApp</a>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<a href="https://t.me/share/url?url={share_url}&text=LifeCraft%20is%20masterful!" target="_blank" class="share-btn">Telegram</a>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<a href="https://www.facebook.com/sharer/sharer.php?u={share_url}" target="_blank" class="share-btn">Messenger</a>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<a href="https://discord.com/channels/@me?message=Join%20LifeCraft:%20{share_url}" target="_blank" class="share-btn">Discord</a>', unsafe_allow_html=True)
            
            st.markdown(f"<p style='text-align: center;'>Join our Telegram: <a href='{telegram_group}' target='_blank'>Click Here</a> - Share with 5 friends for a FREE report!</p>", unsafe_allow_html=True)
            
            if plan == "Craft Peek (Free)":
                st.info("Unlock your full life craft with a paid plan!")
            else:
                if not st.session_state["payment_verified"] and not st.session_state["payment_initiated"]:
                    access_token = get_paypal_access_token()
                    if access_token:
                        amount = {"Craft Spark ($4)": "4.00", "Craft Artisan ($9)": "9.00", "Craft Master ($18)": "18.00", "Craft Legend ($30/month)": "30.00"}[plan]
                        approval_url = create_payment(access_token, amount, f"LifeCraft {plan}")
                        if approval_url:
                            st.session_state["payment_url"] = approval_url
                            st.session_state["payment_initiated"] = True
                            unique_id = uuid.uuid4()
                            st.markdown(f"""
                                <a href="{approval_url}" target="_blank" id="paypal_auto_link_{unique_id}" style="display:none;">PayPal</a>
                                <script>
                                    setTimeout(function() {{
                                        document.getElementById("paypal_auto_link_{unique_id}").click();
                                    }}, 100);
                                </script>
                            """, unsafe_allow_html=True)
                            st.info(f"Life payment opened for {plan}. Complete it to craft your masterpiece!")
                elif st.session_state["payment_verified"]:
                    forecast_buffer, reco = generate_life_forecast(life_goal, language) if plan in ["Craft Artisan ($9)", "Craft Master ($18)", "Craft Legend ($30/month)"] else (None, None)
                    if forecast_buffer:
                        st.session_state["life_data"]["forecast_buffer"] = forecast_buffer.getvalue()
                        st.image(forecast_buffer, caption="7-Day Life Forecast")
                        st.write(reco)
                    
                    life_canvas_buffer = io.BytesIO(st.session_state["life_data"]["life_canvas"])
                    forecast_buffer = io.BytesIO(st.session_state["life_data"]["forecast_buffer"]) if "forecast_buffer" in st.session_state["life_data"] else None
                    book_recommendations = fetch_openlibrary_books(life_goal) if plan in ["Craft Master ($18)", "Craft Legend ($30/month)"] else None
                    pdf_data = generate_report(life_goal, language, life_canvas_buffer, forecast_buffer, book_recommendations, plan)
                    if pdf_data:
                        st.download_button(
                            label=f"Download Your {plan.split(' (')[0]} Life Report",
                            data=pdf_data,
                            file_name=f"{life_goal}_lifecraft_report.pdf",
                            mime="application/pdf",
                            key="download_report"
                        )
                        st.success(f"{plan.split(' (')[0]} Life Crafted! Share to inspire the guild!")
