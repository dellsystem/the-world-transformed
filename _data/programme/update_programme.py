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
schedule_csv = csv.writer(open('schedule.csv', 'wt'))
schedule_csv.writerow(['slug'])
for row in sessions_csv:
    session = dict(zip(session_header, row))
    slug = session.pop('slug')
    if not slug.strip():
        print "Missing slug for", session['title']
        continue

    if session['status'] != 'READY':
        continue

    sessions[slug] = session
    schedule_csv.writerow([slug])
    for speaker_slug in session['speakers'].split(' '):
        if speaker_slug:
            speaker_sessions[speaker_slug].add(slug)
    if not session['image']:
        print "Missing image for", session['title']
    if ' ' in session['day']:
        print "Bad day for", session['title']

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
