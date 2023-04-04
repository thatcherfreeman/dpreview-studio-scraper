# Dpreview Studio Image tool scraper
DPreview is closing April 10, and it would be a shame to lose access to the database of RAW files from these cameras. I've written this python script to download all the images from their video and stills studio comparison scene tools, plus the iso invariance and underexposure tests. In total, these four comparisons are 391 GB, with 267GB of that being files from the Stills comparison tool

## Installation
1. Clone the repo
2. (Recommended) Make a virtual environment with `python -m venv dpreview`
3. Enter the virtual environment with `source dpreview/bin/activate` on unix or `./dpreview/Scripts/activate` if you're on windows
4. Run `python stils_scraper.py`, make sure it works. Then run `python stills_scraper.py --num-images 0` to download all the images
5. Run `python video_scraper.py`, make sure it works. Then run `python video_scraper.py --num-images 0` to download all images.
6. Run `python iso_invariance_scraper.py`, make sure it works. Then run `python iso_invariance_scraper.py --num-images 0` to download all images.
7. Run `python exposure_latitude_scraper.py`, make sure it works. Then run `python exposure_latitude_scraper.py --num-images 0` to download all images.
8. Seed the images via a torrent or something so they live on when the website closes.

## Note
Dpreview will start giving you error 429 (too many requests) if you hit their website too many times in a row, so usually you have to wait 1-5 minutes for the download to progress when that happens. Don't browse dpreview while running the script. Additionally, if it fails, just delete the last folder it made (the folder whose name is the camera model number and whose files haven't finished downloading) and restart the script.
