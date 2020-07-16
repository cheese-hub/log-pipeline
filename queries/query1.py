from elasticsearch import Elasticsearch
from datetime import datetime

# Print out each query
def format_results(results):
    all_hits = results['hits']['hits']
    for doc in all_hits:
        print("%s) %s" % (doc['_id'], doc['_source']))
        for key,value in doc.items():
            print(key, "---->", value)
        print("\n\n")

# Function to find number of events started
def find_start(results):
    #Reset events in results dictionary
    results_dict["events"] = []

    all_hits = results['hits']['hits']
    for doc in all_hits:
        for key in doc['_source']:
            if key == "event" and doc['_source'][key] == "start":
                applicationId = doc['_source']['application_id']
                if applicationId not in results_dict["events"]:
                    results_dict["events"].append(applicationId)

                # Retrieve application names from applications_created dictionary in results dictionary
                if (applicationId in results_dict['applications_created'].keys()):
                    applicationName = results_dict['applications_created'][applicationId]

                    # Increment user per application by one
                    results_dict['users_per_application'][applicationName] += 1

# Function to find events created

def find_create(results):
    # Dictionary mapping application_ids to application names
    create_dict = {}

    # Dictionary of count of distinct applications created
    application_dict = {}

    all_hits = results['hits']['hits']

    for doc in all_hits:
        for key in doc['_source']:
            # If event is a create
            if key == "event" and doc['_source'][key] == "CREATE":
                create_dict[doc['_source']['application_id']] = doc['_source']['ApplicationName']
                if doc['_source']['ApplicationName'] not in application_dict.keys():
                    application_dict[doc['_source']['ApplicationName']] = 0

    results_dict["applications_created"] = create_dict
    results_dict["users_per_application"] = application_dict

def find_users_served(results):
    results_dict["users"] = []

    all_hits = results['hits']['hits']

    for doc in all_hits:
        for key in doc['_source']:
            if key == "Username" and doc['_source']['Username'] not in results_dict["users"]:
                results_dict["users"].append(doc['_source']['Username'])


# Function to find time spent on each application
def find_start_stop_time(results):
    events_in_start = []
    start_times = {}
    event_times = {}
    all_hits = results['hits']['hits']
    for doc in all_hits:
        # If start encountered find the time and add to start_times and events_in_start dictionaries
        if "start" in doc['_source'].values():
            events_in_start.append(doc['_source']['application_id'])
            timestamp = doc['_source']['time']

            # Obtain datetime object from start hits
            dt = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S +%f')
            start_times[doc['_source']['application_id']] = dt

        #   If stop encountered check if applicationid exists in the events_in_start and find time difference
        elif "stop" in doc['_source'].values():
            applicationid = doc['_source']['application_id']
            timestamp = doc['_source']['time']

            # Calculate time difference if start event exists
            if applicationid in events_in_start:
                dt = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S +%f')
                diff = dt - start_times[applicationid]
                diff = diff/60
                
                # Check if applicationid already exists in the created array to obtain application name
                if applicationid in results_dict["applications_created"].keys():
                    
                    # Check if event already started previously to add time spent if not create new time
                    if applicationid in event_times:
                        event_times[results_dict["applications_created"][applicationid]] = event_times[results_dict["applications_created"][applicationid]] + diff
                    else:
                        event_times[results_dict["applications_created"][applicationid]] = diff
                    
                    # Remove event from start times if stop encountered
                    start_times.pop(applicationid)
                    events_in_start.remove(applicationid)

    # Add time spent to results dictionary
    results_dict["time_spent"] = event_times

if __name__ == '__main__': 
    # connection to elastic search
    es = Elasticsearch([{'host':'localhost', 'port':9200}])

    results_dict = {}

    # queries

    # Find all events
    res = es.search(index="logstash-*", size=999)
    # Find all start events
    res_start = es.search(index="logstash-*", size=999, body={"query": {"match": {"event":"start"}}})
    # Find all create events
    res_create = es.search(index="logstash-*", size=999, body={"query": {"match": {"event":"CREATE"}}})
    # Find both start and stop events
    res_start_stop = es.search(index="logstash-*", size=999, body={"query": {"bool": {"should": [{"match": {"event": "start"}},{"match": {"event": "stop"}}]}}          })

    find_create(res)
    find_start(res)
    find_users_served(res)
    find_start_stop_time(res)


    print ("Number of users served: " + str(len(results_dict["users"])))
    print ("Number of applications developed: " + str(len(results_dict["applications_created"])))
    print ("\n Number of users per application: \n")
    for key in results_dict["users_per_application"]:
        if (results_dict["users_per_application"][key] != 0):
            print (key + " ---> " + str(results_dict["users_per_application"][key]))
    print ("\n Time spent on each application: \n")
    for key in results_dict["time_spent"]:
        print (key + " ---> " + str(results_dict["time_spent"][key])) 

