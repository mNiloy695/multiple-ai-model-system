# # ai_model/summerize.py

# from sumy.parsers.plaintext import PlaintextParser
# from sumy.nlp.tokenizers import Tokenizer
# from sumy.summarizers.text_rank import TextRankSummarizer
# import nltk


# try:
#     nltk.data.find('tokenizers/punkt')
# except LookupError:
#     nltk.download('punkt')
#     nltk.download('punkt_tab')

# def local_summarize(text, num_sentences=4):

    
#     if not text or text.strip() == "":
#         return ""
    

#     sentence_count = len([s for s in text.split('.') if s.strip()])
#     if sentence_count <= num_sentences:
#         return text
    
#     try:
    
#         parser = PlaintextParser.from_string(text, Tokenizer("english"))
#         summarizer = TextRankSummarizer()
#         summary = summarizer(parser.document, num_sentences)
        
      
#         result = " ".join([str(sentence) for sentence in summary])
#         return result
        
#     except Exception as e:
        
#         print(f"Summarization error: {e}")
#         sentences = [s.strip() for s in text.split('.') if s.strip()]
#         return '\n'.join(sentences[:num_sentences]) + '.'

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk
def local_summarize(text, max_lines=3, chars_per_line=80):
    if not text or text.strip() == "":
        return ""

    sentence_count = len([s for s in text.split('.') if s.strip()])
    if sentence_count <= max_lines:
        return text

    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary_sentences = summarizer(parser.document, sentence_count)
        summary_text = " ".join([str(sentence) for sentence in summary_sentences])

        # Split into lines of approx chars_per_line
        lines = []
        current_line = ""
        for word in summary_text.split():
            if len(current_line) + len(word) + 1 <= chars_per_line:
                current_line += (" " if current_line else "") + word
            else:
                lines.append(current_line)
                current_line = word
            if len(lines) >= max_lines:
                break
        if current_line and len(lines) < max_lines:
            lines.append(current_line)

        return "\n".join(lines)

    except Exception as e:
        print(f"Summarization error: {e}")
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        return '\n'.join(sentences[:max_lines]) + '.'
