FROM python:3
# Set application working directory
WORKDIR /usr/src/app
# Install application
COPY *.py ./
# Run application
CMD python server.py
EXPOSE 3000