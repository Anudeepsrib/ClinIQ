from faker import Faker
import os
import random

fake = Faker()

def generate_patient_note(filename):
    name = fake.name()
    phone = fake.phone_number()
    email = fake.email()
    ssn = fake.ssn()
    
    # Context that sounds medical but contains PII
    templates = [
        f"Patient {name} (DOB: {fake.date_of_birth()}) presented with severe headaches. Contact: {phone}.",
        f"Subject: {name}. SSN: {ssn}. Email: {email}. Diagnosis: Hypertension.",
        f"Lab results for {name} sent to {email}. Please call {phone} to discuss.",
        f"Medical History for {name}: Patient denies smoking. Emergency contact: {fake.name()} ({fake.phone_number()})."
    ]
    
    content = "\n".join(random.sample(templates, k=3))
    
    os.makedirs("data/test_docs", exist_ok=True)
    filepath = f"data/test_docs/{filename}"
    
    with open(filepath, "w") as f:
        f.write(content)
        
    print(f"Generated {filepath}")
    print(f"Contains: {name}, {phone}, {email}, {ssn}")
    return filepath

if __name__ == "__main__":
    generate_patient_note("patient_alpha.txt")
    generate_patient_note("patient_beta.txt")
