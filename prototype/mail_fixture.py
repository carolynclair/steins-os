#!/usr/bin/python3
"""LOCAL TEST FIXTURE ONLY. Not shipped in the desktop package.

Uses Dovecot IMAP and aiosmtpd. No relaying or external delivery code.
Run setup as the disposable guest's observer; run --serve afterward.
"""
import argparse
import email
from email.message import EmailMessage
from email.utils import formatdate
import json
import mailbox
from pathlib import Path
import shutil
import subprocess
import time

ap = argparse.ArgumentParser()
ap.add_argument('--serve', action='store_true')
a = ap.parse_args()
assert subprocess.check_output(['systemd-detect-virt', '--vm'], text=True).strip() in ('kvm', 'qemu')
assert Path('/etc/hostname').read_text().strip() == 'steins-prototype'
root = Path.home() / '.local/share/steins-mail-fixture'
root.mkdir(parents=True, exist_ok=True)
store = mailbox.Maildir(root / 'mail', create=True)

if a.serve:
    from aiosmtpd.controller import Controller
    class Handler:
        async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
            if address.lower() not in ('observer@lab.invalid', 'recipient@lab.invalid'):
                return '550 Local synthetic recipients only'
            envelope.rcpt_tos.append(address)
            return '250 OK'
        async def handle_DATA(self, server, session, envelope):
            key = store.add(envelope.content)
            msg = email.message_from_bytes(envelope.content)
            print(json.dumps({'delivered': key, 'subject': msg.get('Subject'), 'recipients': envelope.rcpt_tos}), flush=True)
            return '250 Stored in local fixture'
    controller = Controller(Handler(), hostname='127.0.0.1', port=1025)
    controller.start()
    print('Fixture SMTP listening on 127.0.0.1:1025; no relay', flush=True)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        controller.stop()
else:
    conf = '''dovecot_config_version = 2.4.0
dovecot_storage_version = 2.4.0
protocols {
  imap = yes
}
listen = 127.0.0.1
ssl = no
auth_allow_cleartext = yes
auth_mechanisms = plain login
mail_driver = maildir
mail_home = HOME
mail_path = HOME/mail
mail_uid = 1000
mail_gid = 1000
namespace inbox {
  inbox = yes
  separator = /
}
passdb static {
  password = {PLAIN}fixture-only
}
userdb static {
  fields {
    uid = 1000
    gid = 1000
    home = HOME
  }
}
service imap-login {
  inet_listener imap {
    port = 1143
  }
  inet_listener imaps {
    port = 0
  }
}
'''.replace('HOME', str(root))
    (root / 'dovecot.conf').write_text(conf)
    profile = root / 'thunderbird'
    if profile.exists(): raise SystemExit('Fixture profile already exists; preserving it')
    profile.mkdir()
    (profile / 'extensions').mkdir()
    theme_id = '{a170e392-21f1-4ca2-9600-ddcc318894ba}'
    shutil.copyfile('/usr/share/steins-prototype/dmail-laboratory.xpi', profile / 'extensions' / (theme_id + '.xpi'))
    prefs = {
        'mail.accountmanager.accounts': 'account1,account2',
        'mail.accountmanager.defaultaccount': 'account1', 'mail.accountmanager.localfoldersserver': 'server2',
        'mail.account.account1.server': 'server1', 'mail.account.account1.identities': 'id1',
        'mail.account.account2.server': 'server2',
        'mail.server.server1.type': 'imap', 'mail.server.server1.hostname': '127.0.0.1',
        'mail.server.server1.port': 1143, 'mail.server.server1.userName': 'observer@lab.invalid',
        'mail.server.server1.name': 'D-Mail laboratory', 'mail.server.server1.socketType': 0,
        'mail.server.server1.authMethod': 3, 'mail.server.server1.login_at_startup': True,
        'mail.server.server1.directory': str(profile / 'ImapMail/127.0.0.1'),
        'mail.server.server1.check_new_mail': True, 'mail.server.server1.check_time': 1,
        'mail.server.server2.type': 'none', 'mail.server.server2.hostname': 'Local Folders',
        'mail.server.server2.userName': 'nobody', 'mail.server.server2.directory': str(profile / 'Mail/Local Folders'),
        'mail.identity.id1.fullName': 'Laboratory Observer', 'mail.identity.id1.useremail': 'observer@lab.invalid',
        'mail.identity.id1.smtpServer': 'smtp1', 'mail.identity.id1.doFcc': False,
        'mail.smtpservers': 'smtp1', 'mail.smtp.defaultserver': 'smtp1',
        'mail.smtpserver.smtp1.hostname': '127.0.0.1', 'mail.smtpserver.smtp1.port': 1025,
        'mail.smtpserver.smtp1.authMethod': 1, 'mail.smtpserver.smtp1.try_ssl': 0,
        'mail.shell.checkDefaultClient': False, 'mail.provider.suppress_dialog_on_startup': True,
        'mailnews.start_page.enabled': False, 'mail.warn_on_send_accel_key': False,
        'app.donation.eoy.version.viewed': 999, 'datareporting.policy.dataSubmissionEnabled': False,
        'extensions.autoDisableScopes': 0, 'extensions.activeThemeID': theme_id,
    }
    (profile / 'user.js').write_text('\n'.join('user_pref(%s, %s);' % (json.dumps(k), json.dumps(v)) for k,v in prefs.items()) + '\n')
    seed = EmailMessage()
    seed['From'] = 'Future Gadget Laboratory <recipient@lab.invalid>'
    seed['To'] = 'Laboratory Observer <observer@lab.invalid>'
    seed['Date'] = formatdate(localtime=True)
    seed['Subject'] = 'Welcome to the laboratory'
    seed.set_content('The local mail experiment is ready.\n\nThis is a synthetic message in a disposable VM. '
                     'Use Compose, Reply, Search and attachments as usual. Thunderbird handles the mail; '
                     'the D-Mail theme only changes appearance.\n\nNo real account is connected.\n')
    store.add(seed)
    (root / 'fixture-attachment.txt').write_text('Steins local mail fixture attachment.\n')
    print(root)
