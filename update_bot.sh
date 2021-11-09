git checkout master
git reset HEAD --hard
git clean -fd
git pull

venv/bin/pip install -r requirements.txt
screen -S music_bot -X quit
screen -S music_bot venv/bin/python3 run.py