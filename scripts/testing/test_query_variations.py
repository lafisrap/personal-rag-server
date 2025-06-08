#!/usr/bin/env python3
"""
Skript zum Testen verschiedener Abfrage-Formulierungen für die RAG-Suche
"""
import os
import sys
import logging
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Füge das übergeordnete Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(".."))

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_query_variations(
    expected_doc: str = "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
    top_k: int = 20,
    output_dir: str = "results"  # relativer Pfad
):
    """Testet verschiedene Abfrage-Formulierungen für die RAG-Suche."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    # Erstelle den Ausgabeordner, falls er nicht existiert
    os.makedirs(output_dir, exist_ok=True)
    
    # Speicherpfad für die Logs
    log_file = os.path.join(output_dir, "abfrage_variationen_ergebnisse.txt")
    
    # Initialisiere Vector-Datenbank
    logger.info("=== Starte Test mit verschiedenen Abfrage-Formulierungen ===")
    vector_db.init_pinecone()
    
    # Liste der zu testenden Abfragen
    abfragen = [
        "Welches sind die 12 Weltanschauungen?",
        "Die zwölf Weltanschauungen nach Rudolf Steiner",
        "12 Weltanschauungen Materialismus Idealismus Spiritualismus",
        "Weltanschauungen Rudolf Steiner kosmischer Gedanke",
        "Steiner's Klassifikation der Weltanschauungen",
        "Zwölf philosophische Standpunkte Anthroposophie",
        "Materialismus Realismus Idealismus Mathematismus Rationalismus Psychismus Pneumatismus Monadismus Dynamismus Phänomenalismus Sensualismus Nominalismus",
        "Grundlegende Weltanschauungen in der Anthroposophie",
        "Welche Weltanschauungen gibt es nach Steiner?",
        "Der menschliche und der kosmische Gedanke Weltanschauungen"
    ]
    
    # Ergebnissammlung: [Abfrage, Position, Score, Kategorie]
    ergebnisse = []
    
    try:
        for abfrage in abfragen:
            logger.info(f"Teste Abfrage: '{abfrage}'")
            
            # 1. Test ohne Filter
            ergebnisse_ohne_filter = rag_service.query(
                query_text=abfrage,
                filter=None,
                top_k=top_k
            )
            
            # 2. Test mit Kategorie-Filter
            ergebnisse_mit_filter = rag_service.query(
                query_text=abfrage,
                filter={"category": "Realismus"},
                top_k=top_k
            )
            
            # Suche nach dem erwarteten Dokument (ohne Filter)
            found_without_filter = False
            position_without_filter = None
            score_without_filter = None
            category_without_filter = None
            
            for i, ergebnis in enumerate(ergebnisse_ohne_filter):
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc in filename:
                    found_without_filter = True
                    position_without_filter = i + 1
                    score_without_filter = ergebnis['score']
                    category_without_filter = metadata.get('category', 'Unbekannt')
                    break
            
            # Suche nach dem erwarteten Dokument (mit Filter)
            found_with_filter = False
            position_with_filter = None
            score_with_filter = None
            
            for i, ergebnis in enumerate(ergebnisse_mit_filter):
                metadata = ergebnis.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc in filename:
                    found_with_filter = True
                    position_with_filter = i + 1
                    score_with_filter = ergebnis['score']
                    break
            
            # Ergebnisse sammeln
            ergebnisse.append({
                "abfrage": abfrage,
                "ohne_filter": {
                    "gefunden": found_without_filter,
                    "position": position_without_filter,
                    "score": score_without_filter,
                    "kategorie": category_without_filter
                },
                "mit_filter": {
                    "gefunden": found_with_filter,
                    "position": position_with_filter,
                    "score": score_with_filter
                }
            })
        
        # Ergebnisse sortieren nach Position (ohne Filter)
        sortierte_ergebnisse = sorted(
            ergebnisse, 
            key=lambda x: (
                not x["ohne_filter"]["gefunden"],  # Gefundene zuerst
                x["ohne_filter"]["position"] if x["ohne_filter"]["position"] else float('inf')  # Nach Position sortieren
            )
        )
        
        # Ergebnisse in Datei schreiben
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# Ergebnisse der Abfrage-Variationen - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Gesuchtes Dokument\n'{expected_doc}'\n\n")
            f.write(f"## Top-K: {top_k}\n\n")
            
            # Zusammenfassung
            f.write("## Zusammenfassung\n\n")
            f.write("| Abfrage | Ohne Filter | Mit Filter | Score (ohne Filter) | Kategorie |\n")
            f.write("|---------|-------------|------------|---------------------|----------|\n")
            
            for ergebnis in sortierte_ergebnisse:
                ohne_filter = ergebnis["ohne_filter"]
                mit_filter = ergebnis["mit_filter"]
                
                ohne_filter_text = f"Position {ohne_filter['position']}" if ohne_filter["gefunden"] else "Nicht gefunden"
                mit_filter_text = f"Position {mit_filter['position']}" if mit_filter["gefunden"] else "Nicht gefunden"
                score_text = f"{ohne_filter['score']:.4f}" if ohne_filter["gefunden"] else "-"
                kategorie = ohne_filter["kategorie"] if ohne_filter["gefunden"] else "-"
                
                f.write(f"| {ergebnis['abfrage']} | {ohne_filter_text} | {mit_filter_text} | {score_text} | {kategorie} |\n")
            
            f.write("\n")
            
            # Detaillierte Ergebnisse
            f.write("## Detaillierte Ergebnisse\n\n")
            
            for i, ergebnis in enumerate(sortierte_ergebnisse):
                abfrage = ergebnis["abfrage"]
                ohne_filter = ergebnis["ohne_filter"]
                mit_filter = ergebnis["mit_filter"]
                
                f.write(f"### {i+1}. Abfrage: '{abfrage}'\n\n")
                
                # Ohne Filter
                f.write("#### Ohne Filter\n\n")
                if ohne_filter["gefunden"]:
                    f.write(f"✅ **Das erwartete Dokument wurde gefunden!**\n")
                    f.write(f"- Position: {ohne_filter['position']} von {top_k}\n")
                    f.write(f"- Relevanz-Score: {ohne_filter['score']:.4f}\n")
                    f.write(f"- Kategorie: {ohne_filter['kategorie']}\n\n")
                else:
                    f.write(f"❌ **Das erwartete Dokument wurde NICHT gefunden in den Top-{top_k} Ergebnissen.**\n\n")
                
                # Mit Filter
                f.write("#### Mit Filter (Kategorie: 'Realismus')\n\n")
                if mit_filter["gefunden"]:
                    f.write(f"✅ **Das erwartete Dokument wurde gefunden!**\n")
                    f.write(f"- Position: {mit_filter['position']} von {top_k}\n")
                    f.write(f"- Relevanz-Score: {mit_filter['score']:.4f}\n\n")
                else:
                    f.write(f"❌ **Das erwartete Dokument wurde NICHT gefunden in den Top-{top_k} Ergebnissen.**\n\n")
                
                f.write("---\n\n")
        
        # Beste Abfrage finden
        beste_abfrage = None
        beste_position = float('inf')
        
        for ergebnis in ergebnisse:
            if ergebnis["ohne_filter"]["gefunden"]:
                position = ergebnis["ohne_filter"]["position"]
                if position < beste_position:
                    beste_position = position
                    beste_abfrage = ergebnis["abfrage"]
        
        if beste_abfrage:
            logger.info(f"Beste Abfrage: '{beste_abfrage}' (Position {beste_position})")
        else:
            logger.info("Keine der getesteten Abfragen hat das erwartete Dokument gefunden.")
        
        logger.info(f"Ergebnisse wurden in '{log_file}' gespeichert.")
        return True
        
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {str(e)}")
        return False

if __name__ == "__main__":
    erfolg = test_query_variations()
    exit(0 if erfolg else 1) 