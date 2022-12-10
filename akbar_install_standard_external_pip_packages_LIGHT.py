import subprocess

cmd = """
pip install --upgrade pip
pip install regex
pip install Scrapy
""".strip().split('\n')

cmd = [command.split() for command in cmd]

for command in cmd:
    subprocess.run(command)