import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime, timedelta
import scipy.stats as stats

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="VIP PARTNER - Ingénierie Patrimoniale", layout="wide")

# --- DESIGN SYSTÈME (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #0E1117;
        color: #FFFFFF;
    }}
    .metric-card {{
        background-color: #0A1A3F;
        border: 1px solid #B5A27B;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }}
    div.stButton > button:first-child {{
        background-color: #B5A27B;
        color: #0A1A3F;
        border-weight: bold;
    }}
    header {{background-color: #0A1A3F !important;}}
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS UTILES & CACHING ---
@st.cache_data
def fetch_data(ticker, period="1y"):
    """Récupère les données boursières avec gestion d'erreur."""
    try:
        data = yf.download(ticker, period=period)
        if data.empty: return None
        return data
    except Exception:
        return None

def calculate_rsi(data, window=14):
    """Calcule l'indice de force relative (RSI)."""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- GÉNÉRATION PDF ---
class PDF(FPDF):
    def header(self):
        try:
            self.image('logo.png', 10, 8, 33)
        except:
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'VIP PARTNER', 0, 1, 'L')
        self.set_font('Arial', 'B', 15)
        self.set_text_color(10, 26, 63) # Bleu Nuit
        self.cell(0, 10, 'Audit d\'Ingénierie Patrimoniale', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Document confidentiel - VIP PARTNER - Disclaimer : Les performances passées ne préjugent pas des performances futures.', 0, 0, 'C')

# --- INTERFACE PRINCIPALE ---
st.sidebar.title("VIP PARTNER")
st.sidebar.image("logo.png") if fetch_data("^GSPC") is not None else st.sidebar.write("🔒 Accès Conseiller")

menu = st.sidebar.radio("Navigation", ["Marché", "Portefeuille & VaR", "Audit Patrimonial", "IA Chat (Expert)"])

# --- MODULE 1 : ANALYSE MARCHÉ ---
if menu == "Marché":
    st.title("📈 Analyse de Marché Haute Définition")
    ticker = st.text_input("Entrez un Ticker (ex: AI.PA, BTC-USD, MSFT)", "AI.PA")
    
    data = fetch_data(ticker)
    if data is not None:
        col1, col2, col3 = st.columns(3)
        last_price = data['Close'].iloc[-1].item()
        change = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100).item()
        
        col1.metric("Prix Actuel", f"{last_price:.2f} €", f"{change:.2f}%")
        
        # Graphique Chandelier
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                        open=data['Open'], high=data['High'],
                        low=data['Low'], close=data['Close'], name="Cours")])
        fig.update_layout(template="plotly_dark", title=f"Historique {ticker}", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Impossible de récupérer les données pour ce ticker.")

# --- MODULE 2 : PORTEFEUILLE ---
elif menu == "Portefeuille & VaR":
    st.title("💼 Optimisation & Risque")
    
    col1, col2 = st.columns(2)
    with col1:
        capital = st.number_input("Capital Initial (€)", value=100000)
    with col2:
        horizon = st.slider("Horizon de placement (ans)", 1, 30, 5)

    # Simulation simplifiée VaR
    st.subheader("Analyse du Risque (Value at Risk)")
    st.info("La VaR 95% à 1 jour mesure la perte maximale potentielle dans 95% des cas.")
    
    # Placeholder pour calculs complexes
    weights = [0.6, 0.4] # 60% Actions / 40% Oblig
    vol = 0.15 # Volatilité 15%
    var_95 = stats.norm.ppf(0.95) * vol * np.sqrt(1/252) * capital
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>VaR 95% Estimée</h3>
        <h2 style="color: #B5A27B;">- {var_95:.2f} €</h2>
        <p>Risque de perte maximale quotidienne pour un capital de {capital} €</p>
    </div>
    """, unsafe_allow_html=True)

# --- MODULE 3 : AUDIT PATRIMONIAL ---
elif menu == "Audit Patrimonial":
    st.title("⚖️ Simulateur de Capitalisation & Fiscalité")
    
    c1, c2, c3 = st.columns(3)
    epargne_mensuelle = c1.number_input("Versement Mensuel (€)", value=500)
    rendement_espere = c2.slider("Rendement Annuel (%)", 0.0, 10.0, 5.0)
    inflation = c3.slider("Inflation (%)", 0.0, 5.0, 2.0)

    years = np.arange(1, 31)
    # Formule intérêts composés : A = P * (((1 + r)^n - 1) / r)
    r_mensuel = (rendement_espere / 100) / 12
    capital_final = [epargne_mensuelle * (((1 + r_mensuel)**(y*12) - 1) / r_mensuel) for y in years]
    
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(x=years, y=capital_final, fill='tozeroy', line_color='#B5A27B'))
    fig_comp.update_layout(title="Projection du Capital sur 30 ans", template="plotly_dark")
    st.plotly_chart(fig_comp, use_container_width=True)

    if st.button("Générer le rapport PDF"):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Analyse pour un versement de {epargne_mensuelle} euros/mois.", ln=1)
        pdf.cell(200, 10, txt=f"Capital estimé à 30 ans : {capital_final[-1]:,.2f} euros.", ln=1)
        pdf.output("Rapport_VIP_Partner.pdf")
        st.success("Rapport généré avec succès !")

# --- MODULE 4 : IA CHAT ---
elif menu == "IA Chat (Expert)":
    st.title("🤖 Assistant Fiscal VIP")
    st.write("Posez vos questions sur le LMNP, le PEA ou l'Assurance Vie.")
    
    user_input = st.chat_input("Ex: Quels sont les abattements pour une AV de plus de 8 ans ?")
    if user_input:
        st.chat_message("user").write(user_input)
        with st.chat_message("assistant"):
            st.write("C'est une excellente question sur la fiscalité française. (Ceci est une simulation de réponse IA). Pour une Assurance Vie de plus de 8 ans, vous bénéficiez d'un abattement annuel de 4 600 € (célibataire) ou 9 200 € (couple) sur les plus-values.")
