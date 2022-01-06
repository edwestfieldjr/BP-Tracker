# BP Monitor 

A Python/Flask/SQL-based blood pressure reading database. 

## For Testing Purposes Only 
###Not Recommended for Actual Patient Information 

This demonstration web-based application has yet to be evaluated for compliance with current patient privacy laws (HIPAA, PHIPA, DPA, GDPR, etc.) It is not advised for use with actual patient information. For the tiem being, please enter only ficticuous names and identifying information when using this database. 

## Live Demo

https://bp-tracker-2021.herokuapp.com/

### How to use: 

* Click 'Welcome, Guest' to resister a new login account; 
* Create a patient profile ('Add Patient' in the 'Patients' menu); 
  * **THIS IS A TESTING DEMO: Do not add actual patient information (only use fictitious information);**
  * _Patient's 'Date of Birth' must be entered in 'datetime.date' format, e.g.: 'yyyy-mm-dd' (the form defaults to current time)_
* Go to the patient's name in the 'Patients' menu;
* In the patient's 'Blood Pressure Reading Log' page, click 'Add Reading' to a blood pressure reading;
* Add Blood Pressure reading information in the form; 
  * _'Time of Reading' must be entered in 'datetime.datetime' format, e.g.: 'yyyy-mm-dd hh-mm-ss'_
* Click 'Add Update Reading';
* Use 'Edit' and 'Delete' buttons to modify each entry.

### Database Purge and Deletion Advisory 

This demonstration version of this web-based application currently uses a Heroku Postgres 'Hobby Tier' SQL database that may be periodically updated and purged RESULTING IN DATA LOSS. If you are unable to log in, or any of your data is missing, it may be a result of your account being purged; simply create a new account and start over. Please do not use any real or sensitive data in this version.

## MIT License

Copyright © 2021 [Edward Francis Westfield Jr.](https://www.edwestfieldjr.com/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
