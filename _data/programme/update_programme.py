# encoding: utf-8
import collections
import csv
import unicodecsv
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

print_columns = [
    'title', 'organiser', 'day', 'time', 'venue', 'room', 'description',
    'speakers',
]
venues = [
    'Hinterlands', 'Constellations', 'Black-E', 'Baltic Creative',
    'Baltic Cinema', 'Sports Hall'
]

session_header = next(sessions_csv)
sessions = {}
print_sessions = []
speaker_sessions = collections.defaultdict(set)
schedule = collections.defaultdict(list)
statuses = {}  # have to store this separately to ensure deletion from yaml
for row in sessions_csv:
    session = dict(zip(session_header, [cell.strip() for cell in row]))

    slug = session.pop('slug')
    if not slug.strip():
        print "Missing slug for", session['title']
        continue

    status = session.pop('status')
    if status == 'TODO':
        continue
    statuses[slug] = status

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

    # Get rid of the columns where the header's first letter is capitalised.
    for key in session.keys():
        if key[0].upper() == key[0]:
            session.pop(key)

    sessions[slug] = session
    schedule[session['day'].lower().strip()].append(slug)
    speaker_names = []
    for speaker_slug in session['speakers'].split(' '):
        if speaker_slug:
            speaker_sessions[speaker_slug].add(slug)
    if not session['image'] or not os.path.exists('../../images/sessions/%s.jpg' % session['image']):
        print "Missing image for", session['title'], session['image']
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

# Save saturday.csv, sunday.csv, monday.csv, tuesday.csv
# Also for the print programme.
for day in schedule:
    schedule_csv = csv.writer(open('%s.csv' % day, 'wt'))
    schedule_csv.writerow(['slug'])

    # Create the CSV for the printed program (one for each day)
    print_csv_filename = 'print_%s.txt' % day
    print_csv_file = open(print_csv_filename, 'wt')
    print_csv = unicodecsv.writer(
        print_csv_file,
        quoting=csv.QUOTE_ALL,
        delimiter='\t',
    )
    print_csv.writerow(print_columns + venues)

    for slug in schedule[day]:
        schedule_csv.writerow([slug])

        # Only put it in the print programme if the "print" column is 1.
        session = sessions[slug]
        use_session = session.pop('print')  # Shouldn't be saved
        if use_session != '1':
            continue

        print_row = {}
        for print_column in print_columns:
            print_row[print_column] = session[print_column]

        # Remove the photo credit for the new far right session.
        if print_row['title'] == "Britain's New Far Right":
            print_row['description'] = print_row['description'].splitlines()[0]
        print_row['description'] = print_row['description'].replace('\n', ' ')

        speaker_slugs = [s for s in print_row['speakers'].split(' ') if s]
        speaker_names = []
        for speaker_slug in speaker_slugs:
            speaker = speakers[speaker_slug]
            speaker_name = speaker['name']
            if speaker['affiliation']:
                speaker_name += ' (' + speaker['affiliation'] + ')'
            speaker_names.append(speaker_name)
        print_row['speakers'] = ' • '.join(speaker_names)

        # If there are still speakers to announced ...
        if statuses[slug] == 'WAITING':
            # If there are already speakers
            if print_row['speakers']:
                print_row['speakers'] += ' + more speakers TBA!'
            else:
                print_row['speakers'] = 'Speakers to be announced!'
        row = [print_row[c] for c in print_columns]

        # Split up the venue
        session_venue = print_row['venue']
        for venue in venues:
            if venue == session_venue:
                row.append(venue)
            else:
                row.append('')
        print_csv.writerow(row)
        if session_venue not in venues:
            print session_venue, slug
            raise SystemError

    # Have to convert it to utf-16...
    print_csv_file.close()
    f1 = open(print_csv_filename)
    s = f1.read().decode('utf-8').encode('utf-16')
    f1.close()
    f2 = open(print_csv_filename, 'wb')
    f2.write(s)
    f2.close()
    print "%s: %d sessions" % (day, len(schedule[day]))


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
