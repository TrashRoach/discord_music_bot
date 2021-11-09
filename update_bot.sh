git checkout master
git reset HEAD --hard
git clean -fd
git pull

venv/bin/pip install -r requirements.txt
if screen -list | grep -q "music_bot"; then
  screen -S music_bot -X quit
fi
screen -S music_bot venv/bin/python3 run.py