# Use an official Python runtime as a base image
FROM python:3.11
#
# # Working directory in the container
WORKDIR /app
#
# # Copy the current directory contents into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "hiker_competition:app", "--host", "0.0.0.0", "--port", "8000"]