FROM python:3.12
WORKDIR /app

RUN mkdir /build
# Chrome and chromedriver stuff
RUN curl https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chrome-linux64.zip --output /build/chrome.zip
RUN cd /build/ && unzip chrome.zip
RUN curl https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.85/linux64/chromedriver-linux64.zip --output /build/chromedriver.zip
RUN cd /build/ && unzip chromedriver.zip
RUN wget https://dl-ssl.google.com/linux/linux_signing_key.pub -O /tmp/google.pub
RUN gpg --no-default-keyring --keyring /etc/apt/keyrings/google-chrome.gpg --import /tmp/google.pub
RUN echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list
RUN apt-get -y update && apt-get install -y libnss3 google-chrome-stable
RUN rm /opt/google/chrome/chrome && mv /build/chrome-linux64/chrome /build/chrome-linux64/chrome-exec && mv /build/chromedriver-linux64/chromedriver /build/chrome-linux64/chromedriver
COPY docker/chrome /build/chrome-linux64/chrome
RUN chmod +x /build/chrome-linux64/chrome

# Crontab stuff
RUN apt-get -y install cron
ENV PATH="${PATH}:/build/chrome-linux64"
COPY docker/crontab /etc/crontab.sh
RUN sh /etc/crontab.sh
RUN chmod u+s /usr/sbin/cron
RUN mkdir /logs

COPY REQUIRE.txt /app/REQUIRE.txt
RUN python -m pip install -r REQUIRE.txt
COPY . /app
CMD ["python", "bot.py"]