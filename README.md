# Loan Item API

## Overview

A REST API that can be used as a back-end for a physical item loan system. Example uses would be hiring or borrowing
items such as sports equipment, power tools or books. It can be used with any UI that has a REST client. A typical
example UI, would be mobile phone app. In this scenario, the app could be scanning QR stickers affixed to loanable items
to make the job of looking up and loaning items quick and convenient. A different scenario would be a web-based
kiosk where users are able to login and interact with their own-list of loaned items.

The API supports two different modes of operation, self-service and admin-operated. The self-service
use-case would be for a trusted environment where users can borrow and return items unsupervised. In this
scenario, the user would log into to the system and marks items as borrowed or returned using their own account.

In the admin-operated mode, only administrators could associate or dis-associated items with a users account.
The use-case here would be a physical kiosk where staff are administrators and would need to manage the loaning-out
of items.

## Usage

### Modes and User roles

To initialise the system on a blank database, a user called "admin" is created. This user has a role of
"admin" and the password will be set via the "ADMIN_PASSWORD" environment variable otherwise will default to "admin".
The admin user can "promote" other users to the "admin" role. The default mode is admin-operated but can be
changed by the "MODE" environment variable.


| User role |  Mode | What can the role do |
|---|---|---|
| n/a | all | A non-autherised REST call can create any number of regular users. | 
|regular | self-service | Loan un-loaned items against their own account. Un-loan items they have loaned to themselves. Change their own details. Remove themselves. View items they have loaned.|
|regular | admin-operated | Change their own details. Remove themselves. View items they have loaned.|
|admin |all| Can make any change to users or loan items apart from removing or changing the role of the initial "admin" user.  |



### Valid requests


| Action |  HTTP Method  | URL  |  Request body | Header  |
|---|---|---|---|---|
| Register user  | POST  | /users  |```{"username": "bob", "password": "password", "phone": "+441234567890"}```  |   |
| Login | POST  |  /login |  ```{"username": "bob", "password": "password"}```  |   |
| Get all users  | GET  |  /users |   | "access-token": token  | `
| Get Bob's user record  | GET  |  /users/bob |   | "access-token": token  | `
| Change Bob's password  | PUT  |  /users/bob | ```{"password": "password2"}```  | "access-token": token  |
| Change Bob's phone number  | PUT  |  /users/bob | ```{"phone": "+441234567891"}```  | "access-token": token  |
| Delete user Bob  | DELETE  |  /users/bob |   | "access-token": token  | 
| Create a loan item entry  | POST  |  /loan-items |  ```{"id": "123e4567-e89b-12d3-a456-426614174000", "description": "wheelbarrow"}``` | "access-token": token  | 
| Get loan item with id 123e4567-e89b-12d3-a456-426614174000 | GET  |  /loan-items/123e4567-e89b-12d3-a456-426614174000 |   | "access-token": token  | 
| Loan item 123e4567-e89b-12d3-a456-426614174000 to Bob | PUT  |  /loan-items/123e4567-e89b-12d3-a456-426614174000 | ```{"loanedto": "bob"}```  | "access-token": token  | 
| Get all loan items  | GET  |  /loan-items |   | "access-token": token  | 
| Pagination for getting all loan items. This query would return the 20 loan item starting with the 100th item.  | GET  |  /loan-items?limit=20&offset=100  |   | "access-token": token  | 
| Get all loan items loaned to Bob | GET  |  /loan-items?loanedto=bob |   | "access-token": token  | 
| Get all loan items where loan-item description contains "drills" | GET  |  /loan-items?contains=drills |   | "access-token": token  | 
| Get all loan items loaned to Bob where loan-item description contains "boots" | GET  |  /loan-items?loanedto=bob&contains=boots |   | "access-token": token  | 
| Delete loan item with id 123e4567-e89b-12d3-a456-426614174000  | DELETE  |  /loan-items/123e4567-e89b-12d3-a456-426614174000  |   | "access-token": token  | 
| Change mode to self-service  | PUT  |  /mode  | ```{"mode": "self-service"}```  | "access-token": token  | 
| Change mode to admin-operated  | PUT  |  /mode |  ```{"mode": "admin-operated "}```  | "access-token": token  | 
| Get mode  | GET  |  /mode |   | "access-token": token  | 

### Expected return values

Apart from unexpected 500 errors, all requests will return a json object with one or more of the following keys:

| JSON Key |  Description  | Example |
|---|---|---|
|auth_token| Returned by /login on a successful login. Passed to most other calls as the access-token header.|```{'auth_token': 'eyJ0eXAiOi'}``` (truncated example) |
|message| Informational returned by successful deletions and password changes.|```{"message": "Password successfully changed."} ```|
|error| Returned for all 400 errors. Can be generated by any request| ```{"error": "User not found."}```|
|loan-item| Returned by all calls to /loan-item/:id. Value is a single Loan object. | ```{"loan-item": {"id": "123e4567-e89b-12d3-a456-426614174000", "description": "wheelbarrow","loanedto": "bob"}}``` |
|loan-items| Returned by all calls to /loan-item (including those with query parameters). Value is a list of loan-item objects. | ```{"loan-items": [{"id": "123e4567-e89b-12d3-a456-426614174000", "description": "wheelbarrow","loanedto": "bob"},{"id": "123e4567-e89b-12d3-a456-426614174001", "description": "drill","loanedto": "sally"}]}``` |
|user| Returned by all calls to /user/:username, apart from when a password is changed. Value is a single user object.|```{'user': {'phone': 800, 'role': 1, 'username': 'bob'}}``` |
|users| Returned by all calls to /users. Value is a list of user objects. | ```{'users': [{'phone': "+441234567890", 'role': 3, 'username': 'admin'}, {'phone': "+441234567890", 'role': 1, 'username': 'bob'}]}```|
|mode| Returned by all calls to /mode. Value is either self-service or admin-operated. |```{"mode": "self-service"}```|


## Installation

To install and run you will need Docker. Follow these steps to run the API:

1. In the ```docker-compose.yml``` change the following environment variables:
   * ```DATABASE_URL``` - This is a sqlalchemy URL setup for the system test PostgreSQL database. Point this at the database of your
   choice (PostgreSQL has been tested)
   * ```SECRET_KEY``` - Pick a unique key for encoding JWT tokens.
   * ```ADMIN_PASSWORD``` - Pick an initial password for the "admin" user
1. In the ```docker-compose.yml```, remove the postgres service unless using (used for system testing)
1. Open a terminal in this directory
1. Run ```docker-compose build```
1. Run ```docker-compose up -d```

## Implementation details

This system has been implemented in Python using Flask for the REST API and a relational database
as the persistence layer (PostgreSQL or SQLite). Each HTTP request causes a user manager (Users) and Loan
manager (Loans) to be instantiated. These objects handle the bulk of the request logic and interactions with 
the database.

The user manager class (Users) does the following:

* Handles telling the Loan manager who is logged in
* Sets up the database session
* Interacts with User data in the database
* Protects the wrong user accessing another user's User data

The Loan manager class (Loans) does the following:
 
* Protects the wrong user accessing another user's Loan data
* Interacts with Loan data in the database

For authentication the system uses JWT tokens which contain an expiry date and the users's username.
On login, this token is returned back to the client. Every other call will use this
token (provided in the header).

All request logic (apart from login) are run within a eval_and_respond function. This does the job
of running the functions required by the request inside a try block. This handling on this block converts internal
exceptions to HTTP errpr responses. This way, all the error handling can be managed in one place.

## How to run the tests

To run the all tests you will need Python 3.7 and Docker. Follow these steps to run the tests:

1. Open a terminal in this directory
1. Run ```python3 -m venv venv```
1. Run ```. venv/bin/activate```
1. Run ```pip install -r requirements.txt```
1. Run ```python -m unittest discover src```. This will run all the unit tests.
1. Run ```docker-compose build```
1. In a separate terminal in this directory, run ```docker-compose up``` and wait for no more output from that terminal.
   Leave that terminal open.
1. Run ```python -m unittest system_test.py```. This will run all the system tests.
1. In the terminal running docker-compose hit ctrl-c.




