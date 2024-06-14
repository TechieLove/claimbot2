# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make the start.sh script executable
RUN chmod +x start.sh

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run start.sh when the container launches
CMD ["./start.sh"]
