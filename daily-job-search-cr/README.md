
# Daily Job Search — Data Analyst & Graduate Trainee (Nigeria + Remote)

This repository runs two scheduled GitHub Actions:
- **Data Analyst Job Search** — daily at 10:00 AM WAT
- **Graduate Trainee Job Search** — daily at 10:05 AM WAT

Each script:
- collects job listings from Remotive + Nigerian job boards,
- appends results to `job_history.csv`,
- sends a formatted HTML email via SendGrid to `Tanko8668@gmail.com`,
- sends a short WhatsApp summary (top 5 links) via Twilio sandbox.

## What you must add (GitHub Secrets)
- `SENDGRID_API_KEY` — SendGrid API Key
- `TWILIO_SID` — Twilio Account SID
- `TWILIO_AUTH` — Twilio Auth Token
- `WHATSAPP_FROM` — Twilio WhatsApp sandbox number (e.g. 'whatsapp:+14155238886')
- `WHATSAPP_TO` — Your WhatsApp number (e.g. 'whatsapp:+234XXXXXXXXXX')

## Setup
1. Create a new GitHub repository and upload these files.
2. Add the secrets listed above in **Settings → Secrets and variables → Actions**.
3. (Optional) Edit `fetch_analyst_jobs.py` and `fetch_graduate_jobs.py` to tweak sources/keywords.
4. Manually run each workflow from **Actions → (workflow) → Run workflow** to test.

## Notes and troubleshooting
- Wellfound and some job boards use JavaScript to render listings; scraping may be incomplete. Remotive API is the most reliable source included.
- If emails land in Spam, mark one as 'Not Spam' and add a Gmail filter to whitelist `Tanko8668@gmail.com`.
- Twilio sandbox requires you to join the sandbox from your WhatsApp to receive messages.

## License
MIT
