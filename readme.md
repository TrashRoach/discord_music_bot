### **New machine install**
```shell
sudo apt update
sudo apt upgrade
sudo apt install python3-dev python3-venv ffmpeg

sudo adduser discord_music_bot
sudo usermod -aG sudo discord_music_bot
```


### **Music bot service**
```shell
sudo ln -s "$PWD/discord_music_bot/config/systemd/music_bot.service" /etc/systemd/system/
sudo systemctl daemon-reload
```
***
Service actions without sudo (use with caution!)
```shell
sudo touch /etc/sudoers.d/discord_music_bot
# content
discord_music_bot ALL= NOPASSWD: /bin/systemctl restart music_bot
discord_music_bot ALL= NOPASSWD: /bin/systemctl stop music_bot
discord_music_bot ALL= NOPASSWD: /bin/systemctl start music_bot
```