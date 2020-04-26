FROM python:3
# Set application working directory
WORKDIR /usr/src/app
# Install application
RUN pip install awscli --upgrade
COPY *.py ./
COPY server.sh ./
# Run application
VOLUME /root/.aws
CMD ./server.sh
EXPOSE 3000