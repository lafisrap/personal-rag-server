#!/usr/bin/env python3
"""
Test-Script, das die RAG-Antwort mit vollständigen Metadaten in eine Datei schreibt
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath("."))

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_with_metadata():
    """Test ausführen und RAG-Antwort mit Metadaten loggen."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    # Speicherpfad für die Logs
    log_file = "dokument_metadaten.txt"
    
    # Initialisiere Vector-Datenbank
    logger.info("=== Starte RAG-Test mit Metadaten-Logging ===")
    vector_db.init_pinecone()
    
    try:
        # Test durchführen
        logger.info("Welches sind die 12 Weltanschauungen?")
        
        # Definiere Abfrage und Filter
        abfrage_text = "Welches sind die 12 Weltanschauungen?"
        kategorie_filter = {"category": "Realismus"}
        
        logger.info(f"Abfrage: '{abfrage_text}'")
        logger.info(f"Kategorie-Filter: {kategorie_filter}")
        
        # Führe die Abfrage direkt aus (ohne LLM-Antwort zu generieren)
        ergebnisse = rag_service.query(
            query_text=abfrage_text,
            filter=kategorie_filter,
            top_k=5
        )
        
        # Output-Datei vorbereiten und Metadaten speichern
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# Dokument-Metadaten - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Abfrage: '{abfrage_text}'\n")
            f.write(f"## Filter: {kategorie_filter}\n\n")
            
            f.write("## Gefundene Dokumente\n\n")
            
            for i, ergebnis in enumerate(ergebnisse):
                f.write(f"### Dokument {i+1}\n\n")
                f.write(f"- **Relevanz:** {ergebnis['score']:.4f}\n")
                
                # Metadaten extrahieren
                metadaten = ergebnis.get('metadata', {})
                
                # Titel
                titel = metadaten.get('title', 'Kein Titel verfügbar')
                f.write(f"- **Titel:** {titel}\n")
                
                # Autor
                autor = metadaten.get('author', 'Kein Autor verfügbar')
                f.write(f"- **Autor:** {autor}\n")
                
                # Dateiname
                dateiname = metadaten.get('filename', 'Kein Dateiname verfügbar')
                f.write(f"- **Dateiname:** {dateiname}\n")
                
                # Dokument-ID
                dokument_id = metadaten.get('document_id', 'Keine ID verfügbar')
                f.write(f"- **Dokument-ID:** {dokument_id}\n")
                
                # Kategorie
                kategorie = metadaten.get('category', 'Keine Kategorie verfügbar')
                f.write(f"- **Kategorie:** {kategorie}\n")
                
                # Chunk-Index
                chunk_index = metadaten.get('chunk_index', 'Kein Chunk-Index verfügbar')
                f.write(f"- **Chunk-Index:** {chunk_index}\n")
                
                # Textauszug
                textauszug = ergebnis.get('text', '')[:150]
                f.write(f"- **Textauszug:** {textauszug}...\n\n")
                
                # Trennlinie
                if i < len(ergebnisse) - 1:
                    f.write("---\n\n")
        
        logger.info(f"Dokument-Metadaten wurden in '{log_file}' gespeichert.")
        logger.info(f"Anzahl gefundener Dokumente: {len(ergebnisse)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {str(e)}")
        return False

if __name__ == "__main__":
    erfolg = run_test_with_metadata()
    exit(0 if erfolg else 1) 