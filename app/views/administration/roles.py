#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Routes for managing roles.
"""

from flask import render_template
from flask_login import login_required

from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile.decorators import permission_required
from app.views.administration import bp


@bp.route('/roles')
@permission_required(Permission.EditRole)
@login_required
def roles() -> str:
    """
         Show a list of all roles.

         :return: The HTML response.
    """
    return render_template('administration/roles.html', title=_('Roles'))
