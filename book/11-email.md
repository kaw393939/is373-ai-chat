# 11 · Email is a delivery boundary

Registration, address verification and password recovery are different operations. Verification proves control of an address; approval grants access. Neither the browser nor the model can approve an account. Existing accounts survive migration `0002`; new registrations verify mail when delivery is enabled.

[The email adapter](../app/email.py) talks to Resend over HTTPS. Human replies go to the existing Keith inbox through Reply-To. This needs a free sender account and verified sending domain, not another paid Google mailbox. Keep the apex Google MX records.

The HTTP request commits a hashed link and an encrypted outbox message in one database transaction. A small worker delivers committed messages. This avoids losing an email between database commit and network failure. Pending recipients and links use authenticated Fernet encryption with a separate operator key. Delivered, expired and exhausted messages erase their payload; pruning retains quota metadata for 32 days. Rotating the encryption key before draining pending mail makes that mail unreadable.

The worker locks each row, uses a stable provider idempotency key, limits batches to ten and retries at most six times. Tokens expire after 30 minutes. Quotas allow 80 queued emails per UTC day and 2,000 per rolling 30 days. Anonymous requests also have per-IP/address limits. Unknown and ineligible recovery requests receive the same message. Administrators see pending, failed and sent counts without private message contents.

Set EMAIL_PROVIDER=resend, RESEND_API_KEY, EMAIL_FROM, EMAIL_REPLY_TO and EMAIL_ENCRYPTION_KEY in the protected server .env after sender verification. Use a sending-only key restricted to the sender domain. CI uses mock delivery and a fake HTTPS transport; actual inbox receipt must be checked separately.

Sources: [Resend API](https://resend.com/docs/api-reference/emails/send-email), [Fernet](https://cryptography.io/en/latest/fernet/), [OWASP recovery](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).

**Exercise:** simulate a provider failure after accepting a message. Explain why retries keep the same idempotency key and why the outbox contains neither a plaintext recovery token nor the recipient after delivery.
