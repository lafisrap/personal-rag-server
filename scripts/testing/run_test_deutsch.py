#!/usr/bin/env python3
"""
Wrapper-Script für den Realismus-Test mit deutscher Ausgabe
"""
import os
import sys
import logging
from typing import Dict, Any, List

# Füge das aktuelle Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath("."))

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test_deutsch():
    """Test mit deutscher Ausgabe ausführen."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    # Initialisiere Vector-Datenbank
    logger.info("=== Starte Realismus-Kategorie Test (Deutsch) ===")
    vector_db.init_pinecone()
    
    try:
        # 1. Test: Abfrage mit Kategorie-Filter
        logger.info("\n1. Teste RAG-Abfrage mit Kategorie-Filter...")
        logger.info("=== Teste RAG-Abfrage mit Realismus-Kategorie ===")
        
        # Definiere Abfrage und Filter
        abfrage_text = "Was ist Moralische Fantasie?"
        kategorie_filter = {"category": "Realismus"}
        
        logger.info(f"Abfrage: '{abfrage_text}'")
        logger.info(f"Kategorie-Filter: {kategorie_filter}")
        
        # Führe die Abfrage aus
        ergebnisse = rag_service.query(
            query_text=abfrage_text,
            filter=kategorie_filter,
            top_k=5
        )
        
        # Prüfe Ergebnisse
        assert isinstance(ergebnisse, list), "Ergebnisse sollten eine Liste sein"
        logger.info(f"Gefunden: {len(ergebnisse)} Ergebnisse")
        
        # Wenn Ergebnisse vorhanden, überprüfe ihre Struktur und Kategorie
        if ergebnisse:
            for i, ergebnis in enumerate(ergebnisse):
                # Prüfe, ob Kategorie Realismus ist (falls in Metadaten vorhanden)
                if "category" in ergebnis["metadata"]:
                    assert ergebnis["metadata"]["category"] == "Realismus", \
                        f"Ergebnis {i} sollte Kategorie 'Realismus' haben, hat aber '{ergebnis['metadata']['category']}'"
                
                logger.info(f"Ergebnis {i+1}:")
                logger.info(f"  Relevanz: {ergebnis['score']:.4f}")
                logger.info(f"  Textauszug: {ergebnis['text'][:100]}...")
                logger.info(f"  Metadaten: {ergebnis['metadata']}")
        else:
            logger.warning("Keine Ergebnisse für die Abfrage mit Realismus-Kategorie-Filter gefunden")
        
        # 2. Test: RAG-Antwortgenerierung mit Kategorie-Filter
        logger.info("\n2. Teste RAG-Antwortgenerierung mit Kategorie-Filter...")
        logger.info("=== Teste RAG-Antwortgenerierung mit Realismus-Kategorie ===")
        
        # Definiere Konversationsnachrichten
        nachrichten = [
            {"role": "user", "content": "Was ist Moralische Fantasie?"}
        ]
        
        logger.info(f"Nachrichten: {nachrichten}")
        logger.info(f"Kategorie-Filter: {kategorie_filter}")
        
        # Generiere RAG-Antwort
        antwort = rag_service.generate_rag_response(
            messages=nachrichten,
            filter=kategorie_filter,
            top_k=5
        )
        
        # Prüfe Antwort
        assert isinstance(antwort, dict), "Antwort sollte ein Dictionary sein"
        assert "content" in antwort, "Antwort sollte 'content'-Feld haben"
        assert "retrieved_documents" in antwort, "Antwort sollte 'retrieved_documents'-Feld haben"
        
        logger.info(f"Generierte Antwort:")
        logger.info(f"  Modell: {antwort.get('model', 'unbekannt')}")
        logger.info(f"  Länge der Antwort: {len(antwort['content'])} Zeichen")
        logger.info(f"  Abgerufene Dokumente: {len(antwort.get('retrieved_documents', []))}")
        logger.info(f"  Antworttext: {antwort['content']}")
        
        # Prüfe abgerufene Dokumente
        abgerufene_dokumente = antwort.get("retrieved_documents", [])
        if abgerufene_dokumente:
            logger.info("Abgerufene Dokumente:")
            for i, dok in enumerate(abgerufene_dokumente):
                if "metadata" in dok and "category" in dok["metadata"]:
                    assert dok["metadata"]["category"] == "Realismus", \
                        f"Abgerufenes Dokument {i} sollte Kategorie 'Realismus' haben"
                logger.info(f"  Dokument {i+1}: Relevanz {dok.get('score', 'N/A')}, "
                          f"Vorschau: {dok.get('text', '')[:50]}...")
        
        # 3. Test: Vergleichstest ohne Kategorie-Filter
        logger.info("\n3. Teste Abfrage ohne Kategorie-Filter (zum Vergleich)...")
        logger.info("=== Teste Abfrage ohne Kategorie-Filter (zum Vergleich) ===")
        
        # Führe Abfrage ohne Filter aus
        ergebnisse_ohne_filter = rag_service.query(
            query_text=abfrage_text,
            filter=None,  # Kein Filter
            top_k=5
        )
        
        logger.info(f"Gefunden: {len(ergebnisse_ohne_filter)} Ergebnisse ohne Kategorie-Filter")
        
        # Protokolliere gefundene Kategorien
        gefundene_kategorien = set()
        for i, ergebnis in enumerate(ergebnisse_ohne_filter):
            if "metadata" in ergebnis and "category" in ergebnis["metadata"]:
                gefundene_kategorien.add(ergebnis["metadata"]["category"])
            logger.info(f"Ergebnis {i+1}: Relevanz {ergebnis['score']:.4f}, "
                      f"Kategorie: {ergebnis.get('metadata', {}).get('category', 'N/A')}")
        
        logger.info(f"Gefundene Kategorien: {gefundene_kategorien}")
        
        # Zusammenfassung
        logger.info("\n=== Testzusammenfassung ===")
        logger.info(f"✓ Gefilterte Ergebnisse: {len(ergebnisse)} Dokumente")
        logger.info(f"✓ RAG-Antwort generiert: {len(antwort.get('content', ''))} Zeichen")
        logger.info(f"✓ Ungefilterte Ergebnisse: {len(ergebnisse_ohne_filter)} Dokumente")
        logger.info("Alle Tests erfolgreich abgeschlossen!")
        
        return True
        
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {str(e)}")
        return False

if __name__ == "__main__":
    erfolg = run_test_deutsch()
    exit(0 if erfolg else 1) 