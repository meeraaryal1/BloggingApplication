# Import Required Kivy and KivyMD Libraries
import base64
import re
import sqlite3
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from plyer import filechooser

# Creating Required Tables
blogging_db = "blogging_db.db"

# blob= 'Binary Large Object to upload images and files'
blob_path = ""

# Query to create table blog
create_blog = "CREATE TABLE IF NOT EXISTS blog (blogid INTEGER PRIMARY KEY," \
              "time DATETIME DEFAULT CURRENT_TIMESTAMP, subject TEXT, content TEXT," \
              "file BLOB, username TEXT, isprivate Integer)"

# Query to create table users
create_users = "CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY," \
               "password TEXT, isadmin Integer)"

# Query to insert first user(i.e admin) in the users table
first_user = "INSERT OR IGNORE INTO users (username, password, isadmin) VALUES (?,?,?)"

# Query to insert blog in the blog table
post_blog = "INSERT INTO blog (subject, content, file, username, isprivate) VALUES (?,?,?,?,?)"

# Query to insert users in the users table
register_user = "INSERT INTO users (username, password, isadmin) VALUES (?,?,?)"

# log in credentials for admin
admin_username = "admin@gmail.com"
admin_password = base64.b64encode("Admin@123".encode("utf-8"))

# regular expression to check email and password valididty
regex_email = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
regex_password = '[A-Z]', '[a-z]', '[0-9]'

# variable declared to make the post private or public, by default post will be public
isprivate = 0


# Converting the file and Images to binary large object(BLOB) to store it on the database
def convert_to_binary(filename):
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData


def write_data(data, filename):
    with open(filename, 'wb') as file:
        file.write(data)
        toast("Attachment downloaded!")

# Checking the validity of the email
def check_email_valid(email):
    if re.search(regex_email, email):
        return True

# Checking the password strength
def check_password_strength(password):
    if len(password) >= 8 and all(re.search(r, password) for r in regex_password):
        return True


# Creating the Blogging Application
class BloggingApp(MDApp):
    def __init__(self=None, **kwargs):
        self.title = "BLOGGING APP"
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Red"

        # Connection to the database
        conn = sqlite3.connect(blogging_db)

        # Create a Cursor
        c = conn.cursor()

        # Create table for Blog
        c.execute(create_blog)

        # Create table for Users
        c.execute(create_users)

        # Insert first user i.e admin
        c.execute(first_user, (admin_username, admin_password, 1))

        # Commit changes/insert,update
        conn.commit()

        # Close Connection
        conn.close()

        # handeling media and file upload
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            preview=True,
        )

    def on_checkbox_active(self, checkbox, value):
        global isprivate
        if value:
            isprivate = 1
        else:
            isprivate = 0

    def file_manager_open(self):
        self.file_manager.show('/')
        self.manager_open = True

    def select_path(self, path):
        global blob_path
        blob_path = path
        self.exit_manager()
        toast(path)

    def exit_manager(self):
        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device..'''
        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True


class HomeScreen(MDScreen):
    def post_text(self):
        conn = sqlite3.connect(blogging_db)
        c = conn.cursor()
        username = self.username.text
        password = self.password.text
        if username == "" or password == "":
            toast("Please enter login credentials!")
        else:
            # Executing query to fetch the given username
            c.execute("SELECT * FROM users WHERE username = ?", (username,))

            # Fetching Only Single Row to check if there is data in table
            user_data = c.fetchone()

            if user_data is None:
                # toast function will show the popup message
                toast("Invalid Username!")
            else:
                if base64.b64decode(user_data[1]).decode("utf-8") == password:
                    subject = self.subject.text
                    content = self.content.text
                    if subject == "" or content == "":
                        toast("Please enter title and content!")
                    else:
                        if isprivate == 1:
                            content = base64.b64encode(content.encode("utf-8"))
                        if blob_path != "":
                            blob = convert_to_binary(blob_path)
                            toast("Attachment uploaded!")
                        else:
                            blob = "NULL"
                        # Insert data/blog to DB
                        c.execute(post_blog, (subject, content, blob, username, isprivate))

                        # Committing Changes
                        conn.commit()
                        # Using Rowid to determining the number of the blog that has been uploaded
                        last_blog_id = c.execute("SELECT rowid from blog order by ROWID DESC limit 1").fetchone()
                        toast("Post successful! Blog #" + str(last_blog_id))
                else:
                    toast("Invalid password!")
        conn.close()


class ListScreen(MDScreen):
    def on_enter(self, *args):
        conn = sqlite3.connect(blogging_db)
        c = conn.cursor()
        c.execute("SELECT * FROM blog")

        # counting all the blogs
        count = c.fetchall()
        for c in reversed(count):
            blog_id = c[0]
            title = c[2]
            blog_str = "BLOG #" + str(blog_id)
            self.ids.post_list.add_widget(MDLabel(text=blog_str))
            self.ids.post_list.add_widget(MDLabel(text=title))

        # commiting the changes and closing the connection
        conn.close()

    def on_leave(self, *args):
        self.ids.post_list.clear_widgets()


class PostScreen(MDScreen):
    def view_post(self):
        username = self.username.text
        password = self.password.text
        blog_number = self.blog_number.text
        conn = sqlite3.connect(blogging_db)
        c = conn.cursor()
        if blog_number != "":
            post = c.execute("SELECT * from blog WHERE rowid = ?", (blog_number,)).fetchone()
            user_data = c.execute("SELECT * FROM users WHERE username= ?", (post[5],)).fetchone()
            post_privacy = post[6]
            if post_privacy == 1:
                if username != "" or password != "":
                    if username == user_data[0] and password == base64.b64decode(user_data[1]).decode("utf-8"):
                        self.ids.post_data.add_widget(ViewLabel(text="Blog No."))
                        self.ids.post_data.add_widget(MDLabel(text=str(post[0])))
                        self.ids.post_data.add_widget(ViewLabel(text="Subject"))
                        self.ids.post_data.add_widget(MDLabel(text=post[2]))
                        self.ids.post_data.add_widget(ViewLabel(text="Content"))
                        self.ids.post_data.add_widget(MDLabel(text=(base64.b64decode(post[3])).decode("utf-8")))
                        if post[4] != "NULL":
                            write_data(post[4], "Blog" + str(post[0]) + "Attachment")
                    else:
                        toast("Invalid login details!")
                else:
                    toast("This is a private post, please enter login details!", 5)
            else:
                self.ids.post_data.add_widget(ViewLabel(text="Blog #"))
                self.ids.post_data.add_widget(MDLabel(text=str(post[0])))
                self.ids.post_data.add_widget(ViewLabel(text="Subject"))
                self.ids.post_data.add_widget(MDLabel(text=post[2]))
                self.ids.post_data.add_widget(ViewLabel(text="Content"))
                self.ids.post_data.add_widget(MDLabel(text=post[3]))
                if post[4] != "NULL":
                    write_data(post[4], "Blog" + str(post[0]) + "Attachment")
        else:
            toast("Invalid blog number!")
        conn.close()

    def delete_post(self):
        username = self.username.text
        password = self.password.text
        blog_number = self.blog_number.text
        conn = sqlite3.connect(blogging_db)
        c = conn.cursor()
        if username != "" or password != "" or blog_number != "":
            user_data = c.execute("SELECT * FROM users WHERE username = ? AND isadmin = 1", (username,)).fetchone()
            if user_data is None:
                toast("Invalid username or not an admin user!")
            else:
                if username == user_data[0] and password == base64.b64decode(user_data[1]).decode("utf-8"):
                    c.execute("DELETE FROM content WHERE blogid = ?", (blog_number,))

                    # Comitting Changes
                    conn.commit()
                    toast("Post deleted!")
                else:
                    toast("Wrong password!")
        else:
            toast("Please enter the correct login Credentials!")

        # Closing database connection
        conn.close()

    def on_leave(self, *args):
        self.ids.post_data.clear_widgets()


class RegistrationScreen(MDScreen):
    def register(self):
        username = self.username.text
        password = self.password.text
        if username != "" and password != "":
            if check_email_valid(username) is True:
                if check_password_strength(password) is True:
                    encrypted_password = base64.b64encode(password.encode("utf-8"))
                    conn = sqlite3.connect(blogging_db)
                    c = conn.cursor()
                    c.execute(register_user, (username, encrypted_password, 0))
                    conn.commit()
                    conn.close()
                    toast("User Registration successful!")
                else:
                    toast(
                        "Please enter a strong password! (Minimum 8 character, 1 lowercase, 1 uppercase and 1 digit)",
                        5)
            else:
                toast("Invalid email address!")
        else:
            toast("Please enter the correct login credentials!")


# Changing the Screen
class WindowManager(ScreenManager):
    def change_screen(self, screen):
        self.current = screen


# ViewLabel is referencing MDLabel
class ViewLabel(MDLabel):
    pass


# Running the Blogging Application
if __name__ == '__main__':
    BloggingApp().run()
