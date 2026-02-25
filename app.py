import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import datetime
from fpdf import FPDF
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="VIP PARTNER | Cockpit Financier", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(181, 162, 123, 0.05);
        border-left: 4px solid #B5A27B;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1, h2, h3 { color: #B5A27B !important; font-family: 'Arial', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { color: #E0E0E0; font-weight: bold; }
    .stTabs [aria-selected="true"] { color: #B5A27B !important; border-bottom-color: #B5A27B !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTEUR PDF PREMIUM CORRIGÉ ---
class PDF(FPDF):
    def header(self):
        # Affiché sur toutes les pages sauf la page de garde
        if self.page_no() > 1:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(181, 162, 123) # Or
            self.cell(190, 10, "VIP PARTNER - Cockpit Financier", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 20, 200, 20)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(190, 10, f"Page {self.page_no()} - Document strictement confidentiel generé le {datetime.date.today().strftime('%d/%m/%Y')}", align="C")

def generer_pdf_premium(titre_doc, sections, nom_fichier):
    """
    Générateur de PDF de luxe avec gestion stricte de la largeur pour éviter les crashs FPDF.
    """
    pdf = PDF()
    pdf.set_margins(left=10, top=10, right=10)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGE DE GARDE ---
    pdf.add_page()
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=85, y=40, w=40)
    
    pdf.set_y(100)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(10, 26, 63) # Bleu Nuit
    pdf.cell(190, 15, "BILAN FINANCIER", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(181, 162, 123) # Or
    pdf.cell(190, 10, titre_doc.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_y(250)
    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(190, 10, "Edite par VIP PARTNER", align="C", new_x="LMARGIN", new_y="NEXT")
    
    # --- CONTENU ---
    pdf.add_page()
    for titre_section, lignes in sections:
        # En-tête de section coloré
        pdf.set_fill_color(10, 26, 63) # Fond Bleu Nuit
        pdf.set_text_color(181, 162, 123) # Texte Or
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(190, 10, f"  {titre_section}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
        # Lignes de texte
        for ligne in lignes:
            if str(ligne).strip() == "":
                pdf.ln(4)
            else:
                # Nettoyage strict pour FPDF
                l_propre = str(ligne).replace("€", "EUR").replace("%", "pourcents").replace("->", "=>")
                # On force l'encodage pour virer les caractères invisibles qui font planter
                l_propre = l_propre.encode('latin-1', 'ignore').decode('latin-1')
                
                # Mise en gras conditionnelle
                if l_propre.startswith("=>") or "TOTAL" in l_propre.upper() or "NET" in l_propre.upper():
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.set_text_color(10, 26, 63)
                else:
                    pdf.set_font("Helvetica", "", 11)
                    pdf.set_text_color(30, 30, 30)
                
                # CORRECTION CRUCIALE : On fixe w=190 pour empêcher l'erreur 'not enough horizontal space'
                pdf.multi_cell(w=190, h=8, text=l_propre)
        pdf.ln(8)
    
    pdf.output("temp_luxe.pdf")
    with open("temp_luxe.pdf", "rb") as f:
        st.download_button(label=f"📥 Télécharger le Rapport PDF Pro ({nom_fichier})", data=f, file_name=f"{nom_fichier}.pdf", mime="application/pdf")

# --- FONCTIONS DONNÉES EN DIRECT ---
@st.cache_data(ttl=900)
def get_live_price(ticker):
    val = ticker.strip().upper()
    try:
        # Conversion ISIN si besoin
        if len(val) == 12 and val[:2].isalpha():
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={val}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers)
            data = res.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                val = data['quotes'][0]['symbol']
                
        stock = yf.Ticker(val)
        hist = stock.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1], val
        return 0.0, val
    except:
        return 0.0, val

# --- SIDEBAR ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)
else:
    st.sidebar.markdown("## 💎 VIP PARTNER")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Mon Cockpit Financier", [
    "1. Tableau de Bord Global", 
    "2. Gestion du Budget", 
    "3. Portefeuille Live (Expert)", 
    "4. Liberté Financière (FIRE)"
])

# ==========================================
# MODULE 1 : TABLEAU DE BORD (NET WORTH)
# ==========================================
if menu == "1. Tableau de Bord Global":
    st.title("🌐 Vision Globale du Patrimoine")
    st.write("Analysez vos actifs, vos dettes et vos ratios de santé financière.")
    
    col_actifs, col_passifs = st.columns(2)
    
    with col_actifs:
        st.subheader("🟢 Actifs (Ce que je possède)")
        immo = st.number_input("Immobilier (Résidence principale, locatif)", value=250000, step=10000)
        liquidites = st.number_input("Liquidités (Comptes courants, Livret A)", value=20000, step=1000)
        investissements = st.number_input("Placements Bourse & Crypto", value=45000, step=1000)
        assurances_vie = st.number_input("Assurance-Vie (Fonds Euros)", value=15000, step=1000)
        autres_actifs = st.number_input("Autres (Voiture, Montres...)", value=10000, step=1000)
        total_actifs = immo + liquidites + investissements + assurances_vie + autres_actifs

    with col_passifs:
        st.subheader("🔴 Passifs (Ce que je dois)")
        credit_immo = st.number_input("Crédits Immobiliers (Restant dû)", value=180000, step=10000)
        credit_conso = st.number_input("Crédits Consommation / Auto", value=8000, step=1000)
        autres_dettes = st.number_input("Autres dettes (Fisc, Famille)", value=0, step=500)
        total_passifs = credit_immo + credit_conso + autres_dettes

    patrimoine_net = total_actifs - total_passifs
    
    ratio_endettement = (total_passifs / total_actifs * 100) if total_actifs > 0 else 0
    ratio_liquidite = (liquidites / total_actifs * 100) if total_actifs > 0 else 0
    
    st.markdown("---")
    st.subheader("Indicateurs Clés")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Actifs", f"{total_actifs:,.0f} €".replace(',', ' '))
    c2.metric("Total Passifs", f"{total_passifs:,.0f} €".replace(',', ' '))
    c3.metric("💰 PATRIMOINE NET", f"{patrimoine_net:,.0f} €".replace(',', ' '))
    c4.metric("Ratio d'Endettement", f"{ratio_endettement:.1f} %", "Idéal < 33%", delta_color="off")
    
    fig = px.pie(
        values=[immo, liquidites, investissements, assurances_vie, autres_actifs], 
        names=["Immobilier", "Liquidités", "Bourse/Crypto", "Fonds Euros", "Autres"],
        hole=0.4, color_discrete_sequence=['#B5A27B', '#0A1A3F', '#1F3A82', '#4A69A5', '#E0E0E0']
    )
    fig.update_layout(title="Allocation du Patrimoine Brut", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    sections_pdf = [
        ("Synthese des Actifs", [
            f"- Immobilier : {immo:,.0f} EUR",
            f"- Liquidites disponibles : {liquidites:,.0f} EUR",
            f"- Bourse et Cryptomonnaies : {investissements:,.0f} EUR",
            f"- Assurance-Vie (Fonds garantis) : {assurances_vie:,.0f} EUR",
            f"- Actifs divers : {autres_actifs:,.0f} EUR",
            "",
            f"TOTAL ACTIFS : {total_actifs:,.0f} EUR"
        ]),
        ("Synthese des Passifs", [
            f"- Capitaux restants dus (Immobilier) : {credit_immo:,.0f} EUR",
            f"- Credits a la consommation : {credit_conso:,.0f} EUR",
            f"- Dettes diverses : {autres_dettes:,.0f} EUR",
            "",
            f"TOTAL PASSIFS : {total_passifs:,.0f} EUR"
        ]),
        ("Bilan et Ratios", [
            f"=> PATRIMOINE NET (Actifs - Passifs) : {patrimoine_net:,.0f} EUR",
            "",
            f"- Ratio d'endettement global : {ratio_endettement:.1f} %",
            f"- Poids des liquidites : {ratio_liquidite:.1f} % du patrimoine total"
        ])
    ]
    generer_pdf_premium("Photographie du Patrimoine", sections_pdf, "Cockpit_Patrimoine")

# ==========================================
# MODULE 2 : BUDGET MENSUEL & WATERFALL
# ==========================================
elif menu == "2. Gestion du Budget":
    st.title("💶 Cash-Flow & Analyse des Flux")
    st.write("Suivez la règle du **50/30/20** pour structurer vos dépenses et identifier votre capacité d'épargne réelle.")

    col_inc, col_exp = st.columns(2)
    with col_inc:
        st.subheader("Entrées d'argent mensuelles")
        salaire = st.number_input("Salaires et Primes nets", value=3200, step=100)
        revenus_side = st.number_input("Locatif / Dividendes / Autres", value=400, step=50)
        total_revenus = salaire + revenus_side
        
    with col_exp:
        st.subheader("Sorties d'argent mensuelles")
        charges_fixes = st.number_input("Besoins fixes (Loyer, Crédits, Assurances, Courses)", value=1500, step=50)
        depenses_plaisir = st.number_input("Envies (Sorties, Restos, Shopping)", value=700, step=50)
        epargne_invest = st.number_input("Épargne & Investissements programmés", value=800, step=50)
        total_depenses = charges_fixes + depenses_plaisir + epargne_invest

    reste_a_vivre = total_revenus - total_depenses
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Total Revenus", f"{total_revenus:,.0f} €".replace(',', ' '))
    r2.metric("Total Dépenses", f"{total_depenses:,.0f} €".replace(',', ' '))
    r3.metric("Cash-Flow Libre (Non alloué)", f"{reste_a_vivre:,.0f} €".replace(',', ' '), delta="Surplus à investir" if reste_a_vivre >= 0 else "Déficit budgétaire", delta_color="normal" if reste_a_vivre >= 0 else "inverse")

    fig_waterfall = go.Figure(go.Waterfall(
        name="Budget", orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "total"],
        x=["Salaires", "Autres Revenus", "Charges Fixes", "Plaisirs", "Épargne", "Reste à vivre"],
        textposition="outside",
        y=[salaire, revenus_side, -charges_fixes, -depenses_plaisir, -epargne_invest, reste_a_vivre],
        connector={"line":{"color":"#E0E0E0"}},
        decreasing={"marker":{"color":"#0A1A3F"}},
        increasing={"marker":{"color":"#B5A27B"}},
        totals={"marker":{"color":"green" if reste_a_vivre >= 0 else "red"}}
    ))
    fig_waterfall.update_layout(title="Cascade du Budget Mensuel", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_waterfall, use_container_width=True)

    st.markdown("---")
    sections_pdf = [
        ("Flux Entrants (Revenus)", [
            f"- Salaires nets : {salaire:,.0f} EUR",
            f"- Revenus annexes : {revenus_side:,.0f} EUR",
            f"TOTAL REVENUS : {total_revenus:,.0f} EUR"
        ]),
        ("Flux Sortants (Depenses & Epargne)", [
            f"- Besoins incompressibles : {charges_fixes:,.0f} EUR",
            f"- Depenses de confort : {depenses_plaisir:,.0f} EUR",
            f"- Epargne forcee : {epargne_invest:,.0f} EUR",
            f"TOTAL DEPENSES : {total_depenses:,.0f} EUR"
        ]),
        ("Analyse du Cash-Flow", [
            f"=> RESTE A VIVRE (Libre) : {reste_a_vivre:,.0f} EUR",
            "",
            "Conformite a la regle 50/30/20 :",
            f"- Besoins (Ideal 50 pourcents) : {(charges_fixes/total_revenus*100):.1f} pourcents",
            f"- Plaisirs (Ideal 30 pourcents) : {(depenses_plaisir/total_revenus*100):.1f} pourcents",
            f"- Epargne (Ideal 20 pourcents) : {(epargne_invest/total_revenus*100):.1f} pourcents"
        ])
    ]
    generer_pdf_premium("Analyse Budgetaire", sections_pdf, "Cockpit_Budget")

# ==========================================
# MODULE 3 : TABLEAU INTERACTIF BOURSE
# ==========================================
elif menu == "3. Portefeuille Live (Expert)":
    st.title("📈 Portefeuille Dynamique & Plus-Values")
    st.write("Saisissez vos positions. Le tableau se met à jour en temps réel avec les prix du marché.")
    
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = pd.DataFrame({
            "Ticker (ISIN/Symbole)": ["CW8.PA", "BTC-USD", "AAPL"],
            "Quantité": [15.0, 0.25, 10.0],
            "Prix de Revient Unitaire (€/$)": [450.0, 40000.0, 150.0]
        })
    
    st.info("💡 Ajoutez, modifiez ou supprimez des lignes directement dans le tableau ci-dessous.")
    
    edited_df = st.data_editor(st.session_state.portfolio, num_rows="dynamic", use_container_width=True)
    st.session_state.portfolio = edited_df
    
    if st.button("🔄 Calculer la valorisation en direct"):
        result_data = []
        total_investi = 0
        total_actuel = 0
        
        with st.spinner("Récupération des cours en direct..."):
            for index, row in edited_df.iterrows():
                ticker_input = str(row["Ticker (ISIN/Symbole)"])
                try:
                    qty = float(row["Quantité"])
                    pru = float(row["Prix de Revient Unitaire (€/$)"])
                except:
                    continue
                
                if ticker_input and qty > 0:
                    prix_actuel, vrai_ticker = get_live_price(ticker_input)
                    
                    valeur_achat = qty * pru
                    valeur_live = qty * prix_actuel
                    plus_value = valeur_live - valeur_achat
                    performance = (plus_value / valeur_achat * 100) if valeur_achat > 0 else 0
                    
                    total_investi += valeur_achat
                    total_actuel += valeur_live
                    
                    result_data.append({
                        "Actif": vrai_ticker,
                        "Qté": qty,
                        "PRU": round(pru, 2),
                        "Prix Live": round(prix_actuel, 2),
                        "Val. Achat": round(valeur_achat, 2),
                        "Val. Actuelle": round(valeur_live, 2),
                        "P&L": round(plus_value, 2),
                        "Perf %": round(performance, 2)
                    })
        
        if result_data:
            res_df = pd.DataFrame(result_data)
            st.dataframe(res_df.style.map(lambda x: 'color: green' if x > 0 else 'color: red', subset=['P&L', 'Perf %']), use_container_width=True)
            
            pnl_global = total_actuel - total_investi
            perf_globale = (pnl_global / total_investi * 100) if total_investi > 0 else 0
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Montant Investi (Achat)", f"{total_investi:,.2f}")
            c2.metric("Valorisation Directe", f"{total_actuel:,.2f}")
            c3.metric("Plus-Value Latente", f"{pnl_global:,.2f}", f"{perf_globale:.2f} %")
            
            lignes_pdf_pos = []
            for item in result_data:
                lignes_pdf_pos.append(f"- {item['Actif']} : {item['Qté']} unites | Prix Actuel: {item['Prix Live']} | Perf: {item['Perf %']} pourcents")
            
            sections_pdf = [
                ("Positions du Portefeuille", lignes_pdf_pos),
                ("Bilan de Performance", [
                    f"Total Investi : {total_investi:,.2f}",
                    f"Valorisation Actuelle (Live) : {total_actuel:,.2f}",
                    "",
                    f"=> PLUS-VALUE GLOBALE : {pnl_global:,.2f} ({perf_globale:.2f} pourcents)"
                ])
            ]
            generer_pdf_premium("Etat du Portefeuille Boursier", sections_pdf, "Cockpit_Portefeuille")

# ==========================================
# MODULE 4 : INDÉPENDANCE FINANCIÈRE (FIRE)
# ==========================================
elif menu == "4. Liberté Financière (FIRE)":
    st.title("⏳ Simulateur de Liberté Financière")
    st.write("Calculez à quel âge vous pourrez arrêter de travailler grâce à vos investissements (Mouvement F.I.R.E).")
    
    c1, c2, c3, c4 = st.columns(4)
    age_actuel = c1.number_input("Votre âge actuel", value=30, step=1)
    capital_init = c2.number_input("Capital déjà investi (€)", value=25000, step=1000)
    versement = c3.number_input("Capacité d'épargne mensuelle (€)", value=600, step=50)
    rente_visee = c4.number_input("Rente mensuelle visée (€)", value=2500, step=100)
    
    taux_brut = st.slider("Rendement moyen annuel net d'inflation (%)", 2.0, 10.0, 5.0, step=0.5)
    
    capital_cible = (rente_visee * 12) * 25
    
    taux_mensuel = (taux_brut / 100) / 12
    cap = capital_init
    mois_ecoules = 0
    historique_fire = [cap]
    
    while cap < capital_cible and mois_ecoules < (60 * 12): 
        cap = cap * (1 + taux_mensuel) + versement
        mois_ecoules += 1
        if mois_ecoules % 12 == 0:
            historique_fire.append(cap)
            
    annees_necessaires = mois_ecoules / 12
    age_fire = age_actuel + annees_necessaires
    
    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    r1.metric("Capital Cible à atteindre", f"{capital_cible:,.0f} €".replace(',', ' '))
    r2.metric("Années d'effort requises", f"{annees_necessaires:.1f} ans")
    r3.metric("Âge de la Liberté Financière", f"{age_fire:.1f} ans", delta="Indépendance totale !", delta_color="normal")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.arange(age_actuel, age_actuel + len(historique_fire)), y=historique_fire, fill='tozeroy', name="Capital accumulé", line_color='#B5A27B'))
    fig.add_hline(y=capital_cible, line_dash="dash", line_color="green", annotation_text="Objectif FIRE")
    fig.update_layout(title="Trajectoire vers l'Indépendance", xaxis_title="Votre Âge", yaxis_title="Patrimoine Investi (€)", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    sections_pdf = [
        ("Hypotheses de base", [
            f"- Age de depart : {age_actuel} ans",
            f"- Capital de depart investi : {capital_init:,.0f} EUR",
            f"- Epargne mensuelle : {versement:,.0f} EUR",
            f"- Rente cible pour en vivre : {rente_visee:,.0f} EUR / mois",
            f"- Taux de rendement net d'inflation : {taux_brut} pourcents"
        ]),
        ("Projection et Objectif", [
            f"- Capital necessaire pour la rente (Regle des 4 pourcents) : {capital_cible:,.0f} EUR",
            f"- Duree d'accumulation estimee : {annees_necessaires:.1f} annees",
            "",
            f"=> AGE D'INDEPENDANCE FINANCIERE (F.I.R.E) : {age_fire:.1f} ans"
        ])
    ]
    generer_pdf_premium("Bilan d'Independance Financiere", sections_pdf, "Cockpit_FIRE")
