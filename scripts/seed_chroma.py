"""
Seed ChromaDB with 5 synthetic Mumzworld policy documents.
Run once: python scripts/seed_chroma.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.client import get_collection
from loguru import logger


POLICY_DOCS = [
    {
        "id_prefix": "return_refund",
        "category": "return_refund",
        "source": "return_refund_policy.md",
        "text": """MUMZWORLD RETURN & REFUND POLICY

Eligibility: Items may be returned within 15 days of delivery if unused, in original packaging, with all accessories and documentation. Hygiene products (feeding bottles, breast pumps, pacifiers, diapers) may only be returned within 7 days and must be completely sealed and unused.

Non-returnable items: Personalized products, downloaded digital content, gift cards, hazardous materials (batteries when shipped separately).

Refund processing: Once the returned item is received and inspected (2-3 business days), the refund is issued to the original payment method within 5-10 business days. Wallet credits are processed within 24 hours. Cash on delivery refunds are issued as wallet credit.

Exchange policy: Exchanges are handled as a return + new purchase. Items can be exchanged for a different size, color, or product of equal or greater value.

How to initiate: Go to My Orders → Select item → Return Request. Attach photo of item condition. A courier will be arranged for pickup within 1-3 business days.

Damaged items: If the item arrived damaged or defective, escalate immediately via the returns portal with photos. Expedited processing applies (refund within 3 business days).""",
    },
    {
        "id_prefix": "delivery_faq",
        "category": "delivery",
        "source": "delivery_faq.md",
        "text": """MUMZWORLD DELIVERY INFORMATION

Standard delivery times (business days):
- UAE: 2-4 days
- KSA (major cities): 3-5 days
- KSA (other regions): 5-7 days
- Bahrain, Kuwait, Qatar: 3-5 days
- Oman, Jordan: 5-8 days

Express delivery: Available in UAE and KSA major cities. Same-day delivery for orders placed before 12pm in Dubai. Next-day delivery available for orders before 3pm.

Tracking: Tracking link sent via SMS and email once order is dispatched. Visit mumzworld.com/track or use the app under My Orders.

Order delays: If your order has not arrived within the estimated delivery window, please contact support after waiting one additional business day. We will investigate with the courier and provide an update within 4-6 business hours.

Delivery attempts: If no one is available, the courier will attempt delivery twice more on subsequent days before returning the package.

Free delivery: On orders above AED 99 in UAE, SAR 150 in KSA.
International shipping: Currently shipping within GCC + Jordan only.""",
    },
    {
        "id_prefix": "product_safety",
        "category": "product_safety",
        "source": "product_safety.md",
        "text": """PRODUCT SAFETY AND AGE SUITABILITY

Age ratings: All products on Mumzworld display an age suitability label set by the manufacturer. Always check the age label before purchase. Products marked 0+ are suitable from birth; 3+ from 3 months; 6+, 12+, 18+, 24+, and 36+ accordingly.

Choking hazards: Products with small parts carry a choking hazard warning and are not suitable for children under 3 years. These are clearly labeled with a warning icon.

Car seat safety: Car seats sold on Mumzworld meet ECE R44/04 or ECE R129 (i-Size) standards unless otherwise stated. Always install per manufacturer instructions. Mumzworld is not responsible for improper installation.

Chemical safety: Baby skincare and feeding products listed on Mumzworld comply with UAE ESMA and international FDA/CE standards. If your child has a reaction to a product, discontinue use immediately and consult a pediatrician.

Medical devices: Products categorized as medical devices (nebulizers, thermometers, blood pressure monitors) require professional guidance for use on infants.

Recall notices: Mumzworld monitors manufacturer recalls. If a product you purchased is subject to a recall, you will be notified by email and the item will be flagged in My Orders.""",
    },
    {
        "id_prefix": "account_wallet",
        "category": "account",
        "source": "account_wallet_help.md",
        "text": """ACCOUNT AND WALLET GUIDE

Password reset: Click "Forgot Password" on the sign-in page. Enter your registered email or phone number. A reset link/OTP will be sent within 2 minutes.

Account locked: After 5 failed login attempts, your account is locked for 30 minutes for security. Contact support if you need immediate access.

Mumzworld Wallet: Your wallet balance can be topped up via credit card, debit card, or Apple Pay. Wallet funds never expire. Wallet can be used for full or partial payment.

Referral rewards: Earn AED 30 wallet credit for every friend who registers and completes their first order using your referral link. Credited within 24 hours of the friend's first delivery.

Order cancellation: Orders can be cancelled within 30 minutes of placement if not yet dispatched. After dispatch, initiate a return upon delivery.

Multiple accounts: Only one account per email address is permitted. If you suspect unauthorized access, contact support immediately for account freeze.

Gift registry: Create and share a gift registry from the app. Registry items purchased by others are automatically tracked and removed from the list.""",
    },
    {
        "id_prefix": "medical_escalation",
        "category": "medical",
        "source": "medical_escalation_policy.md",
        "text": """MEDICAL DISCLAIMER AND ESCALATION POLICY

Mumzworld is an e-commerce platform and is NOT a medical provider. We do not offer medical advice, diagnoses, or treatment recommendations of any kind.

For any medical concern involving a child or mother:
- Mild symptoms (rash, minor fever): Consult your pediatrician or family doctor.
- Moderate symptoms (persistent vomiting, high fever above 39°C): Visit a clinic or use telehealth services.
- Emergency symptoms (difficulty breathing, severe allergic reaction, loss of consciousness, suspected poisoning): Call emergency services immediately (UAE: 998, KSA: 911 or 920).

Product reactions: If you believe a Mumzworld product has caused a health issue, document the product details, stop use, and seek medical attention first. After medical care, contact Mumzworld support to initiate a product safety report.

Escalation triggers in our support system (internal):
- Any query mentioning symptoms, medicine dosage, or health conditions → auto-escalate
- Queries from users who mention a child under 12 months with health concerns → critical
- Queries with keywords: emergency, hospital, doctor, bleeding, breathing, unconscious, allergic reaction, swallowed → immediate escalation to senior support agent

Telehealth partners: Mumzworld partners with Altibbi and Okadoc for teleconsultations. Details available in the app under Health & Wellness.""",
    },
]


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 20) -> list:
    """Chunk text into overlapping word-based segments."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def seed_chroma():
    """Seed ChromaDB with policy document chunks."""
    collection = get_collection()

    existing_count = collection.count()
    if existing_count > 0:
        logger.info(f"Collection already has {existing_count} documents, checking for idempotency")

    total_seeded = 0

    for doc_idx, doc in enumerate(POLICY_DOCS, 1):
        chunks = chunk_text(doc["text"])
        logger.info(f"Seeding doc {doc_idx}/{len(POLICY_DOCS)}: {doc['source']} ({len(chunks)} chunks)")

        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"{doc['id_prefix']}_{chunk_idx:03d}"

            # Check if already exists (idempotent)
            try:
                existing = collection.get(ids=[chunk_id])
                if existing and existing["ids"]:
                    continue
            except Exception:
                pass

            collection.add(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{
                    "source": doc["source"],
                    "category": doc["category"],
                    "language": "en",
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks),
                }],
            )
            total_seeded += 1

    final_count = collection.count()
    logger.info(f"Total chunks seeded: {total_seeded}")
    logger.info(f"ChromaDB ready. Collection: mumzworld_policies ({final_count} documents)")
    return final_count


if __name__ == "__main__":
    seed_chroma()
