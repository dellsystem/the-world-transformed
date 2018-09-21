Just a static site (using Jekyll) for now.

For The World Transformed 2018.

## Setup

To rebuild the semantic files (CSS, JS), `cd` into `semantic/` and run
`gulp build`. (This only needs to be done if you change any files in the
semantic dir.) Install semantic-ui via npm first.

To serve the website locally, install jekyll (as a Ruby gem) and run
`jekyll serve` in the root directory of the project. It'll be available at
`localhost:4000` by default (you can change the port with the `--port` flag).

## Deploying

Just push. It's hosted on GitHub pages and GitHub will automatically update
after a few minutes.

## Fetching updated programme data

(Only possible if you've been given access to the spreadsheet. This step isn't
required if you simply wish to rebuild the website, as the data will have been
committed already.)

Follow [this guide](https://developers.google.com/drive/api/v3/quickstart/python)
to get credentials.json, then run `_data/programme/update_programme.py`.
Install Python dependencies with `pip -r requirements.txt` first.

## Adding new session images

Add the image (.jpg) to images/sessions/, then run ./resize.sh (requires
ImageMagick and Python).
