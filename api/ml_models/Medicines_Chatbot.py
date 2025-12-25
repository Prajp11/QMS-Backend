import os
import json
import random
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
import nltk
from langdetect import detect
import speech_recognition as sr
import pyttsx3

# Download required NLTK data
try:
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)
except:
    pass

# Get the current script's directory
script_dir = os.path.dirname(__file__)

# Create the full path to the intents.json file
file_path = os.path.join(script_dir, 'intents.json')

# Load the dataset
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    print("✅ Intents.json loaded successfully!")
except Exception as e:
    print(f"❌ Error loading intents.json: {e}")
    data = {"intents": []}

# Initialize stemmer and prepare data
stemmer = PorterStemmer()
words, tags, xy = [], [], []

# Process intents and extract training data
for intent in data.get("intents", []):
    tag = intent.get("tag", "")
    tags.append(tag)
    
    for pattern in intent.get("patterns", []):
        tokenized_words = word_tokenize(pattern)
        words.extend(tokenized_words)
        xy.append((tokenized_words, tag))

# Create vocabulary
words = sorted(set(stemmer.stem(w.lower()) for w in words if w not in ["?", ".", "!"]))
tags = sorted(tags)

print(f"✅ Processed {len(xy)} patterns with {len(words)} unique words and {len(tags)} intents")

# Function to create a bag of words
def bag_of_words(tokenized_sentence, words):
    tokenized_sentence = [stemmer.stem(w.lower()) for w in tokenized_sentence]
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in tokenized_sentence:
            bag[idx] = 1
    return bag

# Prepare training data
X_train, y_train = [], []

for (pattern_sentence, tag) in xy:
    X_train.append(bag_of_words(pattern_sentence, words))
    y_train.append(tags.index(tag))

X_train, y_train = np.array(X_train), np.array(y_train)

# Neural Network Model
class ChatbotRNN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(ChatbotRNN, self).__init__()
        self.hidden_size = hidden_size
        self.rnn = nn.RNN(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(1, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.rnn(x.unsqueeze(1), h0)
        out = self.fc(out[:, -1, :])
        return out

# Model parameters
input_size = len(words)
hidden_size = 8
output_size = len(tags)
learning_rate = 0.01
num_epochs = 210

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize model
model = ChatbotRNN(input_size, hidden_size, output_size).to(device)
model_path = os.path.join(script_dir, "Mental_Health_chatbot_rnn.pth")

# Try to load existing model, otherwise train new one
if os.path.exists(model_path):
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        print("✅ Loaded existing trained model")
    except:
        print("❌ Failed to load model, training new one...")
        train_model = True
else:
    print("🔄 Training new model...")
    train_model = True

if 'train_model' in locals():
    # Convert data to PyTorch tensors
    X_train = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_train = torch.tensor(y_train, dtype=torch.long).to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    for epoch in range(num_epochs):
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Calculate accuracy
        _, predicted = torch.max(outputs, dim=1)
        correct = (predicted == y_train).sum().item()
        accuracy = 100 * correct / y_train.size(0)
        
        if (epoch + 1) % 50 == 0:
            print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}, Accuracy: {accuracy:.2f}%")
    
    # Save model
    torch.save(model.state_dict(), model_path)
    print("✅ Training complete. Model saved as Mental_Health_chatbot_rnn.pth")
    
    # Set model to evaluation mode
    model.eval()

def find_best_matching_response(text, patterns, responses):
    """
    Find the most appropriate response based on pattern similarity
    """
    import string
    
    # Clean the input text
    text_clean = text.lower().translate(str.maketrans('', '', string.punctuation))
    text_words = set(text_clean.split())
    
    best_score = 0
    best_response_idx = 0
    
    # Check each pattern and find the best match
    for i, pattern in enumerate(patterns):
        pattern_clean = pattern.lower().translate(str.maketrans('', '', string.punctuation))
        pattern_words = set(pattern_clean.split())
        
        # Calculate word overlap score
        common_words = text_words.intersection(pattern_words)
        if pattern_words:
            overlap_score = len(common_words) / len(pattern_words)
        else:
            overlap_score = 0
        
        # Bonus for exact phrase matches
        if pattern_clean in text_clean or text_clean in pattern_clean:
            overlap_score += 0.5
        
        # Check for specific question types and give appropriate responses
        if overlap_score > best_score:
            best_score = overlap_score
            best_response_idx = min(i, len(responses) - 1)
    
    # Context-aware response selection based on question keywords
    question_keywords = {
        'usage': ['used for', 'use', 'treat', 'help', 'purpose', 'what is', 'benefits', 'indication'],
        'dosage': ['dose', 'dosage', 'how much', 'amount', 'quantity', 'take', 'mg', 'grams'],
        'side_effects': ['side effect', 'adverse', 'reaction', 'problem', 'effects'],
        'safety': ['safe', 'pregnancy', 'children', 'pregnant', 'danger', 'during pregnancy'],
        'overdose': ['overdose', 'too much', 'excess', 'maximum'],
        'timing': ['how long', 'when', 'time', 'duration', 'work']
    }
    
    # Find the best response based on context with improved scoring
    best_context_score = 0
    best_context_response = None
    
    for context, keywords in question_keywords.items():
        if any(keyword in text_clean for keyword in keywords):
            # Look for responses that match this context
            for i, response in enumerate(responses):
                response_lower = response.lower()
                context_score = 0
                
                if context == 'usage' and any(word in response_lower for word in ['used', 'treat', 'relieve', 'help', 'commonly taken']):
                    context_score = 3
                elif context == 'dosage' and any(word in response_lower for word in ['dose', 'mg', 'gram', 'daily', 'can usually take', 'adults can']):
                    context_score = 3
                elif context == 'side_effects' and any(word in response_lower for word in ['side effects', 'nausea', 'rash', 'drowsiness', 'common side effects']):
                    context_score = 3
                elif context == 'safety' and any(word in response_lower for word in ['safe', 'pregnancy', 'pregnant', 'considered safe', 'during pregnancy']):
                    context_score = 3
                elif context == 'overdose' and any(word in response_lower for word in ['overdose', 'excess', 'damage', 'liver damage']):
                    context_score = 3
                elif context == 'timing' and any(word in response_lower for word in ['minutes', 'hours', 'work', 'time', 'starts working']):
                    context_score = 3
                
                if context_score > best_context_score:
                    best_context_score = context_score
                    best_context_response = response
    
    if best_context_response:
        return best_context_response
    
    # Return the best matching response or first response as fallback
    return responses[best_response_idx] if responses else "I don't have information about that."

# Chatbot response function using the trained neural network
def chatbot_response(text):
    """
    Enhanced neural network-based chatbot response function with smart response selection
    """
    try:
        # Detect language
        try:
            detected_language = detect(text)
        except:
            detected_language = "en"
            
        language_map = {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "ja": "Japanese",
            "de": "German",
            "pt": "Portuguese"
        }
        language = language_map.get(detected_language, "English")
        
        # Tokenize and create bag of words
        bow = bag_of_words(word_tokenize(text), words)
        bow = torch.tensor(bow, dtype=torch.float32).to(device)
        
        # Get prediction from model
        with torch.no_grad():
            output = model(bow.unsqueeze(0))
            _, predicted = torch.max(output, dim=1)
            tag = tags[predicted.item()]
        
        # Find matching intent and return appropriate response
        for intent in data.get("intents", []):
            if intent.get("tag") == tag:
                patterns = intent.get("patterns", [])
                responses = intent.get("responses", [])
                
                if responses:
                    # Use smart response selection instead of random choice
                    if patterns and len(patterns) > 0:
                        best_response = find_best_matching_response(text, patterns, responses)
                        return best_response
                    else:
                        return random.choice(responses)
        
        # Fallback response
        fallback_responses = [
            "I'm not sure about that. Could you ask about a specific medicine or health topic?",
            "I don't have information on that topic. Try asking about medicine names, dosages, or side effects.",
            "Please ask me about medicines, their uses, dosages, or side effects.",
            "I specialize in medicine information. Ask me about any medicine by name!",
            "Could you rephrase your question? I can help with medicine-related queries."
        ]
        return random.choice(fallback_responses)
        
    except Exception as e:
        print(f"❌ Error in chatbot_response: {e}")
        return "I'm having trouble processing your request. Please try again."

# ==========================
# 🔊 Voice Assistant Section
# ==========================

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak_text(text):
    """Convert text to speech"""
    engine.say(text)
    engine.runAndWait()

def listen_to_user():
    """Listen to user's voice input and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            print(f"🧑 You said: {text}")
            return text
        except sr.UnknownValueError:
            print("❗ Sorry, I didn't understand that.")
            speak_text("Sorry, I didn't understand that.")
            return ""
        except sr.RequestError:
            print("❗ Speech service unavailable.")
            speak_text("Speech service is unavailable.")
            return ""

def voice_chatbot():
    """Run the voice-enabled chatbot"""
    print("🔈 Voice Medicine Assistant is now running. Say 'quit' to stop.")
    speak_text("Hi, I'm your medicine assistant. How can I help you today?")

    while True:
        user_input = listen_to_user()
        if user_input.lower() in ["quit", "exit", "stop"]:
            speak_text("Take care. Goodbye!")
            break
        elif user_input.strip():
            response = chatbot_response(user_input)
            print(f"🤖 Chatbot: {response}")
            speak_text(response)

# Test the function when script is run directly
if __name__ == "__main__":
    print("🤖 Medicine Chatbot loaded successfully!")
    print(f"Dataset contains {len(data.get('intents', []))} intents")
    print(f"Vocabulary size: {len(words)} words")
    print(f"Number of tags: {len(tags)} intents")
    
    # Test queries
    test_queries = [
        "Hello",
        "Tell me about Paracetamol",
        "What is Ibuprofen used for?",
        "Side effects of Amoxicillin",
        "Can I take Cetirizine with Paracetamol?",
        "How much Aspirin should I take?"
    ]
    
    print("\n🧪 Testing chatbot responses:")
    print("=" * 60)
    for query in test_queries:
        response = chatbot_response(query)
        print(f"Q: {query}")
        print(f"A: {response}")
        print("-" * 50)
    
    # Interactive mode
    print("\n💬 Interactive mode (type 'quit' to exit, 'voice' for voice mode):")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            print("👋 Goodbye! Stay healthy!")
            break
        elif user_input.lower() == 'voice':
            voice_chatbot()
        elif user_input:
            response = chatbot_response(user_input)
            print(f"Bot: {response}")