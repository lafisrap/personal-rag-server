#!/usr/bin/env python3
"""
Simple gedankenfehler-umkehren command
Creates single umkehrung entries for the database
"""

import sys
import json
import uuid
from datetime import datetime
from pymongo import MongoClient
import argparse

class GedankenfehlerUmkehrenCommand:
    """Simple command to create gedankenfehler umkehrungen"""
    
    def __init__(self):
        self.mongodb_uri = "mongodb+srv://lafisrap:iRyZyiAK3uaXi0ee@ai-cluster-one.m1w8j.mongodb.net/12_weltanschauungen"
        self.client = None
        self.db = None
        
        # Author mappings
        self.authors = {
            "Dynamismus": "Ariadne Ikarus Nietzsche",
            "Idealismus": "Aurelian I. Schelling", 
            "Individualismus": "Amara Illias Leibniz",
            "Materialismus": "Aloys I. Freud",
            "Mathematismus": "Arcadius Ikarus Torvalds",
            "Phänomenalismus": "Aetherius Imaginaris Goethe",
            "Pneumatismus": "Aurelian Irenicus Novalis",
            "Psychismus": "Archetype Intuitionis Fichte",
            "Rationalismus": "Aristoteles Isaak Herder",
            "Realismus": "Arvid I. Steiner",
            "Sensualismus": "Apollo Ikarus Schiller",
            "Spiritualismus": "Amara I. Steiner"
        }
    
    def connect(self):
        """Connect to database"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client['12_weltanschauungen']
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def get_next_nummer(self):
        """Get next available gedankenfehler number"""
        pipeline = [{"$group": {"_id": "$nummer"}}, {"$sort": {"_id": 1}}]
        used_numbers = [item["_id"] for item in self.db.gedanken.aggregate(pipeline)]
        
        for i in range(1, 44):
            if i not in used_numbers:
                return i
        return 44  # If all 1-43 are used, suggest 44
    
    def get_next_rank(self, weltanschauung, nummer):
        """Get next rank for weltanschauung/nummer combination"""
        existing = list(self.db.gedanken.find({"weltanschauung": weltanschauung, "nummer": nummer}))
        if not existing:
            return 1
        max_rank = max(entry.get('rank', 0) for entry in existing)
        return max_rank + 1
    
    def generate_umkehrung(self, gedankenfehler, weltanschauung):
        """Generate simple umkehrung for a gedankenfehler"""
        # Simple template-based generation
        return {
            "gedanke": f"[{weltanschauung}] Umkehrung: {gedankenfehler}",
            "gedanke_einfach": f"Einfache {weltanschauung}-Umkehrung",
            "gedanke_kurz": f"{weltanschauung} Umkehrung"
        }
    
    def create_entry(self, gedankenfehler, weltanschauung, nummer=None):
        """Create a single gedankenfehler-umkehren entry"""
        if not self.connect():
            return False
        
        try:
            # Auto-assign nummer if not provided
            if nummer is None:
                nummer = self.get_next_nummer()
                print(f"📝 Auto-assigned nummer: {nummer}")
            
            # Validate weltanschauung
            if weltanschauung not in self.authors:
                print(f"❌ Unknown weltanschauung: {weltanschauung}")
                print(f"   Available: {list(self.authors.keys())}")
                return False
            
            # Generate umkehrung
            umkehrung = self.generate_umkehrung(gedankenfehler, weltanschauung)
            
            # Get author info
            autor = self.authors[weltanschauung]
            autor_info = self.db.autoren.find_one({"name": autor})
            autor_id = autor_info.get("id") if autor_info else "unknown"
            
            # Get next rank
            rank = self.get_next_rank(weltanschauung, nummer)
            
            # Create entry
            entry = {
                "autor": autor,
                "autorId": autor_id,
                "weltanschauung": weltanschauung,
                "created_at": datetime.now(),
                "ausgangsgedanke": gedankenfehler,
                "ausgangsgedanke_in_weltanschauung": f"Aus {weltanschauung.lower()}er Sicht: {gedankenfehler}",
                "id": str(uuid.uuid4()),
                "gedanke": umkehrung["gedanke"],
                "gedanke_einfach": umkehrung["gedanke_einfach"],
                "gedanke_kurz": umkehrung["gedanke_kurz"],
                "nummer": nummer,
                "model": "gedankenfehler-umkehren-command",
                "rank": rank
            }
            
            # Insert entry
            result = self.db.gedanken.insert_one(entry)
            
            if result.inserted_id:
                print(f"✅ Created entry:")
                print(f"   • Weltanschauung: {weltanschauung}")
                print(f"   • Nummer: {nummer}")
                print(f"   • Rank: {rank}")
                print(f"   • Author: {autor}")
                print(f"   • ID: {entry['id']}")
                return True
            else:
                print(f"❌ Failed to create entry")
                return False
                
        except Exception as e:
            print(f"❌ Error creating entry: {e}")
            return False
        finally:
            if self.client:
                self.client.close()

def main():
    parser = argparse.ArgumentParser(description='Gedankenfehler-Umkehren Command')
    parser.add_argument('gedankenfehler', help='The gedankenfehler text to reverse')
    parser.add_argument('weltanschauung', help='The weltanschauung perspective')
    parser.add_argument('--nummer', type=int, help='Specific nummer (auto-assigned if not provided)')
    
    args = parser.parse_args()
    
    command = GedankenfehlerUmkehrenCommand()
    success = command.create_entry(args.gedankenfehler, args.weltanschauung, args.nummer)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 