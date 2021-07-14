# espeak-singer
Generate lyrics video performed by espeak

If you came here from a YouTube video, this is just a stub of the script we're using; it doesn't automatically upload to youtube yet. Expect great news soon! ;)

## Just try it out
On ubuntu:
- Run `apt update && apt install -y espeak python3 python3-pip imagemagick ffmpeg && pip3 install beautifulsoup4 transliterate`
- Clone this repo
- Enter the folder
- Run for example: `python espeak-singer.py https://www.testietraduzioni.it/lyrics/Africa_toto/ en africa.mp4`

The lyrics must be from https://www.testietraduzioni.it , parsing for more websites coming soon.

The second parameter is the language used by espeak. The third is the output file.
