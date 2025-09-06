FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . /myproject
WORKDIR /myproject

# Create data directory structure for database and media files
RUN mkdir -p /myproject/data/media

RUN pip install --no-cache-dir -r requirements.txt

# Make run.sh executable
RUN chmod +x run.sh

# Declare volume for persistent data (database and media files)
# Recommended volume name: cashya-shoppy-data
VOLUME ["/myproject/data"]

# Add label with recommended volume name
LABEL volume.data.name="cashya-shoppy-data"
LABEL volume.data.path="/myproject/data"
LABEL volume.data.description="Contains SQLite database and media files"

EXPOSE 5025

CMD ["./run.sh"]
