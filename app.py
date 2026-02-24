import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os
import datetime
from fpdf import FPDF

# --- CONFIGURATION ---
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

# --- CLASSE PDF BLINDÉE ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(10, 26, 63)
        self.cell(190, 10, "Bilan d'Expertise Patrimoniale", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(190, 10, f"Edite le {datetime.date.today().strftime('%d/%m/%Y')} - VIP PARTNER", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(190, 10, f"Page {self.page_no()} - Document confidentiel", align="C")

def generer_bouton_pdf(titre, lignes_texte, nom_fichier):
    """Générateur PDF corrigé : largeur fixe (190) pour empêcher le crash 'Not enough horizontal space'"""
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(190, 10, titre, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    
    for ligne in lignes_texte:
        if str(ligne).strip() == "":
            pdf.ln(5) 
        else:
            # Nettoyage des caractères et encodage sûr
            ligne_propre = str(ligne).replace("€", "euros")
            ligne_propre = ligne_propre.encode('latin-1', 'replace').decode('latin-1')
            # Largeur fixe à 190mm pour garantir qu'il y a assez d'espace horizontal
            pdf.multi_cell(w=190, h=8, text=ligne_propre)
    
    pdf.output("temp.pdf")
    with open("temp.pdf", "rb") as f:
        st.download_button(label=f"📥 Télécharger le PDF ({nom_fichier})", data=f, file_name=f"{nom_fichier}.pdf", mime="application/pdf")

# --- FONCTIONS MARCHÉS ---
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
    return stock.history(period="5y")

def determiner_devise(ticker):
    if "-USD" in ticker.upper() or ticker.upper() in ["AAPL", "MSFT", "TSLA", "SPY", "URTH"]: return "$"
    elif ".L" in ticker.upper(): return "£"
    elif ".CHF" in ticker.upper(): return "CHF"
    return "€"

# --- SIDEBAR & LOGO ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
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
# MODULE 1 : MARCHÉS FINANCIERS (ANALYSE BOOSTÉE)
# ==========================================
if menu == "1. Marchés Financiers (Expert)":
    st.title("📈 Analyse et Comparaison d'Actifs")
    st.markdown("Saisissez un ou plusieurs actifs séparés par une virgule (ex: `CW8.PA, LU1681043599, BTC-USD`).")
    
    col_input, col_period = st.columns([3, 1])
    recherche_utilisateur = col_input.text_input("Actifs (ISIN ou Ticker) :", "CW8.PA")
    periode_affichage = col_period.selectbox("Période d'affichage", ["1 an", "3 ans", "5 ans"])
    
    actifs_bruts = [x.strip() for x in recherche_utilisateur.split(",") if x.strip()]
    
    if actifs_bruts:
        try:
            # --- CAS 1 : UN SEUL ACTIF ---
            if len(actifs_bruts) == 1:
                ticker_final = isin_to_ticker(actifs_bruts[0])
                if ticker_final:
                    data = fetch_market_data(ticker_final)
                    if not data.empty:
                        devise = determiner_devise(ticker_final)
                        
                        # Indicateurs techniques
                        data['SMA50'] = data['Close'].rolling(window=50).mean()
                        data['SMA200'] = data['Close'].rolling(window=200).mean()
                        delta = data['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        data['RSI'] = 100 - (100 / (1 + rs))
                        
                        # Filtrage période
                        if periode_affichage == "1 an": df_display = data.last('365D')
                        elif periode_affichage == "3 ans": df_display = data.last('1095D')
                        else: df_display = data
                        
                        prix_actuel = df_display['Close'].iloc[-1]
                        prix_debut = df_display['Close'].iloc[0]
                        perf_periode = ((prix_actuel / prix_debut) - 1) * 100
                        rsi_actuel = df_display['RSI'].iloc[-1]
                        volatilite = df_display['Close'].pct_change().std() * np.sqrt(252) * 100
                        
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Dernier Cours", f"{prix_actuel:,.2f} {devise}")
                        c2.metric(f"Perf. ({periode_affichage})", f"{perf_periode:.2f} %")
                        c3.metric("Volatilité", f"{volatilite:.2f} %")
                        c4.metric("RSI 14j", f"{rsi_actuel:.1f}", 
                                  delta="Surachat (>70)" if rsi_actuel > 70 else "Survente (<30)" if rsi_actuel < 30 else "Neutre",
                                  delta_color="inverse" if rsi_actuel > 70 or rsi_actuel < 30 else "off")
                        
                        # Graphique
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(x=df_display.index, open=df_display['Open'], high=df_display['High'], low=df_display['Low'], close=df_display['Close'], name="Cours"))
                        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SMA50'], line=dict(color='blue', width=1), name="Moy. 50j"))
                        fig.add_trace(go.Scatter(x=df_display.index, y=df_display['SMA200'], line=dict(color='orange', width=1.5), name="Moy. 200j"))
                        fig.update_layout(title=f"Analyse Technique : {ticker_final}", yaxis_title=f"Prix ({devise})", xaxis_rangeslider_visible=False, height=500)
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                        
                        # --- CONSEILS AUTOMATIQUES EXPERTS ---
                        st.markdown("### 💡 Interprétation & Conseils")
                        
                        # 1. Tendance de fond
                        if prix_actuel > df_display['SMA200'].iloc[-1]:
                            st.success(f"**Tendance de fond : Haussière 🟢.** Le cours actuel est au-dessus de sa moyenne à 200 jours. Les flux institutionnels sont globalement acheteurs.")
                        else:
                            st.error(f"**Tendance de fond : Baissière 🔴.** Le cours est sous sa moyenne à 200 jours. L'actif est dans une phase de correction lourde.")
                        
                        # 2. Dynamique Moyen Terme (Croisement)
                        if df_display['SMA50'].iloc[-1] > df_display['SMA200'].iloc[-1]:
                            st.write("- **Dynamique croisée :** Configuration positive (Golden Cross). La tendance récente est plus forte que la tendance longue.")
                        else:
                            st.write("- **Dynamique croisée :** Configuration fragile (Death Cross). La pression vendeuse s'accélère à court terme.")
                            
                        # 3. RSI
                        if rsi_actuel >= 70:
                            st.warning("- **Analyse RSI (Surchauffe) :** L'actif est en zone de surachat. Une prise de bénéfice des marchés ou une correction technique est probable à court terme. Prudence sur les gros versements immédiats.")
                        elif rsi_actuel <= 30:
                            st.success("- **Analyse RSI (Survente) :** L'actif a été massivement vendu. Historiquement, c'est souvent un point d'entrée tactique intéressant pour investir.")
                        else:
                            st.info("- **Analyse RSI (Neutre) :** Le marché respire normalement. Pas d'excès détecté.")
                        
                        # 4. Volatilité
                        if volatilite > 25:
                            st.write("- **Profil de Risque :** Haute volatilité. Cet actif est très spéculatif ou subit des turbulences. À réserver aux profils dynamiques.")
                        elif volatilite < 10:
                            st.write("- **Profil de Risque :** Faible volatilité. Actif défensif, idéal pour un profil prudent (Père de famille).")
                        else:
                            st.write("- **Profil de Risque :** Volatilité classique pour le marché actions.")

                        # --- PDF ---
                        st.markdown("---")
                        lignes_pdf = [
                            f"Analyse de l'actif : {ticker_final}",
                            f"Periode observee : {periode_affichage}",
                            "",
                            f"- Cours actuel : {prix_actuel:,.2f} {devise}",
                            f"- Performance : {perf_periode:.2f} %",
                            f"- Volatilite : {volatilite:.2f} %",
                            f"- Indicateur RSI : {rsi_actuel:.1f} / 100",
                            "",
                            "Avis Synthetique de l'algorithme :",
                            "Tendance Haussiere" if prix_actuel > df_display['SMA200'].iloc[-1] else "Tendance Baissiere",
                            "Surchauffe (Surachat) - Prudence" if rsi_actuel >= 70 else "Decote (Survente) - Point d'entree possible" if rsi_actuel <= 30 else "Marche Neutre"
                        ]
                        generer_bouton_pdf(f"Fiche Valeur - {ticker_final}", lignes_pdf, "Bilan_Marche")

                    else:
                        st.warning(f"Aucune donnée pour {ticker_final}")
            
            # --- CAS 2 : PLUSIEURS ACTIFS ---
            else:
                st.info("Comparaison en Base 100 : Tous les actifs partent de la valeur 100 pour comparer leur croissance exacte.")
                fig = go.Figure()
                pdf_lines = ["Comparatif de performances (Base 100) :", f"Periode : {periode_affichage}", ""]
                
                for actif in actifs_bruts:
                    ticker_final = isin_to_ticker(actif)
                    if ticker_final:
                        data = fetch_market_data(ticker_final)
                        if not data.empty:
                            if periode_affichage == "1 an": df_display = data.last('365D')
                            elif periode_affichage == "3 ans": df_display = data.last('1095D')
                            else: df_display = data
                            
                            base_100 = (df_display['Close'] / df_display['Close'].iloc[0]) * 100
                            fig.add_trace(go.Scatter(x=df_display.index, y=base_100, mode='lines', name=ticker_final))
                            
                            perf_finale = base_100.iloc[-1] - 100
                            pdf_lines.append(f"- {ticker_final} : {perf_finale:+.2f} %")
                
                fig.update_layout(title="Comparaison des performances réelles", yaxis_title="Valeur (Base 100)", xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                
                st.markdown("---")
                generer_bouton_pdf("Comparateur de Fonds", pdf_lines, "Comparatif_Marche")
                
        except Exception as e:
            st.error("⚠️ Yahoo Finance bloque temporairement l'accès (Rate Limit). Attendez une minute et réessayez.")

# ==========================================
# MODULE 2 : CAPITALISATION (INTACT)
# ==========================================
elif menu == "2. Capitalisation & Fiscalité":
    st.title("💰 Croissance & Fiscalité")
    
    c1, c2, c3, c4 = st.columns(4)
    capital_init = c1.number_input("Capital initial (€)", value=50000, step=5000)
    versement = c2.number_input("Versement mensuel (€)", value=500, step=100)
    taux_brut = c3.number_input("Rendement cible (%)", value=6.0, step=0.5)
    annees = c4.slider("Horizon (Années)", 5, 40, 15)
    
    taux_mensuel = (taux_brut / 100) / 12
    cap = capital_init
    total_versements = capital_init
    for _ in range(annees * 12):
        cap = cap * (1 + taux_mensuel) + versement
        total_versements += versement
        
    plus_values = cap - total_versements
    pfu = plus_values * 0.30
    capital_net = cap - pfu
    
    r1, r2, r3 = st.columns(3)
    r1.metric("Capital Brut", f"{cap:,.0f} €".replace(',', ' '))
    r2.metric("Plus-values", f"{plus_values:,.0f} €".replace(',', ' '))
    r3.metric("Impôts (PFU 30%)", f"- {pfu:,.0f} €".replace(',', ' '))
    st.info(f"💶 Valeur Nette disponible : {capital_net:,.0f} €")
    
    st.markdown("---")
    lignes_pdf = [
        "Hypotheses retenues :",
        f"- Capital de depart : {capital_init:,.0f} euros",
        f"- Effort d'epargne : {versement:,.0f} euros / mois",
        f"- Rendement annuel brut : {taux_brut} %",
        f"- Duree de placement : {annees} ans",
        "",
        "Resultats a terme :",
        f"- Capital total brut : {cap:,.0f} euros",
        f"- Dont plus-values latentes : {plus_values:,.0f} euros",
        f"- Fiscalite a la sortie (PFU 30%) : - {pfu:,.0f} euros",
        "",
        f"Resultat Net d'Impot : {capital_net:,.0f} euros"
    ]
    generer_bouton_pdf("Bilan de Capitalisation", lignes_pdf, "Bilan_Capitalisation")

# ==========================================
# MODULE 3 : IFI (INTACT)
# ==========================================
elif menu == "3. Impôt sur la Fortune (IFI)":
    st.title("🏛️ Simulateur IFI")
    c1, c2, c3 = st.columns(3)
    rp = c1.number_input("Valeur Résidence Principale (€)", value=900000, step=50000)
    autre_immo = c2.number_input("Autres Biens Immobiliers (€)", value=600000, step=50000)
    dettes = c3.number_input("Passif déductible (€)", value=150000, step=10000)
    
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

    st.markdown("---")
    lignes_pdf = [
        "Base taxable retenue :",
        f"- Valeur de la Residence Principale : {rp:,.0f} euros",
        f"- Application abattement legal 30% : - {rp - rp_nette:,.0f} euros",
        f"- Autres actifs immobiliers (locatif, SCPI) : {autre_immo:,.0f} euros",
        f"- Dettes deductibles (capital restant) : - {dettes:,.0f} euros",
        "",
        f"Patrimoine Net Taxable IFI : {patrimoine_net_taxable:,.0f} euros",
        f"Impot sur la Fortune Estime : {ifi:,.0f} euros / an"
    ]
    generer_bouton_pdf("Audit IFI", lignes_pdf, "Bilan_IFI")

# ==========================================
# MODULE 4 : TRANSMISSION (INTACT)
# ==========================================
elif menu == "4. Transmission & Démembrement":
    st.title("👨‍👩‍👧‍👦 Démembrement de Propriété")
    c1, c2 = st.columns(2)
    valeur_bien = c1.number_input("Valeur du bien en Pleine Propriété (€)", value=400000, step=10000)
    age_donateur = c2.slider("Âge du donateur (Usufruitier)", 40, 95, 65)
    
    if age_donateur <= 20: u_pct, n_pct = 0.9, 0.1
    elif age_donateur <= 30: u_pct, n_pct = 0.8, 0.2
    elif age_donateur <= 40: u_pct, n_pct = 0.7, 0.3
    elif age_donateur <= 50: u_pct, n_pct = 0.6, 0.4
    elif age_donateur <= 60: u_pct, n_pct = 0.5, 0.5
    elif age_donateur <= 70: u_pct, n_pct = 0.4, 0.6
    elif age_donateur <= 80: u_pct, n_pct = 0.3, 0.7
    elif age_donateur <= 90: u_pct, n_pct = 0.2, 0.8
    else: u_pct, n_pct = 0.1, 0.9
    
    val_u = valeur_bien * u_pct
    val_n = valeur_bien * n_pct
    
    r1, r2 = st.columns(2)
    r1.metric(f"Valeur Usufruit ({u_pct*100:.0f}%)", f"{val_u:,.0f} €".replace(',', ' '))
    r2.metric(f"Valeur Nue-Propriété ({n_pct*100:.0f}%)", f"{val_n:,.0f} €".replace(',', ' '))
    st.info(f"💡 En donnant la nue-propriété, les droits de succession sont calculés sur **{val_n:,.0f} €** au lieu de {valeur_bien:,.0f} €.")

    st.markdown("---")
    lignes_pdf = [
        "Hypotheses de demembrement (Art. 669 CGI) :",
        f"- Age de l'usufruitier : {age_donateur} ans",
        f"- Valeur du patrimoine en pleine propriete : {valeur_bien:,.0f} euros",
        "",
        "Repartition des droits :",
        f"- Valeur de l'usufruit ({u_pct*100:.0f}%) : {val_u:,.0f} euros",
        f"- Valeur de la nue-propriete ({n_pct*100:.0f}%) : {val_n:,.0f} euros",
        "",
        "Conclusion strategique :",
        f"Les droits de succession/donation seront calcules sur une assiette reduite de {val_n:,.0f} euros.",
        "Au deces de l'usufruitier, la pleine propriete est reconstituee",
        "sans impots supplementaires."
    ]
    generer_bouton_pdf("Strategie de Transmission", lignes_pdf, "Bilan_Transmission")
