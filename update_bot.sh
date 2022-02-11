git checkout master
git reset HEAD --hard
git clean -fd
git pull

venv/bin/python -m pip install --upgrade pip setuptools wheel
venv/bin/pip install -r requirements.txt

sudo -S systemctl restart music_bot