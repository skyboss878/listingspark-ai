"""
Supabase-backed replacement for the DB parts of client_management.py.
Same class/method names so server.py's usage (client_service, document_service,
init_client_tables) doesn't need to change beyond the import swap.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from supabase_adapter import _get_client
from client_management import (
    ClientType, DocumentType, DocumentStatus,
    ClientCreate, ClientUpdate, DocumentCreate, DocumentSign,
)


def init_client_tables(db_path: str = None):
    """Seed default document templates into Supabase if none exist for that type."""
    client = _get_client()

    default_templates = [
        {
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
            'variables': ["date", "client_name", "property_address", "agent_name", "brokerage_name",
                          "listing_price", "listing_period", "commission_rate", "property_description"],
        },
        {
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
            'variables': ["date", "client_name", "client_email", "client_phone", "agent_name",
                          "brokerage_name", "budget_min", "budget_max", "preferred_locations",
                          "property_type", "agreement_period"],
        },
        {
            'document_type': 'purchase_agreement',
            'name': 'Real Estate Purchase Agreement',
            'content': '''REAL ESTATE PURCHASE AGREEMENT

This agreement is entered into on {date} between:

BUYER: {client_name}
Contact: {client_email} | {client_phone}

SELLER: {seller_name}

PROPERTY ADDRESS: {property_address}
LEGAL DESCRIPTION: {legal_description}

PURCHASE PRICE: ${purchase_price}
EARNEST MONEY DEPOSIT: ${earnest_money}
CLOSING DATE: {closing_date}

CONTINGENCIES:
- Financing Contingency: {financing_contingency}
- Inspection Contingency: {inspection_contingency}
- Appraisal Contingency: {appraisal_contingency}

INCLUDED ITEMS:
{included_items}

This offer is subject to acceptance by Seller. Time is of the essence.

BUYER'S SIGNATURE: ___________________________
Date: ______________

SELLER'S SIGNATURE: ___________________________
Date: ______________
''',
            'variables': ["date", "client_name", "client_email", "client_phone", "seller_name",
                          "property_address", "legal_description", "purchase_price", "earnest_money",
                          "closing_date", "financing_contingency", "inspection_contingency",
                          "appraisal_contingency", "included_items"],
        },
        {
            'document_type': 'disclosure',
            'name': "Seller's Property Disclosure Statement",
            'content': '''SELLER'S PROPERTY DISCLOSURE STATEMENT

Property Address: {property_address}
Seller: {client_name}
Date: {date}

Seller discloses the following known conditions regarding the property. This
disclosure is not a warranty of condition and is not a substitute for any
inspection.

STRUCTURAL / SYSTEMS:
Known defects (roof, foundation, plumbing, electrical, HVAC): {known_defects}

ENVIRONMENTAL:
Known hazards (lead paint, mold, asbestos, radon, flood zone): {environmental_hazards}

OTHER MATERIAL FACTS:
{other_material_facts}

Seller certifies that the information provided above is true and correct to
the best of Seller's knowledge as of the date signed below.

SELLER'S SIGNATURE: ___________________________
Date: ______________

BUYER ACKNOWLEDGMENT OF RECEIPT: ___________________________
Date: ______________
''',
            'variables': ["property_address", "client_name", "date", "known_defects",
                          "environmental_hazards", "other_material_facts"],
        },
        {
            'document_type': 'addendum',
            'name': 'Addendum to Purchase Agreement',
            'content': '''ADDENDUM TO PURCHASE AGREEMENT

This Addendum is made part of the Purchase Agreement dated {original_agreement_date}
for the property located at:

{property_address}

BUYER: {client_name}
SELLER: {seller_name}

TERMS OF THIS ADDENDUM:
{addendum_terms}

All other terms and conditions of the original Purchase Agreement remain
unchanged and in full effect except as modified above.

BUYER'S SIGNATURE: ___________________________
Date: ______________

SELLER'S SIGNATURE: ___________________________
Date: ______________
''',
            'variables': ["original_agreement_date", "property_address", "client_name",
                          "seller_name", "addendum_terms"],
        },
        {
            'document_type': 'inspection',
            'name': 'Inspection Contingency Addendum',
            'content': '''INSPECTION CONTINGENCY ADDENDUM

Property Address: {property_address}
Buyer: {client_name}
Inspection Period: {inspection_period} days from acceptance date

Buyer shall have the right to conduct inspections of the property at Buyer's
expense during the Inspection Period, including: {inspection_types}.

INSPECTION RESULTS:
Date of Inspection: {inspection_date}
Inspector: {inspector_name}
Summary of Findings: {inspection_findings}

BUYER'S RESPONSE:
[ ] Accept property in its current condition
[ ] Request repairs (see attached list)
[ ] Terminate agreement per inspection contingency

Repair Requests / Notes:
{repair_requests}

BUYER'S SIGNATURE: ___________________________
Date: ______________

SELLER'S SIGNATURE (if repairs agreed): ___________________________
Date: ______________
''',
            'variables': ["property_address", "client_name", "inspection_period", "inspection_types",
                          "inspection_date", "inspector_name", "inspection_findings", "repair_requests"],
        },
        {
            'document_type': 'escrow',
            'name': 'Escrow Instructions',
            'content': '''ESCROW INSTRUCTIONS

Property Address: {property_address}
Escrow Number: {escrow_number}
Escrow Company: {escrow_company}

BUYER: {client_name}
SELLER: {seller_name}

PURCHASE PRICE: ${purchase_price}
EARNEST MONEY HELD IN ESCROW: ${earnest_money}
SCHEDULED CLOSING DATE: {closing_date}

INSTRUCTIONS TO ESCROW HOLDER:
Escrow holder is instructed to hold all funds and documents related to this
transaction and disburse/record them only upon satisfaction of all terms of
the underlying Purchase Agreement, including: {escrow_conditions}

PRORATIONS AND CLOSING COSTS:
{closing_cost_terms}

BUYER'S SIGNATURE: ___________________________
Date: ______________

SELLER'S SIGNATURE: ___________________________
Date: ______________
''',
            'variables': ["property_address", "escrow_number", "escrow_company", "client_name",
                          "seller_name", "purchase_price", "earnest_money", "closing_date",
                          "escrow_conditions", "closing_cost_terms"],
        },
    ]

    for template in default_templates:
        existing = client.table("document_templates").select("id").eq(
            "document_type", template["document_type"]
        ).execute()
        if existing.data:
            continue
        now = datetime.utcnow().isoformat()
        client.table("document_templates").insert({
            "id": str(uuid.uuid4()),
            "document_type": template["document_type"],
            "name": template["name"],
            "content": template["content"],
            "variables": template["variables"],
            "created_at": now,
            "updated_at": now,
        }).execute()

    print("Client management tables initialized (Supabase)")


class ClientManagementServiceSupabase:
    def __init__(self):
        self.client = _get_client()

    async def create_client(self, user_id: str, client_data: ClientCreate) -> Dict[str, Any]:
        client_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        row = {
            "id": client_id, "user_id": user_id,
            "first_name": client_data.first_name, "last_name": client_data.last_name,
            "email": client_data.email, "phone": client_data.phone,
            "client_type": client_data.client_type.value,
            "budget_min": client_data.budget_min, "budget_max": client_data.budget_max,
            "preferred_locations": client_data.preferred_locations or None,
            "notes": client_data.notes, "created_at": now, "updated_at": now
        }
        self.client.table("clients").insert(row).execute()

        self.client.table("client_activity").insert({
            "id": str(uuid.uuid4()), "client_id": client_id, "user_id": user_id,
            "activity_type": "client_created",
            "description": f"Client {client_data.first_name} {client_data.last_name} added",
            "created_at": now
        }).execute()

        return row

    async def get_clients(self, user_id: str, client_type: Optional[str] = None) -> List[Dict[str, Any]]:
        q = self.client.table("clients").select("*").eq("user_id", user_id)
        if client_type:
            q = q.eq("client_type", client_type)
        result = q.order("created_at", desc=True).execute()
        return result.data or []

    async def get_client(self, client_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table("clients").select("*").eq("id", client_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    async def update_client(self, client_id: str, user_id: str, updates: ClientUpdate) -> Optional[Dict[str, Any]]:
        row = {}
        if updates.first_name is not None:
            row["first_name"] = updates.first_name
        if updates.last_name is not None:
            row["last_name"] = updates.last_name
        if updates.email is not None:
            row["email"] = updates.email
        if updates.phone is not None:
            row["phone"] = updates.phone
        if updates.client_type is not None:
            row["client_type"] = updates.client_type.value
        if updates.budget_min is not None:
            row["budget_min"] = updates.budget_min
        if updates.budget_max is not None:
            row["budget_max"] = updates.budget_max
        if updates.preferred_locations is not None:
            row["preferred_locations"] = updates.preferred_locations
        if updates.notes is not None:
            row["notes"] = updates.notes

        if not row:
            return await self.get_client(client_id, user_id)

        row["updated_at"] = datetime.utcnow().isoformat()
        self.client.table("clients").update(row).eq("id", client_id).eq("user_id", user_id).execute()
        return await self.get_client(client_id, user_id)

    async def get_client_activity(self, client_id: str, user_id: str) -> List[Dict[str, Any]]:
        result = self.client.table("client_activity").select("*").eq("client_id", client_id).eq(
            "user_id", user_id
        ).order("created_at", desc=True).limit(50).execute()
        return result.data or []

    async def log_activity(self, client_id: str, user_id: str, activity_type: str,
                            description: str, metadata: Optional[Dict] = None):
        self.client.table("client_activity").insert({
            "id": str(uuid.uuid4()), "client_id": client_id, "user_id": user_id,
            "activity_type": activity_type, "description": description,
            "metadata": metadata, "created_at": datetime.utcnow().isoformat()
        }).execute()


class DocumentManagementServiceSupabase:
    def __init__(self):
        self.client = _get_client()

    async def get_templates(self, document_type: Optional[str] = None) -> List[Dict[str, Any]]:
        q = self.client.table("document_templates").select("*")
        if document_type:
            q = q.eq("document_type", document_type)
        result = q.execute()
        return result.data or []

    async def create_document(self, user_id: str, doc_data: DocumentCreate) -> Dict[str, Any]:
        document_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        content = doc_data.content
        if doc_data.template_id:
            tpl = self.client.table("document_templates").select("content").eq(
                "id", doc_data.template_id
            ).execute()
            if tpl.data:
                content = tpl.data[0]["content"]
                if doc_data.metadata:
                    for key, value in doc_data.metadata.items():
                        content = content.replace(f"{{{key}}}", str(value))

        row = {
            "id": document_id, "user_id": user_id, "client_id": doc_data.client_id,
            "document_type": doc_data.document_type.value, "title": doc_data.title,
            "content": content, "status": DocumentStatus.DRAFT.value,
            "template_id": doc_data.template_id,
            "metadata": doc_data.metadata or None,
            "created_at": now, "updated_at": now
        }
        self.client.table("documents").insert(row).execute()
        return row

    async def get_documents(self, user_id: str, client_id: Optional[str] = None,
                             status: Optional[str] = None) -> List[Dict[str, Any]]:
        q = self.client.table("documents").select("*").eq("user_id", user_id)
        if client_id:
            q = q.eq("client_id", client_id)
        if status:
            q = q.eq("status", status)
        result = q.order("created_at", desc=True).execute()
        return result.data or []

    async def get_document(self, document_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        result = self.client.table("documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Public lookup with no user_id filter - the document_id itself acts as the
        access token for the signing link, same pattern as a password-reset link."""
        result = self.client.table("documents").select("*").eq("id", document_id).execute()
        return result.data[0] if result.data else None

    async def send_document(self, document_id: str, user_id: str) -> bool:
        now = datetime.utcnow().isoformat()
        self.client.table("documents").update({
            "status": DocumentStatus.SENT.value, "sent_at": now, "updated_at": now
        }).eq("id", document_id).eq("user_id", user_id).execute()
        return True

    async def sign_document(self, sign_data: DocumentSign) -> bool:
        now = datetime.utcnow().isoformat()
        self.client.table("documents").update({
            "status": DocumentStatus.SIGNED.value,
            "signature_data": sign_data.signature_data,
            "signed_at": sign_data.signed_at.isoformat(),
            "signed_ip": sign_data.ip_address,
            "updated_at": now
        }).eq("id", sign_data.document_id).execute()
        return True


client_service_supabase = ClientManagementServiceSupabase()
document_service_supabase = DocumentManagementServiceSupabase()
