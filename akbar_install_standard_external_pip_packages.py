import subprocess

cmd = """
pip install --upgrade pip
pip install -U pip setuptools wheel
pip install -U spacy
python -m spacy download en_core_web_sm
pip install regex
pip install Scrapy

""".strip().split('\n')

cmd = [command.split() for command in cmd]

for command in cmd:
    subprocess.run(command)