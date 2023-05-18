# My Personal Blog

This is a full-functioning blog developed using Python and Flask. The blog has basic functionalities such as authentication, registration, and posting of articles and comments.\
The admin can create, edit, and delete posts, while other registered users can view and comment on posts created by the admin.\
The first user registered in the database is automatically given admin privileges (So you have to be careful 😉).

## Getting Started

To get started with my Blog, you will need to have Python 3.5 or above installed on your computer. You will also need to clone this repository to your local machine.

```
git clone https://github.com/yourusername/flask-blog.git
```

After cloning the repository, navigate to the project directory and create a virtual environment. Activate the virtual environment and install the required dependencies using the following commands:

```
cd flask-blog
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuring the Application

Before you can run my Blog, you will need to configure the application by creating a `.env` file in the root directory. The `.env` file should contain the following environment variables:

```
APP_SECRET=<your_app_secret_key>
LINKED-IN=<your_linkedin_url>
GIT-HUB=<your_github_url>
TWITTER_=<your_twitter_url>
NAME=<your_name>
RESUME=<your_online_resume>
MY_EMAIL=<your_email>
EMAIL_PASSWORD=<your_password>
OTHER_EMAIL=<other_emails_you_may_have>
SECOND_EMAIL=<other_emails_you_may_have>
DATABASE=<your_database_url>
```

- `APP_SECRET` is a secret key used by Flask to sign session cookies.
- `DATABASE` is the name of your database file.

## Running the Application

To run my Blog, navigate to the project directory and activate the virtual environment using the following command:

```
source venv/bin/activate
```

Then, start the Flask application using the following command:

```
flask run
```
If you make use of PyCharm or other python IDE, the instructions above may not be necessary. Simply open the project in Pycharm, install requirements and click the "▶️" button in main.py file. I used PyCharm 2022 in developing this blog.\
You can then access the application by navigating to `http://localhost:5000` in your web browser.

## Using the Application

To use my Blog, you simply have to click the home button to access all the articles that the admin has preloaded upfront with or without a user account your account but you will not be able to leave a comment unless you have registered your account. Once you have registered, the app logs you in automatically and your session is created. It logs you out automatically and returns to 'login' page once your user session expires (I set 15 minutes but you can always alter it). While user session is still active, you can not only access posts but comment on them as well. Remember that only the admin has the right to create, edit or delete posts. The app takes active measures to enforce this by hiding these buttons from other users, as well as preventing access to urls responsible for creating, editing or deleting posts. When you clone this app, you'll be creating your database from scratch and so you will have to create the blog posts as an admin. (If I preloaded the posts, the app will only recognise me the admin, which means you'll never have full access to the app because you don't know my password). 

## Contributing

If you would like to contribute to this project, please submit a pull request. Contributions are always welcome!

## Bugs

Bug reports are always welcome. However, there are none as at the time of this report.
