"""
Developed by Michael Habashy
"""

from flask import Flask

app = Flask(__name__)
app.secret_key = 'SOME SECRET KEY HERE'



from filesystem import config # File that would contain server information and passwords - Different on server then local and not on github

import filesystem.views
import filesystem.api
import filesystem.filesystem
import filesystem.ad

