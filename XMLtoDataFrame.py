import os
import pandas as pd
import xml.etree.ElementTree as ET
from glob import glob

fichier = "/Users/Patrice/Proust/Lettres/03987_XVIII_307-637df4d1df8ed-66713160c9a90.xml"
doosier = "/Users/Patrice/Proust/Lettres/"

def extraire_contenu_tei(chemin_fichier):
    """
    Extrait le contenu d'un fichier XML TEI et le stocke sous forme structurée.
    
    Args:
        chemin_fichier: Chemin vers le fichier XML
        
    Returns:
        Dictionnaire contenant les données structurées
    """
    # Définir l'espace de noms TEI
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    # Parser le fichier XML
    tree = ET.parse(chemin_fichier)
    root = tree.getroot()
    
    # Dictionnaire pour stocker les données
    donnees = {
        'fichier': os.path.basename(chemin_fichier)
    }
    
    # Fonction auxiliaire pour extraire le texte en excluant les notes
    def extraire_texte_sans_notes(element):
        if element.tag.endswith('note'):
            return ""
        
        texte = element.text or ""
        for enfant in element:
            texte += extraire_texte_sans_notes(enfant)
            if enfant.tail:
                texte += enfant.tail
        return texte
    
    # 1. Métadonnées de la lettre
    try:
        # ID de la lettre
        corresp_desc = root.find('.//tei:correspDesc', ns)
        if corresp_desc is not None:
            donnees['id_lettre'] = corresp_desc.get('{http://www.w3.org/XML/1998/namespace}id')
        
        # Expéditeur
        expediteur = root.find('.//tei:correspAction[@type="write"]/tei:persName', ns)
        if expediteur is not None:
            prenom = expediteur.find('./tei:forename', ns)
            nom = expediteur.find('./tei:surname', ns)
            if prenom is not None and nom is not None:
                donnees['expediteur'] = f"{prenom.text} {nom.text}"
        
        # Date
        date = root.find('.//tei:correspAction[@type="write"]/tei:date', ns)
        if date is not None:
            donnees['date'] = date.text
            donnees['date_when'] = date.get('when')
        
        # Destinataire
        destinataire = root.find('.//tei:correspAction[@type="received"]/tei:persName', ns)
        if destinataire is not None:
            prenom = destinataire.find('./tei:forename', ns)
            nom = destinataire.find('./tei:surname', ns)
            if prenom is not None and nom is not None:
                donnees['destinataire'] = f"{prenom.text} {nom.text}"
        
        # Mots-clés/thèmes
        mots_cles = root.findall('.//tei:textClass/tei:keywords/tei:term', ns)
        if mots_cles:
            donnees['mots_cles'] = [mot.text for mot in mots_cles if mot.text]
    except Exception as e:
        print(f"Erreur lors de l'extraction des métadonnées: {e}")
    
    # 2. Contenu textuel de la lettre
    try:
        contenu = []
        
        # Extraire l'ouverture (dateline, salutation)
        openers = root.findall('.//tei:opener', ns)
        for opener in openers:
            # Dateline
            dateline = opener.find('./tei:dateline', ns)
            if dateline is not None:
                texte = extraire_texte_sans_notes(dateline).strip()
                if texte:
                    contenu.append(texte)
            
            # Salutation
            salute = opener.find('./tei:salute', ns)
            if salute is not None:
                texte = extraire_texte_sans_notes(salute).strip()
                if texte:
                    contenu.append(texte)
        
        # Extraire les paragraphes du corps
        for p in root.findall('.//tei:div[@type="letter"]/tei:p', ns):
            texte = extraire_texte_sans_notes(p).strip()
            if texte:
                contenu.append(texte)
        
        # Extraire la clôture (signature)
        closer = root.find('.//tei:closer', ns)
        if closer is not None:
            # Salutation finale
            salute = closer.find('./tei:salute', ns)
            if salute is not None:
                texte = extraire_texte_sans_notes(salute).strip()
                if texte:
                    contenu.append(texte)
            
            # Signature
            signed = closer.find('./tei:signed', ns)
            if signed is not None:
                texte = extraire_texte_sans_notes(signed).strip()
                if texte:
                    contenu.append(texte)
        
        # Extraire les post-scriptum
        for ps in root.findall('.//tei:postscript', ns):
            for p in ps.findall('./tei:p', ns):
                texte = extraire_texte_sans_notes(p).strip()
                if texte:
                    contenu.append("P.S.: " + texte)
        
        # Joindre les éléments textuels
        donnees['texte_lettre'] = "\n\n".join([t for t in contenu if t])
    except Exception as e:
        print(f"Erreur lors de l'extraction du texte: {e}")
    
    # 3. Extraire les notes séparément (optionnel)
    # try:
    #     notes = []
    #     for note in root.findall('.//tei:note', ns):
    #         num = note.get('n', '')
    #         resp = note.get('resp', '')
    #         if note.text:
    #             notes.append(f"Note {num} {resp}: {note.text.strip()}")
        
    #     donnees['notes'] = "\n".join(notes)
    # except Exception as e:
    #     print(f"Erreur lors de l'extraction des notes: {e}")
    
    return donnees

def extraire_corpus_tei(chemin_dossier, motif="*.xml"):
    """
    Extrait le contenu de tous les fichiers XML TEI d'un dossier.
    
    Args:
        chemin_dossier: Chemin vers le dossier contenant les fichiers XML
        motif: Motif de filtrage des fichiers (par défaut "*.xml")
        
    Returns:
        DataFrame pandas avec les données extraites
    """
    # Liste pour stocker les données
    donnees = []
    
    # Récupérer tous les fichiers XML du dossier
    chemins_fichiers = glob(os.path.join(chemin_dossier, motif))
    
    for chemin in chemins_fichiers:
        try:
            # Extraire les données du fichier
            donnees_fichier = extraire_contenu_tei(chemin)
            donnees.append(donnees_fichier)
            print(f"Traitement réussi: {os.path.basename(chemin)}")
        except Exception as e:
            print(f"Erreur lors du traitement de {os.path.basename(chemin)}: {e}")
    
    # Créer le dataframe
    df = pd.DataFrame(donnees)
    return df

# Exemple d'utilisation pour un seul fichier
def exemple_fichier_unique(chemin_fichier):
    donnees = extraire_contenu_tei(chemin_fichier)
    df = pd.DataFrame([donnees])
    return df

# Exemple d'utilisation pour un dossier
def exemple_dossier(chemin_dossier):
    df = extraire_corpus_tei(chemin_dossier)
    return df

# Utilisation

print(f"Traitement en cours... {fichier}")
#df = exemple_fichier_unique(fichier)
df=exemple_dossier(doosier)
df.to_csv("corpus_proust.csv", index=False, sep=";")
df.to_excel("corpus_proust.xlsx", index=False)
print(df.head(10))
    
    # Pour un dossier
    # df = exemple_dossier("chemin/vers/dossier")
    
    # Afficher les premières lignes
    # print(df.head())
    
    # Sauvegarder en CSV
    # df.to_csv("corpus_proust.csv", index=False)
    
    # Sauvegarder en Excel
    # df.to_excel("corpus_proust.xlsx", index=False)