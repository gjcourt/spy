import os
from distutils.core import setup

templates_base = 'spy/templates'
template_files = [os.path.join(templates_base, fn) for fn in os.listdir(templates_base)]

setup(
    name='spy',
    description='Super simple monitoring for long running jobs',
    author='George Courtsunis',
    author_email='gjcourt@gmail.com',
    url='http://github.com/gjcourt/spy',
    version='0.1.1.4',
    packages=['spy', 'spy.server'],
    data_files=[
        # ('spy/server/templates', ['spy/templates/monitor.html']),
        ('/usr/local/spy/templates', template_files),
    ],
    requires=['Flask (==0.8)']
    )

