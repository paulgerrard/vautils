from datetime import datetime
import os
from os.path import exists
import json

from pgpt_python.client import PrivateGPTApi

GPTHOST = "http://localhost:8001"
USE_CONTEXT = False          # use the ingested documents to service the comletion
INCLUDE_SOURCES = True      # return the source Chunks used to create the response, which come from the context provided
SYSTEM_PROMPT = ''          # prepratory prompt to guide the bot in its response
CONTEXT_FILTER = []         # a list of document ids to be used for the completion


inboxdir = '/data/inbox/'
outboxdir = '/data/outbox/'
vendorfilesdir = '/data/vendorContent'

def gptConnect(status):

    client = PrivateGPTApi(base_url=GPTHOST)
    if status:
        print(client.health.health())
    return client
#
# get the doc ids to use
# 
def listDocuments(client):
    docids = {}
    
    fname = outboxdir + 'filedocids.ingested'
    fp = open(fname,'r')
    doctext = fp.read()
    fp.close()
    docids = eval(doctext)

    print(len(docids), 'documents')
    for d in docids:
        print(d,docids[d])
    return docids

def getPromptGoals():
    
    gfile = inboxdir + 'promptgoals.json'   
    pg = open(gfile,'r')
    goaltext=pg.read()
    goals = json.loads(goaltext)
    pg.close()
    return goals

#
#   get the pages that have been downloaded.
#
def getPageList(goal):

    pagefile = inboxdir + goal['tag'] +'.ingest'
    pages = []
    fp = open(pagefile,'r')
    pagetext = fp.readlines()
    fp.close()
    
    for p in pagetext:
        pages.append(eval(p))

    print(len(pages), 'tagged pages found')
    
    return pages

def summaryCompletions(goal, client, pages, docids):
    
    responses = []
    for p in pages:
        
#        if p['pagetermtagsid'] != 12:
#            continue
        
        print(80*'*')
        print(p['pagetermtagsid'],p['pageurl'],p['termtagid'], p['tag'], p['term'],
                p['filename'])

        for filename in p['filename']:
            docs = []
            if filename in docids:
                if len(docs) == 0:
                    docs = [docids[filename]]
                else:
                    docs.append([docids[filename]])
            else:
                response = filename + ' not found in ingested file list'

        urls = p['pageurl']

        if len(docs) > 0:
            try:
                result = client.contextual_completions.prompt_completion(
                    prompt=p['summaryprompt'],
                    use_context=True,
                    context_filter={"docs_ids": docs},
                    include_sources=True,
                ).choices[0]
                print('len message content',len(result.message.content))
                print(f" # Source: {p['filename']}")
                response=result.message.content
                
                urltext = '<br><br>Sources:'
                for url in urls:
                    urltext = ''.join(('<br><a href="',url,'" target="_blank">',url,'</a>'))
                response += urltext
                
            except Exception as gpterr:
                print(gpterr)
                response = filename +' failure in completion'
        #
        #   capture the failures as well as successes in output file 
        #   (will ebnd up in the final report).
        #
        source = p['pageurl']
        now = datetime.now()
#        rdict = dict(page=p,response=response,
#                source = source,
#                responsedate=now.strftime("%Y/%m/%d %H:%M:%S"))
        p['summary'] = response
        p['source'] = source
        p['responsedate'] = now.strftime("%Y/%m/%d %H:%M:%S")
                    
        responses.append(p)
        print(p)
        
    return responses

def main():

    client = gptConnect(True)
    docids = listDocuments(client)

    goals = getPromptGoals()
    print(goals)
    respfull = []


    for goal in goals:
        pages = getPageList(goal)
        responses = summaryCompletions(goal, client, pages, docids)
        respfull.extend(responses)
        

    #
    #   write out the responses
    #
    respjson = json.dumps(respfull)

    resfile = outboxdir + '/servicessummary.json'
    fp = open(resfile,'w')
    fp.write(respjson)
    fp.close()
    

if __name__ == '__main__':
     main()


