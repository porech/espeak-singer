import sys, os, requests, tempfile, shutil, subprocess
from bs4 import BeautifulSoup
from transliterate import translit

"""
First argument: link to lyrics from testietraduzioni.it , i.e. https://www.testietraduzioni.it/lyrics/mille-fedez/
Second argument: language , i.e. 'en', or https://detectlanguage.com/ API key
Third argument: output file path, i.e. mille.mp4
"""

if len(sys.argv) < 4:
    print(f"Usage: python {sys.argv[0]} lyric_url language-or-api-key output.mp4")
    sys.exit(1)

lyric_url = sys.argv[1]
if len(sys.argv[2]) == 2:
    language = sys.argv[2]
    language_api_key = None
else:
    language = None
    language_api_key = sys.argv[2]
output = sys.argv[3]

def txt_file(path):
    p_texts = []
    with open(path) as f:
        lines = [line.strip() for line in f.readlines()]
    title = lines[0]
    lines = lines[1:]
    p_text = []
    for line in lines:
        if not line:
            p_texts.append("\n".join(p_text).strip())
            p_text = []
        else:
            p_text.append(translit(line, 'ru', reversed=True).strip())
    p_texts.append("\n".join(p_text).strip())
    return title, p_texts

def testietraduzioni(url):
    p_texts = []
    html = requests.get(lyric_url).text
    soup = BeautifulSoup(html, features="html.parser")

    author_text = soup.find("div", {"class": "lyrics-title"}).find("h3").get_text()
    trimmed_author_text = " ".join(map(lambda t: t.strip(), author_text.split("\n"))).strip()

    title_text = soup.find("div", {"class": "lyrics-title"}).find("div", {"class": "pull-left"}).get_text().strip()

    title = f"{trimmed_author_text} - {title_text}"

    lyrics_div = soup.find_all("div", {"class": "lyric-text"}).pop()
    for p in lyrics_div.find_all("p"):
        p_class = []
        try:
            p_class = p["class"]
        except KeyError:
            pass
        if 'copyright-lyrics-text' in p_class:
            continue
        p_text = translit(p.get_text(), 'ru', reversed=True).strip()
        if p_text.startswith('[') or p_text.endswith(']'):
            continue
        p_texts.append(p_text)
    return title, p_texts

def angolotesti(url):
    p_texts = []
    html = requests.get(lyric_url).text
    soup = BeautifulSoup(html, features="html.parser")

    pathway = soup.find("ul", {"class": "pathway"})
    lis = pathway.find_all("li")
    author_text = lis[4].get_text().strip()
    title_text = lis[8].get_text().strip()

    title = f"{author_text} - {title_text}"

    text_div = soup.find("div", {"class": "testo"})
    for br in text_div.find_all("br"):
        br.replace_with("\n")
    for noselect in text_div.find_all("div", {"class": "user-noselection"}):
        noselect.replace_with("")
    lines = [line.strip() for line in text_div.get_text().strip().split("\n")]
    p_text = []
    for line in lines:
        if not line:
            p_texts.append("\n".join(p_text).strip())
            p_text = []
        else:
            p_text.append(translit(line, 'ru', reversed=True).strip())
    p_texts.append("\n".join(p_text).strip())
    return title, p_texts


def get_language_from_api(text):
    import detectlanguage
    detectlanguage.configuration.api_key = language_api_key
    res = detectlanguage.detect(text)
    reliables = [r for r in res if r['isReliable']]
    if len(reliables) != 1:
        raise Exception(f"Could not determine language: {len(reliables)} reliable matches found")
    return reliables[0]['language']


x = 0
tempdir = tempfile.mkdtemp()
if os.path.isfile(lyric_url):
    title, p_texts = txt_file(lyric_url)
elif "testietraduzioni.it" in lyric_url:
    title, p_texts = testietraduzioni(lyric_url)
elif "angolotesti.it" in lyric_url:
    title, p_texts = angolotesti(lyric_url)
else:
    raise ValueError("unrecoginzed url")
title = f"{title} (performed by espeak)"
print(title)
print(f"Temp folder: {tempdir}")
for x, p_text in enumerate(p_texts):
    joined_path = os.path.join(tempdir, f"{x}")
    speech_text = ". ".join([p_line[0].upper() + p_line[1:] for p_line in p_text.split("\n")]).replace(",.", ".").replace("?.", "?").replace("!.", "!")
    with open(os.path.join(f"{joined_path}.txt"), "w") as f:
        f.write(speech_text)
    print(speech_text)
    if language:
        lang = language
    else:
        lang = get_language_from_api(speech_text)
    print(f"Language: {lang}")
    subprocess.run(["espeak", "-v", lang, "-f", f"{joined_path}.txt", "-w", f"{joined_path}.wav"])
    subprocess.run(["convert", "-size", "1920x1080", "-background", "black", "-bordercolor", "black", "-border", "100x100", "-fill", "white", "-gravity", "Center", f'caption:{p_text}', "-flatten", f"{joined_path}.png"])
    subprocess.run(["ffmpeg", "-loop", "1", "-i", f"{joined_path}.png", "-i", f"{joined_path}.wav", "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", "-shortest", f"{joined_path}.mp4"])

with open(os.path.join(tempdir, "list.txt"), "w") as f:
    f.write("\r\n".join(map(lambda y: f"file '{os.path.join(tempdir, str(y))}.mp4'", range(0, len(p_texts)))))
subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", os.path.join(tempdir, "list.txt"), "-c", "copy", output])
shutil.rmtree(tempdir)
print(title)
