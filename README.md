# Presenter
Pilot your presentations with ease

## Description
Presenter allows you to easily control presentations remotely with a minimal remote control style interface.
The project was born from the need to present my slides in a comfortable and simple way for the high school exam.

## Usage
First of all install the necessary dependencies:<br>
`$ pip3 install -r requirements.txt`

For quick use with Flask use:
`$ python3 presenter.py -f`

For production deployment it is recommended to use a production WSGI server like [Gunicorn](https://github.com/benoitc/gunicorn):
`$ gunicorn presenter:app`

## IMPORTANT
Before expose the presentation make sure you have **changed** the **auth token** for the host and the **Flask secret key** in `config.py`
```
"auth_token": "EQGw6oFdVqsiKiojZLWph8nWRzbfr0",
"secret_key": "TleEM9bQHPcGmB8BSzeWllwPAx745c",
```

## Add a new presentation
`$ python3 presenter.py -n "Presentation Name"`
After that, you will be able to upload the presentation images to the created folder `static/images/Presentation_Name`

## Delete a presentation
`$ python3 presenter.py -d "Presentation Name"`

## Manage a presentation
After creating a presentation, you will have to use the auth token to start a presentation from the host page
