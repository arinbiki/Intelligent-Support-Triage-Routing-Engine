import json
import random
import os

SEED = 42
random.seed(SEED)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "golden_support_tickets_1000.json")

# Templates and vocabulary for realistic e-commerce support tickets

BILLING_TEMPLATES = [
    ("I was double charged for order {order_id}. My credit card statement shows two identical charges of ${amt}.", "Billing", -0.6, 2, False),
    ("Please send me the formal VAT invoice and tax receipt for order {order_id}.", "Billing", 0.1, 0, False),
    ("I need an immediate refund for order {order_id}. The product arrived shattered and I want my money back.", "Billing", -0.8, 3, True),
    ("Why was my credit card charged ${amt} when the total at checkout was ${amt2}? Please refund the difference.", "Billing", -0.5, 2, True),
    ("I demand a full refund immediately or I will file a chargeback with my bank and report to BBB.", "Billing", -0.9, 3, True),
    ("Can I change my payment method for subscription renewal before next billing cycle?", "Billing", 0.0, 1, False),
    ("My discount code 20OFF was not applied at payment, I was charged full price ${amt}.", "Billing", -0.4, 1, True),
    ("I returned the package last week. When will the refund of ${amt} be credited back to my account?", "Billing", -0.2, 1, True),
    ("You guys charged me twice. If this is not refunded today, I am contacting my lawyer for credit card fraud.", "Billing", -0.95, 3, True),
    ("Is there a payment plan available for high ticket orders over $500?", "Billing", 0.2, 0, False),
    ("Billing dispute regarding unauthorized transaction on my account for order {order_id}.", "Billing", -0.7, 3, False),
    ("Cancel order {order_id} right now and process a full refund to my original payment card.", "Billing", -0.6, 2, True),
    ("I received a refund notification email but the funds are not showing on my bank statement.", "Billing", -0.3, 1, True),
    ("Tax calculation on order {order_id} seems incorrect for state California. Please recalculate.", "Billing", -0.1, 1, False),
    ("I want to update my billing address and registered credit card on file.", "Billing", 0.1, 0, False),
]

FULFILLMENT_TEMPLATES = [
    ("Where is my package for order {order_id}? The tracking number {tracking} has not moved in 6 days.", "Fulfillment", -0.6, 2, False),
    ("My delivery driver left the box in the rain. The item inside is completely water damaged and broken.", "Fulfillment", -0.8, 2, True),
    ("The courier tracking {tracking} says delivered to porch, but nothing is here. Package is missing.", "Fulfillment", -0.7, 3, False),
    ("I only received 2 out of the 3 items I ordered in order {order_id}. Missing the black jacket.", "Fulfillment", -0.5, 2, False),
    ("Can I change my shipping address for order {order_id}? I moved to a new apartment.", "Fulfillment", 0.0, 1, False),
    ("Tracking status for {tracking} shows returned to sender due to incorrect postal code.", "Fulfillment", -0.4, 2, False),
    ("You sent me the wrong color variant. I ordered Navy Blue but received Bright Neon Pink.", "Fulfillment", -0.5, 2, False),
    ("What is the estimated delivery time for express DHL shipping to Chicago?", "Fulfillment", 0.2, 0, False),
    ("Customs is holding my international package {tracking} asking for an import declaration.", "Fulfillment", -0.3, 2, False),
    ("Order {order_id} was supposed to arrive yesterday for my son's birthday. It is late and ruined our plans.", "Fulfillment", -0.7, 3, False),
    ("The tracking number {tracking} provided in the shipment confirmation email is invalid on FedEx website.", "Fulfillment", -0.4, 1, False),
    ("Need signature release authorization for delivery {tracking} as I will not be home.", "Fulfillment", 0.1, 0, False),
    ("Package arrived open with the tape cut and the contents stolen. Empty box delivered.", "Fulfillment", -0.9, 3, False),
    ("Can I upgrade order {order_id} to overnight priority courier?", "Fulfillment", 0.1, 1, False),
    ("Carrier delayed shipment due to weather exception. Can you provide updated ETA?", "Fulfillment", -0.2, 1, False),
]

TECHNICAL_TEMPLATES = [
    ("When I click the 'Complete Purchase' checkout button, the website spins and gives an error 500.", "Technical", -0.6, 2, False),
    ("I cannot log into my account. The password reset link says 'Token Expired' immediately.", "Technical", -0.5, 2, False),
    ("The mobile iOS app crashes as soon as I open my shopping bag.", "Technical", -0.6, 2, False),
    ("Your website search bar is returning 404 page not found when searching for denim jeans.", "Technical", -0.3, 1, False),
    ("The 2FA SMS code is never arriving to my mobile phone number. Cannot authenticate.", "Technical", -0.5, 2, False),
    ("I am stuck in an infinite redirect loop between the login page and profile settings.", "Technical", -0.5, 2, False),
    ("Product images are not loading on product page SKU-208 on Chrome browser.", "Technical", -0.2, 1, False),
    ("Unable to apply gift card code at checkout. Error message says 'Gateway Timeout'.", "Technical", -0.4, 1, False),
    ("Browser console shows Javascript unhandled exception TypeError when selecting size XL.", "Technical", -0.3, 1, False),
    ("I accidentally created two customer accounts with different emails. Can you merge them?", "Technical", 0.0, 0, False),
    ("API webhook for inventory sync returned 401 Unauthorized token header error.", "Technical", -0.2, 1, False),
    ("Wishlist items keep disappearing every time I refresh the browser tab.", "Technical", -0.4, 1, False),
    ("Accessibility issue: screen reader is not announcing dropdown select menu options.", "Technical", -0.1, 1, False),
    ("The auto-fill address feature is pasting the zip code into the city field on checkout form.", "Technical", -0.2, 1, False),
    ("Apple Pay button fails to initialize on Safari desktop version 17.", "Technical", -0.3, 1, False),
]

GENERAL_TEMPLATES = [
    ("Do you offer wholesale pricing or bulk discounts for corporate orders over 50 units?", "General", 0.4, 0, False),
    ("What are the exact chest and sleeve measurements for the Merino wool sweater in size Large?", "General", 0.2, 0, False),
    ("When will the sold-out canvas duffle bag be restocked in olive green?", "General", 0.3, 0, False),
    ("Are your cosmetics and skincare products certified cruelty-free and vegan?", "General", 0.4, 0, False),
    ("Do you have a physical flagship store in Manhattan where I can try on clothes?", "General", 0.5, 0, False),
    ("What is your standard warranty and return policy for electronic accessories?", "General", 0.2, 0, False),
    ("Do you offer gift wrapping and personalized handwritten message cards?", "General", 0.6, 0, False),
    ("Can I purchase an electronic gift card in amounts of $100 and email it to a friend?", "General", 0.5, 0, False),
    ("I love your products! The quality of my last purchase was outstanding. Just wanted to say thanks.", "General", 0.9, 0, False),
    ("Do you ship internationally to Australia and what are the duties/tariffs?", "General", 0.3, 0, False),
    ("Is the organic cotton tee pre-shrunk or will it shrink in hot water wash?", "General", 0.1, 0, False),
    ("Do you offer educational student or military discounts?", "General", 0.4, 0, False),
    ("Are there care instructions for dry cleaning the silk scarf?", "General", 0.2, 0, False),
    ("Can you provide the MSDS safety data sheet for the cleaning solvent formula?", "General", 0.0, 0, False),
    ("How do I unsubscribe from your weekly promotional newsletter emails?", "General", -0.1, 0, False),
]

CATEGORIES = {
    "Billing": BILLING_TEMPLATES,
    "Fulfillment": FULFILLMENT_TEMPLATES,
    "Technical": TECHNICAL_TEMPLATES,
    "General": GENERAL_TEMPLATES
}

def generate_ticket(idx, dept):
    templates = CATEGORIES[dept]
    template, cat, base_sent, base_urg, is_refund = random.choice(templates)
    
    order_num = random.randint(1000, 99999)
    order_id = f"#{order_num}"
    amt = round(random.uniform(25.0, 350.0), 2)
    amt2 = round(amt + random.uniform(15.0, 50.0), 2)
    tracking = f"1Z{random.randint(10000000, 99999999)}{random.randint(10000000, 99999999)}"
    
    text = template.format(order_id=order_id, amt=amt, amt2=amt2, tracking=tracking)
    
    # Randomly add customer emotion/modifiers
    modifiers = [
        "",
        " Please respond ASAP.",
        " This is ridiculous.",
        " Thank you for your assistance.",
        " I am very frustrated with this situation.",
        " Best regards.",
        " Looking forward to hearing from you."
    ]
    mod = random.choice(modifiers)
    full_text = text + mod
    
    # Determine customer tier (15% VIP)
    tier = "VIP" if random.random() < 0.15 else "Standard"
    
    return {
        "id": f"TICK-{idx:05d}",
        "department": dept,
        "text": full_text,
        "order_id": order_id if ("#" in text or is_refund) else None,
        "customer_tier": tier,
        "is_refund_intent": is_refund,
        "expected_urgency": base_urg
    }

def main():
    tickets = []
    idx = 1
    departments = ["Billing", "Fulfillment", "Technical", "General"]
    
    # Generate 250 tickets per department = 1,000 total golden tickets
    for dept in departments:
        for _ in range(250):
            tickets.append(generate_ticket(idx, dept))
            idx += 1
            
    random.shuffle(tickets)
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)
        
    print(f"[+] Successfully generated {len(tickets)} golden support tickets at {OUTPUT_PATH}")
    
    counts = {}
    for t in tickets:
        counts[t['department']] = counts.get(t['department'], 0) + 1
    print("[*] Class distribution:", counts)

if __name__ == "__main__":
    main()
