import gradio as gr

def greet(name):
    return f"Hello, {name}!"

iface = gr.Interface(fn=greet, inputs="text", outputs="text")

if __name__ == "main":
    iface.launch(server_name="0.0.0.0", server_port=7860, share=True)