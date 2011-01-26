import logging

from pylons import url, request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect

from openbiblio.lib.base import BaseController, render
import openbiblio.model as model

log = logging.getLogger(__name__)

class AccountController(BaseController):
    def index(self):
        c.accounts = [ model.Account.get(id_) for id_ in model.Account.find() ]
        return render('account/index.html')

    def view(self, id):
        c.is_myself = (id == c.user)
        # HACK: (should have a better way to tell if not really an account)
        c.account = model.Account.get(c.user)
        if not c.account.openid:
            c.account = None
        return render('account/view.html')

    def login(self):
        if c.user:
            redirect(url(controller='account', action='index', id=None))
        else:
            c.error = request.params.get('error', '')
            form = render('account/openid_form.html')
            # /login_openid page need not exist -- request gets intercepted by openid plugin
            form = form.replace('FORM_ACTION', '/login_openid')
            return form

    def logout(self):
        if c.user:
            redirect('/logout_openid')
        c.user = None
        return render('account/logout.html')

