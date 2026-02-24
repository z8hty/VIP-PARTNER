import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os
from fpdf import FPDF
import datetime

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

# --- FONCTIONS CACHÉES & CONVERSION ISIN ---
@st.cache_data(ttl=3600)
def isin_to_ticker(user_input):
    val = user_input.strip().upper()
    if len(val) == 12 and val[:2].isalpha():
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={val}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            data = res.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                return data['quotes'][0]['symbol']
        except:
            return None
    return val

@st.cache_data(ttl=3600)
def fetch_market_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="5y")
    return data

def determiner_devise(ticker):
    if "-USD" in ticker.upper() or ticker.upper() in ["AAPL", "MSFT", "TSLA", "SPY", "URTH"]: return "$"
    elif ".L" in ticker.upper(): return "£"
    elif ".CHF" in ticker.upper(): return "CHF"
    return "€"

def calcul_usufruit_nue_prop(age):
    if age <= 20: return 0.9, 0.1
    elif age <= 30: return 0.8, 0.2
    elif age <= 40: return 0.7, 0.3
    elif age <= 50: return 0.6, 0.4
    elif age <= 60: return 0.5, 0.5
    elif age <= 70: return 0.4, 0.6
    elif age <= 80: return 0.3, 0.7
    elif age <= 90: return 0.2, 0.8
    else: return 0.1, 0.9

# --- CLASSE PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(10, 26, 63) # Bleu Nuit
        self.cell(0, 10, "Bilan d'Expertise Patrimoniale", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 10, f"Edite le {datetime.date.today().strftime('%d/%m/%Y')} - VIP PARTNER", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} - Document strictement confidentiel", align="C")

# --- SIDEBAR & LOGO ---
chemin_logo = "logo.png"
if os.path.exists(chemin_logo):
    st.sidebar.image(chemin_logo, use_column_width=True)
else:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Expertise Patrimoniale", [
    "1. Marchés Financiers (Expert)", 
    "2. Capitalisation & Fiscalité", 
    "3. Impôt sur la Fortune (IFI)", 
    "4. Transmission & Démembrement"
])

# ==========================================
# MODULE 1 : MARCHÉS FINANCIERS (MULTI-ACTIFS)
# ==========================================
if menu == "1. Marchés Financiers (Expert)":
    st.title("📈 Analyse et Comparaison d'Actifs")
    st.markdown("Recherchez un ou plusieurs actifs séparés par une virgule (ISIN ou Ticker). Ex: `CW8.PA, LU1681043599, BTC-USD`.")
    
    col_input, col_period = st.columns([3, 1])
    recherche_utilisateur = col_input.text_input("Saisir les actifs :", "CW8.PA, AI.PA")
    periode_affichage = col_period.selectbox("Période d'affichage", ["1 an", "3 ans", "5 ans"])
    
    actifs_bruts = [x.strip() for x in recherche_utilisateur.split(",") if x.strip()]
    
    if actifs_bruts:
        fig = go.Figure()
        
        # Si on a un seul actif, on garde les chandeliers et moyennes mobiles
        if len(actifs_bruts) == 1:
            ticker_final = isin_to_ticker(actifs_bruts[0])
            if ticker_final:
                data = fetch_market_data(ticker_final)
                if not data.empty:
                    if periode_affichage == "1 an": df_display = data.last('365D')
                    elif periode_affichage == "3 ans": df_display = data.last('1095D')
                    else: df_display = data
                    
                    data['SMA50'] = data['Close'].rolling(window=50).mean()
                    data['SMA200'] = data['Close'].rolling(window=200).mean()
                    
                    fig.add_trace(go.Candlestick(x=df_display.index, open=df_display['Open'], high=df_display['High'], low=df_display['Low'], close=df_display['Close'], name="Cours"))
                    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SMA50'], line=dict(color='blue', width=1), name="Moy. 50j"))
                    fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SMA200'], line=dict(color='orange', width=1.5), name="Moy. 200j"))
                    
                    fig.update_layout(title=f"Analyse {ticker_final}", yaxis_title="Prix", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                else:
                    st.error(f"Données introuvables pour {ticker_final}")
        
        # Si on a PLUSIEURS actifs, on fait un graphique comparatif en Base 100
        else:
            st.info("Comparaison en Base 100 : Tous les actifs partent de 100 pour comparer leur croissance réelle.")
            for actif in actifs_bruts:
                ticker_final = isin_to_ticker(actif)
                if ticker_final:
                    data = fetch_market_data(ticker_final)
                    if not data.empty:
                        if periode_affichage == "1 an": df_display = data.last('365D')
                        elif periode_affichage == "3 ans": df_display = data.last('1095D')
                        else: df_display = data
                        
                        # Conversion en base 100
                        base_100 = (df_display['Close'] / df_display['Close'].iloc[0]) * 100
                        fig.add_trace(go.Scatter(x=df_display.index, y=base_100, mode='lines', name=ticker_final))
            
            fig.update_layout(title="Comparaison des performances (Base 100)", yaxis_title="Performance", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)

# ==========================================
# MODULE 2 : CAPITALISATION & PFU (AVEC PDF)
# ==========================================
elif menu == "2. Capitalisation & Fiscalité":
    st.title("💰 Croissance & Fiscalité")
    
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
    pfu = plus_values * 0.30
    capital_net_fiscal = cap - pfu
    pouvoir_achat_net = capital_net_fiscal / ((1 + (inflation/100))**annees)
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Capital Brut Construit", f"{cap:,.0f} €".replace(',', ' '))
    r2.metric("Plus-values générées", f"{plus_values:,.0f} €".replace(',', ' '))
    r3.metric("Impôts (PFU 30%)", f"- {pfu:,.0f} €".replace(',', ' '))
    st.info(f"💶 Valeur Nette : {capital_net_fiscal:,.0f} € | 🛒 Pouvoir d'achat réel (après inflation) : {pouvoir_achat_net:,.0f} €")
    
    # --- GÉNÉRATION PDF ---
    st.markdown("---")
    st.subheader("📄 Générer la synthèse client")
    if st.button("Créer le rapport PDF de Capitalisation"):
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "1. Hypotheses de la simulation", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"- Capital de depart : {capital_init:,.0f} euros", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"- Versement mensuel : {versement:,.0f} euros", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"- Rendement estime : {taux_brut} %", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"- Horizon de placement : {annees} ans", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, "2. Resultats a terme", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, f"- Capital brut obtenu : {cap:,.0f} euros", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"- Dont plus-values : {plus_values:,.0f} euros", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 10, f"- Fiscalite (Flat Tax 30%) : - {pfu:,.0f} euros", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 10, f"- CAPITAL NET D'IMPOT : {capital_net_fiscal:,.0f} euros", new_x="LMARGIN", new_y="NEXT")
        
        # Sauvegarde
        pdf.output("Rapport_Simulation.pdf")
        
        # Bouton de téléchargement
        with open("Rapport_Simulation.pdf", "rb") as f:
            st.download_button(
                label="📥 Télécharger le PDF",
                data=f,
                file_name="Bilan_Capitalisation_VIP.pdf",
                mime="application/pdf"
            )

# ==========================================
# MODULE 3 ET 4 (IDENTIQUES À LA V5)
# ==========================================
elif menu == "3. Impôt sur la Fortune (IFI)":
    st.title("🏛️ Simulateur IFI (Barème 2024)")
    c1, c2, c3 = st.columns(3)
    rp = c1.number_input("Valeur Résidence Principale (€)", value=900000, step=50000)
    autre_immo = c2.number_input("Autres Biens Immobiliers & SCPI (€)", value=600000, step=50000)
    dettes = c3.number_input("Passif déductible (Capital restant dû) (€)", value=150000, step=10000)
    
    rp_nette = rp * 0.70
    patrimoine_net_taxable = rp_nette + autre_immo - dettes
    
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
        if p > 800000: ifi += (p - 800000) * 0.005
        
        if 1300000 < patrimoine_net_taxable < 1400000:
            decote = 17500 - (0.0125 * patrimoine_net_taxable)
            ifi = max(0, ifi - decote)
        st.error(f"🔴 Montant de l'IFI à régler : {ifi:,.0f} € / an")
    else:
        st.success("🟢 Patrimoine Net Taxable inférieur à 1 300 000 €. Non assujetti à l'IFI.")

elif menu == "4. Transmission & Démembrement":
    st.title("👨‍👩‍👧‍👦 Démembrement de Propriété (Art. 669 CGI)")
    c1, c2 = st.columns(2)
    valeur_bien = c1.number_input("Valeur du bien en Pleine Propriété (€)", value=400000, step=10000)
    age_donateur = c2.slider("Âge du donateur (Usufruitier)", 40, 95, 65)
    
    usufruit_pct, nue_prop_pct = calcul_usufruit_nue_prop(age_donateur)
    valeur_usufruit = valeur_bien * usufruit_pct
    valeur_nue_prop = valeur_bien * nue_prop_pct
    
    r1, r2 = st.columns(2)
    r1.metric(f"Valeur Usufruit ({usufruit_pct*100:.0f}%)", f"{valeur_usufruit:,.0f} €".replace(',', ' '))
    r2.metric(f"Valeur Nue-Propriété ({nue_prop_pct*100:.0f}%)", f"{valeur_nue_prop:,.0f} €".replace(',', ' '))
    st.info(f"💡 **Stratégie :** Droits de succession calculés sur **{valeur_nue_prop:,.0f} €** au lieu de {valeur_bien:,.0f} €.")
