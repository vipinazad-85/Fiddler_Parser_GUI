#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7

from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import tkinter as tk
import json
import os
import zipfile
import xml.etree.ElementTree as ET
import datetime
import shutil

#Defining the path where saz file will be unzipped and par.txt file will be placed.
pathz = "/tmp/fiddler/"
pathraw = pathz+"raw/"
parsed = pathz+"par.txt"

if os.path.exists(pathraw):
    shutil.rmtree(pathraw)

#Defining the function to create popup message if user select file other than har/saz.
def popup_message(msg):
    popup = Tk()
    popup.wm_title("!")
    label = ttk.Label(popup,text=msg)
    label.pack(side='top', fill = 'x', pady=10)
    Bt = ttk.Button(popup, text="Okay", command=popup.destroy)
    Bt.pack()
    popup.mainloop()


#defining function to parse saz file further and pull the require info and put it in par.txt which will be present on window.
def saz_parser(y):
    if os.path.exists(parsed):
        os.remove(parsed)

    for i in y:
        doc = ET.parse(pathraw+i)
        docroot = doc.getroot()
        st = docroot[0].attrib['ClientBeginRequest'][11:24]
        st = datetime.datetime.strptime(st, '%H:%M:%S.%f')
        et = docroot[0].attrib['ServerDoneResponse'][11:24]
        if len(et) < 11:
            et = datetime.datetime.strptime(et, '%H:%M:%S')
            continue
        else:
            et = datetime.datetime.strptime(et, '%H:%M:%S.%f')
            tt = et - st
        tt = tt.total_seconds()
        if int(float(tt)) >= 5:
            with open(parsed, 'a') as h:
                print("sid : " + str(i)[:4], file=h)
                print("Time lines ==> \nClientConnected:{0} \nClientBeginRequest :{1} \nGotRequestHeaders: {2} \nClientDoneRequest: {3} \nGatewayTime: {4} \nTCPConnectTime: {5} \nHTTPSHandshakeTime : {6} \nServerConnected: {7} \nFiddlerBeginRequest: {8} \nServerGotRequest: {9} \nServerBeginResponse: {10} \nGotResponseHeaders: {11} \nServerDoneResponse: {12} \nClientBeginResponse: {13} \nClientDoneResponse: {14}" .format(docroot[0].attrib['ClientConnected'], docroot[0].attrib['ClientBeginRequest'], docroot[0].attrib['GotRequestHeaders'], docroot[0].attrib['ClientDoneRequest'], docroot[0].attrib['GatewayTime'], docroot[0].attrib['TCPConnectTime'], docroot[0].attrib['HTTPSHandshakeTime'], docroot[0].attrib['ServerConnected'], docroot[0].attrib['FiddlerBeginRequest'], docroot[0].attrib['ServerGotRequest'], docroot[0].attrib['ServerBeginResponse'], docroot[0].attrib['GotResponseHeaders'], docroot[0].attrib['ServerDoneResponse'], docroot[0].attrib['ClientBeginResponse'], docroot[0].attrib['ClientDoneResponse']), file=h)
                print("Total Time {0} sec".format(int(float(tt))), file=h)
                File = i.replace('m.xml', 'c.txt')

                with open(pathraw+File, 'rb') as f:
                    for l in f:
                        s = l.decode('ascii', errors='ignore')
                        if re.search("https:", s):
                            print(s.rstrip("\n"), file=h)
                        if re.search("Cache-Control", s):
                            print(s.rstrip("\n"), file=h)
                Files = i.replace('m.xml', 's.txt')

                with open(pathraw + Files, 'rb') as f:
                    c = 0
                    for l in f:
                        l = l.decode('ascii', errors='ignore')
                        if re.search("Adf-Context-Id:", l) or re.search("X-ORACLE-DMS-ECID:", l):
                            c += 1
                            if c <= 1:
                                print(l.rstrip("\n"), file=h)
                        if re.search("Time-out", l):
                            print(l.rstrip("\n"), file=h)
                print("\n", file=h)


#Defiing function to parse saz type file below function will unzip the saz file and create list of session file only for oraclecloud url amd call saz_parser(y) for parse only these sessions.
def saz_par(filename):
    with zipfile.ZipFile(filename) as zip_ref:
        zip_ref.extractall(pathz)
        x = [i for i in os.listdir(pathraw) if i.endswith("c.txt")]
        y = []
        print(filename)
        for i in x:
            with open(pathraw+i, 'rb') as f:
                c = 0
                for line in f:
                    if "oraclecloud" in line.decode('ascii', errors='ignore'):
                        c += 1
                        if c <= 1:
                            o = i.replace('c.txt', 'm.xml')
                            y.append(o)
    saz_parser(y)


#Defining a function to parse har file and printing the details for requests taking more than 5 sec to file parsed.
def har_par(filename):
    with open(filename, 'r', encoding='utf-8-sig') as f:
        data = json.loads(f.read())
        data1 = data[u'log'][u'entries']
        l = len(data1)
        try:
            os.remove(parsed)
        except FileNotFoundError:
            pass
        for i in range(l):
            with open(parsed, 'a') as h:
                if int(data1[i][u'time']) > 5000 and "oraclecloud" in data1[i][u'request'][u'url']:
                    print("Time taken {0} sec ".format(data1[i][u'time'] / 1000), file=h)
                    print("URL : " + data1[i][u'request'][u'url'], file=h)
                    c = 0
                    for k in data1[i][u'response'][u'headers']:
                        if k[u'name'] == "X-ORACLE-DMS-ECID" or k[u'name'] == "Adf-Context-Id":
                            c += 1
                            if c <= 1:
                                print ("ECID : " + k[u'value'], file=h )
                        if k[u'name'] == "Date":
                            print ("Date : " + k[u'value'], file=h)
                        if k[u'name'] == "X-FA-CARD-ID":
                            print ("X-FA-CARD-ID : " + k[u'value'], file=h)
                    print("Status : " + str(data1[i][u'response'][u'status']), file=h )
                    print("Status Text : " + str(data1[i][u'response'][u'statusText']), file=h)
                    try:
                        print("ADF CTRL STATE ID : " + [a for a in data1[i][u'request'][u'queryString'] if a[u'name'] == "_adf.ctrl-state"][0][u'value'], file=h)
                    except IndexError:
                        pass
                    print("\n", file=h)
        if os.stat(parsed).st_size == 0:
            with open(parsed, 'a') as h:
                print("could not found any request taking more than 5sec",file=h)



#Defining f_name() function, this function will provide the functionality to browse and select a file and get the complete dir path of the file in the
#system. once the path of the filename captured other functions saz_par(filename) for saz and har_par(filename) for gar been called to do parsing for
#same. if wrong file selected then it will call the function popup_message(msg) to create a another window to show the warning message.
turn = 0
def f_name():
    global turn
    filename = filedialog.askopenfilename(initialdir="/", title="Select A File")
    name = filename.split("/")
    l = len(name)
    n = name[l-1]

    #Calling the other function as per selected file extention.
    if filename[-3:] == "saz":
        saz_par(filename)
    elif filename[-3:] == "har":
        har_par(filename)
    else:
        msg = "you choose a wrong type of file please select har/saz"
        popup_message(msg)

    text2 = open(parsed).read()
    t = Text(notebook, height=40, width=140)
    t.delete(1.0, "end")
    t.insert(END,text2)
    notebook.add(t, text=n)
    notebook.select(turn)
    turn += 1


#Starting the main window
root = Tk()
root.title("Fiddler Parser ") # Defining the window title here
root.geometry('1200x600+150+150') # Defining window size and location on screen
notebook = ttk.Notebook(root)  # Defining notebook widget to enable tab functionality
ttk.Button(root, text="click me to select the file ", command=f_name).pack() #Defining click button and calling f_name() function
notebook.pack(side='left') # Attaching notebook object to main window
root.mainloop()
