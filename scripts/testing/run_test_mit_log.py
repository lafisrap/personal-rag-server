#!/usr/bin/env python3
"""
Test-Script, das die RAG-Antwort und die zum LLM gesendeten Daten in eine Datei schreibt
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

def run_test_with_logging():
    """Test ausführen und RAG-Antwort sowie LLM-Input loggen."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    from app.services.llm_service import llm_service
    
    # Speicherpfad für die Logs
    log_file = "last-rag-response.txt"
    
    # Initialisiere Vector-Datenbank
    logger.info("=== Starte RAG-Test mit detailliertem Logging ===")
    vector_db.init_pinecone()
    
    # Ursprüngliche LLM-Methode speichern, um sie später wiederherzustellen
    original_generate_with_rag = llm_service.generate_with_rag
    
    # Output-Datei vorbereiten
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"# RAG-Protokoll - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    try:
        # LLM-Methode überschreiben, um den Input zu loggen
        def logging_generate_with_rag(messages, context, system_prompt=None):
            # Log-Informationen in die Datei schreiben
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("## 1. Abgerufene RAG-Dokumente\n\n")
                for i, doc in enumerate(context):
                    f.write(f"### Dokument {i+1}\n")
                    f.write(f"```\n{doc}\n```\n\n")
                
                f.write("## 2. An das LLM gesendete Nachrichten\n\n")
                
                # System Prompt
                if system_prompt:
                    f.write("### System Prompt\n")
                    f.write(f"```\n{system_prompt}\n```\n\n")
                
                # RAG-Kontext für das LLM
                f.write("### RAG-Kontext\n")
                f.write("```\n")
                f.write("Hier sind relevante Informationen, die helfen könnten, die Frage zu beantworten:\n\n")
                for i, doc in enumerate(context):
                    f.write(f"Dokument {i+1}:\n{doc}\n\n")
                f.write("```\n\n")
                
                # Benutzer-Nachrichten
                f.write("### Benutzer-Nachrichten\n")
                for msg in messages:
                    f.write(f"**{msg['role']}**: {msg['content']}\n\n")
            
            # Original-Methode aufrufen
            result = original_generate_with_rag(messages, context, system_prompt)
            
            # Antwort des LLM loggen
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("## 3. Antwort des LLM\n\n")
                f.write("```\n")
                f.write(result.get("content", "Keine Antwort erhalten"))
                f.write("\n```\n")
            
            return result
        
        # Original-Methode mit unserer Logging-Methode ersetzen
        llm_service.generate_with_rag = logging_generate_with_rag
        
        # Test durchführen
        logger.info("Führe RAG-Abfrage mit Kategorie-Filter 'Realismus' durch...")
        
        # Definiere Abfrage und Filter
        abfrage_text = "Was ist Moralische Fantasie?"
        kategorie_filter = {"category": "Realismus"}
        
        logger.info(f"Abfrage: '{abfrage_text}'")
        logger.info(f"Kategorie-Filter: {kategorie_filter}")
        
        # Definiere Konversationsnachrichten
        nachrichten = [
            {"role": "user", "content": abfrage_text}
        ]
        
        # Generiere RAG-Antwort
        antwort = rag_service.generate_rag_response(
            messages=nachrichten,
            filter=kategorie_filter,
            top_k=5
        )
        
        logger.info(f"RAG-Antwort wurde generiert und in '{log_file}' gespeichert.")
        logger.info(f"Antwortlänge: {len(antwort.get('content', ''))} Zeichen")
        logger.info(f"Verwendetes Modell: {antwort.get('model', 'unbekannt')}")
        logger.info(f"Anzahl abgerufener Dokumente: {len(antwort.get('retrieved_documents', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {str(e)}")
        return False
    
    finally:
        # Original-Methode wiederherstellen
        llm_service.generate_with_rag = original_generate_with_rag

if __name__ == "__main__":
    erfolg = run_test_with_logging()
    exit(0 if erfolg else 1) 