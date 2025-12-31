import sqlite3

# Connect to database
conn = sqlite3.connect('listingspark.db')
cursor = conn.cursor()

# Create listings table
cursor.execute('''
CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    price REAL,
    bedrooms INTEGER,
    bathrooms REAL,
    square_feet INTEGER,
    description TEXT,
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tour_url TEXT,
    images TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Create mls_accounts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS mls_accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    mls_name TEXT,
    api_key TEXT,
    credentials TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
''')

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_user_id ON listings(user_id)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_mls_user_id ON mls_accounts(user_id)')

conn.commit()
conn.close()

print("✅ SQLite tables created successfully!")
