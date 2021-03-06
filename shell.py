# -*- coding: utf-8 -*-

import os
from flask import g
from flask.ext.script import Manager, prompt, prompt_pass, prompt_bool, Server
from funfunsay import create_app


app = create_app()
manager = Manager(app)

project_root_path = os.path.join(os.path.dirname(app.root_path))


@manager.command
def run():
    """Run local server."""
    app.run()
    #@faq:allow internet access
    #for test OAuth2
    #app.run(host='0.0.0.0', port=80)



manager.add_option('-c', '--config',
                   dest="config",
                   required=False,
                   help="config file")
# Turn on debugger by default and reloader
manager.add_command("runserver", Server(
    use_debugger = True,
    use_reloader = True)
    )
if __name__ == "__main__":
    manager.run()
    #manager.run(host='0.0.0.0', port=80)
