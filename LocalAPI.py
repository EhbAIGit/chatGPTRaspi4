from gpt4all import GPT4All
#model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf") # downloads / loads a 4.66GB LLM
model = GPT4All("Phi-3-mini-4k-instruct.Q4_0.gguf") # downloads / loads a 4.66GB LLM

with model.chat_session():
    print(model.generate("Hoe gaat het met jou?", max_tokens=512))