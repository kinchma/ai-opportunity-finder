# Laurel Run Trailer Works website

This is a fictional academic discovery-test website. The company, people, products, and dealer names are invented. Contact and dealer-inquiry forms prepare text locally in the browser; they do not send messages. The dealer finder uses fictional names and states without contact details or directions.

## Run locally

Python 3 is the only build and server requirement; no packages, account, credentials, environment variables, database, or network connection are needed. From this directory:

```sh
python3 build_site.py
python3 -m http.server 3000 --bind 127.0.0.1 --directory site
```

Open <http://127.0.0.1:3000/> in a browser. Stop the server with Ctrl+C. The `site` directory must be served as the web root because page and asset links begin with `/`; opening HTML files directly with `file://` or hosting the site under a URL subdirectory will not resolve those links correctly. JavaScript is needed for dealer filtering and the local form interactions.

This portable copy uses locally available system fonts instead of requesting Google Fonts, so its typography may differ slightly from the hosted version and no font download is needed.

## Files

- `build_site.py` and `pages.py` generate the static HTML in `site/`. Re-run the build after changing either file. The existing `site/` output can also be served without rebuilding.
- `site/assets/` contains the stylesheet, JavaScript, fictional dealer data, and five completed generated WebP images. The copied source and HTML reference the bundled images at `/assets/image-1.webp` through `/assets/image-5.webp`; they do not depend on Manus managed-storage paths. A generated route-list JSON file is harmless static metadata, not required by the local server.
- No Git history, platform project configuration, environment files, credentials, or private company files are included in this website copy.

The original published site was private at the time of this copy; the independent local preview above does not depend on its availability.
