"""
Client Management System - Real360 Proprietary Module
Handles client management, document generation, and e-signatures
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# ENUMS
# ============================================================================

class ClientType(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    BOTH = "both"

class DocumentType(str, Enum):
    LISTING_AGREEMENT = "listing_agreement"
    BUYER_AGREEMENT = "buyer_agreement"
    PURCHASE_AGREEMENT = "purchase_agreement"
    DISCLOSURE = "disclosure"
    ADDENDUM = "addendum"
    INSPECTION = "inspection"
    ESCROW = "escrow"
    OTHER = "other"

class DocumentStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"
    COMPLETED = "completed"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ClientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    client_type: ClientType
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_locations: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None

class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    client_type: Optional[ClientType] = None
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_locations: Optional[List[str]] = None
    notes: Optional[str] = None

class DocumentCreate(BaseModel):
    client_id: str
    document_type: DocumentType
    title: str
    content: Optional[str] = None
    template_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DocumentSign(BaseModel):
    document_id: str
    signature_data: str  # Base64 encoded signature
    ip_address: str
    signed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_client_tables(db_path: str = "listingspark.db"):
    """Initialize client management tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            client_type TEXT NOT NULL,
            budget_min INTEGER,
            budget_max INTEGER,
            preferred_locations TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            client_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            template_id TEXT,
            metadata TEXT,
            signature_data TEXT,
            signed_at TEXT,
            signed_ip TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            sent_at TEXT,
            viewed_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    
    # Document templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_templates (
            id TEXT PRIMARY KEY,
            document_type TEXT NOT NULL,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            variables TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Client activity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_activity (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create default templates if they don't exist
    default_templates = [
        {
            'id': str(uuid.uuid4()),
            'document_type': 'listing_agreement',
            'name': 'Standard Listing Agreement',
            'content': '''EXCLUSIVE RIGHT TO SELL LISTING AGREEMENT

This agreement is entered into on {date} between:

SELLER: {client_name}
Address: {property_address}

AGENT: {agent_name}
Brokerage: {brokerage_name}

LISTING PRICE: ${listing_price}
LISTING PERIOD: {listing_period} months
COMMISSION: {commission_rate}%

PROPERTY DESCRIPTION:
{property_description}

SELLER'S SIGNATURE: ___________________________
Date: ______________

AGENT'S SIGNATURE: ___________________________
Date: ______________
''',
            'variables': '["date", "client_name", "property_address", "agent_name", "brokerage_name", "listing_price", "listing_period", "commission_rate", "property_description"]',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        },
        {
            'id': str(uuid.uuid4()),
            'document_type': 'buyer_agreement',
            'name': 'Buyer Representation Agreement',
            'content': '''BUYER REPRESENTATION AGREEMENT

This agreement is entered into on {date} between:

BUYER: {client_name}
Contact: {client_email} | {client_phone}

AGENT: {agent_name}
Brokerage: {brokerage_name}

SEARCH CRITERIA:
Price Range: ${budget_min} - ${budget_max}
Preferred Locations: {preferred_locations}
Property Type: {property_type}

AGREEMENT PERIOD: {agreement_period} months
COMMISSION: Buyer acknowledges that agent commission is typically paid by the seller.

BUYER'S SIGNATURE: ___________________________
Date: ______________

AGENT'S SIGNATURE: ___________________________
Date: ______________
''',
            'variables': '["date", "client_name", "client_email", "client_phone", "agent_name", "brokerage_name", "budget_min", "budget_max", "preferred_locations", "property_type", "agreement_period"]',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
    ]
    
    for template in default_templates:
        cursor.execute("""
            INSERT OR IGNORE INTO document_templates (id, document_type, name, content, variables, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            template['id'],
            template['document_type'],
            template['name'],
            template['content'],
            template['variables'],
            template['created_at'],
            template['updated_at']
        ))
    
    conn.commit()
    conn.close()
    print("✅ Client management tables initialized")


# ============================================================================
# CLIENT MANAGEMENT SERVICE
# ============================================================================

class ClientManagementService:
    """Service for managing clients"""
    
    def __init__(self, db_path: str = "listingspark.db"):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def create_client(self, user_id: str, client_data: ClientCreate) -> Dict[str, Any]:
        """Create a new client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        client_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO clients (id, user_id, first_name, last_name, email, phone, client_type,
                               budget_min, budget_max, preferred_locations, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id, user_id, client_data.first_name, client_data.last_name,
            client_data.email, client_data.phone, client_data.client_type.value,
            client_data.budget_min, client_data.budget_max,
            json.dumps(client_data.preferred_locations) if client_data.preferred_locations else None,
            client_data.notes, now, now
        ))
        
        # Log activity
        activity_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO client_activity (id, client_id, user_id, activity_type, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            activity_id, client_id, user_id, 'client_created',
            f"Client {client_data.first_name} {client_data.last_name} added", now
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'id': client_id,
            'user_id': user_id,
            'first_name': client_data.first_name,
            'last_name': client_data.last_name,
            'email': client_data.email,
            'phone': client_data.phone,
            'client_type': client_data.client_type.value,
            'budget_min': client_data.budget_min,
            'budget_max': client_data.budget_max,
            'preferred_locations': client_data.preferred_locations,
            'notes': client_data.notes,
            'created_at': now,
            'updated_at': now
        }
    
    async def get_clients(self, user_id: str, client_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all clients for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if client_type:
            cursor.execute("""
                SELECT * FROM clients
                WHERE user_id = ? AND client_type = ?
                ORDER BY created_at DESC
            """, (user_id, client_type))
        else:
            cursor.execute("""
                SELECT * FROM clients
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        clients = []
        for row in rows:
            client = dict(row)
            if client['preferred_locations']:
                client['preferred_locations'] = json.loads(client['preferred_locations'])
            clients.append(client)
        
        return clients
    
    async def get_client(self, client_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM clients
            WHERE id = ? AND user_id = ?
        """, (client_id, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        client = dict(row)
        if client['preferred_locations']:
            client['preferred_locations'] = json.loads(client['preferred_locations'])
        
        return client
    
    async def update_client(self, client_id: str, user_id: str, updates: ClientUpdate) -> Optional[Dict[str, Any]]:
        """Update client information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if updates.first_name is not None:
            update_fields.append("first_name = ?")
            values.append(updates.first_name)
        if updates.last_name is not None:
            update_fields.append("last_name = ?")
            values.append(updates.last_name)
        if updates.email is not None:
            update_fields.append("email = ?")
            values.append(updates.email)
        if updates.phone is not None:
            update_fields.append("phone = ?")
            values.append(updates.phone)
        if updates.client_type is not None:
            update_fields.append("client_type = ?")
            values.append(updates.client_type.value)
        if updates.budget_min is not None:
            update_fields.append("budget_min = ?")
            values.append(updates.budget_min)
        if updates.budget_max is not None:
            update_fields.append("budget_max = ?")
            values.append(updates.budget_max)
        if updates.preferred_locations is not None:
            update_fields.append("preferred_locations = ?")
            values.append(json.dumps(updates.preferred_locations))
        if updates.notes is not None:
            update_fields.append("notes = ?")
            values.append(updates.notes)
        
        if not update_fields:
            return await self.get_client(client_id, user_id)
        
        update_fields.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        
        values.extend([client_id, user_id])
        
        cursor.execute(f"""
            UPDATE clients
            SET {', '.join(update_fields)}
            WHERE id = ? AND user_id = ?
        """, values)
        
        conn.commit()
        conn.close()
        
        return await self.get_client(client_id, user_id)
    
    async def get_client_activity(self, client_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get activity timeline for a client"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM client_activity
            WHERE client_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (client_id, user_id))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    async def log_activity(self, client_id: str, user_id: str, activity_type: str, description: str, metadata: Optional[Dict] = None):
        """Log client activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        activity_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO client_activity (id, client_id, user_id, activity_type, description, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_id, client_id, user_id, activity_type, description,
            json.dumps(metadata) if metadata else None, now
        ))
        
        conn.commit()
        conn.close()


# ============================================================================
# DOCUMENT MANAGEMENT SERVICE
# ============================================================================

class DocumentManagementService:
    """Service for managing documents and e-signatures"""
    
    def __init__(self, db_path: str = "listingspark.db"):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    async def get_templates(self, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get document templates"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if document_type:
            cursor.execute("""
                SELECT * FROM document_templates
                WHERE document_type = ?
            """, (document_type,))
        else:
            cursor.execute("SELECT * FROM document_templates")
        
        rows = cursor.fetchall()
        conn.close()
        
        templates = []
        for row in rows:
            template = dict(row)
            if template['variables']:
                template['variables'] = json.loads(template['variables'])
            templates.append(template)
        
        return templates
    
    async def create_document(self, user_id: str, doc_data: DocumentCreate) -> Dict[str, Any]:
        """Create a new document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        document_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # If template_id provided, get template content
        content = doc_data.content
        if doc_data.template_id:
            cursor.execute("SELECT content FROM document_templates WHERE id = ?", (doc_data.template_id,))
            template = cursor.fetchone()
            if template:
                content = template['content']
                # Replace variables with metadata
                if doc_data.metadata:
                    for key, value in doc_data.metadata.items():
                        content = content.replace(f"{{{key}}}", str(value))
        
        cursor.execute("""
            INSERT INTO documents (id, user_id, client_id, document_type, title, content, status,
                                 template_id, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id, user_id, doc_data.client_id, doc_data.document_type.value,
            doc_data.title, content, DocumentStatus.DRAFT.value, doc_data.template_id,
            json.dumps(doc_data.metadata) if doc_data.metadata else None, now, now
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'id': document_id,
            'user_id': user_id,
            'client_id': doc_data.client_id,
            'document_type': doc_data.document_type.value,
            'title': doc_data.title,
            'content': content,
            'status': DocumentStatus.DRAFT.value,
            'created_at': now
        }
    
    async def get_documents(self, user_id: str, client_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get documents"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM documents WHERE user_id = ?"
        params = [user_id]
        
        if client_id:
            query += " AND client_id = ?"
            params.append(client_id)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        documents = []
        for row in rows:
            doc = dict(row)
            if doc['metadata']:
                doc['metadata'] = json.loads(doc['metadata'])
            documents.append(doc)
        
        return documents
    
    async def get_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM documents
            WHERE id = ? AND user_id = ?
        """, (document_id, user_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        doc = dict(row)
        if doc['metadata']:
            doc['metadata'] = json.loads(doc['metadata'])
        
        return doc
    
    async def send_document(self, document_id: str, user_id: str) -> bool:
        """Mark document as sent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            UPDATE documents
            SET status = ?, sent_at = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (DocumentStatus.SENT.value, now, now, document_id, user_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    async def sign_document(self, sign_data: DocumentSign) -> bool:
        """Sign a document"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            UPDATE documents
            SET status = ?, signature_data = ?, signed_at = ?, signed_ip = ?, updated_at = ?
            WHERE id = ?
        """, (
            DocumentStatus.SIGNED.value,
            sign_data.signature_data,
            sign_data.signed_at.isoformat(),
            sign_data.ip_address,
            now,
            sign_data.document_id
        ))
        
        conn.commit()
        conn.close()
        
        return True


# Global instances
client_service = ClientManagementService()
document_service = DocumentManagementService()
