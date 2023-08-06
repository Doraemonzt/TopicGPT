import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import tiktoken
import openai
from typing import Callable
import numpy as np

basic_instruction =  "You are a helpful assistant. You are excellent at inferring topics from top-words extracted via topic-modelling. You make sure that everything you output is strictly based on the provided text."

class TopwordEnhancement:
    
    def __init__(self, openai_key: str, openai_model: str = "gpt-3.5-turbo", max_context_length = 4000, openai_model_temperature:float = 0.5, basic_model_instruction: str = basic_instruction, corpus_instruction: str = ""):
        """
        params:
            openai_key: your openai key
            openai_model: the openai model to use
            max_context_length: the maximum length of the context for the openai model
            openai_model_temperature: the softmax temperature to use for the openai model
            basic_model_instruction: the basic instruction for the model
            corpus_instruction: the instruction for the corpus. Useful if specific information on the corpus on hand is available
        """
        self.openai_key = openai_key
        self.openai_model = openai_model
        self.max_context_length = max_context_length
        self.openai_model_temperature = openai_model_temperature
        self.basic_model_instruction = basic_model_instruction
        self.corpus_instruction = corpus_instruction

    def __str__(self) -> str:
        repr = f"TopwordEnhancement(openai_model = {self.openai_model})"
        return repr

    def __repr__(self) -> str:
        repr = f"TopwordEnhancement(openai_model = {self.openai_model})"
        return repr
    
    def count_tokens_api_message(self, messages: list[dict[str]]) -> int:
        """
        Count the number of tokens in the API message
        params:
            message: the message from the API
        returns:
            number of tokens in the message
        """
        encoding = tiktoken.encoding_for_model(self.openai_model)
        n_tokens = 0
        for message in messages: 
            for key, value in message.items():
                if key == "content":
                    n_tokens += len(encoding.encode(value))
        
        return n_tokens
    
    def describe_topic_topwords_completion_object(self, 
                               topwords: list[str], 
                               n_words: int = None,
                               query_function: Callable = lambda tws: f"Please give me the common topic of those words: {tws}. Also describe the various aspects and sub-topics of the topic.") -> openai.ChatCompletion:
        """
        Describe the given topic based on its topwords by using the openai model. The given query is used together with the base query to query the model.
        params:
            topwords: list of topwords
            n_words: number of words to use for the query. If None, all words are used
            query_function: function to query the model. The function should take a list of topwords and return a string
        returns:
            A description of the topics by the model in form of an openai.ChatCompletion object
        """
        if n_words is None:
            n_words = len(topwords)
        topwords = topwords[:n_words]
        topwords = np.array(topwords)

        # if too many topwords are given, use only the first part of the topwords that fits into the context length
        tokens_cumsum = np.cumsum([len(tiktoken.encoding_for_model(self.openai_model).encode(tw + ", ")) for tw in topwords]) + len(tiktoken.encoding_for_model(self.openai_model).encode(self.basic_model_instruction + " " + self.corpus_instruction))
        print(tokens_cumsum[-1])
        if tokens_cumsum[-1] > self.max_context_length:
            print("Too many topwords given. Using only the first part of the topwords that fits into the context length. Number of topwords used: ", np.argmax(tokens_cumsum > self.max_context_length))
            n_words = np.argmax(tokens_cumsum > self.max_context_length)
            topwords = topwords[:n_words]



        completion = openai.ChatCompletion.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content":  self.basic_model_instruction + " " + self.corpus_instruction},
                {"role": "user", "content": query_function(topwords)},
            ],
            temperature = self.openai_model_temperature
        )

        return completion
    
    def describe_topic_topwords_str(self, 
                               topwords: list[str], 
                               n_words: int = None,
                               query_function: Callable = lambda tws: f"Please give me the common topic of those words: {tws}. Also describe the various aspects and sub-topics of the topic.") -> str:
        """
        Describe the given topic based on its topwords by using the openai model. The given query is used together with the base query to query the model.
        params:
            topwords: list of topwords
            n_words: number of words to use for the query. If None, all words are used
            query_function: function to query the model. The function should take a list of topwords and return a string
        returns:
            A description of the topics by the model in form of a string
        """
        completion = self.describe_topic_topwords_completion_object(topwords, n_words, query_function)
        return completion.choices[0].message["content"]
