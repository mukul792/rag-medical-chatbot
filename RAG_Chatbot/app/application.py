from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from markupsafe import Markup
from dotenv import load_dotenv
import os

from app.components.retriever import create_qa_chain

load_dotenv()
HF_TOKEN = os.environ.get("HF_TOKEN")

app = FastAPI()

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

templates = Jinja2Templates(directory="templates")


def nl2br(value):
    return Markup(value.replace("\n", "<br>\n"))

templates.env.filters["nl2br"] = nl2br


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    if "messages" not in request.session:
        request.session["messages"] = []

    messages = request.session["messages"]

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "messages": messages}
    )


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, prompt: str = Form(...)):

    if "messages" not in request.session:
        request.session["messages"] = []

    messages = request.session["messages"]

    user_input = prompt

    if user_input:

        messages.append({"role": "user", "content": user_input})
        request.session["messages"] = messages

        langchain_history = []

        history_length = len(messages) - 1

        for i in range(0, history_length, 2):
            user_msg = messages[i]["content"]
            assistant_msg = messages[i + 1]["content"]
            langchain_history.append((user_msg, assistant_msg))

        try:
            qa_chain = create_qa_chain()

            response = qa_chain.invoke({
                "question": user_input,
                "chat_history": langchain_history
            })

            result = response.get(
                "answer",
                "I could not find a relevant answer in my knowledge base."
            )

            messages.append({"role": "assistant", "content": result})
            request.session["messages"] = messages

        except Exception as e:
            messages.pop()
            request.session["messages"] = messages

            error_msg = f"Error processing request: {str(e)}"

            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "messages": request.session["messages"],
                    "error": error_msg
                }
            )

    return RedirectResponse(url="/", status_code=303)


@app.get("/clear")
async def clear(request: Request):
    request.session.pop("messages", None)
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
