# set base image (host OS)
FROM python:3.10

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY ./shiny-first-steps/qr-code-display.py .
COPY ./waiting-for-checkin.png .

# command to run on container start
CMD [ "sh", "-c", "shiny run --host 0.0.0.0 ./qr-code-display.py" ]

EXPOSE 5000
EXPOSE 8000