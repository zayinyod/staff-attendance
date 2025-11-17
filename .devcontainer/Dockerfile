FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

ARG USERNAME=vscode

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alias/.alias /home/$USERNAME
RUN cat /home/$USERNAME/.alias >> /home/$USERNAME/.bashrc
