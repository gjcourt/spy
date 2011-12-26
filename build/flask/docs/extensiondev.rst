Flask Extension Development
===========================

Flask, being a microframework, often requires some repetitive steps to get
a third party library working.  Because very often these steps could be
abstracted to support multiple projects the `Flask Extension Registry`_
was created.

If you want to create your own Flask extension for something that does not
exist yet, this guide to extension development will help you get your
extension running in no time and to feel like users would expect your
extension to behave.

.. _Flask Extension Registry: http://flask.pocoo.org/extensions/

Anatomy of an Extension
-----------------------

Extensions are all located in a package called ``flask_something``
where "something" is the name of the library you want to bridge.  So for
example if you plan to add support for a library named `simplexml` to
Flask, you would name your extension's package ``flask_simplexml``.

The name of the actual extension (the human readable name) however would
be something like "Flask-SimpleXML".  Make sure to include the name
"Flask" somewhere in that name and that you check the capitalization.
This is how users can then register dependencies to your extension in
their `setup.py` files.

Flask sets up a redirect package called :data:`flask.ext` where users
should import the extensions from.  If you for instance have a package
called ``flask_something`` users would import it as
``flask.ext.something``.  This is done to transition from the old
namespace packages.  See :ref:`ext-import-transition` for more details.

But how do extensions look like themselves?  An extension has to ensure
that it works with multiple Flask application instances at once.  This is
a requirement because many people will use patterns like the
:ref:`app-factories` pattern to create their application as needed to aid
unittests and to support multiple configurations.  Because of that it is
crucial that your application supports that kind of behaviour.

Most importantly the extension must be shipped with a `setup.py` file and
registered on PyPI.  Also the development checkout link should work so
that people can easily install the development version into their
virtualenv without having to download the library by hand.

Flask extensions must be licensed as BSD or MIT or a more liberal license
to be enlisted on the Flask Extension Registry.  Keep in mind that the
Flask Extension Registry is a moderated place and libraries will be
reviewed upfront if they behave as required.

"Hello Flaskext!"
-----------------

So let's get started with creating such a Flask extension.  The extension
we want to create here will provide very basic support for SQLite3.

First we create the following folder structure::

    flask-sqlite3/
        flask_sqlite3.py
        LICENSE
        README

Here's the contents of the most important files:

setup.py
````````

The next file that is absolutely required is the `setup.py` file which is
used to install your Flask extension.  The following contents are
something you can work with::

    """
    Flask-SQLite3
    -------------

    This is the description for that library
    """
    from setuptools import setup


    setup(
        name='Flask-SQLite3',
        version='1.0',
        url='http://example.com/flask-sqlite3/',
        license='BSD',
        author='Your Name',
        author_email='your-email@example.com',
        description='Very short description',
        long_description=__doc__,
        py_modules=['flask_sqlite3'],
        # if you would be using a package instead use packages instead
        # of py_modules:
        # packages=['flask_sqlite3'],
        zip_safe=False,
        include_package_data=True,
        platforms='any',
        install_requires=[
            'Flask'
        ],
        classifiers=[
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'Topic :: Software Development :: Libraries :: Python Modules'
        ]
    )

That's a lot of code but you can really just copy/paste that from existing
extensions and adapt.

flask_sqlite3.py
````````````````

Now this is where your extension code goes.  But how exactly should such
an extension look like?  What are the best practices?  Continue reading
for some insight.

Initializing Extensions
-----------------------

Many extensions will need some kind of initialization step.  For example,
consider your application is currently connecting to SQLite like the
documentation suggests (:ref:`sqlite3`) you will need to provide a few
functions and before / after request handlers.  So how does the extension
know the name of the application object?

Quite simple: you pass it to it.

There are two recommended ways for an extension to initialize:

initialization functions:
    If your extension is called `helloworld` you might have a function
    called ``init_helloworld(app[, extra_args])`` that initializes the
    extension for that application.  It could attach before / after
    handlers etc.

classes:
    Classes work mostly like initialization functions but can later be
    used to further change the behaviour.  For an example look at how the
    `OAuth extension`_ works: there is an `OAuth` object that provides
    some helper functions like `OAuth.remote_app` to create a reference to
    a remote application that uses OAuth.

What to use depends on what you have in mind.  For the SQLite 3 extension
we will use the class based approach because it will provide users with a
manager object that handles opening and closing database connections.

The Extension Code
------------------

Here's the contents of the `flask_sqlite3.py` for copy/paste::

    from __future__ import absolute_import
    import sqlite3

    from flask import _request_ctx_stack

    class SQLite3(object):

        def __init__(self, app):
            self.app = app
            self.app.config.setdefault('SQLITE3_DATABASE', ':memory:')
            self.app.teardown_request(self.teardown_request)
            self.app.before_request(self.before_request)

        def connect(self):
            return sqlite3.connect(self.app.config['SQLITE3_DATABASE'])

        def before_request(self):
            ctx = _request_ctx_stack.top
            ctx.sqlite3_db = self.connect()

        def teardown_request(self, exception):
            ctx = _request_ctx_stack.top
            ctx.sqlite3_db.close()

        def get_db(self):
            ctx = _request_ctx_stack.top
            if ctx is not None:
                return ctx.sqlite3_db

So here's what these lines of code do:

1.  The ``__future__`` import is necessary to activate absolute imports.
    Otherwise we could not call our module `sqlite3.py` and import the
    top-level `sqlite3` module which actually implements the connection to
    SQLite.
2.  We create a class for our extension that requires a supplied `app` object,
    sets a configuration for the database if it's not there
    (:meth:`dict.setdefault`), and attaches `before_request` and
    `teardown_request` handlers.
3.  Next, we define a `connect` function that opens a database connection.
4.  Then we set up the request handlers we bound to the app above.  Note here
    that we're attaching our database connection to the top request context via
    `_request_ctx_stack.top`. Extensions should use the top context and not the
    `g` object to store things like database connections.
5.  Finally, we add a `get_db` function that simplifies access to the context's
    database.

So why did we decide on a class based approach here?  Because using our
extension looks something like this::

    from flask import Flask
    from flask_sqlite3 import SQLite3

    app = Flask(__name__)
    app.config.from_pyfile('the-config.cfg')
    manager = SQLite3(app)
    db = manager.get_db()

You can then use the database from views like this::

    @app.route('/')
    def show_all():
        cur = db.cursor()
        cur.execute(...)

Opening a database connection from outside a view function is simple.

>>> from yourapplication import db
>>> cur = db.cursor()
>>> cur.execute(...)

Adding an `init_app` Function
-----------------------------

In practice, you'll almost always want to permit users to initialize your
extension and provide an app object after the fact. This can help avoid
circular import problems when a user is breaking their app into multiple files.
Our extension could add an `init_app` function as follows::

    class SQLite3(object):

        def __init__(self, app=None):
            if app is not None:
                self.app = app
                self.init_app(self.app)
            else:
                self.app = None

        def init_app(self, app):
            self.app = app
            self.app.config.setdefault('SQLITE3_DATABASE', ':memory:')
            self.app.teardown_request(self.teardown_request)
            self.app.before_request(self.before_request)

        def connect(self):
            return sqlite3.connect(app.config['SQLITE3_DATABASE'])

        def before_request(self):
            ctx = _request_ctx_stack.top
            ctx.sqlite3_db = self.connect()

        def teardown_request(self, exception):
            ctx = _request_ctx_stack.top
            ctx.sqlite3_db.close()

        def get_db(self):
            ctx = _request_ctx_stack.top
            if ctx is not None:
                return ctx.sqlite3_db

The user could then initialize the extension in one file::

    manager = SQLite3()

and bind their app to the extension in another file::

    manager.init_app(app)

End-Of-Request Behavior
-----------------------

Due to the change in Flask 0.7 regarding functions that are run at the end
of the request your extension will have to be extra careful there if it
wants to continue to support older versions of Flask.  The following
pattern is a good way to support both::

    def close_connection(response):
        ctx = _request_ctx_stack.top
        ctx.sqlite3_db.close()
        return response

    if hasattr(app, 'teardown_request'):
        app.teardown_request(close_connection)
    else:
        app.after_request(close_connection)

Strictly speaking the above code is wrong, because teardown functions are
passed the exception and typically don't return anything.  However because
the return value is discarded this will just work assuming that the code
in between does not touch the passed parameter.

Learn from Others
-----------------

This documentation only touches the bare minimum for extension
development.  If you want to learn more, it's a very good idea to check
out existing extensions on the `Flask Extension Registry`_.  If you feel
lost there is still the `mailinglist`_ and the `IRC channel`_ to get some
ideas for nice looking APIs.  Especially if you do something nobody before
you did, it might be a very good idea to get some more input.  This not
only to get an idea about what people might want to have from an
extension, but also to avoid having multiple developers working on pretty
much the same side by side.

Remember: good API design is hard, so introduce your project on the
mailinglist, and let other developers give you a helping hand with
designing the API.

The best Flask extensions are extensions that share common idioms for the
API.  And this can only work if collaboration happens early.

Approved Extensions
-------------------

Flask also has the concept of approved extensions.  Approved extensions
are tested as part of Flask itself to ensure extensions do not break on
new releases.  These approved extensions are listed on the `Flask
Extension Registry`_ and marked appropriately.  If you want your own
extension to be approved you have to follow these guidelines:

1.  An approved Flask extension must provide exactly one package or module
    named ``flask_extensionname``.  They might also reside inside a
    ``flaskext`` namespace packages though this is discouraged now.
2.  It must ship a testing suite that can either be invoked with ``make test``
    or ``python setup.py test``.  For test suites invoked with ``make
    test`` the extension has to ensure that all dependencies for the test
    are installed automatically, in case of ``python setup.py test``
    dependencies for tests alone can be specified in the `setup.py`
    file.  The test suite also has to be part of the distribution.
3.  APIs of approved extensions will be checked for the following
    characteristics:

    -   an approved extension has to support multiple applications
        running in the same Python process.
    -   it must be possible to use the factory pattern for creating
        applications.

4.  The license must be BSD/MIT/WTFPL licensed.
5.  The naming scheme for official extensions is *Flask-ExtensionName* or
    *ExtensionName-Flask*.
6.  Approved extensions must define all their dependencies in the
    `setup.py` file unless a dependency cannot be met because it is not
    available on PyPI.
7.  The extension must have documentation that uses one of the two Flask
    themes for Sphinx documentation.
8.  The setup.py description (and thus the PyPI description) has to
    link to the documentation, website (if there is one) and there
    must be a link to automatically install the development version
    (``PackageName==dev``).
9.  The ``zip_safe`` flag in the setup script must be set to ``False``,
    even if the extension would be safe for zipping.
10. An extension currently has to support Python 2.5, 2.6 as well as
    Python 2.7


.. _ext-import-transition:

Extension Import Transition
---------------------------

For a while we recommended using namespace packages for Flask extensions.
This turned out to be problematic in practice because many different
competing namespace package systems exist and pip would automatically
switch between different systems and this caused a lot of problems for
users.

Instead we now recommend naming packages ``flask_foo`` instead of the now
deprecated ``flaskext.foo``.  Flask 0.8 introduces a redirect import
system that lets uses import from ``flask.ext.foo`` and it will try
``flask_foo`` first and if that fails ``flaskext.foo``.

Flask extensions should urge users to import from ``flask.ext.foo``
instead of ``flask_foo`` or ``flaskext_foo`` so that extensions can
transition to the new package name without affecting users.


.. _OAuth extension: http://packages.python.org/Flask-OAuth/
.. _mailinglist: http://flask.pocoo.org/mailinglist/
.. _IRC channel: http://flask.pocoo.org/community/irc/
