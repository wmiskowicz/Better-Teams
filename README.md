# Better Teams

## Project Overview

Better Teams is a Python application designed to improve team coordination and productivity. The project is built to run on Windows systems and includes a simple launch flow for development and testing.

## Features

- Easy setup using a Python virtual environment
- Simple execution of the main application entry point
- Designed for local development on Windows

## Requirements

- Python 3.13 or newer
- Windows 10 / Windows 11
- PowerShell

## Installation and Setup

Open PowerShell in the project folder and run the following commands:

```ps
python -m venv venv
```

```ps
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

```ps
.\venv\Scripts\Activate.ps1
```

This creates and activates a virtual environment for the project.

## Running the Application

With the virtual environment active, start the application by running:

```ps
python.exe main.py
```

## Notes

- If the project contains any dependencies, install them inside the virtual environment using `pip install -r requirements`.
- If `main.py` is the application entry point, ensure it is present in the project root before running.

## Project Structure

A basic project structure might include:

- `main.py` - application entry point
- `README.md` - project documentation
- `requirements` - dependency list (optional)
- `venv/` - virtual environment directory (created locally)
