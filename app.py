import streamlit as st
from datetime import datetime
import pandas as pd
import os
import json
import base64
from io import BytesIO
from PIL import Image
from fpdf import FPDF

# Configuration des fichiers
DB_FILE = "rapports_les_palmiers.csv"
LOGO_FILE = "logo.png"

# ==========================================
# CONFIGURATION DE L'ICÔNE DE L'APPLI SEULEMENT
# ==========================================
app_icon = "📝" 
if os.path.exists(LOGO_FILE):
    try:
        img_ouverture = Image.open(LOGO_FILE)
        app_icon = img_ouverture.resize((192, 192))
    except:
        app_icon = "📝"

st.set_page_config(
    page_title="Les Palmiers - Rapports", 
    page_icon=app_icon, 
    layout="centered"
)

# Fonction intelligente : Gère les ajouts de rapports ET les modifications de doublons
def sauvegarder_rapport(donnees):
    nouveau_df = pd.DataFrame([donnees])
    
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            
            if not df.empty and 'Date' in df.columns and 'Shift' in df.columns:
                doublon_index = df[(df['Date'] == donnees['Date']) & (df['Shift'] == donnees['Shift'])].index
                if not doublon_index.empty:
                    df = df.drop(doublon_index)
            
            df = pd.concat([df, nouveau_df], ignore_index=True, sort=False)
        except Exception:
            df = nouveau_df
    else:
        df = nouveau_df
        
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# Fonction pour nettoyer les textes pour FPDF (compatibilité latin-1)
def clean_txt(valeur):
    if pd.isna(valeur) or str(valeur).strip().lower() == "nan" or str(valeur).strip() == "":
        return "Aucune"
    return str(valeur).encode('latin-1', 'replace').decode('latin-1')

# Fonction pour décoder proprement le JSON stocké dans le CSV
def safe_load_json(valeur):
    if pd.isna(valeur) or str(valeur).strip() == "" or str(valeur).strip().lower() == "nan":
        return []
    try:
        return json.loads(valeur)
    except:
        import ast
        try:
            return ast.literal_eval(valeur)
        except:
            return []

# Fonction pour encoder une image uploadée en Base64
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        try:
            bytes_data = uploaded_file.getvalue()
            return base64.b64encode(bytes_data).decode("utf-8")
        except:
            return ""
    return ""

# =========================================================================
# FONCTION PDF STANDARDISÉE ET UNIVERSELLE (AVEC PROVENANCE PISCINE)
# =========================================================================
def generer_pdf(row, date_texte, shift, espaces_liste):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    
    # Couleurs du thème
    c_titre = (94, 80, 63)      
    c_texte = (40, 40, 40)      
    c_gris_clair = (245, 242, 238) 
    
    # --- 1. EN-TÊTE ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*c_titre)
    pdf.cell(0, 10, clean_txt(f"{shift} SHIFT REPORT"), ln=True, align="L")
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, clean_txt("Les Palmiers Boutique Hotel & Spa"), ln=True, align="L")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*c_texte)
    pdf.cell(40, 6, clean_txt(f"Date : {date_texte}"), ln=False)
    pdf.cell(40, 6, clean_txt(f"Shift : {shift}"), ln=True)
    pdf.ln(8)
    
    # --- 2. OPÉRATIONS DU JOUR ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*c_titre)
    pdf.cell(0, 8, clean_txt("OPÉRATIONS DU JOUR"), ln=True)
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*c_gris_clair)
    pdf.cell(110, 7, clean_txt("Informations"), border=1, fill=True)
    pdf.cell(55, 7, clean_txt("Total"), border=1, ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(110, 6, clean_txt("Chambres occupées"), border=1)
    pdf.cell(55, 6, clean_txt(str(int(row.get('Chambres_Occupees', 0)))), border=1, ln=True, align="C")
    
    if shift == "MATIN":
        pdf.cell(110, 6, clean_txt("Arrivées prévues"), border=1)
        pdf.cell(55, 6, clean_txt(str(int(row.get('Arrivees_Prevues', 0)))), border=1, ln=True, align="C")
        pdf.cell(110, 6, clean_txt("Départs prévus"), border=1)
        pdf.cell(55, 6, clean_txt(str(int(row.get('Departs_Prevus', 0)))), border=1, ln=True, align="C")
    else:
        pdf.cell(110, 6, clean_txt("Late Check-in"), border=1)
        pdf.cell(55, 6, clean_txt(str(int(row.get('Late_Check_In', 0)))), border=1, ln=True, align="C")
        pdf.cell(110, 6, clean_txt("Départs tardifs"), border=1)
        pdf.cell(55, 6, clean_txt(str(int(row.get('Departs_Tardifs', 0)))), border=1, ln=True, align="C")
        
    pdf.cell(110, 6, clean_txt("Chambres VIP"), border=1)
    pdf.cell(55, 6, clean_txt(str(int(row.get('VIP', 0)))), border=1, ln=True, align="C")
    
    # Ajout de la provenance des réservations Piscine (avec Marrakech For You)
    p_eat = int(row.get('Piscine_Eatnow', 0))
    p_bed = int(row.get('Piscine_Mysonbed', 0))
    p_mfy = int(row.get('Piscine_MarrakechForYou', 0))
    p_dir = int(row.get('Piscine_Direct', 0))
    p_tot = p_eat + p_bed + p_mfy + p_dir
    
    pdf.cell(110, 6, clean_txt(f"Réservations Piscine (Total : {p_tot}) | Eatnow:{p_eat} - MySonBed:{p_bed} - MFY:{p_mfy} - Direct:{p_dir}"), border=1)
    pdf.cell(55, 6, clean_txt(str(p_tot)), border=1, ln=True, align="C")
    
    liste_rec = safe_load_json(row.get('Reclamations_Detail', '[]'))
    pdf.cell(110, 6, clean_txt("Réclamations clients"), border=1)
    pdf.cell(55, 6, clean_txt(str(len(liste_rec))), border=1, ln=True, align="C")
    
    pdf.cell(110, 6, clean_txt("Incidents techniques"), border=1)
    pdf.cell(55, 6, clean_txt(str(int(row.get('Incidents_Techniques', 0)))), border=1, ln=True, align="C")
    
    pdf.ln(8)
    
    # --- 3. SUIVI DES ESPACES ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*c_titre)
    pdf.cell(0, 8, clean_txt("SUIVI DES ESPACES"), ln=True)
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*c_gris_clair)
    pdf.cell(45, 7, clean_txt("Espace"), border=1, fill=True)
    pdf.cell(20, 7, clean_txt("État"), border=1, fill=True, align="C")
    pdf.cell(55, 7, clean_txt("Observations"), border=1, fill=True)
    pdf.cell(45, 7, clean_txt("Intervention nécessaire"), border=1, fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 9)
    for esp in espaces_liste:
        pdf.cell(45, 6, clean_txt(esp), border=1)
        raw_etat = row.get(f"{esp}_Etat", "OK")
        etat_val = "Alerte" if str(raw_etat).strip().lower() == "alerte" else "OK"
        
        if etat_val == "Alerte":
            pdf.set_text_color(211, 47, 47) 
        else:
            pdf.set_text_color(56, 142, 60)  
            
        pdf.cell(20, 6, clean_txt(etat_val), border=1, align="C")
        pdf.set_text_color(*c_texte) 
        
        obs_val = clean_txt(row.get(f"{esp}_Observations", "Aucune"))
        interv_val = clean_txt(row.get(f"{esp}_Intervention", "Aucune"))
        
        pdf.cell(55, 6, obs_val[:32], border=1)
        pdf.cell(45, 6, interv_val[:25], border=1, ln=True)
        
    pdf.ln(8)
    
    # --- 4. RÉCLAMATIONS CLIENTS ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*c_titre)
    pdf.cell(0, 8, clean_txt("RÉCLAMATIONS CLIENTS"), ln=True)
    pdf.ln(1)
    
    if liste_rec and len(liste_rec) > 0:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*c_gris_clair)
        pdf.cell(20, 7, clean_txt("Heure"), border=1, fill=True, align="C")
        pdf.cell(35, 7, clean_txt("Chambre / Client"), border=1, fill=True)
        pdf.cell(55, 7, clean_txt("Sujet"), border=1, fill=True)
        pdf.cell(55, 7, clean_txt("Action prise"), border=1, fill=True, ln=True)
        
        pdf.set_font("Helvetica", "", 9)
        for rec in liste_rec:
            pdf.cell(20, 6, clean_txt(rec.get('Heure','')), border=1, align="C")
            pdf.cell(35, 6, clean_txt(rec.get('Chambre',''))[:20], border=1)
            pdf.cell(55, 6, clean_txt(rec.get('Sujet',''))[:32], border=1)
            pdf.cell(55, 6, clean_txt(rec.get('Action',''))[:32], border=1, ln=True)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, clean_txt("Aucune réclamation signalée sur ce shift."), ln=True)
        
    pdf.ln(8)
    
    # --- 5. PRIORITÉS TRANSMISES ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*c_titre)
    titre_prio = "PRIORITÉS POUR LE SHIFT SOIR" if shift == "MATIN" else "PRIORITÉS POUR LA NUIT"
    pdf.cell(0, 8, clean_txt(titre_prio), ln=True)
    pdf.ln(1)
    
    liste_prio = safe_load_json(row.get('Priorites_Liste', '[]'))
    pdf.set_font("Helvetica", "", 10)
    if liste_prio and len(liste_prio) > 0:
        for idx, p in enumerate(liste_prio, 1):
            pdf.multi_cell(0, 6, clean_txt(f"- {p}"))
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, clean_txt("Aucune priorité spécifique enregistrée."), ln=True)
        
    pdf.ln(8)
    
    # --- 6. NOTES MANAGER & SIGNATURE ---
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*c_titre)
    pdf.cell(0, 8, clean_txt("NOTES MANAGER"), ln=True)
    pdf.ln(1)
    
    notes = row.get('Notes_Manager', '')
    pdf.set_font("Helvetica", "", 10)
    if pd.isna(notes) or str(notes).strip() == "" or str(notes).strip().lower() == "nan":
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, clean_txt("Aucune observation générale rédigée."), ln=True)
    else:
        pdf.multi_cell(0, 6, clean_txt(notes))
        
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(120, 6, "", ln=False)
    pdf.cell(45, 6, clean_txt("Signature :"), ln=True, align="L")
    
    return pdf.output(dest='S').encode('latin-1')

# --- APPARENCE ET NAVIGATION ---
st.title("Les Palmiers Boutique Hotel & Spa")
st.markdown("---")

page = st.sidebar.radio("Navigation", ["✍️ Saisir un Rapport", "📋 Consulter les Rapports"])

# Initialisation des Session States
if 'reclamations_matin' not in st.session_state:
    st.session_state.reclamations_matin = []
if 'reclamations_soir' not in st.session_state:
    st.session_state.reclamations_soir = []
if 'priorites_matin' not in st.session_state:
    st.session_state.priorites_matin = []
if 'priorites_soir' not in st.session_state:
    st.session_state.priorites_soir = []

espaces = [
    "Entrée / Réception", "Piscine 1", "Piscine 2", "Restaurant", 
    "Salle de Sport", "Spa", "Restaurant Noir", "Vestiaire Piscine", "Cuisine"
]

# ==========================================
# PAGE 1 : SAISIR UN RAPPORT
# ==========================================
if page == "✍️ Saisir un Rapport":
    shift = st.sidebar.radio("Sélectionnez le Shift", ["☀️ Shift MATIN", "🌙 Shift SOIR"])
    date_selectionnee = st.sidebar.date_input("📅 Date du Rapport", value=datetime.now().date())
    date_rapport_str = date_selectionnee.strftime("%Y-%m-%d")

    if shift == "☀️ Shift MATIN":
        st.header(f"☀️ Morning Shift Manager Report — {date_selectionnee.strftime('%d/%m/%Y')}")
        st.subheader("Opérations du Jour")
        col1, col2 = st.columns(2)
        with col1:
            chambres_occ = st.number_input("Chambres occupées", min_value=0, value=0, key="m_occ_input")
            arrivees = st.number_input("Arrivées prévues", min_value=0, value=0, key="m_arr_input")
            departs = st.number_input("Départs prévus", min_value=0, value=0, key="m_dep_input")
        with col2:
            vip = st.number_input("Chambres VIP", min_value=0, value=0, key="m_vip_input")
            incidents = st.number_input("Incidents techniques", min_value=0, value=0, key="m_inc_input")
            
        st.markdown("#### Réservations Piscine (Provenance)")
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            m_piscine_eat = st.number_input("Eatnow", min_value=0, value=0, key="m_p_eat")
        with cp2:
            m_piscine_bed = st.number_input("Mysonbed", min_value=0, value=0, key="m_p_bed")
        with cp3:
            m_piscine_mfy = st.number_input("Marrakech For You", min_value=0, value=0, key="m_p_mfy")
        with cp4:
            m_piscine_dir = st.number_input("Direct (Tél / Accueil)", min_value=0, value=0, key="m_p_dir")

        st.markdown("---")
        st.subheader("SUIVI DES ESPACES")
        etat_espaces_matin = {}
        for espace in espaces:
            st.write(f"**{espace}**")
            c1, c2, c3 = st.columns([1.2, 2.4, 2.4])
            with c1:
                etat = st.selectbox("État", ["OK", "Alerte"], key=f"matin_etat_{espace}")
            with c2:
                obs = st.text_input("Observations", placeholder="RAS", key=f"matin_obs_{espace}")
            with c3:
                interv = st.text_input("Intervention nécessaire", placeholder="Aucune", key=f"matin_int_{espace}")
            
            photo_espace = st.file_uploader("📷 Photo de l'espace (Optionnel)", type=["jpg", "jpeg", "png"], key=f"matin_photo_{espace}")
            
            etat_espaces_matin[f"{espace}_Etat"] = etat
            etat_espaces_matin[f"{espace}_Observations"] = obs if obs.strip() != "" else "Aucune"
            etat_espaces_matin[f"{espace}_Intervention"] = interv if interv.strip() != "" else "Aucune"
            etat_espaces_matin[f"{espace}_Photo"] = image_to_base64(photo_espace)
            
            st.markdown("<hr style='margin:0.5em 0px;', size='1'>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("RÉCLAMATIONS CLIENTS")
        
        with st.form("form_rec_matin", clear_on_submit=True):
            rc1, rc2, rc3, rc4 = st.columns([1, 1.5, 2.5, 2.5])
            rm_heure = rc1.text_input("Heure", placeholder="10h00")
            rm_chambre = rc2.text_input("Chambre / Client", placeholder="Ch 2")
            rm_sujet = rc3.text_input("Sujet", placeholder="Problème Wi-Fi")
            rm_action = rc4.text_input("Action prise", placeholder="Répéteur relancé")
            rm_photo = st.file_uploader("📷 Ajouter une photo d'illustration (Optionnel)", type=["jpg", "jpeg", "png"], key="photo_rec_m")
            submit_rec_m = st.form_submit_button("➕ Ajouter la réclamation (Matin)", use_container_width=True)
            
            if submit_rec_m:
                if rm_chambre or rm_sujet:
                    base64_img = image_to_base64(rm_photo)
                    st.session_state.reclamations_matin.append({
                        "Heure": rm_heure if rm_heure else "--h--", 
                        "Chambre": rm_chambre if rm_chambre else "Inconnu", 
                        "Sujet": rm_sujet if rm_sujet else "Non spécifié", 
                        "Action": rm_action if rm_action else "Aucune",
                        "Photo": base64_img
                    })
                st.rerun()
                
        if st.session_state.reclamations_matin:
            df_m_aff = pd.DataFrame(st.session_state.reclamations_matin)
            if "Photo" in df_m_aff.columns:
                df_m_aff["Photo"] = df_m_aff["Photo"].apply(lambda x: "📸 Oui" if x else "Non")
            st.table(df_m_aff)
            if st.button("❌ Effacer la liste des réclamations (Matin)", key="btn_del_rm"):
                st.session_state.reclamations_matin = []
                st.rerun()

        st.markdown("---")
        st.subheader("PRIORITÉS POUR LE SOIR")
        with st.form("form_prio_matin", clear_on_submit=True):
            nouvelle_prio_m = st.text_input("Rédiger une priorité pour le soir...", placeholder="Ex: Donner la clé de la 10...")
            submit_prio_m = st.form_submit_button("➕ Ajouter cette priorité", use_container_width=True)
            
            if submit_prio_m and nouvelle_prio_m:
                st.session_state.priorites_matin.append(nouvelle_prio_m)
                st.rerun()
                
        if st.session_state.priorites_matin:
            for i, prio in enumerate(st.session_state.priorites_matin, 1):
                st.write(f"**{i}.** {prio}")
            if st.button("❌ Effacer les priorités (Matin)", key="btn_del_prio_m"):
                st.session_state.priorites_matin = []
                st.rerun()

        st.markdown("---")
        st.subheader("NOTES MANAGER")
        notes_manager_matin = st.text_area("Observations générales du matin", placeholder="Saisir vos notes ici...", key="nm_text")

        if st.button("💾 Enregistrer le Rapport Matin", use_container_width=True, key="btn_save_matin"):
            donnees_rapport = {
                "Date": date_rapport_str,
                "Shift": "MATIN",
                "Chambres_Occupees": chambres_occ,
                "Arrivees_Prevues": arrivees,
                "Departs_Prevus": departs,
                "VIP": vip,
                "Incidents_Techniques": incidents,
                "Piscine_Eatnow": m_piscine_eat,
                "Piscine_Mysonbed": m_piscine_bed,
                "Piscine_MarrakechForYou": m_piscine_mfy,
                "Piscine_Direct": m_piscine_dir,
                "Priorites_Liste": json.dumps(st.session_state.priorites_matin),
                "Notes_Manager": notes_manager_matin if notes_manager_matin.strip() != "" else "Aucune",
                "Reclamations_Detail": json.dumps(st.session_state.reclamations_matin)
            }
            donnees_rapport.update(etat_espaces_matin)
            sauvegarder_rapport(donnees_rapport)
            st.success("🎉 Le rapport du matin a été enregistré / mis à jour avec succès !")
            
            st.session_state.reclamations_matin = []
            st.session_state.priorites_matin = []
            st.rerun()

    elif shift == "🌙 Shift SOIR":
        st.header(f"🌙 Evening Shift Manager Report — {date_selectionnee.strftime('%d/%m/%Y')}")
        if os.path.exists(DB_FILE):
            try:
                df = pd.read_csv(DB_FILE)
                rapport_matin = df[(df['Date'] == date_rapport_str) & (df['Shift'] == 'MATIN')]
                if not rapport_matin.empty:
                    st.warning("⚠️ **Rappel du Shift MATIN :**")
                    st.write(f"• Incidents techniques ce matin : {rapport_matin['Incidents_Techniques'].values[0]}")
                    
                    prio_m_aff = safe_load_json(rapport_matin['Priorites_Liste'].values[0])
                    if prio_m_aff:
                        for idx, p in enumerate(prio_m_aff, 1):
                            st.write(f"   {idx}. {p}")
                    else:
                        st.write("• Aucune priorité transmise.")
            except:
                pass
        
        st.markdown("---")
        st.subheader("RÉSUMÉ DU SOIR")
        col1, col2 = st.columns(2)
        with col1:
            s_chambres_occ = st.number_input("Chambres occupées", min_value=0, value=0, key="s_occ")
            s_late_check = st.number_input("Late Check-in", min_value=0, value=0, key="s_late")
            s_departs_tardifs = st.number_input("Départs tardifs", min_value=0, value=0, key="s_dep_t")
        with col2:
            s_vip = st.number_input("Chambres VIP", min_value=0, value=0, key="s_vip")
            s_incidents = st.number_input("Incidents techniques", min_value=0, value=0, key="s_inc")
            
        st.markdown("#### Réservations Piscine (Provenance)")
        cps1, cps2, cps3, cps4 = st.columns(4)
        with cps1:
            s_piscine_eat = st.number_input("Eatnow", min_value=0, value=0, key="s_p_eat")
        with cps2:
            s_piscine_bed = st.number_input("Mysonbed", min_value=0, value=0, key="s_p_bed")
        with cps3:
            s_piscine_mfy = st.number_input("Marrakech For You", min_value=0, value=0, key="s_p_mfy")
        with cps4:
            s_piscine_dir = st.number_input("Direct (Tél / Accueil)", min_value=0, value=0, key="s_p_dir")

        st.markdown("---")
        st.subheader("SUIVI DES ESPACES")
        etat_espaces_soir = {}
        for espace in espaces:
            st.write(f"**{espace}**")
            c1, c2, c3 = st.columns([1.2, 2.4, 2.4])
            with c1:
                etat = st.selectbox("État", ["OK", "Alerte"], key=f"soir_etat_{espace}")
            with c2:
                obs = st.text_input("Observations", placeholder="RAS", key=f"soir_obs_{espace}")
            with c3:
                interv = st.text_input("Intervention nécessaire", placeholder="Aucune", key=f"soir_int_{espace}")
            
            photo_espace = st.file_uploader("📷 Photo de l'espace (Optionnel)", type=["jpg", "jpeg", "png"], key=f"soir_photo_{espace}")
            
            etat_espaces_soir[f"{espace}_Etat"] = etat
            etat_espaces_soir[f"{espace}_Observations"] = obs if obs.strip() != "" else "Aucune"
            etat_espaces_soir[f"{espace}_Intervention"] = interv if interv.strip() != "" else "Aucune"
            etat_espaces_soir[f"{espace}_Photo"] = image_to_base64(photo_espace)
            
            st.markdown("<hr style='margin:0.5em 0px;', size='1'>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("RÉCLAMATIONS CLIENTS")
        with st.form("form_rec_soir", clear_on_submit=True):
            rc1, rc2, rc3, rc4 = st.columns([1, 1.5, 2.5, 2.5])
            r_heure = rc1.text_input("Heure", placeholder="20h30")
            r_chambre = rc2.text_input("Chambre / Client", placeholder="Ch 1")
            r_sujet = rc3.text_input("Sujet", placeholder="Pas d'eau chaude")
            r_action = rc4.text_input("Action prise", placeholder="Technicien envoyé")
            rs_photo = st.file_uploader("📷 Ajouter une photo d'illustration (Optionnel)", type=["jpg", "jpeg", "png"], key="photo_rec_s")
            submit_rec_s = st.form_submit_button("➕ Ajouter la réclamation (Soir)", use_container_width=True)
            
            if submit_rec_s:
                if r_chambre or r_sujet:
                    base64_img = image_to_base64(rs_photo)
                    st.session_state.reclamations_soir.append({
                        "Heure": r_heure if r_heure else "--h--", 
                        "Chambre": r_chambre if r_chambre else "Inconnu", 
                        "Sujet": r_sujet if r_sujet else "Non spécifié", 
                        "Action": r_action if r_action else "Aucune",
                        "Photo": base64_img
                    })
                st.rerun()
        
        if st.session_state.reclamations_soir:
            df_s_aff = pd.DataFrame(st.session_state.reclamations_soir)
            if "Photo" in df_s_aff.columns:
                df_s_aff["Photo"] = df_s_aff["Photo"].apply(lambda x: "📸 Oui" if x else "Non")
            st.table(df_s_aff)
            if st.button("❌ Effacer la liste des réclamations (Soir)", key="btn_del_rs"):
                st.session_state.reclamations_soir = []
                st.rerun()

        st.markdown("---")
        st.subheader("PRIORITÉS POUR LA NUIT")
        with st.form("form_prio_soir", clear_on_submit=True):
            nouvelle_prio_s = st.text_input("Rédiger une priorité pour la nuit...", placeholder="Ex: Ronde à faire à 3h du matin...")
            submit_prio_s = st.form_submit_button("➕ Ajouter cette priorité", use_container_width=True)
            
            if submit_prio_s and nouvelle_prio_s:
                st.session_state.priorites_soir.append(nouvelle_prio_s)
                st.rerun()
                
        if st.session_state.priorites_soir:
            for i, prio in enumerate(st.session_state.priorites_soir, 1):
                st.write(f"**{i}.** {prio}")
            if st.button("❌ Effacer les priorités (Soir)", key="btn_del_prio_s"):
                st.session_state.priorites_soir = []
                st.rerun()

        st.markdown("---")
        st.subheader("NOTES MANAGER")
        notes_manager_soir = st.text_area("Observations générales du soir", placeholder="Saisir vos notes ici...", key="ns_text")

        if st.button("💾 Enregistrer le Rapport Soir", use_container_width=True, key="btn_save_soir"):
            donnees_soir = {
                "Date": date_rapport_str,
                "Shift": "SOIR",
                "Chambres_Occupees": s_chambres_occ,
                "Late_Check_In": s_late_check,
                "Departs_Tardifs": s_departs_tardifs,
                "VIP": s_vip,
                "Incidents_Techniques": s_incidents,
                "Piscine_Eatnow": s_piscine_eat,
                "Piscine_Mysonbed": s_piscine_bed,
                "Piscine_MarrakechForYou": s_piscine_mfy,
                "Piscine_Direct": s_piscine_dir,
                "Priorites_Liste": json.dumps(st.session_state.priorites_soir),
                "Notes_Manager": notes_manager_soir if notes_manager_soir.strip() != "" else "Aucune",
                "Reclamations_Detail": json.dumps(st.session_state.reclamations_soir)
            }
            donnees_soir.update(etat_espaces_soir)
            sauvegarder_rapport(donnees_soir)
            st.success("🎉 Le rapport du soir a été enregistré / mis à jour avec succès !")
            
            st.session_state.reclamations_soir = []
            st.session_state.priorites_soir = []
            st.rerun()

# ==========================================
# PAGE 2 : CONSULTATION ET FILTRAGE AMÉLIORÉ
# ==========================================
elif page == "📋 Consulter les Rapports":
    st.header("📋 Consultation des Rapports")
    
    c_date, c_shift = st.columns(2)
    with c_date:
        date_selectionnee_dt = st.date_input("📅 Choisir la Date", value=datetime.now().date())
        date_choisie = date_selectionnee_dt.strftime("%Y-%m-%d")
        date_fr = date_selectionnee_dt.strftime("%d/%m/%Y")
    
    with c_shift:
        shift_choisi = st.selectbox("⏰ Choisir le Shift", ["MATIN", "SOIR"])
        
    st.markdown("---")
    
    if not os.path.exists(DB_FILE):
        st.info("ℹ️ Aucun rapport n'a encore été créé dans l'application.")
    else:
        df_consult = pd.read_csv(DB_FILE)
        
        if df_consult.empty:
            st.info("ℹ️ La base de données est vide pour le moment.")
        else:
            rapport_selectionne = df_consult[(df_consult['Date'] == date_choisie) & (df_consult['Shift'] == shift_choisi)]
            
            if rapport_selectionne.empty:
                st.warning(f"⚠️ Aucun rapport n'a été enregistré pour le **{date_fr}** lors du shift **{shift_choisi}**.")
            else:
                st.success(f"### 📄 Fiche trouvée : {date_fr} — Shift {shift_choisi}")
                row = rapport_selectionne.iloc[0]
                
                # Génération du PDF
                pdf_data = generer_pdf(row, date_fr, shift_choisi, espaces)
                
                st.download_button(
                    label="📥 Télécharger le Rapport PDF (Format Papier)",
                    data=pdf_data,
                    file_name=f"Rapport_{shift_choisi}_{date_choisie}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.markdown("---")
                st.subheader("📊 Résumé des Opérations")
                
                # Calcul des stats piscine pour la consultation
                p_eat = int(row.get('Piscine_Eatnow', 0))
                p_bed = int(row.get('Piscine_Mysonbed', 0))
                p_mfy = int(row.get('Piscine_MarrakechForYou', 0))
                p_dir = int(row.get('Piscine_Direct', 0))
                total_piscine = p_eat + p_bed + p_mfy + p_dir
                
                if shift_choisi == "MATIN":
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Chambres Occ.", int(row.get('Chambres_Occupees', 0)))
                    c2.metric("Chambres VIP", int(row.get('VIP', 0)))
                    c3.metric("Arrivées Prév.", int(row.get('Arrivees_Prevues', 0)))
                    c4.metric("Départs Prév.", int(row.get('Departs_Prevus', 0)))
                    c5.metric("Incidents Tech.", int(row.get('Incidents_Techniques', 0)))
                elif shift_choisi == "SOIR":
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Chambres Occ.", int(row.get('Chambres_Occupees', 0)))
                    c2.metric("Chambres VIP", int(row.get('VIP', 0)))
                    c3.metric("Late Check-in", int(row.get('Late_Check_In', 0)))
                    c4.metric("Départs Tard.", int(row.get('Departs_Tardifs', 0)))
                    c5.metric("Incidents Tech.", int(row.get('Incidents_Techniques', 0)))
                
                # Affichage des statistiques de provenance de la Piscine (4 colonnes)
                st.markdown(f"#### Détail des réservations Piscine (Total : {total_piscine})")
                cp_aff1, cp_aff2, cp_aff3, cp_aff4 = st.columns(4)
                cp_aff1.metric("Eatnow", p_eat)
                cp_aff2.metric("Mysonbed", p_bed)
                cp_aff3.metric("Marrakech For You", p_mfy)
                cp_aff4.metric("Direct", p_dir)
                
                st.markdown("---")
                st.subheader("🔍 Suivi de l'état des espaces")
                espaces_data = []
                for esp in espaces:
                    has_photo_esp = f"{esp}_Photo" in row and not pd.isna(row.get(f"{esp}_Photo")) and str(row.get(f"{esp}_Photo")).strip() != ""
                    espaces_data.append({
                        "Espace": esp,
                        "État": row.get(f"{esp}_Etat", "N/A"),
                        "Observations": "Aucune" if pd.isna(row.get(f"{esp}_Observations")) or str(row.get(f"{esp}_Observations")).strip().lower() == "nan" or str(row.get(f"{esp}_Observations")).strip() == "" else row.get(f"{esp}_Observations"),
                        "Intervention": "Aucune" if pd.isna(row.get(f"{esp}_Intervention")) or str(row.get(f"{esp}_Intervention")).strip().lower() == "nan" or str(row.get(f"{esp}_Intervention")).strip() == "" else row.get(f"{esp}_Intervention"),
                        "Photo": "📸 Oui" if has_photo_esp else "Non"
                    })
                st.table(pd.DataFrame(espaces_data))
                
                with st.expander("🖼️ Visualiser les photos des espaces communs"):
                    photo_trouvee = False
                    for esp in espaces:
                        img_b64 = row.get(f"{esp}_Photo")
                        if not pd.isna(img_b64) and str(img_b64).strip() != "":
                            photo_trouvee = True
                            try:
                                st.write(f"**Espace : {esp} ({row.get(f'{esp}_Etat')})**")
                                img_data = base64.b64decode(img_b64)
                                image = Image.open(BytesIO(img_data))
                                st.image(image, width=400)
                            except:
                                st.error(f"Erreur d'affichage : {esp}")
                    if not photo_trouvee:
                        st.write("Aucune photo disponible pour les espaces.")
                
                st.subheader("🚨 Réclamations Clients")
                liste_rec = safe_load_json(row.get('Reclamations_Detail', '[]'))
                if liste_rec and len(liste_rec) > 0:
                    df_table_rec = pd.DataFrame(liste_rec)
                    if "Photo" in df_table_rec.columns:
                        df_table_rec["Photo"] = df_table_rec["Photo"].apply(lambda x: "📸 Oui" if x else "Non")
                    st.table(df_table_rec)
                else:
                    st.write("✓ Aucune réclamation.")

                st.markdown("---")
                titre_prio_interface = "📌 Priorités pour le Shift Soir" if shift_choisi == "MATIN" else "📌 Priorités pour la Nuit"
                st.subheader(titre_prio_interface)
                liste_prio = safe_load_json(row.get('Priorites_Liste', '[]'))
                if liste_prio and len(liste_prio) > 0:
                    for idx, p in enumerate(liste_prio, 1):
                        st.write(f"**{idx}.** {p}")
                else:
                    st.write("_Aucune priorité enregistrée._")
                
                st.markdown("---")
                st.subheader("📝 Notes du Manager")
                notes = row.get('Notes_Manager', 'Aucune')
                st.write(notes)
