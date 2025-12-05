from flask import Flask,render_template,request,session,redirect,url_for
from app.components.retriever import create_qa_chain
from dotenv import load_dotenv
import os

load_dotenv()
HF_TOKEN = os.environ.get("HF_TOKEN")

app = Flask(__name__)
app.secret_key = os.urandom(24)

from markupsafe import Markup
def nl2br(value):
    return Markup(value.replace("\n" , "<br>\n"))

app.jinja_env.filters['nl2br'] = nl2br

@app.route("/", methods=["GET","POST"])
def index():
    if "messages" not in session:
        session["messages"]=[]

    messages = session["messages"]

    if request.method=="POST":
        user_input = request.form.get("prompt")

        if user_input:

            messages.append({"role" : "user" , "content":user_input})
            session["messages"] = messages
            

            langchain_history = [] 
            
            history_length = len(messages) - 1 

            for i in range(0, history_length, 2):
                user_msg = messages[i]["content"]    
                assistant_msg = messages[i+1]["content"] 
                langchain_history.append((user_msg, assistant_msg))

            try:
                qa_chain = create_qa_chain()
                response = qa_chain.invoke({
                    "question": user_input, 
                    "chat_history": langchain_history 
                })
                
                result = response.get("answer" , "I could not find a relevant answer in my knowledge base.")

                messages.append({"role" : "assistant" , "content" : result})
                session["messages"] = messages

            except Exception as e:
                messages.pop()
                session["messages"] = messages
                error_msg = f"Error processing request: {str(e)}"
                return render_template("index.html" , messages = session["messages"] , error = error_msg)
            
            return redirect(url_for("index"))
            
    return render_template("index.html" , messages=session.get("messages" , []))

@app.route("/clear")
def clear():
    session.pop("messages" , None)
    return redirect(url_for("index"))

if __name__=="__main__":
    app.run(host="0.0.0.0" , port=5000 , debug=False , use_reloader = False)