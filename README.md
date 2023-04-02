# Dpreview Studio Image tool scraper
DPreview is closing April 10, and it would be a shame to lose access to the database of RAW files from these cameras. I've written this python script to download all the images from their video and stills studio comparison scene tools.

## Installation
1. Clone the repo
2. (Recommended) Make a virtual environment with `python -m venv dpreview`
  b. Enter the virtual environment with `source dpreview/bin/activate` on unix or `./dpreview/Scripts/activate` if you're on windows
4. Run `python stils_scraper.py`, make sure it works. Then run `python stills_scraper.py --num-images 0` to download all the images
5. Run `python video_scraper.py`, make sure it works. Then run `python video_scraper.py --num-images 0` to download all images.
6. Seed the images via a torrent or something so they live on when the website closes.
