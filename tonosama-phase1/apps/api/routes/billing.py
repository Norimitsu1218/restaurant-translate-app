from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
import stripe
import os

router = APIRouter(prefix="/api/billing", tags=["billing"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# --- Models ---
class CreateCheckoutRequest(BaseModel):
    demo_session_id: str
    plan_code: int # 39, 69, 99
    # User info to pre-fill Stripe
    email: str
    company_name: str

class CheckoutResponse(BaseModel):
    checkout_url: str

# --- Endpoints ---
@router.post("/create_checkout", response_model=CheckoutResponse)
async def create_checkout(req: CreateCheckoutRequest):
    if not stripe.api_key:
        # Mock for dev if key missing
        return {"checkout_url": "https://checkout.stripe.mock/pay"}

    try:
        # Map plan code to Price ID (Env vars in real world)
        price_id = os.getenv(f"STRIPE_PRICE_{req.plan_code}", "price_mock")
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('APP_URL')}/done?session={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('APP_URL')}/cancel",
            metadata={
                "demo_session_id": req.demo_session_id,
                "plan_code": req.plan_code,
                "company_name": req.company_name
            },
            customer_email=req.email
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def valid_webhook(request: Request, stripe_signature: str = Header(None)):
    if not WEBHOOK_SECRET:
        return {"status": "ignored", "reason": "no_secret"}

    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_successful_payment(session)

    return {"status": "ok"}

async def handle_successful_payment(session):
    # Logic:
    # 1. Extract metadata (demo_session_id)
    # 2. Create Store in DB (Supabase)
    # 3. Trigger Drive Copy (Async)
    # 4. Send Owner Email (Magic Link)
    print(f"Payment success for session {session.get('id')}")
    # Mock Drive Copy
    print("Drive Sync: Initiated")
    # Mock Email
    print("Email: Magic Link Sent")
