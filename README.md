celery -A CheckSiteOut worker --loglevel=info --pool=solo
celery -A CheckSiteOut  beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
python manage.py runserver
python -m CheckSiteOut.bot