# -*- coding: utf-8 -*-
"""
(C) 2020 DeltaQuad (enwp.org/User:DeltaQuad)

This file is part of DeltaQuadBot.

DeltaQuadBot is free software: you can redistribute it and/or modify
it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

DeltaQuadBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU AFFERO GENERAL PUBLIC LICENSE for more details.

You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
along with DeltaQuadBot. If not, see <https://www.gnu.org/licenses/agpl.txt>.
"""

from datetime import datetime
import sys
import platform
import time
import json
import re

import credentials
import mwclient

masterwiki =  mwclient.Site('en.wikipedia.org')
masterwiki.login(credentials.username,credentials.password)

page = masterwiki.pages["Category:Requests for unblock"]
clerks = page.text()

def callAPI(params):
    return masterwiki.api(**params)

def getMembers(category):
    category = "Category:" + category
    params = {'action': 'query',
        	'list': 'categorymembers',
        	'cmtitle': category,
                'cmnamespace':'3',
                'cmlimit':'500',
                'format':'json'
                }
    raw = callAPI(params)
    reg = raw["query"]["categorymembers"]
    return reg

def getHistory(title):
    params = {'action':'query',
              'prop':'revisions',
              'titles':title,
              'rvlimit':'500',
              'rvprop':'timestamp|user',
              'format':'json'}
    history = callAPI(params)
    full = history["query"]["pages"]
    for singleid in full:
        pageid = singleid
    history = history['query']['pages'][pageid]['revisions']
    return history

def getLastEdit(title):
    history=getHistory(title)
    last = history[0]
    timestamp = last["timestamp"]
    return {'user':last["user"],'timestamp':timestamp}

def findblock(user):
    params = {'action': 'query',
            'format': 'json',
            'list': 'blocks',
            'bkusers': user
            }
    raw = callAPI(params)
    if len(raw["query"]["blocks"])>0:
        info = raw["query"]["blocks"][0]
        if len(info["reason"])>65:
            try:reason=info["reason"].split(": ")[0]
            except:reason = info["reason"]
        else:reason = info["reason"]
        return {'user':user,'blockadmin':info["by"],'blockdate':info["timestamp"],'blockreason':"<nowiki>"+reason+"</nowiki>",'blocklength':info["expiry"]}
    else:
        params = {'action': 'query',
        'format': 'json',
        'list': 'blocks',
        'bkip': user
        }
        try:raw = callAPI(params)
        except:return {'user':user,'blockadmin':"N/A",'blockdate':"N/A",'blockreason':"N/A",'blocklength':"N/A"}
        if len(raw["query"]["blocks"])>0:
            info = raw["query"]["blocks"][0]
            return {'user':user,'blockadmin':info["by"],'blockdate':info["timestamp"],'blockreason':"<nowiki>"+info["reason"]+"</nowiki>",'blocklength':info["expiry"]}
        else:

            params = {'action': 'query',
            'format': 'json',
            'list': 'blocks',
            'bkids': user
            }
            try:raw = callAPI(params)
            except:
                return {'user':user,'blockadmin':"N/A",'blockdate':"N/A",'blockreason':"N/A",'blocklength':"N/A"}
            if len(raw["query"]["blocks"])>0:
                info = raw["query"]["blocks"][0]
                return {'user':user,'blockadmin':info["by"],'blockdate':info["timestamp"],'blockreason':"<nowiki>"+info["reason"]+"</nowiki>",'blocklength':info["expiry"]}
def findunblocktime(pagename,id,limit=50,increase=False):
    if increase:limit=limit+50
    if limit == 500:return ""
    params = {'action': 'query',
        'format': 'json',
        'prop': 'revisions',
        'titles': pagename,
        'rvslots': '*',
        'rvprop':"timestamp|user|content",
        'rvlimit':limit
        }
    raw = callAPI(params)
    time=""
    revisions= raw['query']['pages'][str(id)]['revisions']
    for revision in revisions:
        try:
            if revision['user'] != pagename.split(":")[1]:
                continue
        except:
            continue
        found=False
        timebefore = time
        time = revision['timestamp']
        try:content = revision['slots']['main']['*']
        except:return "Unknown"
        unblocktemplates = ["{{unblock|","{{unblockonhold|","{{unblock-auto|","{{unblock-bot|","{{unblock-spamun|","{{unblock-un|","{{unblock-unonhold|","{{unblockrequest|","{{unblock-spamun|"]
        for item in unblocktemplates:
            if item in content.lower().strip():
                found=True
                break
        if found:continue       
        return timebefore
        break
    try:crazy=timebefore
    except UnboundLocalError:timebefore = findunblocktime(pagename, id, limit, True)
    return timebefore
def formatrow(block,appealtime,lastedit,type):
    if type=="normal":style="|-\n"
    if type=="auto":style='|- style="background-color:#ADD8E6"\n'
    if type=="username":style='|- style="background-color:#FFEFDB"\n'
    if type=="hold":style='|- style="background-color:#CC99CC"\n'
    return style+"|"+appealtime+"\n|[[User talk:"+block['user']+"|"+block['user']+"]]\n"+"|Admin: "+block['blockadmin']+"<br>Date: "+block['blockdate']+"<br>Reason: "+block['blockreason']+"<br>Length: "+block['blocklength']+"\n|"+lastedit['user']+"\n|"+lastedit['timestamp']+"\n"
def runCategory(cat,type,table):
    ulist = getMembers(cat)
    if len(ulist)==0:return
    specialappeallist = {}
    for page in ulist:
        user = page['title'].split("User talk:")[1]
        for item in table.values():
            if user in item:
                #print('User '+user+" is in "+ item)
                continue
        blockinfo = findblock(user)
        appealtime = findunblocktime(page['title'],page['pageid'])
        lastedit = getLastEdit(page['title'])
        currentrow = formatrow(blockinfo,appealtime,lastedit,type)

        if not appealtime:appealtime="Placeholder "+str(user)
        specialappeallist.update({str(appealtime): currentrow})
    ### for item in specialappealarray:
        ### alltable += item[1]
    ### Old: alltable += formatrow(blockinfo,appealtime,lastedit,type)
    #print(specialappeallist[specialtime])
    return specialappeallist
tableheader = """
{|class="wikitable sortable" width="100%"
!Request time!!User!!Block info!!Last user edit!!Timestamp
"""
tablefooter="|}"
table = {}

table.update(runCategory("Requests for username changes when blocked‎","username",table))
time.sleep(2)
table.update(runCategory("Requests for unblock","normal",table) or {})
time.sleep(2)
table.update(runCategory("Requests for unblock-auto‎","auto",table) or {})
time.sleep(2)
table.update(runCategory("Unblock on hold‎","hold",table) or {})
time.sleep(2)

result = sorted(table.items(), key=lambda appeals: appeals[0])
    #r"([0-2]|)[0-9]:[0-5][0-9], ([0-3]|)[0-9] .* 20[0-9][0-9] \(UTC\)"
wikitable=""
for item in result:
    wikitable+=item[1]
wikitable = tableheader + wikitable + tablefooter
page = masterwiki.pages["User:AmandaNP/unblock table"]
page.save(wikitable, "Update unblock table")
