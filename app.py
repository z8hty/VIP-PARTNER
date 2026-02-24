import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

st.set_page_config(page_title="VIP PARTNER | Outils CGP", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(181, 162, 123, 0.1);
        border-left: 5px solid #B5A27B;
        padding: 10px 20px;
        border-radius: 5px;
    }
    h1, h2, h3 { color: #B5A27B !important; font-family: 'Arial', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS MÉTIERS ---
def determiner_devise(ticker):
    if "-USD" in ticker.upper() or ticker.upper() in ["AAPL", "MSFT", "TSLA", "SPY"]: return "$"
    elif ".L" in ticker.upper(): return "£"
    elif ".CHF" in ticker.upper(): return "CHF"
    return "€"

def calcul_usufruit_nue_prop(age):
    """Article 669 du CGI"""
    if age <= 20: return 0.9, 0.1
    elif age <= 30: return 0.8, 0.2
    elif age <= 40: return 0.7, 0.3
    elif age <= 50: return 0.6, 0.4
    elif age <= 60: return 0.5, 0.5
    elif age <= 70: return 0.4, 0.6
    elif age <= 80: return 0.3, 0.7
    elif age <= 90: return 0.2, 0.8
    else: return 0.1, 0.9

# --- SIDEBAR ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Expertise Patrimoniale", [
    "1. Marchés Financiers", 
    "2. Capitalisation & Fiscalité", 
    "3. Impôt sur la Fortune (IFI)", 
    "4. Transmission & Démembrement"
])

# ==========================================
# MODULE 1 : MARCHÉS FINANCIERS
# ==========================================
if menu == "1. Marchés Financiers":
    st.title("📈 Analyse des Supports")
    ticker = st.text_input("Ticker (ex: CW8.PA, AI.PA, BTC-USD, AAPL)", "BTC-USD")
    
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")
        
        if not data.empty:
            devise = determiner_devise(ticker)
            
            c1, c2, c3, c4 = st.columns(4)
            current_price = data['Close'].iloc[-1]
            first_price = data['Close'].iloc[0]
            perf = ((current_price / first_price) - 1) * 100
            volatility = data['Close'].pct_change().std() * np.sqrt(252) * 100
            
            # Calcul du Max Drawdown (Perte maximale)
            roll_max = data['Close'].cummax()
            drawdown = data['Close'] / roll_max - 1.0
            max_drawdown = drawdown.min() * 100
            
            c1.metric("Dernier Cours", f"{current_price:,.2f} {devise}")
            c2.metric("Performance 1 an", f"{perf:.2f} %")
            c3.metric("Volatilité", f"{volatility:.2f} %")
            c4.metric("Max Drawdown", f"{max_drawdown:.2f} %")
            
            fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], line=dict(color='#B5A27B', width=2))])
            fig.update_layout(title=f"Historique {ticker} (en {devise})", xaxis_title="Date", yaxis_title=f"Prix ({devise})")
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        else:
            st.warning("Aucune donnée pour ce ticker.")
    except Exception as e:
        st.error(f"Erreur de connexion : {e}")

# ==========================================
# MODULE 2 : CAPITALISATION & PFU
# ==========================================
elif menu == "2. Capitalisation & Fiscalité":
    st.title("💰 Croissance & Fiscalité (Flat Tax)")
    
    c1, c2, c3, c4 = st.columns(4)
    capital_init = c1.number_input("Capital initial (€)", value=50000, step=5000)
    versement = c2.number_input("Versement mensuel (€)", value=500, step=100)
    taux_brut = c3.number_input("Rendement cible brut (%)", value=6.0, step=0.5)
    annees = c4.slider("Horizon (Années)", 5, 40, 15)
    
    inflation = st.slider("Inflation annuelle estimée (%)", 0.0, 5.0, 2.0, step=0.1)
    
    taux_mensuel = (taux_brut / 100) / 12
    mois = annees * 12
    
    cap = capital_init
    total_versements = capital_init
    for _ in range(mois):
        cap = cap * (1 + taux_mensuel) + versement
        total_versements += versement
        
    plus_values = cap - total_versements
    pfu = plus_values * 0.30 # Flat tax 30%
    capital_net_fiscal = cap - pfu
    
    # Impact inflation (Valeur actualisée)
    pouvoir_achat_net = capital_net_fiscal / ((1 + (inflation/100))**annees)
    
    st.subheader("Synthèse à la sortie")
    r1, r2, r3 = st.columns(3)
    r1.metric("Capital Brut Construit", f"{cap:,.0f} €".replace(',', ' '))
    r2.metric("Plus-values générées", f"{plus_values:,.0f} €".replace(',', ' '))
    r3.metric("Impôts (PFU 30%)", f"- {pfu:,.0f} €".replace(',', ' '))
    
    st.info(f"💶 **Valeur Nette dans la poche du client : {capital_net_fiscal:,.0f} €**")
    st.warning(f"🛒 **Pouvoir d'achat réel** (Ajusté de {inflation}% d'inflation) : **{pouvoir_achat_net:,.0f} €** (C'est ce que l'argent vaudra vraiment dans {annees} ans).")

# ==========================================
# MODULE 3 : IFI COMPLEXE
# ==========================================
elif menu == "3. Impôt sur la Fortune (IFI)":
    st.title("🏛️ Simulateur IFI (Barème 2024)")
    
    st.write("Calcul du patrimoine net taxable avec abattement Résidence Principale et dettes.")
    
    c1, c2, c3 = st.columns(3)
    rp = c1.number_input("Valeur Résidence Principale (€)", value=900000, step=50000)
    autre_immo = c2.number_input("Autres Biens Immobiliers & SCPI (€)", value=600000, step=50000)
    dettes = c3.number_input("Passif déductible (Capital restant dû, etc.) (€)", value=150000, step=10000)
    
    rp_nette = rp * 0.70 # Abattement 30% légal
    patrimoine_net_taxable = rp_nette + autre_immo - dettes
    
    st.markdown("### Synthèse du Patrimoine")
    r1, r2 = st.columns(2)
    r1.metric("Résidence Principale (après abattement 30%)", f"{rp_nette:,.0f} €".replace(',', ' '))
    r2.metric("Patrimoine Net Taxable IFI", f"{patrimoine_net_taxable:,.0f} €".replace(',', ' '))
    
    ifi = 0
    if patrimoine_net_taxable > 1300000:
        p = patrimoine_net_taxable
        if p > 10000000: ifi += (p - 10000000) * 0.015; p = 10000000
        if p > 5000000: ifi += (p - 5000000) * 0.0125; p = 5000000
        if p > 2570000: ifi += (p - 2570000) * 0.01; p = 2570000
        if p > 1300000: ifi += (p - 1300000) * 0.007; p = 1300000
        if p > 800000: ifi += (p - 800000) * 0.005 # Le barème commence à 800k si le seuil de 1.3M est franchi
        
        # Application de la décote légale pour les patrimoines entre 1.3M et 1.4M
        if 1300000 < patrimoine_net_taxable < 1400000:
            decote = 17500 - (0.0125 * patrimoine_net_taxable)
            ifi = max(0, ifi - decote)
            st.info(f"Une décote de lissage de {decote:,.0f} € a été appliquée.")
            
        st.error(f"🔴 Montant de l'IFI à régler : {ifi:,.0f} € / an")
    else:
        st.success("🟢 Patrimoine Net Taxable inférieur à 1 300 000 €. Vous n'êtes pas assujetti à l'IFI.")

# ==========================================
# MODULE 4 : DÉMEMBREMENT
# ==========================================
elif menu == "4. Transmission & Démembrement":
    st.title("👨‍👩‍👧‍👦 Démembrement de Propriété (Art. 669 CGI)")
    st.write("Stratégie de donation avec réserve d'usufruit.")
    
    c1, c2 = st.columns(2)
    valeur_bien = c1.number_input("Valeur du bien en Pleine Propriété (€)", value=400000, step=10000)
    age_donateur = c2.slider("Âge du donateur (Usufruitier)", 40, 95, 65)
    
    usufruit_pct, nue_prop_pct = calcul_usufruit_nue_prop(age_donateur)
    
    valeur_usufruit = valeur_bien * usufruit_pct
    valeur_nue_prop = valeur_bien * nue_prop_pct
    
    r1, r2 = st.columns(2)
    r1.metric(f"Valeur Usufruit ({usufruit_pct*100:.0f}%)", f"{valeur_usufruit:,.0f} €".replace(',', ' '))
    r2.metric(f"Valeur Nue-Propriété ({nue_prop_pct*100:.0f}%)", f"{valeur_nue_prop:,.0f} €".replace(',', ' '))
    
    st.info(f"💡 **Stratégie :** En donnant la Nue-Propriété aujourd'hui (à {age_donateur} ans), les droits de succession seront calculés uniquement sur **{valeur_nue_prop:,.0f} €** au lieu de {valeur_bien:,.0f} €. Au décès, l'usufruit s'éteint et l'enfant récupère la pleine propriété sans impôt supplémentaire.")
