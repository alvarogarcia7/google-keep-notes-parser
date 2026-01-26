FROM ubuntu:22.04
RUN apt update
RUN apt install -y python-is-python3 python3-pip
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "kim.py", "--help"]
