#!/usr/bin/env python3
"""Generate a public, rolling school lunch ICS from LINQ Connect."""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DISTRICT = '1c00c699-3151-ec11-8b1d-a5b3899f9b97'
BUILDING = 'c1642223-2b64-ec11-ae91-966e225cc97d'
OUT = Path('site/lunch.ics')

def esc(s):
    return str(s).replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')

def fold(line):
    # iCalendar lines should not exceed 75 octets; preserve UTF-8 boundaries.
    chunks=[]; current=''
    for ch in line:
        if len((current+ch).encode('utf-8')) > (75 if not chunks else 74):
            chunks.append(current);current=ch
        else: current+=ch
    chunks.append(current)
    return '\r\n '.join(chunks)

def date_parse(value):
    if not value:return None
    for fmt in ('%m/%d/%Y','%Y-%m-%d','%Y-%m-%dT%H:%M:%S','%Y-%m-%dT%H:%M:%S.%f'):
        try:return dt.datetime.strptime(value[:len(dt.datetime.now().strftime(fmt))],fmt).date()
        except ValueError:pass
    try:return dt.date.fromisoformat(value[:10])
    except ValueError:return None

def fetch(start,end):
    q=urlencode({'buildingId':BUILDING,'districtId':DISTRICT,'startDate':start.strftime('%m-%d-%Y'),'endDate':end.strftime('%m-%d-%Y')})
    req = Request('https://api.linqconnect.com/api/FamilyMenu?' + q,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36','Accept': 'application/json'})
    with urlopen(req,timeout=35) as response:
        return json.load(response)

def extract(data):
    days={}
    for session in data.get('FamilyMenuSessions',[]):
        if 'lunch' not in str(session.get('ServingSession','')).lower():continue
        for plan in session.get('MenuPlans',[]):
            for day in plan.get('Days',[]):
                d=date_parse(str(day.get('Date','')))
                if not d:continue
                categories=[]
                for meal in day.get('MenuMeals',[]):
                    for cat in meal.get('RecipeCategories',[]):
                        names=[r.get('RecipeName','').strip() for r in cat.get('Recipes',[]) if isinstance(r,dict) and r.get('RecipeName','').strip()]
                        if names:categories.append((str(cat.get('CategoryName','Other')),names))
                if not categories:continue
                entry=days.setdefault(d,{})
                for label,names in categories:
                    entry.setdefault(label,[])
                    for name in names:
                        if name not in entry[label]:entry[label].append(name)
    return days

def main():
    today=dt.datetime.now(dt.timezone.utc).date()
    # Smaller 14-day windows improve compatibility with LINQ date-range limits.
    all_days={}
    for offset in range(0,70,14):
        start=today+dt.timedelta(days=offset)
        end=start+dt.timedelta(days=13)
        all_days.update(extract(fetch(start,end)))
    if not all_days:raise RuntimeError('LINQ returned no lunch items; retaining previous feed instead of publishing an empty calendar')
    now=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Thomas Elementary Lunch Feed//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Thomas Elementary Lunch']
    for day, categories in sorted(all_days.items()):
        main=[name for label,names in categories.items() if any(k in label.lower() for k in ('entree','entrée','main')) for name in names]
        if not main:main=next(iter(categories.values()))
        summary='School Lunch: '+ ' / '.join(main[:2])
        description='Thomas Elementary lunch menu\\n'+'\\n'.join(label+': '+', '.join(names) for label,names in categories.items())+'\\nSource: LINQ Connect. Check school for changes.'
        lines+=['BEGIN:VEVENT','UID:thomas-lunch-'+day.strftime('%Y%m%d')+'@school-lunch.local','DTSTAMP:'+now,'DTSTART;VALUE=DATE:'+day.strftime('%Y%m%d'),'DTEND;VALUE=DATE:'+(day+dt.timedelta(days=1)).strftime('%Y%m%d'),'SUMMARY:'+esc(summary),'DESCRIPTION:'+esc(description.replace('\\n','\n')),'END:VEVENT']
    lines.append('END:VCALENDAR')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_bytes(('\r\n'.join(fold(line) for line in lines)+'\r\n').encode('utf-8'))
    print(f'Generated {len(all_days)} lunch dates: {OUT}')

if __name__=='__main__':main()
