# Homebank-online-purse
A Django app to manage your daily purse and export data to Homebank app

Well, here I go again. The main idea for this software is to be a simple transaction recorder for your daily purse expenses. Te aim of this software is to produce an output file to be imported directly by Homebank application.

A bit of history:  

I've used Homebank for years. At first time, I used to write down a list of my daily expenses, and periodiaclly write on the app account. Some times there were a lots of records and was tedious and non error-free.  
After that, I tried a CSV editor app, so I write my expenses directly on an blanked exported CSV file. That was very interesting. Because I sysnced it with Dropbox and onli informed a few fields. But Androids versions updated and stopped working for my wife. :(  it also didn't was error-free for input data and I couldn't fill categories...  It was good, but not enough.  

By now, I still use a CSV editor, and my wife uses a raw texfile with 3 fields comma separated. So I can easily transform it into a CSV with the help of an spreadsheet. But one again, it is not input data error free.  

After learning some basics on Django I thought it could be nice to have a personal app on a raspberrypi server to manage my expenses and generate a CSV file for Homebank.

### Features:  
Starting with:  
 - user login for personal data.
 - easy input data in forms.
 - it marks exported data and non exported data.
 - it tells you how many do you have at this time.
 - Export to Homebank CSV.
 - use SQlite database.
 
