import pandas as pd
import numpy as np
import streamlit as st
import hashlib
import cv2
from PIL import Image
import sqlite3
from streamlit_lottie import st_lottie
import requests
import face_recognition
from twilio.rest import Client
import datetime
import os

account_sid = 'AC8d5d31a229913e27f860f83a91c2eea5'
auth_token = '8d744332689bb2103a8dae342ae4ccf1'
client = Client(account_sid, auth_token)

conn = sqlite3.connect('database.db')
c = conn.cursor()

face_casecade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

parties = ['BJP', 'INC', 'AAP', 'NOTA']

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def create_usertable():
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT, email TEXT,DOB TEXT,Gender TEXT,Aadr TEXT, voterid TEXT, mobilenumber TEXT, time TEXT)')

def add_userdata(username,password,email,dob,gender,aadr,voterid,mobilenumber, time):
	c.execute('INSERT INTO userstable(username,password,email,dob,gender,aadr,voterid,mobilenumber,time) VALUES (?,?,?,?,?,?,?,?,?)',(username,password,email,dob,gender,aadr,voterid,mobilenumber, time))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data

def animation(value):
    r = requests.get(value)
    if r.status_code != 200:
        return None
    return r.json()

def plot(val):
    st_lottie(
            val,
            speed=1,
            reverse=False,
            loop=True,
            quality="High",
            #renderer="svg",
            height=400,
            width=-900,
            key=None,
        )


def vote_table():
    c.execute('CREATE TABLE IF NOT EXISTS votetable(username TEXT,party TEXT)')

def add_vote(username,party):
    c.execute('INSERT INTO votetable(username,party) VALUES (?,?)',(username,party))
    conn.commit()

def get_votes(party):
    c.execute('SELECT * FROM votetable WHERE party = ?',(party,))
    data = c.fetchall()
    return data

def get_mobilenumber(username,password):
    c.execute('SELECT mobilenumber FROM userstable WHERE username =? AND password = ?',(username,password))
    data = c.fetchall()
    return data

def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data

def get_time(username,password):
    c.execute('SELECT time FROM userstable WHERE username =? AND password = ?',(username,password))
    data = c.fetchall()
    return data

def main():
    st.title("Smart Voting System using Facial Recognition")
    menu = ["AdminPage", "Login", "SignUp"]
    choice = st.sidebar.selectbox("Menu", menu)
    anim = animation('https://assets7.lottiefiles.com/packages/lf20_MtN0BG.json')
    plot(anim)

    if choice == "AdminPage":
        st.subheader("Admin Page")
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.checkbox("Login"):
            if username == 'admin' and password == 'admin':
                st.success("Logged In as {}".format(username))
                st.subheader("Select Action")
                opt = st.selectbox("Action", ["View All Users", "View All Votes"])
                if opt == "View All Users":
                    result = view_all_users()
                    df = pd.DataFrame(result,columns=['Username','Password','email','DOB','Gender','Aadr','voterid','mobilenumber','image','time'])
                    st.dataframe(df)
                elif opt == "View All Votes":
                    part = st.selectbox("Party", parties)
                    result = get_votes(part)
                    df = pd.DataFrame(result,columns=['Username','Party'])
                    st.dataframe(df['Username'])
            else:
                st.warning("Incorrect Username/Password")

    elif choice == "Login":
        st.subheader("Login Section")

        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.checkbox("Login"):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username,check_hashes(password,hashed_pswd))
            if result:
                st.write("Logged In as {}".format(username))
                img = st.camera_input("Image", key="image")
                if img is not None:

                    img = Image.open(img)
                    img = np.array(img)
                    filename = '{}.jpg'.format(username+'1')
                    cv2.imwrite(filename, img)

                    frst = cv2.imread('{}.jpg'.format(username))
                    frst = cv2.cvtColor(frst, cv2.COLOR_BGR2RGB)
                    frst = face_recognition.face_encodings(frst)[0]   

                    sec = cv2.imread('{}.jpg'.format(username+'1'))
                    sec = cv2.cvtColor(sec, cv2.COLOR_BGR2RGB)
                    sec = face_recognition.face_encodings(sec)[0]

                    res = face_recognition.compare_faces([frst], sec)

                    if res[0] == True:
                        st.success("Face Matched")
                        os.remove('{}.jpg'.format(username))
                        os.remove('{}.jpg'.format(username+'1'))
                        mob = get_mobilenumber(username,check_hashes(password,hashed_pswd))
                        mob = mob[0][0]
                        mob = '+91'+mob

                        otp = get_time(username,check_hashes(password,hashed_pswd))
                        otp = otp[0][0]
                        otp = otp.split(':')
                        min = otp[1]
                        sec = otp[2].split('.')
                        otp = min+sec[0]
                        otp = 2*int(otp)

                        message = client.messages.create(
                                    body='Your OTP for voting system is '+str(otp),
                                    from_='+12563305069',
                                    to=mob
                                )

                        if message.sid:
                            otp1 = st.text_input("Enter OTP that you have received")
                            if st.checkbox("Verify"):
                                if otp1 == str(otp):
                                        st.success("OTP Verification Successfull")
                                        party = st.selectbox("Select Party", parties)
                                        if st.button("Vote"):
                                            if party == 'NOTA':
                                                st.warning("You have selected NOTA")
                                                st.warning("Your vote will not be counted")
                                                st.snowflake()
                                            else:
                                                st.success("You have selected {}".format(party))
                                                st.balloons()
                                            
                                            vote_table()
                                            add_vote(username,party)
                                            
                                else:
                                        st.warning("Incorrect OTP")
                    else:
                        st.warning("Face Not Matched ")


            else:
                st.warning("Incorrect Username/Password")
            
    elif choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        email = st.text_input("Email")
        dob = st.number_input("Year of Birth", max_value=2005, value=1999, step=1)
        gender = st.selectbox("Gender",['Male','Female','Others'])
        aadr = st.number_input("Aadhar Number (12 digits)", max_value=999999999999, value=123456789012, step=1)
        voterid = st.text_input("Voter ID")
        mobilenumber = st.number_input("Mobile Number (10 digits)", max_value=9999999999, value=1234567890, step=1)
        st.error("Enter a valid mobile number as you will receive OTP on this number while voting")
        image = st.camera_input("Image", key="image")
        time = datetime.datetime.now()
        if image is not None:
            # save the image to the images folder using opencv
            filename = "{}.jpg".format(new_user)
            image = Image.open(image)
            image = np.array(image)
            cv2.imwrite(filename, image)

        if st.button("Signup"):
            create_usertable()
            hashed_new_password = make_hashes(new_password)
            add_userdata(new_user,hashed_new_password,email,dob,gender,aadr,voterid,mobilenumber,time)
            st.success("You have successfully created a valid Account for voting")
            st.info("Go to Login Menu to login and vote")

if __name__ == '__main__':
    main()