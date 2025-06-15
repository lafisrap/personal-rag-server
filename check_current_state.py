#!/usr/bin/env python3
from pymongo import MongoClient

client = MongoClient('mongodb+srv://lafisrap:iRyZyiAK3uaXi0ee@ai-cluster-one.m1w8j.mongodb.net/12_weltanschauungen')
db = client['12_weltanschauungen']

print('📊 CURRENT DATABASE STATE:')
total = db.gedanken.count_documents({})
print(f'Total gedanken entries: {total}')

print('\n📋 GEDANKENFEHLER COVERAGE:')
pipeline = [{'$group': {'_id': '$nummer', 'count': {'$sum': 1}}}, {'$sort': {'_id': 1}}]
coverage = list(db.gedanken.aggregate(pipeline))
covered_numbers = [item['_id'] for item in coverage]
print(f'Covered numbers: {sorted(covered_numbers)}')
print(f'Total coverage: {len(covered_numbers)}/43 numbers')

missing = [n for n in range(1, 44) if n not in covered_numbers]
print(f'Missing numbers: {missing}')

# Show recent additions
print('\n🔍 RECENT ADDITIONS (last 10 entries):')
recent = list(db.gedanken.find().sort('_id', -1).limit(10))
for entry in recent:
    print(f'  #{entry.get("nummer", "?")} {entry.get("weltanschauung", "?")} - {entry.get("model", "?")}')

client.close() 