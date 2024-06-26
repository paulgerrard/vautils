import datetime
import os
from os.path import exists
import json

from pgpt_python.client import PrivateGPTApi

GPTHOST = "http://localhost:8001"
USE_CONTEXT = False          # use the ingested documents to service the comletion
INCLUDE_SOURCES = True      # return the source Chunks used to create the response, which come from the context provided
SYSTEM_PROMPT = ''          # prepratory prompt to guide the bot in its response
CONTEXT_FILTER = []         # a list of document ids to be used for the completion


# prepratory prompt to guide the bot in its response
PROMPTS = {'theme':"""Companies usually provide information on their mssion, activities, policies and performance on their website. 
We will call these topics THEMES.
Using your experience of accessing company websites, prepare an example prompt to explore a range of THEMES.
The prompt will be used to enquire about the THEME and explore it in more detail.
THEMES might be a single word or a short phrase. 
If the THEME is too vague, please say so rather than inventing prompt content you think might be related.
The prompt should identify subject headings that you think are important to investigate for each THEMR.
When companies publish information on this THEME, what would you expect them to write?:'
""",
"testservice":"""Using your experience of testing services market, examin a service description and 
write a prompt thatasks for detail in specific areas such a) aims/purpose b) description of the service 
c) benefits of the activity, d) any other claims made for the service. 
What would you look for in a testing service description titled: """,
"capabilities":"""These documents set out the capabilities of the supplier on their webpage. 
Using your experience of testing services, processes and approaches and knowledge of the technologies market:
1. identify the capabilities listed in the document.
2. If a degree or measure of capability is mentioned, please add that to the listing. 
What capabilities are available from this vendor: """}

inboxdir = '/data/inbox/'
outboxdir = '/data/outbox/'
vendorfilesdir = '/data/vendorContent/'

def gptConnect(status):

    client = PrivateGPTApi(base_url=GPTHOST)
    if status:
        print(client.health.health())
    return client

def getTaggedTerms():

    tagsfile = inboxdir+'tag.taggedterms'
    if exists(tagsfile):
        fp=open(tagsfile)
        tagrecs = fp.readlines()
        fp.close()
        tags = []
        for t in tagrecs:
            tagrec = eval(t)
            tags.append(tagrec)
        print(len(tags), 'tags found in ',tagsfile)
    else:
        print(tagsfile, 'does not exist')
    return tags

def generateIdeals(goal, tags, client):   
    #
    #   next, load the files from the testservice.ingest file
    #
    goalprompt = goal['idealprompt']
    tagideals = []
    for t in tags:
        result = None
        try:
            term = t['term']
            company_id = t['company_id']
            print(2*'\n',80*'*','\nThe term is: ',term, '\n')
            chat_result = client.contextual_completions.chat_completion(
                messages=[{"role": "user", "content":  goalprompt + term}])
            print(chat_result.choices[0].message.content)
            profile = dict(
                id=t['termtags_id'],
                ideal=chat_result.choices[0].message.content,
                source='')
            tagideals.append(profile)
            
        except Exception as conterror:
            print('Error is:', conterror)

    tpfile = outboxdir + '/tagideals.json'
    tpjson = json.dumps(tagideals)
    fp = open(tpfile,'w')
    fp.write(tpjson)
    fp.close()
    
#    print(tpjson)

def getPromptGoals():
    
    gfile = inboxdir + 'prompt.goals'   
    pg = open(gfile,'r')
    goaltext=pg.readlines()
    goals = []
    for g in goaltext:
        goal = eval(g)
        goals.append(goal)
        
    pg.close()
    return goals

def main():

    client = gptConnect(True)

    tags = getTaggedTerms()
    
    goals = getPromptGoals()

    for goal in goals:
        generateIdeals(goal, tags, client)

    return
    
if __name__ == '__main__':

    main()
