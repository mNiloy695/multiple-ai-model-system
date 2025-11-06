# ai_model/summerize.py

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk


try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')

def local_summarize(text, num_sentences=4):

    
    if not text or text.strip() == "":
        return ""
    

    sentence_count = len([s for s in text.split('.') if s.strip()])
    if sentence_count <= num_sentences:
        return text
    
    try:
    
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary = summarizer(parser.document, num_sentences)
        
      
        result = " ".join([str(sentence) for sentence in summary])
        return result
        
    except Exception as e:
        
        print(f"Summarization error: {e}")
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        return '\n'.join(sentences[:num_sentences]) + '.'