def get_questions():
    # Connect to the database
    client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=False)
    db = client['medical_history_db']
    collection = db['questions']
    
    # Fetch the document
    document_id = "670d068a4ba8ed07b544d7e4"
    document = collection.find_one({"_id": ObjectId(document_id)})

    # Iterate through sections and questions
    for section in document['sections']:
        print(f"Category: {section['category']}")
        for question in section['questions']:
            print(f"Question: {question['question']}")
            if 'follow_up' in question:
                if isinstance(question['follow_up'], str):
                    print(f"Follow-Up: {question['follow_up']}")
                elif isinstance(question['follow_up'], list):
                    for follow_up in question['follow_up']:
                        print(f"Follow-Up Question: {follow_up['question']}")
