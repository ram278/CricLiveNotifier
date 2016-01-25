import getpass
import os
from crontab import CronTab
from bs4 import BeautifulSoup
import urllib2
from xml.dom.minidom import parse, parseString
import sys
from sys import argv
import Foundation
import objc
import AppKit
import subprocess
import pickle
import time
NSUserNotification = objc.lookUpClass('NSUserNotification')
NSUserNotificationCenter = objc.lookUpClass('NSUserNotificationCenter')
tab = CronTab(user=getpass.getuser())
def notify(clear, title, subtitle, info_text, url, delay=0, sound=False, userInfo={}):

    notification = NSUserNotification.alloc().init()
    notification.setTitle_(title)
    notification.setSubtitle_(subtitle)
    notification.setInformativeText_(info_text)
    notification.setHasActionButton_(True)
    notification.setActionButtonTitle_("View")
    notification.setUserInfo_({"action":"open_url", "value":url})
    if sound:
        notification.setSoundName_("NSUserNotificationDefaultSoundName")
    notification.setDeliveryDate_(Foundation.NSDate.dateWithTimeInterval_sinceDate_(delay, Foundation.NSDate.date()))
    center = NSUserNotificationCenter.defaultUserNotificationCenter()
    center.setDelegate_(notification)
    if clear == True:
        NSUserNotificationCenter.defaultUserNotificationCenter().removeAllDeliveredNotifications()
    else:
        NSUserNotificationCenter.defaultUserNotificationCenter().scheduleNotification_(notification)
def StopCricLive():
    tab.remove_all(comment="CricLiveNotifier")
    tab.write()
    try:
        os.remove(path)
    except OSError:
        pass
    sys.exit(0)
def ConnectionIssue():
    print "Something went wrong.Please check your internet connection."
    sys.exit(0)
if len(argv) == 1:
    print "Please wait.."
    try:
        livematches,livematches1 = urllib2.urlopen("http://synd.cricbuzz.com/j2me/1.0/livematches.xml"),urllib2.urlopen("http://synd.cricbuzz.com/j2me/1.0/livematches.xml")
    except Exception:
        ConnectionIssue()
    if "<html" in livematches.read():
        ConnectionIssue()
    soup = BeautifulSoup(livematches1,"xml")
    match_list = {}
    os.system('clear')
    sp_status = ""
    for idx,mtch in enumerate(soup.findAll('match')):
        for sts in mtch.findAll('state'):
            if sts.get('mchState') == 'tea' or sts.get('mchState') == 'innings break' or sts.get('mchState') == 'inprogress':
                if sts.get('mchState') == 'tea': sp_status = "Tea Break"
                if sts.get('mchState') == 'innings break': sp_status = "Innings Break"
                match_list[idx+1] = mtch.get('datapath')
                print '{0}: {1} - {2}'.format(idx+1,mtch.get('mchDesc'),mtch.get('mnum'))
    if any(match_list):
        match_no = raw_input("Select your Match by Entering the Number > ")
        sound_alert = raw_input("Notification with sound (Y/N) > ")
        sound_alert = (sound_alert.lower() == 'y')
        auto_close = raw_input("Auto Close Notification after seconds( 0 - 15 && manual close - 0) > ")
        match_link_com = match_list[int(match_no)] + "commentary.xml"
        os.system('clear')
        print "Please wait.."
        try:
            commentary,commentary1 = urllib2.urlopen(match_link_com),urllib2.urlopen(match_link_com)
        except Exception:
            ConnectionIssue()
        if "<html" in commentary.read():
            ConnectionIssue()
        soup = BeautifulSoup(commentary1,"xml")
        bat_tm_id,last_ball,last_over,wickets,runs = 0,0.0,0,0,0
        for btId in soup.findAll('btTm'):
            bat_tm_id = btId.get('id')
            bat_tm_name = btId.get('sName')
            for Ov in btId.findAll('Inngs'):
                last_ball = float(Ov.get('ovrs'))
                last_over = int(round(float(Ov.get('ovrs'))))
                wickets = Ov.get('wkts')
                runs = Ov.get('r')
                break
        data = {"last_ball_updated": last_ball,"last_over_updated": last_over,"batting_team_id": bat_tm_id,"autoclose":int(auto_close),"sound":sound_alert}
        cric_file = open('CricLiveNotifier.txt', 'w+')
        cric_file.truncate()
        pickle.dump(data, cric_file)
        cric_file.close()
        StopCricLive()
        com_file = 'python '+os.path.realpath(__file__)+' '+ match_list[int(match_no)]
        cron_job = tab.new(command=com_file,comment="CricLiveNotifier")
        cron_job.minute.every(1)
        tab.write()
        os.system('clear')
        print "Done. Enjoy the match with CricLiveNotifier :)"
        bat_tm_name = bat_tm_name+" "+runs+"/"+wickets
        last_ball = str(last_ball) + " Overs"
        notify(False,bat_tm_name, last_ball, sp_status,"", sound=True)
        if int(auto_close) > 0:
            time.sleep(int(auto_close))
            notify(True,"", "", "","")
    else:
        print "There are currently no live cricket matches"
if len(argv) > 1:
    if argv[1] == 'stop':
        StopCricLive()
    else:
        match_link_com = argv[1] + "commentary.xml"
        try:
            commentary,commentary1 = urllib2.urlopen(match_link_com),urllib2.urlopen(match_link_com)
        except Exception:
            notify(False, "Something went wrong!", "CricLiveNotifier Turned Off", "Check your Internet Connection", "http://github.com/hasgar/CricLiveNotifier", sound=True)
            StopCricLive()
        if "<html" in commentary.read():
            notify(False, "Something went wrong!", "CricLiveNotifier Turned Off", "Check your Internet Connection", "http://github.com/hasgar/CricLiveNotifier", sound=True)
            StopCricLive()
        soup = BeautifulSoup(commentary1,"xml")
        last_updated = pickle.load( open( "CricLiveNotifier.txt", "rb" ) )
        idx,balls_to_update,fours,sixes,wicket = 0,[],0,0,0
        balls_update = {"wickets": [],"fours": [],"sixers": []}
        for btId in soup.findAll('btTm'):
            bat_tm_name = btId.get('sName')
            bat_tm_id = btId.get('id')
            for Ov in btId.findAll('Inngs'):
                last_ball = Ov.get('ovrs')
                wickets = Ov.get('wkts')
                runs = Ov.get('r')
                break
        new_team_id = bat_tm_id
        def check_ball(com):
            com_txt = com.text.split(',')
            if 'out' in com_txt[1].strip().lower():
                notify(False,"WICKET!!!!!", com_txt[0], "","", sound=last_updated['sound'])
            if 'six' in com_txt[1].strip().lower():
                notify(False,"SIIIXXXXX!!!!!", com_txt[0], "","", sound=last_updated['sound'])
            if 'four' in com_txt[1].strip().lower():
                notify(False,"FOOURRRRR!!!!!", com_txt[0], "","", sound=last_updated['sound'])
                #complete and stumb
        last_ball_to_update = 0
        for com in soup.findAll('c'):
                com_txt = com.text.split(' ')
                if "." in com_txt[0]:
                    com_txt[0] = float(com_txt[0])
                    if last_updated['batting_team_id'] != new_team_id:
                        if com_txt[0] < 2.0:
                            check_ball(com)
                            if idx == 0:last_ball_to_update,idx = com_txt[0],1
                        else:
                            if com_txt[0] > last_updated['last_ball_updated']:
                                check_ball(com)
                                if idx == 0:last_ball_to_update,idx = com_txt[0],1
                                last_updated['batting_team_id'] = new_team_id
                    else:
                        if com_txt[0] > last_updated['last_ball_updated']:
                            check_ball(com)
                            if idx == 0:last_ball_to_update,idx = com_txt[0],1

        if last_ball_to_update == 0:
            last_updated['last_over_updated'] = int(round(last_updated['last_ball_updated']))
        else:
            if(last_updated['last_over_updated'] !=  int(round(last_ball_to_update))):
                bat_tm_name = bat_tm_name+" "+runs+"/"+wickets
                last_ball = last_ball + " Overs"
                notify(False,"Over Update", bat_tm_name, last_ball,"", sound=True)
            last_updated['last_over_updated'] = last_ball_to_update
            last_updated['last_over_updated'] = int(round(last_updated['last_ball_updated']))
        cric_file = open('CricLiveNotifier.txt', 'w+')
        cric_file.truncate()
        pickle.dump(last_updated, cric_file)
        cric_file.close()
        for sts in soup.findAll('state'):
            if sts.get('mchState') == 'stump' or sts.get('mchState') == 'complete':
                if sts.get('mchState') == 'stump': title,subtitle = sts.get('addnStatus'),sts.get('status')
                if sts.get('mchState') == 'complete': title,subtitle = "Match Over",sts.get('status')
                notify(False,title, subtitle, "CricLiveNotifier Turned Off", "")
                StopCricLive()
        if last_updated['autoclose'] > 0:
            time.sleep(last_updated['autoclose'])
            notify(True,"", "", "","")
