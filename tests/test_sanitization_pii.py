import unittest
import re

class TestSanitizationAndPII(unittest.TestCase):

    def sanitize_and_redact(self, raw_text: str):
        # 1. Strip HTML tags
        clean = re.sub(r"<[^>]+>", " ", raw_text)
        clean = clean.replace("&nbsp;", " ").replace("&amp;", "&")
        clean = re.sub(r"\s+", " ", clean).strip()
        clean = re.sub(r"\s+([,.!?;:])", r"\1", clean)

        # 2. Redact Credit Cards (15-16 digits with optional spaces or dashes)
        cc_regex = r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11}|(?:\d{4}[ -]?){3}\d{4})\b"
        clean = re.sub(cc_regex, "[REDACTED_CC]", clean)

        # 3. Redact Phone Numbers
        phone_regex = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
        clean = re.sub(phone_regex, "[REDACTED_PHONE]", clean)

        # 4. Redact Emails
        email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b"
        clean = re.sub(email_regex, "[REDACTED_EMAIL]", clean)

        return clean

    def extract_entities(self, text: str):
        order_matches = re.findall(r"#\d{4,7}|ORD-[A-Za-z0-9]+", text, re.IGNORECASE)
        tracking_matches = re.findall(r"\b(1Z[0-9A-Z]{16}|\d{12,15}|9\d{21})\b", text, re.IGNORECASE)
        amounts = re.findall(r"\$\d+(?:\.\d{2})?", text)
        return {
            "order_ids": list(set([o.upper() for o in order_matches])),
            "tracking_numbers": list(set(tracking_matches)),
            "amounts": list(set(amounts))
        }

    def test_credit_card_masking(self):
        sample = "My card number 4111 2222 3333 4444 was charged twice for $89.00."
        sanitized = self.sanitize_and_redact(sample)
        self.assertNotIn("4111", sanitized)
        self.assertIn("[REDACTED_CC]", sanitized)

    def test_phone_and_email_masking(self):
        sample = "Please call me at +1 (555) 234-5678 or write to john.doe@ecommerce.org"
        sanitized = self.sanitize_and_redact(sample)
        self.assertNotIn("555", sanitized)
        self.assertNotIn("john.doe", sanitized)
        self.assertIn("[REDACTED_PHONE]", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)

    def test_html_tag_stripping(self):
        sample = "<div><p>Hello <b>Support</b>, my order is broken.<br/></p></div>"
        sanitized = self.sanitize_and_redact(sample)
        self.assertEqual(sanitized, "Hello Support, my order is broken.")

    def test_entity_extraction_orders_and_tracking(self):
        sample = "Inquiry regarding order #84920 and ORD-9012. UPS Tracking number is 1Z9999999999999999 for $149.99."
        entities = self.extract_entities(sample)
        self.assertIn("#84920", entities["order_ids"])
        self.assertIn("ORD-9012", entities["order_ids"])
        self.assertIn("1Z9999999999999999", entities["tracking_numbers"])
        self.assertIn("$149.99", entities["amounts"])

if __name__ == "__main__":
    unittest.main()
