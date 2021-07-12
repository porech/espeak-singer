import sys, os, requests, tempfile
from bs4 import BeautifulSoup
import subprocess

"""
First argument: link to lyrics from testietraduzioni.it 
i.e. https://www.testietraduzioni.it/lyrics/mille-fedez/
"""

if len(sys.argv) < 3:
    print(f"Usage: python {sys.argv[0]} lyric_url language")
    sys.exit(1)

lyric_url = sys.argv[1]
language = sys.argv[2]

html = requests.get(lyric_url).text
soup = BeautifulSoup(html, features="html.parser")

author_text = soup.find("div", {"class": "lyrics-title"}).find("h3").get_text()
trimmed_author_text = " ".join(map(lambda t: t.strip(), author_text.split("\n"))).strip()

title_text = soup.find("div", {"class": "lyrics-title"}).find("div", {"class": "pull-left"}).get_text().strip()

title = f"{trimmed_author_text} - {title_text}"
print(f"{title} (performed by espeak)")

lyrics_div = soup.find("div", {"class": "lyric-text"})
x = 0
tempdir = tempfile.mkdtemp()
print(f"Temp folder: {tempdir}")
for p in lyrics_div.find_all("p"):
    p_class = []
    try:
        p_class = p["class"]
    except KeyError:
        pass
    if 'copyright-lyrics-text' in p_class:
        continue
    p_text = p.get_text().strip()
    joined_path = os.path.join(tempdir, f"{x}")
    with open(os.path.join(f"{joined_path}.txt"), "w") as f:
        f.write(p_text.replace("\n", ". "))
    subprocess.run(["espeak", "-v", language, "-f", f"{joined_path}.txt", "-w", f"{joined_path}.wav"])
    subprocess.run(["convert", "-size", "1920x1080", "-background", "black", "-bordercolor", "black", "-border", "100x100", "-fill", "white", "-gravity", "Center", f'caption:{p_text}', "-flatten", f"{joined_path}.png"])
    subprocess.run(["ffmpeg", "-loop", "1", "-i", f"{joined_path}.png", "-i", f"{joined_path}.wav", "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", f"{joined_path}.mp4"])
    x += 1
# tempdir = "/tmp/tmpnc0n_u90"
# x = 8

with open(os.path.join(tempdir, "list.txt"), "w") as f:
    f.write("\r\n".join(map(lambda y: f"file '{os.path.join(tempdir, str(y))}.mp4'", range(0, x))))
subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", os.path.join(tempdir, "list.txt"), "-c", "copy", os.path.join(tempdir, "result.mp4")])
