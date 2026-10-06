# Email without another paid mailbox

Checked October 6, 2026. Public MX records for firehose360.com point to Google. The app currently uses administrator approval and administrator-issued recovery; automated email is a proposed extension.

## Receive replies in the existing inbox

Google Workspace allows up to 30 aliases per user at no extra charge. Add support@firehose360.com to Keith's existing account; mail arrives in the same inbox. An alias is an address, not another login/mailbox/license. Configure Gmail “Send mail as” for personal replies. [Google alias instructions](https://support.google.com/a/answer/33327).

## Recommended app sender

Resend's free transactional tier currently includes 3,000 emails/month, 100/day and three domains. A free Resend account is required; another Google mailbox is not. Verify notify.firehose360.com, send from accounts@notify.firehose360.com and set Reply-To to Keith or the support alias. Keep root-domain Google MX records. Add the sender's verification/authentication DNS records on the appropriate subdomain. [Pricing](https://resend.com/pricing), [verified domains](https://resend.com/docs/dashboard/domains/introduction).

Use its HTTPS API: DigitalOcean documents blocked SMTP ports 25/465/587 on Droplets. [DigitalOcean policy](https://docs.digitalocean.com/support/why-is-smtp-blocked/).

## Google-only alternative

The Gmail HTTPS API can send from the existing account using OAuth authorization. This avoids a separate email-provider account, but needs Google Cloud/OAuth setup and shares the existing mailbox's limits and access boundary. [Gmail API](https://developers.google.com/workspace/gmail/api/guides), [server authorization](https://developers.google.com/workspace/gmail/api/auth/web-server).

Receiving replies in Gmail is different from processing email inside the app. If that becomes necessary, use a separate receiving subdomain and authenticated webhooks; preserve Keith's existing inbox routing.

An eventual email adapter should have mock tests, bounded sending, expiring single-use verification/recovery tokens, generic recovery responses and retry handling. Activation requires the chosen provider credentials and domain verification; no email was sent or mail-routing configuration changed during this research.

## Setup status

Google Admin was opened for the existing Keith account; Google requires the owner to reauthenticate. Resend's login is prepared for keith@firehose360.com, pending approval of the terms displayed on its login page. Neither a Resend account nor a sending credential has been created. Public nameservers are ns15/ns16.domaincontrol.com (GoDaddy); sender verification will require access to that DNS account. Existing Google MX routing remains unchanged.
