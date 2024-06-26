import datetime
import os
from os.path import exists
import json

from pgpt_python.client import PrivateGPTApi

GPTHOST = "http://localhost:8001"
USE_CONTEXT = True          # use the ingested documents to service the comletion
INCLUDE_SOURCES = True      # return the source Chunks used to create the response, which come from the context provided
SYSTEM_PROMPT = ''          # preapratory prompt to guide the bot in its response
CONTEXT_FILTER = []         # a list of document ids to be used for the completion
#
#	constants
# 
inboxdir = '/data/inbox/'
outboxdir = '/data/outbox/'
vendorfilesdir = '/data/vendorContent'

def gptConnect(status):

    client = PrivateGPTApi(base_url=GPTHOST)
    if status:
        print(client.health.health())
    return client

def getIngestedFiles(client):
    docfiles = {}
    for doc in client.ingestion.list_ingested().data:
        docfiles[doc.dict()['doc_metadata']['file_name']] = doc.doc_id
    return docfiles
    	
def ingestFile(client, filename):
    with open(filename, "rb") as f:
        docid = client.ingestion.ingest_file(file=f).data[0].doc_id
        print("Ingested file doc id: ", docid)
    return docid

def readInbox():
    infiles = os.listdir(inboxdir)
    for f in infiles:
        print(f,'\n')
        
    return infiles

def getPromptGoals():
    
    gfile = inboxdir + 'promptgoals.json'   
    pg = open(gfile,'r')
    goaltext=pg.read()
    goals = json.loads(goaltext)
    pg.close()
    return goals

def processInbox(client, goals, docfiles):
    #
    #   first, load the compaines found in the inbox
    #
    companiesfile = inboxdir+'/companies.ingest'
    if exists(companiesfile):
        fp=open(companiesfile)
        companyrecs = fp.readlines()
        fp.close()
        companies = {}
        for c in companyrecs:
            corecs = eval(c)
            for cid in corecs:
                companies[cid] = corecs[cid]
        print(len(companies), 'companies found in ',companiesfile)
    else:
        print(companiesfile, 'does not exist')
    #
    #   next, load the files from the testservice.inget file
    #
    filedocids = {} 
    for g in goals:
        infilename = inboxdir+g['tag'] + '.ingest'
        if exists(infilename):
            fp=open(infilename)
            filerecs = fp.readlines()
            fp.close()
            print(len(filerecs), 'web pages found in ',infilename)
            #
            #   for each rows, do one ingestion
            #
            nfiles = 0
            errmsg=''
            for f in filerecs:
                file = eval(f)
                filenames = file['filename']
                for filename in filenames:
                    if filename in docfiles:
                        print(filename,'already ingested')
                        filedocids[filename] = docfiles[filename]
                    else:
                        path = '/'.join((vendorfilesdir,file['parent'],filename)) 
                        if exists(path):
                            print(path)
                            #
                            #   and ingest the file
                            #
                            try:
                                with open(path, "rb") as f:
                                    docid = client.ingestion.ingest_file(file=f).data[0].doc_id
                                    nfiles += 1
                                    print('Ingested (',nfiles,'):',path,'doc id: ', docid)
                                    filedocids[filename] = docid
                            except:
                                print('*** Could not ingest',path,'***')
                        else:
                            errmsg = ''.join((errmsg,'*** cannot be opened ' + path,'\n'))
            
            print(len(filerecs), 'service web pages found in ',infilename)
            print((nfiles), 'files ingested')
            print(errmsg)

        docidsfile = outboxdir + '/filedocids.ingested'
        fp = open(docidsfile,'w')
        fp.write(str(filedocids))
        fp.close()
        
def main():

    client = gptConnect(True)
    docfiles = getIngestedFiles(client)

    goals = getPromptGoals()

    processInbox(client, goals, docfiles)
    

    return
    
if __name__ == '__main__':

    main()
