import collections
import csv
import httplib2
import io
import os
import yaml

# pip install --upgrade google-api-python-client
from oauth2client.file import Storage
from apiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')

storage = Storage(CREDS_FILE)
credentials = storage.get()

http = httplib2.Http()
http = credentials.authorize(http)

drive_service = build('drive', 'v2', http=http)


def download_file(file_id):
    request = drive_service.files().export_media(fileId=file_id,
                                                 mimeType='text/csv')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return io.BytesIO(fh.getvalue()) 


speakers_csv = csv.reader(
    download_file('1YjTxC0y6lV2cTDCMr_I1oBWEPULX-Ui1Ls9TCKmyZZE')
)
sessions_csv = csv.reader(
    download_file('1_Abpuo5P6R4WKz9OxV8lveCFon7VqRpjL-U4ntdXorw')
)

session_header = next(sessions_csv)
sessions = {}
speaker_sessions = collections.defaultdict(set)
schedule = collections.defaultdict(list)
for row in sessions_csv:
    session = dict(zip(session_header, [cell.strip() for cell in row]))
    slug = session.pop('slug')
    if not slug.strip():
        print "Missing slug for", session['title']
        continue

    status = session.pop('status')
    if status == 'TODO':
        continue

    session['final'] = False if status == 'WAITING' else True

    # Calculate the start and end time (for calendar)
    if session['day'] == 'Saturday':
        day = 2
    elif session['day'] == 'Sunday':
        day = 3
    elif session['day'] == 'Monday':
        day = 4
    elif session['day'] == 'Tuesday':
        day = 5
    try:
        start_time, end_time = session['time'].split('-')
    except ValueError:
        print 'bad time', session['time'], session['title']
    session['start_timestamp'] = '2018092{day}T{start_time}00'.format(
        day=day,
        start_time=start_time.replace(':', '').zfill(4),
    )
    session['end_timestamp'] = '2018092{day}T{end_time}00'.format(
        day=day,
        end_time=end_time.replace(':', '').zfill(4),
    )

    sessions[slug] = session
    schedule[session['day'].lower().strip()].append(slug)
    for speaker_slug in session['speakers'].split(' '):
        if speaker_slug:
            speaker_sessions[speaker_slug].add(slug)
    if not session['image'] or not os.path.exists('../../images/sessions/%s.jpg' % session['image']):
        print "Missing image for", session['title'], session['image']
    if ' ' in session['day']:
        print "Bad day for", session['title']

# Save saturday.csv, sunday.csv, monday.csv, tuesday.csv
for day in schedule:
    schedule_csv = csv.writer(open('%s.csv' % day, 'wt'))
    schedule_csv.writerow(['slug'])
    for slug in schedule[day]:
        schedule_csv.writerow([slug])
    print "%s: %d sessions" % (day, len(schedule[day]))

# Save speakers.yml
speaker_header = next(speakers_csv)
speakers = {}
for row in speakers_csv:
    speaker = dict(zip(speaker_header, row))
    slug = speaker.pop('slug')
    speaker['sessions'] = ' '.join(sorted(speaker_sessions[slug]))
    if speaker['sessions']:
        # Check if the speaker image file exists on the filesystem.
        speaker['photo'] = os.path.exists('../../images/speakers/%s.jpg' % slug)
        if not speaker['photo']:
            print "Missing image", slug, speaker['name']

        speakers[slug] = speaker
    else:
        pass
        #print "No sessions for", speaker['name']

yaml.dump(speakers, open('speakers.yml', 'wt'))

# Store the full list of speakers in alphabetical order.
speakers_list_csv = csv.writer(open('speakers_list.csv', 'wt'))
speakers_list_csv.writerow(['slug'])
for speaker_slug in sorted(speakers.keys()):
    speakers_list_csv.writerow(
        [
            speaker_slug,
        ]
    )

yaml.dump(sessions, open('sessions.yml', 'wt'))

# For each session, make sure there is a corresponding .html page in sessions/
front_matter = """---
layout: session
slug: {slug}
title: "{title} // The World Transformed"
image: "sessions/{image}.jpg"
description: "A session at {time} on {day} in {venue}{details}"
---"""
for slug, session in sessions.iteritems():
    # If there's an organiser, mention that
    if session['organiser']:
        details = ' organised by ' + session['organiser']
    else:
        details = ''

    filename = '../../sessions/%s.html' % slug
    file = open(filename, 'wt')
    file.write(
        front_matter.format(
            slug=slug,
            title=session['title'].replace('"', '\\"'),
            image=session['image'],
            time=session['time'],
            day=session['day'],
            venue=session['venue'],
            details=details
        )
    )
    file.close()

# If there are any speakers for whom we don't have data, print them
for speaker_slug in speaker_sessions:
    if speaker_slug not in speakers:
        print speaker_slug, speaker_sessions[speaker_slug]
