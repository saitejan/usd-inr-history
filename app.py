from flask import Flask, render_template, request, send_file
import PyPDF2
import requests
import pandas as pd
import io
import re

app = Flask(__name__)

def find_tt_rate(input_date):
    base_url = "https://raw.githubusercontent.com/sahilgupta/sbi-fx-ratekeeper/main/pdf_files"
    year, month, day = input_date.split("-")
    correct_url = f'{base_url}/{year}/{month.lstrip("0")}/{year}-{month}-{day}.pdf'
    pdf_file = requests.get(correct_url)
    pdf_file_like = io.BytesIO(pdf_file.content)
    reader = PyPDF2.PdfReader(pdf_file_like)
    text = ""

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    rows = text.split("\n")
    df = pd.DataFrame(rows, columns=["Raw Text"])
    text_to_fetch = df[df["Raw Text"].str.contains("USD")]["Raw Text"].values[0]
    exchange_rate = re.search(r"USD/INR (\d+\.\d+)", text_to_fetch).group(1)
    return exchange_rate, correct_url

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        date_input = request.form["date"]
        try:
            exchange_rate, pdf_url = find_tt_rate(date_input)
            # Download the PDF for the user
            pdf_response = requests.get(pdf_url)
            pdf_io = io.BytesIO(pdf_response.content)
            return render_template("index.html", exchange_rate=exchange_rate, pdf_url=pdf_url, date=date_input)
        except Exception as e:
            return render_template("index.html", error=f"Error fetching data: Not available or invalid date.")
    return render_template("index.html", exchange_rate=None)

@app.route("/download_pdf")
def download_pdf():
    date_input = request.args.get("date")
    _, pdf_url = find_tt_rate(date_input)
    pdf_response = requests.get(pdf_url)
    pdf_io = io.BytesIO(pdf_response.content)
    return send_file(pdf_io, as_attachment=True, download_name=f"{date_input}_USD_INR.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
