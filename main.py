from website import create_app
from flask import render_template, request

app = create_app()

@app.route('/',methods = ['GET','POST'])
def home():
    if request.method == 'POST':
        archivo = request.form['archivo_java']
        
    return render_template('home.html')

if __name__ ==  '__main__':
    app.run(debug=True)



