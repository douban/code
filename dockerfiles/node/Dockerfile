FROM node:0.10

RUN apt-get update && apt-get install -y --no-install-recommends \
    ruby-dev \
    rubygems
RUN gem install compass -V

RUN mkdir /code \
        /node_modules
ADD package.json /code/package.json

WORKDIR /code
RUN npm install \
    && cp -R node_modules /

ENV PATH=/code/node_modules/.bin:/code/node_modules/grunt-cli/bin:${PATH}
