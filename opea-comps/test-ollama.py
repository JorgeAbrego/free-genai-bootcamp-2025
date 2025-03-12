from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama',
)

def llm(prompt):
    response = client.chat.completions.create(
        # Set model to gemma:2b running on local ollama
        model='llama3.2:1b',
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

print(llm("Hi, how are you?"))
