FROM python:3.9

WORKDIR /app

COPY . /app

RUN pip install nb-cli \
    && pip install -r requirements.txt

RUN curl -fsSL https://deno.land/x/install/install.sh | sh

CMD ["nb", "run", "--reload"]
