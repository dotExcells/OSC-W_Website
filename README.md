# OSC-W website

The website of the Wageningen Open Science Community, <https://openscience-wageningen.nl>.

All content is plain text: Markdown for pages and events, YAML for lists (team, funding calls, newsletters). A small Python script (`build.py`) turns it into a static website. GitHub builds and publishes it automatically whenever something changes, so editing the site means editing a text file.

## Where things are

```
content/
  site.yml                  site name, logo, menu, contact email
  pages/                    one Markdown file per page (home, about, join-us, ...)
  events/                   one Markdown file per event
    _template.md            copy this to make a new event
  data/
    team.yml                team members on the About page
    funding.yml             open calls on the Funding Opportunities page
    newsletters.yml         newsletter archive on the Join Us page
static/
  css/style.css             colours, fonts, layout
  fonts/                    web fonts, served from this site
  wp-content/uploads/       images and PDFs (copied from the old WordPress site)
templates/                  HTML layout of each page type (rarely needs changing)
build.py                    the build script
requirements.txt            the three Python packages the build uses, with exact versions
.github/workflows/          tells GitHub how to build and publish the site
```

## Common edits

You can do all of these directly on github.com: open the file, click the pencil icon, edit, and click "Commit changes". The live site updates about a minute later.

### Add an event

1. In `content/events/`, open `_template.md` and copy its contents.
2. Create a new file in the same folder, for example `open-data-lunch.md`. The file name becomes the web address: `/event/open-data-lunch/`.
3. Paste and fill in the fields. Only `title` and `date` are required.

Events appear under "Upcoming" until their date has passed, then move to "Past events" on their own (the site rebuilds every night). The "Register here" button only shows while an event is upcoming.

### Add a newsletter

1. Upload the PDF to `static/wp-content/uploads/` (any subfolder is fine, e.g. `2026/11/`). On GitHub: open the folder, "Add file" then "Upload files".
2. Add an entry at the top of `content/data/newsletters.yml`:

   ```yaml
   - number: 11
     title: November 2026
     file: /wp-content/uploads/2026/11/OSC-W-Newsletter-November-2026.pdf
   ```

### Update funding calls

Edit `content/data/funding.yml`. Each call has a `name`, `description`, optional `deadline`, and `link`. Delete a block when a call closes.

### Update the team

Edit `content/data/team.yml`. Upload the photo to `static/wp-content/uploads/` first and point `photo:` to it. Square photos look best.

### Edit page text

Edit the Markdown files in `content/pages/`. The home page uses a little HTML around each section to place the images next to the text; just edit the text between the tags.

## First-time setup

The images and newsletter PDFs from the old WordPress site are already included in `static/wp-content/uploads/`, at the same paths as before, so old links to newsletter PDFs keep working.

### 1. Put the code on GitHub

1. Create a free account at <https://github.com> (or use an existing one; a GitHub organisation for OSC-W lets several people manage it).
2. Create a new repository, e.g. `osc-w-website`. It can be public.
3. Upload all files from this folder (drag them into "uploading an existing file"), including the hidden `.github` folder. If your file browser hides it, use GitHub Desktop or `git` instead.

### 2. Turn on GitHub Pages

1. In the repository: **Settings → Pages**.
2. Under "Build and deployment", set **Source** to **GitHub Actions**.
3. Open the **Actions** tab. The "Build and deploy" workflow runs; when it has a green tick, the site is live at `https://<your-account>.github.io/osc-w-website/`.

   Note: on that temporary address, images and links may look broken because the site expects to live at the root of a domain. That fixes itself once your domain points to it (next step).

### 3. Point your domain at it

1. In **Settings → Pages → Custom domain**, enter `openscience-wageningen.nl` and save.
2. At the company where you registered the domain, open the DNS settings and set:

   | Type  | Name | Value |
   |-------|------|-------|
   | A     | @    | 185.199.108.153 |
   | A     | @    | 185.199.109.153 |
   | A     | @    | 185.199.110.153 |
   | A     | @    | 185.199.111.153 |
   | CNAME | www  | `<your-account>.github.io` |

   Remove the old A records that pointed to your WordPress host. Leave any MX or TXT records alone (they handle email and verification).
3. Wait until GitHub shows the domain as verified (minutes to a few hours), then tick **Enforce HTTPS**.
4. Check the site works on the domain, then cancel the old hosting. Keep the domain registration.

### Alternative: Cloudflare Pages

If you'd rather use Cloudflare Pages, connect the GitHub repository there and use these build settings:

- Build command: `pip install -r requirements.txt && python build.py`
- Build output directory: `_site`

Cloudflare doesn't rebuild on a schedule by itself, so events move to "past" on the next change you push. The GitHub Pages route above handles that automatically.

## How the build works

You only need this section if you want to change the layout or the build itself.

`build.py` is a single, commented Python file. Each time it runs, it:

1. Copies everything in `static/` to the output folder `_site/` unchanged.
2. Reads `content/site.yml` and the lists in `content/data/`.
3. Reads every event in `content/events/`, converts the Markdown to HTML, and sorts events into upcoming and past by comparing their date to today.
4. Renders each page in `content/pages/` with the template named in its `template:` field, and each event with `templates/event.html`.
5. Writes small redirect pages for old addresses listed under `aliases:`.
6. Writes the calendar feed `events.ics`.

Templates use Jinja2: `{{ page.title }}` inserts a value, `{% for ... %}` and `{% if ... %}` loop and branch. To change how a page type looks, edit its file in `templates/`. To change colours or spacing, edit `static/css/style.css`.

It uses three well-established Python packages: Markdown (Markdown to HTML), PyYAML (reads the YAML files) and Jinja2 (templates).

## Security

The public site is static: plain HTML, CSS, images and PDFs. No code runs when someone visits, and there is no database, login page or plugin to break into or keep patched. HTTPS is provided by GitHub Pages.

What security depends on now:

- **Write access to the GitHub repository.** Anyone with it can change the site, including adding scripts to pages. Give access only to people who need it, and make sure each of them has two-factor authentication turned on (GitHub: Settings → Password and authentication).
- **The domain registrar account.** Whoever controls it controls where the domain points. Turn on two-factor authentication there if offered.

Other measures in place:

- **Fonts are served from this site**, not from Google Fonts, so visiting the site doesn't send visitors' IP addresses to a third party.
- **Package versions are pinned** in `requirements.txt`, so a new release of a package can't change the build unless someone chooses to update it. To update: change the version numbers, run `python build.py` locally to check nothing broke, and commit.
- YAML is read with the safe loader, and templates escape text by default.

## Fonts

Both fonts are included in `static/fonts/` and served from this site:

- **Open Sans** for body text and headings (`OpenSans.woff`, one file with all weights from light to extra bold)
- **Poppins** for the menu and buttons (`Poppins-Regular.woff`, `Poppins-Medium.woff`)

They were reduced to the characters used in Western European languages to keep them small (about 85 KB together). Both are under the SIL Open Font License (see `static/fonts/LICENSE.txt`), which allows this.

## Preview on your own computer (optional)

You need Python 3.10 or newer.

```
pip install -r requirements.txt
python build.py serve
```

Then open <http://localhost:8000>. Press Ctrl+C to stop. Run it again after editing to see changes.

## Extras

- **Calendar feed:** `/events.ics` lists all events. People can subscribe to it in Outlook, Google Calendar or Apple Calendar, and new events show up automatically.
- **Old links keep working:** the old WordPress addresses for the events page and the March 2025 event redirect to their new addresses. Add more with `aliases:` in a page's or event's front matter.
- **Newsletter signup** stays on Microsoft Forms. The link is in `content/pages/join-us.md` (`signup_url`).
