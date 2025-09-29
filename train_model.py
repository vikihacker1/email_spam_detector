import os
import re
from email import message_from_file
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from joblib import dump
import nltk
from nltk.corpus import stopwords

# Download stopwords if you haven't already
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+', '', text) # Remove URLs
    text = re.sub(r'[^a-zA-Z\s]', '', text) # Remove punctuation and numbers
    text = ' '.join([word for word in text.split() if word not in stopwords.words('english')])
    return text

def load_emails(directory):
    emails = []
    for filename in os.listdir(directory):
        if not filename.startswith('.'): # Ignore hidden files
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='latin-1') as f:
                try:
                    msg = message_from_file(f)
                    content = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                content += str(part.get_payload(decode=True), 'latin-1', 'ignore')
                    else:
                        content = str(msg.get_payload(decode=True), 'latin-1', 'ignore')
                    emails.append(clean_text(content))
                except Exception as e:
                    print(f"Skipping file {filename}: {e}")
    return emails

def main():
    print("Loading datasets...")
    # Create these folders and place email files in them
    spam_emails = load_emails('dataset/spam')
    ham_emails = load_emails('dataset/easy_ham')

    if not spam_emails or not ham_emails:
        print("\nError: Dataset folders ('dataset/spam', 'dataset/easy_ham') are empty or not found.")
        print("Please download the SpamAssassin public corpus and place files in these directories.")
        return

    # Create labels: 1 for spam, 0 for ham
    X = spam_emails + ham_emails
    y = [1] * len(spam_emails) + [0] * len(ham_emails)

    print(f"Training model on {len(X)} emails...")
    
    # Create a model pipeline: TfidfVectorizer -> MultinomialNB
    model = make_pipeline(TfidfVectorizer(), MultinomialNB())
    
    # Train the model
    model.fit(X, y)

    # Save the trained model to the model/ directory
    os.makedirs('model', exist_ok=True)
    dump(model, 'model/spam_classifier.joblib')

    print("\nModel training complete!")
    print("Model saved to model/spam_classifier.joblib")

if __name__ == '__main__':
    main()