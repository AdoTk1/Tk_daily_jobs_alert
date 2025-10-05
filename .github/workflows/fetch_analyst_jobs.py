
#!/usr/bin/env python3
"""Fetch Data Analyst / Analytics jobs (Remote + Nigeria) and email + WhatsApp summary.
Appends results to job_history.csv
Secrets required as GitHub Actions secrets:
  - SENDGRID_API_KEY
  - TWILIO_SID
  - TWILIO_AUTH
  - WHATSAPP_FROM  (e.g. 'whatsapp:+14155238886')
  - WHATSAPP_TO    (e.g. 'whatsapp:+234XXXXXXXXXX')
"""
import os, time, csv
import requests
from bs4 import BeautifulSoup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from datetime import datetime

JOB_CSV = "job_history.csv"

def fetch_remotive(query="Data Analyst OR Data Analytics OR SQL OR Power BI OR Nigeria", limit=50):
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": query, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get('jobs', [])
    except Exception as e:
        print("Remotive error:", e)
        data = []
    jobs = []
    for j in data:
        title = j.get('title','').strip()
        company = j.get('company_name') or '-'
        loc = (j.get('candidate_required_location') or '').strip()
        link = j.get('url') or j.get('job_url') or ''
        desc = j.get('description','') or ''
        if any(k in (loc+' '+desc+' '+title).lower() for k in ['nigeria', 'africa', 'remote']):
            jobs.append({
                'date': datetime.utcnow().date().isoformat(),
                'category': 'Data Analyst',
                'title': title,
                'company': company,
                'location': loc or 'Remote',
                'link': link,
                'keywords': 'data; analysis; dashboards; reporting; metrics',
                'skills': 'SQL; Python; Excel; BI tools; statistics',
                'source': 'Remotive'
            })
    return jobs

def fetch_topstartups():
    url = "https://topstartups.io/jobs/?role=Data+Analyst"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print('TopStartups error:', e)
        return []
    jobs = []
    for a in soup.select('a[href]'):
        txt = a.get_text(' ', strip=True)
        href = a.get('href') or ''
        if not txt or 'analyst' not in txt.lower():
            continue
        full = href if href.startswith('http') else 'https://topstartups.io' + href
        jobs.append({
            'date': datetime.utcnow().date().isoformat(),
            'category': 'Data Analyst',
            'title': txt[:200],
            'company': '-',
            'location': 'Remote',
            'link': full,
            'keywords': 'data; metrics; dashboards; insights; reporting',
            'skills': 'SQL; Python; visualization; data pipelines; statistics',
            'source': 'TopStartups'
        })
    return jobs

def fetch_wellfound():
    url = 'https://wellfound.com/role/r/data-analyst'
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print('Wellfound error:', e)
        return []
    jobs = []
    for a in soup.select('a[href]'):
        txt = a.get_text(' ', strip=True)
        href = a.get('href') or ''
        if not txt or 'data analyst' not in txt.lower():
            continue
        full = href if href.startswith('http') else 'https://wellfound.com' + href
        jobs.append({
            'date': datetime.utcnow().date().isoformat(),
            'category': 'Data Analyst',
            'title': txt[:200],
            'company': '-',
            'location': 'Remote',
            'link': full,
            'keywords': 'data; metrics; reporting; dashboards; insights',
            'skills': 'SQL; Python; Looker/Tableau; Excel; stats',
            'source': 'Wellfound'
        })
    return jobs

def dedupe(jobs):
    seen = set()
    out = []
    for j in jobs:
        key = (j.get('link') or '').strip()
        if not key:
            key = (j.get('company','') + '|' + j.get('title','')).strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out

def append_to_csv(rows):
    header = ['date','category','title','company','location','link','keywords','skills','source']
    file_exists = os.path.isfile(JOB_CSV)
    with open(JOB_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not file_exists:
            writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k,'') for k in header})

def send_email(rows):
    rows = rows[:20]
    html = '<h3>Daily Data Analyst jobs</h3>'
    html += '<table border="1" cellpadding="6" style="border-collapse:collapse">'
    html += '<tr><th>Company</th><th>Title</th><th>Location</th><th>Keywords</th><th>Skills</th><th>Link</th></tr>'
    for r in rows:
        html += f"<tr><td>{r['company']}</td><td>{r['title']}</td><td>{r['location']}</td><td>{r['keywords']}</td><td>{r['skills']}</td><td><a href='{r['link']}'>Apply</a></td></tr>"
    html += '</table>'
    to_email = os.getenv('TO_EMAIL','Tanko8668@gmail.com')
    from_email = os.getenv('FROM_EMAIL', to_email)
    message = Mail(
        from_email=(from_email, 'Ahmed Tanko Job Bot'),
        to_emails=to_email,
        subject=f"🔍 Data Analyst Jobs — {datetime.utcnow().date().isoformat()}",
        html_content=html
    )
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        resp = sg.send(message)
        print('Email send status:', getattr(resp, 'status_code', 'unknown'))
    except Exception as e:
        print('SendGrid error:', e)

def send_whatsapp(rows):
    top5 = rows[:5]
    analysts = len([r for r in rows if r['category']=='Data Analyst'])
    body_lines = [f"✅ Data Analyst update — {analysts} results found\nTop 5:" ]
    for i, r in enumerate(top5, start=1):
        title = (r.get('title') or '')[:80]
        company = r.get('company') or ''
        link = r.get('link') or ''
        body_lines.append(f"{i}. {company} — {title} — {link}")
    body_lines.append('\nFull details sent to your email.')
    body = '\n'.join(body_lines)
    try:
        client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_AUTH'))
        msg = client.messages.create(body=body, from_=os.getenv('WHATSAPP_FROM'), to=os.getenv('WHATSAPP_TO'))
        print('WhatsApp SID:', getattr(msg, 'sid', None))
    except Exception as e:
        print('Twilio error:', e)

def main():
    all_jobs = []
    all_jobs += fetch_remotive()
    time.sleep(1)
    all_jobs += fetch_topstartups()
    time.sleep(1)
    all_jobs += fetch_wellfound()
    jobs = dedupe(all_jobs)
    if not jobs:
        print('No Data Analyst jobs found today.')
        return
    append_to_csv(jobs)
    send_email(jobs)
    send_whatsapp(jobs)

if __name__ == '__main__':
    main()
