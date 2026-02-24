import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
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

# --- FONCTIONS CACHÉES & CONVERSION ISIN ---
@st.cache_data(ttl=3600)
def isin_to_ticker(user_input):
    """Convertit un ISIN en Ticker via l'API de recherche Yahoo Finance"""
    val = user_input.strip().upper()
    # Si ça ressemble à un ISIN (12 caractères, commence par 2 lettres)
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
    return val # Si ce n'est pas un ISIN, on renvoie le texte tel quel

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

# --- SIDEBAR & LOGO ---
# Appel direct du logo. S'il est bien nommé "logo.png" sur le dépôt, il s'affichera.
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Expertise Patrimoniale", [
    "1. Marchés Financiers (Expert)", 
    "2. Capitalisation & Fiscalité", 
    "3. Impôt sur la Fortune (IFI)", 
    "4. Transmission & Démembrement"
])

# ==========================================
# MODULE 1 : MARCHÉS FINANCIERS (AVEC ISIN)
# ==========================================
if menu == "1. Marchés Financiers (Expert)":
    st.title("📈 Analyse Technique & Fondamentale")
    st.markdown("Recherchez un actif via son **Code ISIN** ou son **Ticker** (Ex: `FR0010315770`, `LU1681043599`, `CW8.PA`, `BTC-USD`).")
    
    col_input, col_period = st.columns([3, 1])
    recherche_utilisateur = col_input.text_input("ISIN ou Ticker :", "LU1681043599")
    periode_affichage = col_period.selectbox("Période d'affichage", ["1 an", "3 ans", "5 ans"])
    
    try:
        # 1. Conversion de l'ISIN en Ticker si nécessaire
        ticker_final = isin_to_ticker(recherche_utilisateur)
        
        if ticker_final is None:
            st.error("Impossible de trouver un actif correspondant à ce code ISIN sur les marchés publics.")
        else:
            if ticker_final != recherche_utilisateur.upper():
                st.success(f"✅ Code ISIN reconnu. Ticker associé : **{ticker_final}**")
            
            # 2. Récupération des données
            data = fetch_market_data(ticker_final)
            
            if not data.empty:
                devise = determiner_devise(ticker_final)
                
                # Calcul des indicateurs techniques
                data['SMA50'] = data['Close'].rolling(window=50).mean()
                data['SMA200'] = data['Close'].rolling(window=200).mean()
                
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                data['RSI'] = 100 - (100 / (1 + rs))
                
                if periode_affichage == "1 an":
                    df_display = data.last('365D')
                elif periode_affichage == "3 ans":
                    df_display = data.last('1095D')
                else:
                    df_display = data
                
                # --- MÉTRIQUES CLÉS ---
                c1, c2, c3, c4 = st.columns(4)
                prix_actuel = df_display['Close'].iloc[-1]
                prix_debut = df_display['Close'].iloc[0]
                perf_periode = ((prix_actuel / prix_debut) - 1) * 100
                rsi_actuel = df_display['RSI'].iloc[-1]
                volatilite = df_display['Close'].pct_change().std() * np.sqrt(252) * 100
                
                c1.metric("Dernier Cours", f"{prix_actuel:,.2f} {devise}")
                c2.metric(f"Perf. {periode_affichage}", f"{perf_periode:.2f} %")
                c3.metric("Volatilité (Risque)", f"{volatilite:.2f} %")
                c4.metric("RSI 14j", f"{rsi_actuel:.1f}", 
                          delta="Surchat (>70)" if rsi_actuel > 70 else "Survente (<30)" if rsi_actuel < 30 else "Neutre",
                          delta_color="inverse" if rsi_actuel > 70 or rsi_actuel < 30 else "off")
                
                # --- GRAPHIQUE ---
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df_display.index, open=df_display['Open'], high=df_display['High'], low=df_display['Low'], close=df_display['Close'], name="Cours"))
                fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SMA50'], line=dict(color='blue', width=1), name="Moyenne 50j"))
                fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SMA200'], line=dict(color='orange', width=1.5), name="Moyenne 200j (Tendance longue)"))
                
                fig.update_layout(title=f"Analyse Graphique - {ticker_final}", yaxis_title=f"Prix ({devise})", xaxis_rangeslider_visible=False, height=600, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                
                st.subheader("💡 Interprétation Rapide")
                tendance = "Haussière 🟢" if prix_actuel > df_display['SMA200'].iloc[-1] else "Baissière 🔴"
                st.write(f"- **Tendance de fond (Moyenne 200j) :** La tendance long terme est **{tendance}**.")
                if rsi_actuel > 70: st.warning("- **Indicateur RSI :** L'actif est potentiellement en surchauffe (surachat). Risque de correction.")
                elif rsi_actuel < 30: st.success("- **Indicateur RSI :** L'actif a été fortement vendu (survente). Point d'entrée intéressant possible.")
                else: st.info("- **Indicateur RSI :** Le marché est dans une zone neutre.")

            else:
                st.warning("Aucune donnée trouvée pour cet actif.")
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
    pfu = plus_values * 0.30
    capital_net_fiscal = cap - pfu
    pouvoir_achat_net = capital_net_fiscal / ((1 + (inflation/100))**annees)
    
    st.subheader("Synthèse à la sortie")
    r1, r2, r3 = st.columns(3)
    r1.metric("Capital Brut Construit", f"{cap:,.0f} €".replace(',', ' '))
    r2.metric("Plus-values générées", f"{plus_values:,.0f} €".replace(',', ' '))
    r3.metric("Impôts (PFU 30%)", f"- {pfu:,.0f} €".replace(',', ' '))
    
    st.info(f"💶 **Valeur Nette dans la poche du client : {capital_net_fiscal:,.0f} €**")
    st.warning(f"🛒 **Pouvoir d'achat réel** (Ajusté de {inflation}% d'inflation) : **{pouvoir_achat_net:,.0f} €**")

# ==========================================
# MODULE 3 : IFI COMPLEXE
# ==========================================
elif menu == "3. Impôt sur la Fortune (IFI)":
    st.title("🏛️ Simulateur IFI (Barème 2024)")
    st.write("Calcul du patrimoine net taxable avec abattement Résidence Principale et dettes.")
    
    c1, c2, c3 = st.columns(3)
    rp = c1.number_input("Valeur Résidence Principale (€)", value=900000, step=50000)
    autre_immo = c2.number_input("Autres Biens Immobiliers & SCPI (€)", value=600000, step=50000)
    dettes = c3.number_input("Passif déductible (Capital restant dû) (€)", value=150000, step=10000)
    
    rp_nette = rp * 0.70
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
        if p > 800000: ifi += (p - 800000) * 0.005
        
        if 1300000 < patrimoine_net_taxable < 1400000:
            decote = 17500 - (0.0125 * patrimoine_net_taxable)
            ifi = max(0, ifi - decote)
            st.info(f"Une décote de lissage de {decote:,.0f} € a été appliquée.")
            
        st.error(f"🔴 Montant de l'IFI à régler : {ifi:,.0f} € / an")
    else:
        st.success("🟢 Patrimoine Net Taxable inférieur à 1 300 000 €. Non assujetti à l'IFI.")

# ==========================================
# MODULE 4 : DÉMEMBREMENT
# ==========================================
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
    
    st.info(f"💡 **Stratégie :** En donnant la Nue-Propriété aujourd'hui, les droits de succession seront calculés sur **{valeur_nue_prop:,.0f} €** au lieu de {valeur_bien:,.0f} €.")
