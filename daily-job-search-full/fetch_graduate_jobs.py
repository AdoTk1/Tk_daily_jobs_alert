
#!/usr/bin/env python3
"""Fetch Graduate Trainee / Entry-level jobs for Nigeria and email + WhatsApp summary.
Appends results to job_history.csv
"""
import os, time, csv
import requests
from bs4 import BeautifulSoup
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from datetime import datetime

JOB_CSV = "job_history.csv"

def remotive_graduates(query='graduate trainee OR entry level OR intern OR trainee', limit=50):
    url = 'https://remotive.com/api/remote-jobs'
    params = {'search': query, 'limit': limit}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json().get('jobs', [])
    except Exception as e:
        print('Remotive grads error:', e)
        data = []
    jobs = []
    for j in data:
        title = j.get('title','').strip()
        company = j.get('company_name') or '-'
        loc = (j.get('candidate_required_location') or '').strip()
        link = j.get('url') or j.get('job_url') or ''
        desc = j.get('description','') or ''
        if any(k in (loc+' '+desc+' '+title).lower() for k in ['nigeria', 'africa']):
            jobs.append({
                'date': datetime.utcnow().date().isoformat(),
                'category': 'Graduate Trainee',
                'title': title,
                'company': company,
                'location': loc or 'Nigeria',
                'link': link,
                'keywords': 'graduate; trainee; internship; entry level; training',
                'skills': 'communication; MS Excel; data basics; willingness to learn; teamwork',
                'source': 'Remotive'
            })
    return jobs

def myjobmag():
    url = 'https://www.myjobmag.com/search/jobs?q=graduate+trainee'
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print('MyJobMag error:', e)
        return []
    jobs = []
    for post in soup.select('.job-list-details'):
        a = post.select_one('h2 a')
        if not a: continue
        title = a.get_text(strip=True)
        href = a.get('href')
        link = 'https://www.myjobmag.com' + href if href and href.startswith('/') else href
        company = post.select_one('.job-company').get_text(strip=True) if post.select_one('.job-company') else '-'
        jobs.append({
            'date': datetime.utcnow().date().isoformat(),
            'category': 'Graduate Trainee',
            'title': title,
            'company': company,
            'location': 'Nigeria',
            'link': link,
            'keywords': 'graduate; trainee; internship; entry level; training',
            'skills': 'communication; MS Excel; data basics; willingness to learn; teamwork',
            'source': 'MyJobMag'
        })
    return jobs

def jobberman():
    url = 'https://www.jobberman.com/jobs?query=graduate%20trainee'
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print('Jobberman error:', e)
        return []
    jobs = []
    for a in soup.select('a[href*="/listing/"]')[:40]:
        href = a.get('href')
        title = a.get_text(strip=True)
        link = 'https://www.jobberman.com' + href if href and href.startswith('/') else href
        jobs.append({
            'date': datetime.utcnow().date().isoformat(),
            'category': 'Graduate Trainee',
            'title': title[:200],
            'company': '-',
            'location': 'Nigeria',
            'link': link,
            'keywords': 'graduate; trainee; internship; entry level; training',
            'skills': 'communication; MS Excel; data basics; willingness to learn; teamwork',
            'source': 'Jobberman'
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
    html = '<h3>Daily Graduate Trainee / Entry-level jobs (Nigeria)</h3>'
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
        subject=f"🎓 Graduate Trainee Jobs — {datetime.utcnow().date().isoformat()}",
        html_content=html
    )
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sg.send(message)
        print('Graduate email sent.')
    except Exception as e:
        print('SendGrid error (grads):', e)

def send_whatsapp(rows):
    top5 = rows[:5]
    grads = len([r for r in rows if r['category']=='Graduate Trainee'])
    body_lines = [f"✅ Graduate Trainee update — {grads} results found\nTop 5:" ]
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
        print('Twilio error (grads):', e)

def main():
    all_jobs = []
    all_jobs += remotive_graduates()
    time.sleep(1)
    all_jobs += myjobmag()
    time.sleep(1)
    all_jobs += jobberman()
    jobs = dedupe(all_jobs)
    if not jobs:
        print('No graduate jobs found today.')
        return
    append_to_csv(jobs)
    send_email(jobs)
    send_whatsapp(jobs)

if __name__ == '__main__':
    main()
