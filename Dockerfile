# Use an official Python runtime as a parent image
FROM python:3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir data

# Copy the rest of the application code to the working directory
COPY static/ ./static/
COPY templates/ ./templates/
COPY *.py .
COPY *.yaml .

# Expose the Flask app port
EXPOSE 8000

# Run Gunicorn to serve the Flask app
CMD ["gunicorn", "--workers=4", "--bind", "0.0.0.0:8000", "web:app"]