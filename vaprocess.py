
import os

from pgpt_python.client import PrivateGPTApi

GPTHOST = "http://localhost:8001"
USE_CONTEXT = True          # use the ingested documents to service the comletion
INCLUDE_SOURCES = True      # return the source Chunks used to create the response, which come from the context provided
SYSTEM_PROMPT = ''          # preapratory prompt to guide the bot in its response
CONTEXT_FILTER = []         # a list of document ids to be used for the completion
#
#	Create a PrivateGPTApi instance. Point it to your PrivateGPT url:
#

def gptConnect(status):

    client = PrivateGPTApi(base_url=GPTHOST)
    if status:
        print(client.health.health())
    return client
	
def getDocuments(client):

    docids = []
    for doc in client.ingestion.list_ingested().data:
        docids.append(doc.doc_id)
    return docids

def listDocuments(client):

    nd = 0
    for doc in client.ingestion.list_ingested().data:
        print(doc.doc_id, doc.doc_metadata['file_name'])
        nd += 1
    print(nd, 'documents')
    return

def deleteDocuments(client, docids):

    for d in docids:
        client.ingestion.delete_ingested(d)
        print('Deleted:',d)
    return

def ingestFile(client, filename):
    with open(filename, "rb") as f:
        docid = client.ingestion.ingest_file(file=f).data[0].doc_id
        print("Ingested file doc id: ", docid)
    return docid

def ingestFolder(client, folder):
    files = os.listdir(folder)
    nf = 0
    docids = []
    for f in files:
        filename = '/'.join((folder, f))
        docid = ingestFile(client, filename)
        nf += 1
        docids.append(docid)
    print(nf,'files ingested')
    return docids

def contCompletion(client, prompt, docids):

    result = None
    try:
        result = client.contextual_completions.prompt_completion(
            prompt=prompt,
            use_context=USE_CONTEXT,
            context_filter={"docs_ids": docids},
            include_sources=INCLUDE_SOURCES,
        ).choices[0]
    except Exception as conterror:
        print('Errors is:', conterror)

    return result


def main():

    client = gptConnect(True)
    docids = getDocuments(client)

#    deleteDocuments(client, docids)
#    docids = ingestFolder(client, '/data/vendorContent/6b128744-a2f9-58b8-a334-610473d72a16/')

    listDocuments(client)
    
    prompts = [
        'what services are described in the ingested documents? Please list what these services, whether there is a description of them or not',
        'could you describe in more detail these services',
        'what can you tell us about the company?'
        ]

    for prompt in prompts:
        result = contCompletion(client, prompt, docids)
        print("\nPrompt:", prompt, '\n')
        print(result.message.content)
        print(f"\nSource: {result.sources[0].document.doc_metadata['file_name']}")

    return
    
if __name__ == '__main__':

    main()
