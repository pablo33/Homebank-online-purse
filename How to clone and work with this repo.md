##Setup your HomeBank online Django app

This note will setup your repo:

#Create a working directory and move into it
mkdir git
cd git

#install python3, git, virtualenv
sudo apt-get install git python3 python3.9-venv

#Clone the repo
git clone https://github.com/pablo33/Homebank-online-purse.git
#move into the repo
cd Homebank-online-purse

#setup your virtual environment
python3 -m venv myvenv

#activate your virtual environment
source myvenv/bin/activate

#Update pip and install requirements
python -m pip install --upgrade pip
pip install -r requirements.txt


#hbpurse/settings.py rely on a config file with your environment
# creating your config file, duplicate template file and edit it > fill with your mail provider data (this part is used to send mails)
cp "settings(blank_template).ini" settings.ini
gedit settings.ini

#provide a secret Key
# open this site, and generate one, copy and paste into your settings.ini file
https://djecrety.ir/

#setup your blank database
cp "db(blank).sqlite3" db.sqlite3

#Check for latest database migrations
python manage.py migrate

#Create your superuser (follow the questions)
python manage.py createsuperuser

#run your Django server
python manage.py runserver

#go to admin site and log with your user, delete other users if you want to clean the database
You can enter the Django app with admin and Pa$$w0rD
but please, create and use your own superuser and delete others

http://127.0.0.1:8000/admin

You can enter the app path here: http://127.0.0.1:8000/purse

Thats all. for production use, you need other instructions.
