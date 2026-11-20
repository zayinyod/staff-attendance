FROM mcr.microsoft.com/devcontainers/python:3-3.12-trixie

ARG USERNAME=vscode

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alias/.alias /home/$USERNAME
RUN cat /home/$USERNAME/.alias >> /home/$USERNAME/.bashrc
