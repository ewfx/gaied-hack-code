#!/usr/bin/env python
# coding: utf-8

# In[70]:


system_prompt = """You are an banking support assitant. You will be provided with the following inputs:  
1. An **email** or other relevant **document** related to banking operations.  
2. A set of **rules** (guidelines) defining data extraction, classification criteria, and processing logic.  
3. A predefined list of **request type definitions** relevant to the domain.

*Output Requirements:*  
Based on the input, your task is to generate the following outputs:  
1. **Request Types with Prioritization and Confidence Scores:**  
   - Determine the possible request types from the input.  
   - Assign a priority level to each request type (e.g., High, Medium, Low).  
   - Provide a confidence score (in percentage) for each request type based on your assessment.  

2. **Extracted Field Values:**  
   - Identify and extract all relevant field values mentioned in the input (e.g., customer ID, account details, loan type, date, amount).  
   - Ensure the extracted fields comply with the provided rules and are consistent across documents.  

3. **Duplicate Detection Fields with Classification Flags:**  
   - Analyze the content for potential duplicate records or information.  
   - If a duplicate is detected, classify it as a "Duplicate" and provide a detailed reason (e.g., matching request ID, similar account details, etc.).  
   - Include a flag to indicate the reason for classification.

4.**Based on the provided email content, generate a service ticket in JSON format. The ticket must include the following fields:**

   - ticket_id: A unique identifier for the ticket, prefixed with 'TICKET-' followed by the email file name (without the extension).
   - request_types: A list of request types, each with a type, priority (High, Medium, Low), and confidence (percentage).
   - fields: A dictionary of extracted fields such as account numbers, references, and other relevant details.
   - duplicates: A list of duplicate detection results, if any, with reasons for classification.
   Ensure the output is a valid JSON object and does not include any additional text, notes, or explanations outside the JSON object."   


Print json output in the following format: 
{ 
  "ticket_id": "TICKET-<file_name>", 
  "request_types": [ 
    { 
      "type": "<request_type>", 
      "priority": "<High|Medium|Low>", 
      "confidence": <percentage> 
    } 
  ], 
  "fields": { 
    "<field_name>": "<field_value>" 
  }, 
  "duplicates": [ 
    { 
      "duplicate": true, 
      "reason": "<reason>" 
    } 
  ] 
}  
Note:Don't output the email body back."""


# In[ ]:


import os
import hashlib
from email import policy
from email.parser import BytesParser

from groq import Groq

def parse_eml_standard(eml_content):
    msg = BytesParser(policy=policy.default).parsebytes(eml_content)
    from_ = msg['From']
    to = msg['To']
    cc = msg['Cc']
    body = msg.get_body(preferencelist=('plain')).get_content()
    return from_, to, cc, body

def extract_email_attributes_standard(eml_folder):
    email_tuples = []
    total_emails = len([f for f in os.listdir(eml_folder) if f.endswith('.eml')])
    for index, eml_file in enumerate(os.listdir(eml_folder)):
        if eml_file.endswith('.eml'):
            with open(os.path.join(eml_folder, eml_file), 'rb') as file:
                from_, to, cc, body = parse_eml_standard(file.read())
                email_tuples.append((from_, to, cc, body, eml_file, index))
                process_email_attributes(from_, to, cc, body, eml_file, index, total_emails)
    return email_tuples

# Set to store hashes of processed emails
processed_hashes = set()

def generate_email_hash(from_, to, cc, body):
    """
    Generate a unique hash for an email based on its content.
    """
    email_content = f"{from_}{to}{cc}{body}"
    return hashlib.md5(email_content.encode('utf-8')).hexdigest()


def process_email_attributes(from_, to, cc, body, eml_file, index, total_emails):
    """
    Process email attributes and avoid processing duplicates.
    """
    global processed_hashes

    # Generate a hash for the current email
    email_hash = generate_email_hash(from_, to, cc, body)

    # Check if the email is a duplicate
    if email_hash in processed_hashes:
        print(f"Skipping duplicate email: {eml_file}")
        return

    # Add the hash to the set of processed emails
    processed_hashes.add(email_hash)

    # Process the email
   # print(f"# Processing email {index + 1}/{total_emails}: {eml_file}")
    print(classify_email_with_groq(body))


def classify_email_with_groq(body):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    classification = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": body
            }
        ],
        model="llama3-8b-8192"
    )
    return classification.choices[0].message.content.strip()

# Example usage
eml_folder = './emails'  # Replace with the path to your EML files
email_tuples_standard = extract_email_attributes_standard(eml_folder)

