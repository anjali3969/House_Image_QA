# House Image QA API
 - A FastAPI-based application that analyzes house images and answers structured questions using Google Gemini Vision.
 - This system validates images, processes them using AI vision, and returns structured JSON outputs for house inspection, remodeling, or assessment workflows.

## Features
- Upload house images
- Image validation
- AI-powered image analysis using Gemini
- Structured JSON response based on graph rules
- FastAPI REST API

## Flow Chart

<img width="527" height="740" alt="image" src="https://github.com/user-attachments/assets/dbef2e6a-bef3-4746-91b4-149da4481b75" />


## Project Structure

<img width="665" height="355" alt="image" src="https://github.com/user-attachments/assets/2e725e61-c59e-4303-a3da-19de7094a519" />

## Create virtual environment

### Windows
python -m venv env 

env\Scripts\activate

### MAC
python -m venv env 

source env/bin/activate

## Install dependencies

pip install -r requirements.txt

## Run the Application
uvicorn main:app --reload

Server will start at:
http://127.0.0.1:8000
