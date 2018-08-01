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
