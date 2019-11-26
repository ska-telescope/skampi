#!/bin/bash

function dev() {
        virtualenv venv
        source venv/bin/activate
        pip install pipenv
        pipenv install
}

dev
